from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from dash_cytoscape import Cytoscape, load_extra_layouts
from os import PathLike
from webbrowser import open as open_url

from dash_app.layout import (
    get_add_vertex_button, get_cytoscape_stylesheet, get_edit_button, get_log
)
from dialogue_editor.graph_editor import GraphEditor
from dialogue_model.codecs import (
    convert_effect_to_text, 
    convert_predicate_to_text, 
    convert_text_to_effect, 
    convert_text_to_predicate
)
from dialogue_viewer.cytoscape_adapter import CytoscapeAdapter

class App(Dash):
    def __init__(self, yaml_file: str | PathLike | None = None) -> None:
        super().__init__()
        self.graph_editor = GraphEditor(yaml_file)
        load_extra_layouts()
        self.layout = html.Div(
            [
                html.Div(
                    get_log()
                    + [html.Hr()]
                    + get_edit_button() 
                    + [html.Hr()] 
                    + get_add_vertex_button() ,
                    style={
                        "width": "320px",
                        "flexShrink": 0,
                        "padding": "12px",
                        "backgroundColor": "#1f252b",
                        "color": "#e6e6e6",
                        "borderRight": "1px solid #444"
                    }
                ),
                html.Div(
                    Cytoscape(
                        id=f"dialogue-graph",
                        layout={"name": "dagre", "rankDir": "TB"},
                        style={
                            "width": "100%", 
                            "height": "100%", 
                            "backgroundColor": "#303841"
                        },
                        elements=self.get_elements(),
                        stylesheet=get_cytoscape_stylesheet()
                    ),
                    style={"flex": "1", "minWidth": 0, "height": "100%"}
                )
            ],
            style={
                "display": "flex", 
                "width": "100vw", 
                "height": "100vh", 
                "overflow": "hidden"
            }
        )
        self.register_callbacks()

    def add_vertex(self, text: str | None) -> str:
        self.graph_editor.add_vertex(text)
        return f"vertex_{self.graph_editor.next_vertex_index-1}"

    def append_action_status(
        self, current_log: str | None, new_message: str
    ) -> str:
        if not current_log:
            return new_message
        return f"{current_log}\n{new_message}"

    def get_elements(self) -> list[dict[str, dict[str, str]]]:
        cytoscape_adapter = CytoscapeAdapter(self.graph_editor.graph)
        return cytoscape_adapter.nodes + cytoscape_adapter.edges

    def get_node_effects(self, node_id: str) -> str:
        if node_id in self.graph_editor.graph.vertex_dict:
            effects = self.graph_editor.graph.vertex_dict[node_id].effects
            return "\n".join(
                convert_effect_to_text(effect) for effect in effects
            )
        if node_id in self.graph_editor.graph.edge_dict:
            effects = self.graph_editor.graph.edge_dict[node_id].effects
            return "\n".join(
                convert_effect_to_text(effect) for effect in effects
            )
        return ""

    def get_node_predicates(self, node_id: str) -> str:
        if node_id in self.graph_editor.graph.edge_dict:
            predicates = self.graph_editor.graph.edge_dict[node_id].predicates
            return "\n".join(
                convert_predicate_to_text(predicate) 
                for predicate in predicates
            )
        return ""

    def get_node_text(self, node_id: str) -> str:
        if node_id in self.graph_editor.graph.vertex_dict:
            return self.graph_editor.graph.vertex_dict[node_id].text
        if node_id in self.graph_editor.graph.edge_dict:
            return self.graph_editor.graph.edge_dict[node_id].text
        return ""

    def parse_effects(self, effects_text: str) -> list[dict[str, str | int]]:
        effects = []
        for line_number, line in enumerate(effects_text.split("\n"), start=1):
            stripped_line = line.strip()
            if not stripped_line:
                continue
            try:
                effects.append(convert_text_to_effect(stripped_line))
            except ValueError as exception:
                raise ValueError(
                    f"Invalid effect on line {line_number}: {stripped_line}"
                ) from exception
        return effects

    def parse_predicates(
        self, predicates_text: str
    ) -> list[dict[str, str | int]]:
        predicates = []
        for line_number, line in enumerate(
            predicates_text.split("\n"), start=1
        ):
            stripped_line = line.strip()
            if not stripped_line:
                continue
            try:
                predicates.append(convert_text_to_predicate(stripped_line))
            except ValueError as exception:
                raise ValueError(
                    f"Invalid predicate on line {line_number}: {stripped_line}"
                ) from exception
        return predicates

    def register_callbacks(self) -> None:
        self.clientside_callback(
            """
            function(actionLog) {
                const logBox = document.getElementById("action-status");
                if (logBox) {
                    window.requestAnimationFrame(function() {
                        logBox.scrollTop = logBox.scrollHeight;
                    });
                }
                return "";
            }
            """,
            Output("action-status-scroll-trigger", "children"),
            Input("action-status", "value")
        )

        @self.callback(
            Output("edit-text", "value"),
            Output("edit-predicates", "value"),
            Output("edit-predicates", "disabled"),
            Output("edit-effects", "value"),
            Input("dialogue-graph", "selectedNodeData")
        )
        def autofill_edit_fields(
            selected_nodes: list[dict] | None
        ) -> tuple[str, str, bool, str]:
            if not selected_nodes:
                return "", "", True, ""
            node_id = selected_nodes[0].get("id")
            if not node_id:
                return "", "", True, ""
            node_text = self.get_node_text(node_id)
            if node_text is None:
                return "", "", True, ""
            is_vertex = node_id in self.graph_editor.graph.vertex_dict
            predicates_text = self.get_node_predicates(node_id)
            effects_text = self.get_node_effects(node_id)
            return node_text, predicates_text, is_vertex, effects_text

        @self.callback(
            Output("selected-node-display", "children"),
            Input("dialogue-graph", "selectedNodeData")
        )
        def display_selected_node(selected_nodes: list[dict] | None) -> str:
            if not selected_nodes:
                return "Selected node: None"
            node_id = selected_nodes[0].get("id", "None")
            return f"Selected node: {node_id}"

        @self.callback(
            Output("dialogue-graph", "elements"),
            Output("action-status", "value"),
            Output("new-vertex-text", "value"),
            Input("save-text", "n_clicks"),
            Input("add-vertex", "n_clicks"),
            State("dialogue-graph", "selectedNodeData"),
            State("edit-text", "value"),
            State("edit-predicates", "value"),
            State("edit-effects", "value"),
            State("new-vertex-text", "value"),
            State("action-status", "value"),
            prevent_initial_call=True
        )
        def handle_graph_updates(
            save_clicks: int,
            add_vertex_clicks: int,
            selected_nodes: list[dict] | None,
            new_text: str | None,
            new_predicates_text: str | None,
            new_effects_text: str | None,
            new_vertex_text: str | None,
            current_log: str | None
        ) -> tuple[list[dict], str, str]:
            triggered_id = ctx.triggered_id
            if triggered_id == "add-vertex":
                if not new_vertex_text:
                    raise PreventUpdate
                new_vertex_name = self.add_vertex(new_vertex_text)
                return (
                    self.get_elements(), 
                    self.append_action_status(
                        current_log, f"Added {new_vertex_name}."
                    ),
                    ""
                )
            if triggered_id == "save-text":
                if not selected_nodes:
                    raise PreventUpdate
                node_id = selected_nodes[0].get("id")
                if not node_id:
                    raise PreventUpdate
                try:
                    predicates = self.parse_predicates(new_predicates_text)
                    effects = self.parse_effects(new_effects_text)
                except ValueError as exception:
                    return (
                        no_update, 
                        self.append_action_status(
                            current_log, f"Save failed: {exception}"
                        ), 
                        no_update
                    )
                was_updated = self.update_node(
                    node_id, new_text or "", predicates, effects
                )
                if not was_updated:
                    raise PreventUpdate
                return (
                    self.get_elements(), 
                    self.append_action_status(
                        current_log, f"Saved node data for {node_id}."
                    ),
                    no_update
                )
            raise PreventUpdate

    def update_node(
        self, 
        node_id: str, 
        new_text: str, 
        new_predicates: list[dict[str, str | int]] | None,
        new_effects: list[dict[str, str | int]]
    ) -> bool:
        was_updated = False
        if node_id in self.graph_editor.graph.vertex_dict:
            vertex = self.graph_editor.graph.vertex_dict[node_id]
            if vertex.text != new_text:
                self.graph_editor.edit_vertex_text(node_id, new_text)
                was_updated = True
            if vertex.effects != new_effects:
                self.graph_editor.edit_vertex_effects(node_id, new_effects)
                was_updated = True
        if node_id in self.graph_editor.graph.edge_dict:
            edge = self.graph_editor.graph.edge_dict[node_id]
            if edge.text != new_text:
                self.graph_editor.edit_edge_text(node_id, new_text)
                was_updated = True
            if edge.predicates != new_predicates:
                self.graph_editor.edit_edge_predicates(node_id, new_predicates)
                was_updated = True
            if edge.effects != new_effects:
                self.graph_editor.edit_edge_effects(node_id, new_effects)
                was_updated = True
        return was_updated

def main():
    open_url("http://localhost:8050")
    app = App("data/hello_world.yaml")
    app.run(debug=True, use_reloader=False)

if __name__ == "__main__":
    main()

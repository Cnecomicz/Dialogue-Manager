from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from dash_cytoscape import Cytoscape, load_extra_layouts
from os import PathLike
from webbrowser import open as open_url

from dash_app.layout import (
    get_add_edge_section, 
    get_add_vertex_section, 
    get_cytoscape_stylesheet, 
    get_delete_section,
    get_edit_section, 
    get_log
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
                    + get_edit_section() 
                    + [html.Hr()] 
                    + get_add_vertex_section()
                    + [html.Hr()]
                    + get_add_edge_section()
                    + [html.Hr()]
                    + get_delete_section(),
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

    def add_edge(
        self, 
        from_vertex: str, 
        to_vertex: str | None, 
        text: str | None, 
        predicates: list[dict[str, str | int]] | None = None,
        effects: list[dict[str, str | int]] | None = None
    ) -> str:
        self.graph_editor.add_edge(
            from_vertex, to_vertex, text, predicates, effects
        )
        return f"edge_{self.graph_editor.next_edge_index-1}"

    def add_vertex(
        self, 
        text: str | None, 
        effects: list[dict[str, str | int]] | None = None
    ) -> str:
        self.graph_editor.add_vertex(text, effects)
        return f"vertex_{self.graph_editor.next_vertex_index-1}"

    def append_action_status(
        self, current_log: str | None, new_message: str
    ) -> str:
        if not current_log:
            return new_message
        return f"{current_log}\n{new_message}"

    def get_delete_section_state(
        self, 
        selected_nodes: list[dict] | None, 
        current_delete_cascade: list[str] | None
    ) -> tuple[str, list[dict[str, str | bool]], list[str]]:
        if not selected_nodes:
            return (
                "Selected node: None",
                [
                    {
                        "label": "Cascade delete", 
                        "value": "cascade", 
                        "disabled": False
                    }
                ],
                current_delete_cascade or []
            )
        node_id = selected_nodes[0].get("id", "None")
        is_edge = node_id in self.graph_editor.graph.edge_dict
        options = [
            {
                "label": "Cascade delete", 
                "value": "cascade", 
                "disabled": is_edge
            }
        ]
        value = [] if is_edge else (current_delete_cascade or [])
        return f"Selected node: {node_id}", options, value

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

    def parse_effects(
        self, effects_text: str | None
    ) -> list[dict[str, str | int]]:
        if not effects_text:
            return []
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
        self, predicates_text: str | None
    ) -> list[dict[str, str | int]]:
        if not predicates_text:
            return []
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
            Output("new-edge-from", "value"),
            Input("dialogue-graph", "selectedNodeData")
        )
        def autofill_edit_fields(
            selected_nodes: list[dict] | None
        ) -> tuple[str, str, bool, str, str]:
            if not selected_nodes:
                return "", "", True, "", ""
            node_id = selected_nodes[0].get("id")
            if not node_id:
                return "", "", True, "", ""
            node_text = self.get_node_text(node_id)
            if node_text is None:
                return "", "", True, "", ""
            is_vertex = node_id in self.graph_editor.graph.vertex_dict
            predicates_text = self.get_node_predicates(node_id)
            effects_text = self.get_node_effects(node_id)
            new_edge_from = node_id if is_vertex else ""
            return (
                node_text, 
                predicates_text, 
                is_vertex, 
                effects_text, 
                new_edge_from
            )

        @self.callback(
            Output("selected-node-display", "children"),
            Output("delete-selected-node-display", "children"),
            Output("delete-cascade", "options"),
            Output("delete-cascade", "value"),
            Input("dialogue-graph", "selectedNodeData"),
            State("delete-cascade", "value")
        )
        def display_selected_node(
            selected_nodes: list[dict] | None, 
            current_delete_cascade: list[str] | None
        ) -> tuple[str, str, list[dict[str, str | bool]], list[str]]:
            delete_text, delete_options, delete_value = (
                self.get_delete_section_state(
                    selected_nodes, current_delete_cascade
                )
            )
            return delete_text, delete_text, delete_options, delete_value

        @self.callback(
            Output("dialogue-graph", "elements"),
            Output("action-status", "value"),
            Output("new-vertex-text", "value"),
            Output("new-vertex-effects", "value"),
            Output("new-edge-to", "value"),
            Output("new-edge-text", "value"),
            Output("new-edge-predicates", "value"),
            Output("new-edge-effects", "value"),
            Output("confirm-delete-node", "displayed"),
            Output("dialogue-graph", "selectedNodeData"),
            Input("save-text", "n_clicks"),
            Input("add-vertex", "n_clicks"),
            Input("add-edge", "n_clicks"),
            Input("delete-node", "n_clicks"),
            Input("confirm-delete-node", "submit_n_clicks"),
            State("dialogue-graph", "selectedNodeData"),
            State("edit-text", "value"),
            State("edit-predicates", "value"),
            State("edit-effects", "value"),
            State("new-vertex-text", "value"),
            State("new-vertex-effects", "value"),
            State("new-edge-from", "value"),
            State("new-edge-to", "value"),
            State("new-edge-text", "value"),
            State("new-edge-predicates", "value"),
            State("new-edge-effects", "value"),
            State("delete-cascade", "value"),
            State("action-status", "value"),
            prevent_initial_call=True
        )
        def handle_graph_updates(
            save_clicks: int,
            add_vertex_clicks: int,
            add_edge_clicks: int,
            delete_node_clicks: int,
            confirm_delete_submit_clicks: int,
            selected_nodes: list[dict] | None,
            new_text: str | None,
            new_predicates_text: str | None,
            new_effects_text: str | None,
            new_vertex_text: str | None,
            new_vertex_effects_text: str | None,
            new_edge_from: str | None,
            new_edge_to: str | None,
            new_edge_text: str | None,
            new_edge_predicates_text: str | None,
            new_edge_effects_text: str | None,
            delete_cascade: list[str] | None,
            current_log: str | None
        ) -> tuple[list[dict], str, str, str, str, str, str, str, bool, list]:
            triggered_id = ctx.triggered_id
            if triggered_id == "add-vertex":
                if not new_vertex_text:
                    raise PreventUpdate
                try:
                    new_vertex_effects = self.parse_effects(
                        new_vertex_effects_text
                    )
                except ValueError as exception:
                    return (
                        no_update,
                        self.append_action_status(
                            current_log, f"Add vertex failed: {exception}"
                        ),
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update
                    )
                new_vertex_name = self.add_vertex(
                    new_vertex_text, new_vertex_effects
                )
                return (
                    self.get_elements(), 
                    self.append_action_status(
                        current_log, f"Added {new_vertex_name}."
                    ),
                    "",
                    "",
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    False,
                    no_update
                )
            if triggered_id == "add-edge":
                if not new_edge_from or not new_edge_from.strip():
                    return (
                        no_update,
                        self.append_action_status(
                            current_log, 
                            "Add edge failed: from vertex is required."
                        ),
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update
                    )
                try: 
                    new_edge_predicates = self.parse_predicates(
                        new_edge_predicates_text
                    )
                    new_edge_effects = self.parse_effects(
                        new_edge_effects_text
                    )
                except ValueError as exception:
                    return (
                        no_update,
                        self.append_action_status(
                            current_log, f"Add edge failed: {exception}"
                        ),
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update
                    )
                normalized_to_vertex = (
                    new_edge_to.strip() 
                    if new_edge_to and new_edge_to.strip()
                    else None
                )
                new_edge_name = self.add_edge(
                    new_edge_from.strip(),
                    normalized_to_vertex,
                    new_edge_text,
                    new_edge_predicates,
                    new_edge_effects
                )
                return (
                    self.get_elements(),
                    self.append_action_status(
                        current_log, f"Added {new_edge_name}."
                    ),
                    no_update,
                    no_update,
                    "",
                    "",
                    "",
                    "",
                    False,
                    no_update
                )
            if triggered_id == "delete-node":
                if not selected_nodes:
                    return (
                        no_update,
                        self.append_action_status(
                            current_log, "Delete failed: no node selected."
                        ),
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update
                    )
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    True,
                    no_update
                )
            if triggered_id == "confirm-delete-node":
                if not selected_nodes:
                    return (
                        no_update,
                        self.append_action_status(
                            current_log, "Delete failed: no node selected."
                        ),
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update
                    )
                node_id = selected_nodes[0].get("id")
                if not node_id:
                    raise PreventUpdate
                was_removed = self.remove_node(
                    node_id, "cascade" in (delete_cascade or [])
                )
                if not was_removed:
                    return (
                        no_update,
                        self.append_action_status(
                            current_log, 
                            f"Delete failed: unknown node {node_id}."
                        ),
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update
                    )
                return (
                    self.get_elements(),
                    self.append_action_status(
                        current_log, f"Deleted {node_id}."
                    ),
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    False,
                    []
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
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        False,
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
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    False,
                    no_update
                )
            raise PreventUpdate

    def remove_node(self, node_id: str, cascade_delete: bool = False) -> bool:
        if node_id in self.graph_editor.graph.vertex_dict:
            self.graph_editor.remove_vertex(node_id, cascade_delete)
            return True
        if node_id in self.graph_editor.graph.edge_dict:
            self.graph_editor.remove_edge(node_id)
            return True
        return False

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

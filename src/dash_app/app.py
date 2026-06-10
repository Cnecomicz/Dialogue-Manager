from base64 import b64decode
from binascii import Error as BinasciiError
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from dash_cytoscape import Cytoscape, load_extra_layouts
from os import PathLike
from re import sub
from webbrowser import open as open_url
from yaml import YAMLError, safe_load

from dash_app.layout import (
    get_add_edge_section, 
    get_add_vertex_section, 
    get_cytoscape_stylesheet, 
    get_delete_section,
    get_edit_section, 
    get_header,
    get_index_string,
    get_log,
    get_name_section,
    get_upload_graph
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
        self.index_string = get_index_string()
        self.graph_editor = GraphEditor()
        if yaml_file is not None:
            self.graph_editor.load(yaml_file=yaml_file)
        load_extra_layouts()
        self.layout = html.Div(
            [
                html.Div(
                    get_log()
                    + [html.Hr()]
                    + get_name_section(
                        self.normalize_name(self.graph_editor.graph.name)
                    )
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
                        "boxSizing": "border-box",
                        "padding": "12px",
                        "paddingBottom": "24px",
                        "backgroundColor": "#1f252b",
                        "color": "#e6e6e6",
                        "borderRight": "1px solid #444",
                        "overflowY": "auto",
                        "height": "100vh"
                    }
                ),
                html.Div(
                    [
                        get_header(),
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
                            style={"flex": "1", "minHeight": 0}
                        )
                    ],
                    style={
                        "flex": "1",
                        "minWidth": 0,
                        "height": "100%",
                        "display": "flex",
                        "flexDirection": "column"
                    }
                ),
                dcc.Store(id="unsaved-changes", data=False),
                dcc.Store(
                    id="current-document", 
                    data=self.normalize_name(self.graph_editor.graph.name)
                ),
                dcc.Store(id="pending-action", data=""),
                dcc.Store(id="pending-upload", data={}),
                dcc.Download(id="download-yaml"),
                dcc.ConfirmDialog(
                    id="confirm-unsaved-work", 
                    message="You have unsaved changes. Continue?"
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

    def count_unresolved_connections(self, vertex_name: str) -> int:
        unresolved_count = 0
        for edge in self.graph_editor.graph.edge_dict.values():
            unresolved_count += int(edge.from_vertex == vertex_name)
            unresolved_count += int(edge.to_vertex == vertex_name)
        return unresolved_count

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

    def get_edge_endpoints_for_edit(self, node_id: str) -> tuple[str, str]:
        if node_id not in self.graph_editor.graph.edge_dict:
            return "", ""
        edge = self.graph_editor.graph.edge_dict[node_id]
        from_vertex = (
            "" if edge.from_vertex == "__MISSING__" else edge.from_vertex
        )
        to_vertex = (
            "" if edge.to_vertex == "__MISSING__" else edge.to_vertex
        )
        return from_vertex, to_vertex

    def get_elements(self) -> list[dict[str, dict[str, str]]]:
        cytoscape_adapter = CytoscapeAdapter(self.graph_editor.graph)
        return cytoscape_adapter.nodes + cytoscape_adapter.edges

    def get_filename(self, name: str | None) -> str:
        normalized = self.normalize_name(name)
        slug = sub(r"[^a-z0-9]+", "_", normalized.lower()).strip("_")
        if not slug:
            slug = "untitled"
        return f"{slug}_dialogue_graph.yaml"

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

    def normalize_name(self, name: str | None) -> str:
        normalized = (name or "").strip()
        return normalized if normalized else "Untitled"

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

    def parse_uploaded_yaml(self, upload_contents: str | None) -> dict:
        if not upload_contents or "," not in upload_contents:
            raise ValueError("Upload failed: missing file contents.")
        _, encoded_content = upload_contents.split(",", 1)
        try:
            raw_bytes = b64decode(encoded_content, validate=True)
        except BinasciiError as e:
            raise ValueError("Upload failed: invalid file encoding.") from e
        try:
            decoded_text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError("Upload failed: file must be UTF-8 text.") from e
        try:
            parsed_yaml = safe_load(decoded_text) or {}
        except YAMLError as e:
            raise ValueError("Upload failed: invalid yaml format.") from e
        if not isinstance(parsed_yaml, dict):
            raise ValueError("Upload failed: yaml root must be a dictionary.")
        return parsed_yaml

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
            Output("edit-from-vertex", "value"),
            Output("edit-to-vertex", "value"),
            Output("edit-from-vertex", "disabled"),
            Output("edit-to-vertex", "disabled"),
            Input("dialogue-graph", "selectedNodeData")
        )
        def autofill_edit_fields(
            selected_nodes: list[dict] | None
        ) -> tuple[str, str, bool, str, str, str, str, bool, bool]:
            if not selected_nodes:
                return "", "", True, "", "", "", "", True, True
            node_id = selected_nodes[0].get("id")
            if not node_id:
                return "", "", True, "", "", "", "", True, True
            node_text = self.get_node_text(node_id)
            if node_text is None:
                return "", "", True, "", "", "", "", True, True
            is_vertex = node_id in self.graph_editor.graph.vertex_dict
            predicates_text = self.get_node_predicates(node_id)
            effects_text = self.get_node_effects(node_id)
            new_edge_from = node_id if is_vertex else ""
            edit_from_vertex, edit_to_vertex = (
                self.get_edge_endpoints_for_edit(node_id)
            )
            disable_edge_endpoint_edit = is_vertex
            return (
                node_text, 
                predicates_text, 
                is_vertex, 
                effects_text, 
                new_edge_from,
                edit_from_vertex,
                edit_to_vertex,
                disable_edge_endpoint_edit,
                disable_edge_endpoint_edit
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
            Output("unsaved-changes", "data"),
            Output("current-document", "data"),
            Output("confirm-unsaved-work", "displayed"),
            Output("confirm-unsaved-work", "message"),
            Output("pending-action", "data"),
            Output("pending-upload", "data"),
            Output("download-yaml", "data"),
            Input("save-name", "n_clicks"),
            Input("save-text", "n_clicks"),
            Input("add-vertex", "n_clicks"),
            Input("add-edge", "n_clicks"),
            Input("delete-node", "n_clicks"),
            Input("confirm-delete-node", "submit_n_clicks"),
            Input("new-graph", "n_clicks"),
            Input("download-graph", "n_clicks"),
            Input("upload-graph", "contents"),
            Input("confirm-unsaved-work", "submit_n_clicks"),
            Input("confirm-unsaved-work", "cancel_n_clicks"),
            State("dialogue-graph", "selectedNodeData"),
            State("edit-text", "value"),
            State("edit-predicates", "value"),
            State("edit-effects", "value"),
            State("edit-from-vertex", "value"),
            State("edit-to-vertex", "value"),
            State("new-vertex-text", "value"),
            State("new-vertex-effects", "value"),
            State("new-edge-from", "value"),
            State("new-edge-to", "value"),
            State("new-edge-text", "value"),
            State("new-edge-predicates", "value"),
            State("new-edge-effects", "value"),
            State("delete-cascade", "value"),
            State("action-status", "value"),
            State("document-name", "value"),
            State("upload-graph", "filename"),
            State("unsaved-changes", "data"),
            State("current-document", "data"),
            State("pending-action", "data"),
            State("pending-upload", "data"),
            prevent_initial_call=True
        )
        def handle_graph_updates(
            save_name_clicks: int,
            save_clicks: int,
            add_vertex_clicks: int,
            add_edge_clicks: int,
            delete_node_clicks: int,
            confirm_delete_submit_clicks: int,
            new_graph_clicks: int,
            download_graph_clicks: int,
            upload_contents: str | None,
            confirm_unsaved_submit_clicks: int,
            confirm_unsaved_cancel_clicks: int,
            selected_nodes: list[dict] | None,
            new_text: str | None,
            new_predicates_text: str | None,
            new_effects_text: str | None,
            new_from_vertex: str | None,
            new_to_vertex: str | None,
            new_vertex_text: str | None,
            new_vertex_effects_text: str | None,
            new_edge_from: str | None,
            new_edge_to: str | None,
            new_edge_text: str | None,
            new_edge_predicates_text: str | None,
            new_edge_effects_text: str | None,
            delete_cascade: list[str] | None,
            current_log: str | None,
            document_name: str | None,
            upload_filename: str | None,
            unsaved_changes: bool,
            current_document: str | None,
            pending_action: str | None,
            pending_upload: dict | None
        ) -> tuple[
            list[dict], 
            str, 
            str, 
            str, 
            str, 
            str, 
            str, 
            str, 
            bool, 
            list,
            bool,
            str,
            bool,
            str,
            str,
            dict,
            dict
        ]:
            def default_result() -> tuple:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    False,
                    no_update,
                    no_update,
                    no_update,
                    False,
                    no_update,
                    no_update,
                    no_update,
                    no_update
                )
            triggered_id = ctx.triggered_id
            triggered_prop_id = (
                ctx.triggered[0]["prop_id"] if ctx.triggered else ""
            )
            if triggered_id == "save-name":
                normalized = self.normalize_name(document_name)
                self.graph_editor.edit_name(normalized)
                return (
                    no_update,
                    self.append_action_status(
                        current_log, f"Saved NPC name as {normalized}."
                    ),
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    False,
                    no_update,
                    True,
                    normalized,
                    False,
                    no_update,
                    "",
                    {},
                    no_update
                )
            if triggered_id == "download-graph":
                download_name = self.get_filename(current_document)
                return (
                    no_update,
                    self.append_action_status(
                        current_log, f"Downloaded {download_name}."
                    ),
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    False,
                    no_update,
                    no_update,
                    no_update,
                    False,
                    no_update,
                    "",
                    {},
                    dcc.send_string(
                        self.graph_editor.export_yaml_text(), download_name
                    )
                )
            if triggered_id == "new-graph":
                if unsaved_changes:
                    return (
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update,
                        no_update,
                        no_update,
                        True,
                        "You have unsaved changes. Start a new graph anyway?",
                        "new",
                        {},
                        no_update
                    )
                self.graph_editor.load()
                return (
                    self.get_elements(),
                    self.append_action_status(
                        current_log, "Started a new graph."
                    ),
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    False,
                    [],
                    False,
                    self.normalize_name(self.graph_editor.graph.name),
                    False,
                    no_update,
                    "",
                    {},
                    no_update
                )
            if triggered_id == "upload-graph":
                if not upload_contents:
                    raise PreventUpdate
                if unsaved_changes:
                    return (
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update,
                        no_update,
                        no_update,
                        True,
                        "You have unsaved changes. Upload and replace anyway?",
                        "upload",
                        {
                            "contents": upload_contents, 
                            "filename": upload_filename or "Untitled"
                        },
                        no_update
                    )
                try:
                    parsed_yaml = self.parse_uploaded_yaml(upload_contents)
                except ValueError as exception:
                    return (
                        no_update,
                        self.append_action_status(current_log, str(exception)),
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update,
                        "",
                        {},
                        no_update
                    )
                self.graph_editor.load(yaml_data=parsed_yaml)
                loaded_name = self.normalize_name(self.graph_editor.graph.name)
                return (
                    self.get_elements(),
                    self.append_action_status(
                        current_log, 
                        f"Opened {upload_filename or loaded_name}."
                    ),
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    False,
                    [],
                    False,
                    loaded_name,
                    False,
                    no_update,
                    "",
                    {},
                    no_update
                )
            if triggered_prop_id == "confirm-unsaved-work.submit_n_clicks":
                if pending_action == "new":
                    self.graph_editor.load()
                    return (
                        self.get_elements(),
                        self.append_action_status(
                            current_log, 
                            "Discarded changes and started a new graph."
                        ),
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        False,
                        [],
                        False,
                        self.normalize_name(self.graph_editor.graph.name),
                        False,
                        no_update,
                        "",
                        {},
                        no_update
                    )
                if pending_action == "upload":
                    queued_upload = pending_upload or {}
                    queued_contents = queued_upload.get("contents")
                    queued_filename = (
                        queued_upload.get("filename") or "Untitled"
                    )
                    if not queued_contents:
                        return (
                            no_update,
                            self.append_action_status(
                                current_log, 
                                "Open failed: no pending upload data."
                            ),
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            False,
                            no_update,
                            no_update,
                            no_update,
                            False,
                            no_update,
                            "",
                            {},
                            no_update
                        )
                    try:
                        parsed_yaml = self.parse_uploaded_yaml(queued_contents)
                    except ValueError as exception:
                        return (
                            no_update,
                            self.append_action_status(
                                current_log, str(exception)
                            ),
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            False,
                            no_update,
                            no_update,
                            no_update,
                            False,
                            no_update,
                            "",
                            {},
                            no_update
                        )
                    self.graph_editor.load(yaml_data=parsed_yaml)
                    loaded_name = self.normalize_name(
                        self.graph_editor.graph.name
                    )
                    return (
                        self.get_elements(),
                        self.append_action_status(
                            current_log,
                            "Discarded changes and opened "
                            f"{queued_filename}."
                        ),
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        False,
                        [],
                        False,
                        loaded_name,
                        False,
                        no_update,
                        "",
                        {},
                        no_update
                    )
                return default_result()
            if triggered_prop_id == "confirm-unsaved-work.cancel_n_clicks":
                return (
                    no_update,
                    self.append_action_status(
                        current_log, "Cancelled action."
                    ),
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    False,
                    no_update,
                    no_update,
                    no_update,
                    False,
                    no_update,
                    "",
                    {},
                    no_update
                )
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
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update,
                        "",
                        {},
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
                    no_update,
                    True,
                    no_update,
                    False,
                    no_update,
                    "",
                    {},
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
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update,
                        "",
                        {},
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
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update,
                        "",
                        {},
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
                    no_update,
                    True,
                    no_update,
                    False,
                    no_update,
                    "",
                    {},
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
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update,
                        "",
                        {},
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
                    no_update,
                    no_update,
                    no_update,
                    False,
                    no_update,
                    "",
                    {},
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
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update,
                        "",
                        {},
                        no_update
                    )
                node_id = selected_nodes[0].get("id")
                if not node_id:
                    raise PreventUpdate
                was_edge_delete = node_id in self.graph_editor.graph.edge_dict
                was_vertex_delete = (
                    node_id in self.graph_editor.graph.vertex_dict
                )
                cascade_delete_enabled = "cascade" in (delete_cascade or [])
                unresolved_connections_created = (
                    self.count_unresolved_connections(node_id)
                    if was_vertex_delete and not cascade_delete_enabled 
                    else 0
                )
                was_removed = self.remove_node(node_id, cascade_delete_enabled)
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
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update,
                        "",
                        {},
                        no_update
                    )
                return (
                    self.get_elements(),
                    self.append_action_status(
                        current_log, 
                        (
                            f"Deleted {node_id}."
                            if was_edge_delete or cascade_delete_enabled
                            else (
                                f"Deleted {node_id}. "
                                f"{unresolved_connections_created} unresolved "
                                "connections created."
                            )
                        )
                    ),
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    False,
                    [],
                    True,
                    no_update,
                    False,
                    no_update,
                    "",
                    {},
                    no_update
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
                        no_update,
                        no_update,
                        no_update,
                        False,
                        no_update,
                        "",
                        {},
                        no_update
                    )
                was_updated = self.update_node(
                    node_id, new_text or "", predicates, effects
                )
                endpoint_warnings = []
                endpoint_updated = False
                if node_id in self.graph_editor.graph.edge_dict:
                    endpoint_updated, endpoint_warnings = (
                        self.update_edge_endpoints(
                            node_id, new_from_vertex, new_to_vertex
                        )
                    )
                was_anything_updated = was_updated or endpoint_updated
                if not was_anything_updated and not endpoint_warnings:
                    raise PreventUpdate
                new_log = current_log
                if was_anything_updated:
                    new_log = self.append_action_status(
                        new_log, f"Saved node data for {node_id}."
                    )
                for warning in endpoint_warnings:
                    new_log = self.append_action_status(new_log, warning)
                return (
                    self.get_elements() if was_anything_updated else no_update, 
                    new_log,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    False,
                    no_update,
                    True if was_anything_updated else no_update,
                    no_update,
                    False,
                    no_update,
                    "",
                    {},
                    no_update
                )
            raise PreventUpdate

        @self.callback(
            Output("current-document-label", "children"),
            Input("current-document", "data"),
            Input("unsaved-changes", "data")
        )
        def render_document_label(
            current_document: str | None,
            unsaved_changes: bool
        ) -> str:
            document_name = self.get_filename(current_document)
            dirty_marker = " *" if unsaved_changes else ""
            return f"Document: {document_name}{dirty_marker}"

        @self.callback(
            Output("upload-graph-container", "children"),
            Input("action-status", "value"),
            prevent_initial_call=True
        )
        def reset_upload_contents_after_actions(
            action_log: str | None
        ) -> dcc.Upload:
            return get_upload_graph()

        @self.callback(
            Output("document-name", "value"),
            Input("current-document", "data")
        )
        def sync_document_name(current_document: str | None) -> str:
            return self.normalize_name(current_document)

    def remove_node(self, node_id: str, cascade_delete: bool = False) -> bool:
        if node_id in self.graph_editor.graph.vertex_dict:
            self.graph_editor.remove_vertex(node_id, cascade_delete)
            return True
        if node_id in self.graph_editor.graph.edge_dict:
            self.graph_editor.remove_edge(node_id)
            return True
        return False

    def update_edge_endpoints(
        self, 
        node_id: str, 
        new_from_vertex: str | None, 
        new_to_vertex: str | None
    ) -> tuple[bool, list[str]]:
        if node_id not in self.graph_editor.graph.edge_dict:
            return False, []
        edge = self.graph_editor.graph.edge_dict[node_id]
        warnings = []
        was_updated = False
        candidate_from_vertex = (new_from_vertex or "").strip()
        candidate_to_vertex = (new_to_vertex or "").strip()
        if candidate_from_vertex:
            if candidate_from_vertex in self.graph_editor.graph.vertex_dict:
                if edge.from_vertex != candidate_from_vertex:
                    self.graph_editor.edit_from_vertex(
                        node_id, candidate_from_vertex
                    )
                    was_updated = True
            else:
                warnings.append(
                    f"Invalid from vertex: {candidate_from_vertex}"
                )
        elif edge.from_vertex == "__MISSING__":
            pass
        else:
            warnings.append("Invalid from vertex: (empty)")
        if candidate_to_vertex:
            if candidate_to_vertex in self.graph_editor.graph.vertex_dict:
                if edge.to_vertex != candidate_to_vertex:
                    self.graph_editor.edit_to_vertex(
                        node_id, candidate_to_vertex
                    )
                    was_updated = True
            else:
                warnings.append(f"Invalid to vertex: {candidate_to_vertex}")
        elif edge.to_vertex == "__MISSING__":
            pass
        else:
            warnings.append("Invalid to vertex: (empty)")
        return was_updated, warnings

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
    app = App()
    app.run(debug=True, use_reloader=False)

if __name__ == "__main__":
    main()

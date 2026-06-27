from base64 import b64decode
from binascii import Error as BinasciiError
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from dash_cytoscape import load_extra_layouts
from os import PathLike
from re import sub
from webbrowser import open as open_url
from yaml import YAMLError, safe_load

from dash_app.layout import (
    get_add_edge_modal,
    get_add_vertex_modal,
    get_center_panel,
    get_delete_node_modal,
    get_edit_node_modal,
    get_graph_component,
    get_index_string,
    get_left_panel,
    get_modal_overlay_style,
    get_project_metadata,
    get_right_panel,
    get_upload_graph
)
from dash_app.logger import Logger
from dialogue_editor.graph_editor import (
    GraphEditor, VertexCannotBeDeletedError, VertexNotFoundError
)
from dialogue_model.codecs import (
    convert_effect_to_text, 
    convert_predicate_to_text, 
    convert_text_to_effect, 
    convert_text_to_predicate
)
from dialogue_navigator.graph_navigator import collect_validation_errors
from dialogue_viewer.cytoscape_adapter import CytoscapeAdapter

class App(Dash):
    """Dash application wrapper for dialogue graph editing."""

    MISSING_VERTEX = "__MISSING__"
    PENDING_ACTION_NEW = "new"
    PENDING_ACTION_UPLOAD = "upload"

    def __init__(self, yaml_file: str | PathLike | None = None) -> None:
        """Initialize the app layout, state stores, and callbacks.

        Args:
            yaml_file (str | PathLike | None): Optional yaml file to preload.
        """
        super().__init__()
        self.index_string = get_index_string()
        self.graph_editor = GraphEditor()
        self.action_logger = Logger(self.graph_editor)
        self.graph_render_count = 0
        if yaml_file is not None:
            self.graph_editor.load(yaml_file=yaml_file)
        load_extra_layouts()
        author, version = get_project_metadata()
        initial_name = self.normalize_name(self.graph_editor.graph.name)
        self.layout = html.Div(
            [
                get_left_panel(initial_name, author, version),
                get_center_panel(self.get_elements()),
                get_right_panel(),
                get_add_vertex_modal(),
                get_add_edge_modal(),
                get_edit_node_modal(),
                get_delete_node_modal(),
                dcc.Store(id="unsaved-changes", data=False),
                dcc.Store(id="current-document", data=initial_name),
                dcc.Store(id="pending-action", data=""),
                dcc.Store(id="pending-upload", data={}),
                dcc.Store(id="selected-node-id", data=None),
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
        """Add an edge through the graph editor and return its identifier.

        Args:
            from_vertex (str): Source vertex id.
            to_vertex (str | None): Target vertex id.
            text (str | None): Edge dialogue text.
            predicates (list[dict[str, str | int]] | None): Edge predicates.
            effects (list[dict[str, str | int]] | None): Edge effects.

        Returns:
            str: Newly created edge identifier.
        """
        return self.graph_editor.add_edge(
            from_vertex, to_vertex, text, predicates, effects
        )

    def add_vertex(
        self, 
        text: str | None, 
        effects: list[dict[str, str | int]] | None = None
    ) -> str:
        """Add a vertex through the graph editor and return its identifier.

        Args:
            text (str | None): Vertex dialogue text.
            effects (list[dict[str, str | int]] | None): Vertex effects.

        Returns:
            str: Newly created vertex identifier.
        """
        return self.graph_editor.add_vertex(text, effects)

    def count_unresolved_connections(self, vertex_name: str) -> int:
        """Count edges referencing a vertex that is about to be removed.

        Args:
            vertex_name (str): Vertex identifier.

        Returns:
            int: Number of connected edge endpoints.
        """
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
        """Build current delete-panel text and cascade control state.

        Args:
            selected_nodes (list[dict] | None): Selected Cytoscape nodes.
            current_delete_cascade (list[str] | None): Current checklist value.

        Returns:
            tuple[str, list[dict[str, str | bool]], list[str]]: Display text,
            checklist options, and checklist value.
        """
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
        """Get edge endpoint values for edit controls.

        Args:
            node_id (str): Selected node identifier.

        Returns:
            tuple[str, str]: "from" and "to" endpoint values.
        """
        if node_id not in self.graph_editor.graph.edge_dict:
            return "", ""
        edge = self.graph_editor.graph.edge_dict[node_id]
        from_vertex = (
            "" if edge.from_vertex == self.MISSING_VERTEX else edge.from_vertex
        )
        to_vertex = (
            "" if edge.to_vertex == self.MISSING_VERTEX else edge.to_vertex
        )
        return from_vertex, to_vertex

    def get_elements(self) -> list[dict[str, dict[str, str]]]:
        """Build Cytoscape elements for the current graph state.

        Returns:
            list[dict[str, dict[str, str]]]: Node and edge element mappings.
        """
        cytoscape_adapter = CytoscapeAdapter(self.graph_editor.graph)
        return cytoscape_adapter.nodes + cytoscape_adapter.edges

    def get_filename(self, name: str | None) -> str:
        """Build a normalized yaml filename from a graph name.

        Args:
            name (str | None): NPC name.

        Returns:
            str: Slugified "*_dialogue_graph.yaml" filename.
        """
        normalized = self.normalize_name(name)
        slug = sub(r"[^a-z0-9]+", "_", normalized.lower()).strip("_")
        if not slug:
            slug = "untitled"
        return f"{slug}_dialogue_graph.yaml"

    def get_fresh_graph_component(self):
        """Build a graph component with a new key to force a remount.

        A unique key makes React mount a brand new Cytoscape instance,
        clearing any selection or render state carried over from a
        previously loaded graph. Use this for whole-graph swaps (New/Open).

        Returns:
            Cytoscape: A freshly keyed graph component for the current graph.
        """
        self.graph_render_count += 1
        return get_graph_component(
            self.get_elements(), key=str(self.graph_render_count)
        )

    def get_node_effects(self, node_id: str) -> str:
        """Return serialized effects text for a node.

        Args:
            node_id (str): Vertex or edge identifier.

        Returns:
            str: Newline-separated effects text.
        """
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
        """Return serialized predicates text for an edge node.

        Args:
            node_id (str): Edge identifier.

        Returns:
            str: Newline-separated predicates text.
        """
        if node_id in self.graph_editor.graph.edge_dict:
            predicates = self.graph_editor.graph.edge_dict[node_id].predicates
            return "\n".join(
                convert_predicate_to_text(predicate) 
                for predicate in predicates
            )
        return ""

    def get_node_text(self, node_id: str) -> str:
        """Return dialogue text associated with a node id.

        Args:
            node_id (str): Vertex or edge identifier.

        Returns:
            str: Node dialogue text, or an empty string if missing.
        """
        if node_id in self.graph_editor.graph.vertex_dict:
            return self.graph_editor.graph.vertex_dict[node_id].text
        if node_id in self.graph_editor.graph.edge_dict:
            return self.graph_editor.graph.edge_dict[node_id].text
        return ""

    def get_runtime_validation_warnings(self) -> list[str]:
        """Return runtime validation warnings for the current graph.

        Returns:
            list[str]: Warning summary and full issue list, or an empty 
                list when the graph is runtime-valid.
        """
        errors = collect_validation_errors(self.graph_editor.graph)
        if not errors:
            return []
        warning_lines = [
            f"Runtime validation found {len(errors)} issue(s):",
            *[f"- {error}" for error in errors]
        ]
        return warning_lines

    def normalize_name(self, name: str | None) -> str:
        """Normalize an NPC name to a non-empty display value.

        Args:
            name (str | None): NPC name.

        Returns:
            str: Stripped name, or "Untitled" when empty.
        """
        normalized = (name or "").strip()
        return normalized if normalized else "Untitled"

    def parse_effects(
        self, effects_text: str | None
    ) -> list[dict[str, str | int]]:
        """Parse multiline effect text into effect mappings.

        Args:
            effects_text (str | None): One effect per line.

        Returns: list[dict[str, str | int]]: Parsed effect mappings.

        Raises:
            ValueError: If any nonempty line has invalid syntax.

        Examples:
            Multiple lines such as "player.gold = player.gold+1" and
            "player.inventory.append(key)" are supported.
        """
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
        """Parse multiline predicate text into predicate mappings.

        Args:
            predicates_text (str | None): One predicate per line.

        Returns:
            list[dict[str, str | int]]: Parsed predicate mappings.

        Raises:
            ValueError: If any nonempty line has invalid syntax.

        Examples:
            Lines such as "player.level >= 2" and "key in player.inventory"
            are supported.
        """
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
        """Decode and validate uploaded base64 yaml content.

        Args:
            upload_contents (str | None): Dash upload "contents" payload.

        Returns:
            dict: Parsed yaml mapping.

        Raises:
            ValueError: If payload encoding, text decoding, or yaml parsing
                fails, or yaml root is not a dictionary.
        """
        if not upload_contents or "," not in upload_contents:
            raise ValueError(
                "Could not open the file because no file data was received. "
                "Select the file again and try one more time."
            )
        _, encoded_content = upload_contents.split(",", 1)
        try:
            raw_bytes = b64decode(encoded_content, validate=True)
        except BinasciiError as e:
            raise ValueError(
                "Could not open the file because the upload data is "
                "invalid. Select the file again and try one more time."
            ) from e
        try:
            decoded_text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(
                "Could not open the file because it is not UTF-8 text. "
                "Save the file as UTF-8 yaml and try again."
            ) from e
        try:
            parsed_yaml = safe_load(decoded_text) or {}
        except YAMLError as e:
            raise ValueError(
                "Could not open the file because the yaml format is "
                "invalid. Fix the yaml syntax and try again."
            ) from e
        if not isinstance(parsed_yaml, dict):
            raise ValueError(
                "Could not open the file because the top level must be a "
                "dictionary. Use a yaml object with name, vertices, and "
                "edges."
            )
        return parsed_yaml

    def register_callbacks(self) -> None:
        """Register all Dash callbacks for graph editing actions."""
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
            Output("new-edge-from", "value"),
            Input("open-add-edge-modal", "n_clicks"),
            State("dialogue-editor", "selectedNodeData"),
            prevent_initial_call=True
        )
        def autofill_add_edge_from_field(
            open_clicks: int, selected_nodes: list[dict] | None
        ) -> str:
            if not selected_nodes:
                return ""
            node_id = selected_nodes[0].get("id")
            if not node_id:
                return ""
            is_vertex = node_id in self.graph_editor.graph.vertex_dict
            return node_id if is_vertex else ""

        @self.callback(
            Output("edit-text", "value"),
            Output("edit-predicates", "value"),
            Output("edit-effects", "value"),
            Output("edit-from-vertex", "value"),
            Output("edit-to-vertex", "value"),
            Input("open-edit-modal", "n_clicks"),
            State("dialogue-editor", "selectedNodeData"),
            prevent_initial_call=True
        )
        def autofill_edit_modal_fields(
            open_clicks: int, selected_nodes: list[dict] | None
        ) -> tuple[str, str, str, str, str]:
            if not selected_nodes:
                return "", "", "", "", ""
            node_id = selected_nodes[0].get("id")
            if not node_id:
                return "", "", "", "", ""
            node_text = self.get_node_text(node_id)
            if node_text is None:
                return "", "", "", "", ""
            predicates_text = self.get_node_predicates(node_id)
            effects_text = self.get_node_effects(node_id)
            edit_from_vertex, edit_to_vertex = (
                self.get_edge_endpoints_for_edit(node_id)
            )
            return (
                node_text,
                predicates_text,
                effects_text,
                edit_from_vertex,
                edit_to_vertex
            )

        @self.callback(
            Output("new-edge-from", "value"),
            Output("new-edge-to", "value"),
            Output("new-edge-text", "value"),
            Output("new-edge-predicates", "value"),
            Output("new-edge-effects", "value"),
            Input("cancel-add-edge", "n_clicks"),
            Input("save-add-edge", "n_clicks"),
            prevent_initial_call=True
        )
        def clear_add_edge_form(
            cancel_clicks: int, save_clicks: int
        ) -> tuple[str, str, str, str, str]:
            return "", "", "", "", ""

        @self.callback(
            Output("new-vertex-text", "value"),
            Output("new-vertex-effects", "value"),
            Input("cancel-add-vertex", "n_clicks"),
            Input("save-add-vertex", "n_clicks"),
            prevent_initial_call=True
        )
        def clear_add_vertex_form(
            cancel_clicks: int, save_clicks: int
        ) -> tuple[str, str]:
            return "", ""

        @self.callback(
            Output("delete-cascade", "value"),
            Input("cancel-delete-node-modal", "n_clicks"),
            Input("confirm-delete-node-modal", "n_clicks"),
            prevent_initial_call=True
        )
        def clear_delete_form(
                cancel_clicks: int, confirm_clicks: int
        ) -> list:
            return []

        @self.callback(
            Output("edit-text", "value"),
            Output("edit-from-vertex", "value"),
            Output("edit-to-vertex", "value"),
            Output("edit-predicates", "value"),
            Output("edit-effects", "value"),
            Input("cancel-edit-node", "n_clicks"),
            Input("save-edit-node", "n_clicks"),
            prevent_initial_call=True
        )
        def clear_edit_form(
            cancel_clicks: int, save_clicks: int
        ) -> tuple[str, str, str, str, str]:
            return "", "", "", "", ""

        @self.callback(
            Output("dialogue-editor", "elements", allow_duplicate=True),
            Output("action-status", "value", allow_duplicate=True),
            Output("unsaved-changes", "data", allow_duplicate=True),
            Input("confirm-delete-node-modal", "n_clicks"),
            State("dialogue-editor", "selectedNodeData"),
            State("delete-cascade", "value"),
            State("action-status", "value"),
            prevent_initial_call=True
        )
        def on_confirm_delete_node(
            confirm_delete_clicks: int,
            selected_nodes: list[dict] | None,
            delete_cascade: list[str] | None,
            current_log: str | None
        ) -> tuple[object, str, object]:
            if not confirm_delete_clicks:
                raise PreventUpdate
            if not selected_nodes:
                return (
                    no_update,
                    self.action_logger.append_status(
                        current_log,
                        "Could not delete a node because nothing is "
                        "selected. Select a node and try again."
                    ),
                    no_update
                )
            node_id = selected_nodes[0].get("id")
            if not node_id:
                raise PreventUpdate
            was_edge_delete = node_id in self.graph_editor.graph.edge_dict
            was_vertex_delete = node_id in self.graph_editor.graph.vertex_dict
            cascade_delete_enabled = "cascade" in (delete_cascade or [])
            delete_messages = []
            if was_vertex_delete and cascade_delete_enabled:
                delete_messages.append(
                    self.action_logger.build_delete_log(
                        "NPC node",
                        node_id,
                        self.action_logger.get_npc_log_fields(
                            node_id,
                            include_empty=True
                        )
                    )
                )
            if was_edge_delete:
                delete_messages.append(
                    self.action_logger.build_delete_log(
                        "Player node",
                        node_id,
                        self.action_logger.get_player_log_fields(
                            node_id,
                            include_empty=True
                        )
                    )
                )
            if was_vertex_delete and cascade_delete_enabled:
                connected_player_ids = sorted(
                    edge_name
                    for edge_name, edge 
                    in self.graph_editor.graph.edge_dict.items()
                    if edge.from_vertex == node_id 
                    or edge.to_vertex == node_id
                )
                for edge_name in connected_player_ids:
                    delete_messages.append(
                        self.action_logger.build_delete_log(
                            "Player node",
                            edge_name,
                            self.action_logger.get_player_log_fields(
                                edge_name,
                                include_empty=True
                            )
                        )
                    )
            unresolved_connections_created = (
                self.count_unresolved_connections(node_id)
                if was_vertex_delete and not cascade_delete_enabled
                else 0
            )
            npc_log_fields_before_delete = None
            if was_vertex_delete and not cascade_delete_enabled:
                npc_log_fields_before_delete = (
                    self.action_logger.get_npc_log_fields(
                    node_id, include_empty=True
                    )
                )
            try:
                was_removed = self.remove_node(node_id, cascade_delete_enabled)
            except VertexCannotBeDeletedError:
                return (
                    no_update,
                    self.action_logger.append_status(
                        current_log,
                        "You could not delete NPC node "
                        f"{self.action_logger.quote_value(node_id)} "
                        "because the first NPC node cannot be deleted."
                    ),
                    no_update
                )
            if not was_removed:
                return (
                    no_update,
                    self.action_logger.append_status(
                        current_log,
                        "Could not delete "
                        f"{self.action_logger.quote_value(node_id)} "
                        "because it no longer exists. Select a current "
                        "node and try again."
                    ),
                    no_update
                )
            new_log = self.action_logger.append_statuses(
                current_log,
                delete_messages
            )
            if was_vertex_delete and not cascade_delete_enabled:
                npc_delete_message = self.action_logger.build_delete_log(
                    "NPC node",
                    node_id,
                    npc_log_fields_before_delete
                ).removesuffix(".")
                new_log = self.action_logger.append_status(
                    new_log,
                    f"{npc_delete_message}. "
                    f"{unresolved_connections_created} unresolved "
                    "connections were left behind. Open each affected "
                    "Player node and set Source/Target to a valid NPC "
                    "node."
                )
            return (self.get_elements(), new_log, True)

        @self.callback(
            Output("confirm-unsaved-work", "displayed", allow_duplicate=True),
            Output("pending-action", "data", allow_duplicate=True),
            Output("pending-upload", "data", allow_duplicate=True),
            Input("confirm-unsaved-work", "cancel_n_clicks"),
            prevent_initial_call=True
        )
        def on_confirm_unsaved_cancel(
            confirm_unsaved_cancel_clicks: int
        ) -> tuple[bool, str, dict]:
            if not confirm_unsaved_cancel_clicks:
                raise PreventUpdate
            return False, "", {}

        @self.callback(
            Output("action-status", "value", allow_duplicate=True),
            Output("graph-container", "children", allow_duplicate=True),
            Output("unsaved-changes", "data", allow_duplicate=True),
            Output("current-document", "data", allow_duplicate=True),
            Output("confirm-unsaved-work", "displayed", allow_duplicate=True),
            Output("pending-action", "data", allow_duplicate=True),
            Output("pending-upload", "data", allow_duplicate=True),
            Input("confirm-unsaved-work", "submit_n_clicks"),
            State("pending-action", "data"),
            State("pending-upload", "data"),
            State("action-status", "value"),
            prevent_initial_call=True
        )
        def on_confirm_unsaved_submit(
            confirm_unsaved_submit_clicks: int,
            pending_action: str | None,
            pending_upload: dict | None,
            current_log: str | None
        ) -> tuple[object, object, object, object, bool, str, dict]:
            if not confirm_unsaved_submit_clicks:
                raise PreventUpdate
            if pending_action == self.PENDING_ACTION_NEW:
                self.graph_editor.load()
                return (
                    self.action_logger.append_status(
                        current_log,
                        "Discarded unsaved changes and started a new "
                        "dialogue graph."
                    ),
                    self.get_fresh_graph_component(),
                    False,
                    self.normalize_name(self.graph_editor.graph.name),
                    False,
                    "",
                    {}
                )
            if pending_action == self.PENDING_ACTION_UPLOAD:
                queued_upload = pending_upload or {}
                queued_contents = queued_upload.get("contents")
                queued_filename = queued_upload.get("filename") or "Untitled"
                if not queued_contents:
                    return (
                        self.action_logger.append_status(
                            current_log,
                            "Could not open the file because no pending "
                            "file data was found. Select the file again "
                            "and try one more time."
                        ),
                        no_update,
                        no_update,
                        no_update,
                        False,
                        "",
                        {}
                    )
                try:
                    parsed_yaml = self.parse_uploaded_yaml(queued_contents)
                except ValueError as exception:
                    return (
                        self.action_logger.append_status(
                            current_log, str(exception)
                        ),
                        no_update,
                        no_update,
                        no_update,
                        False,
                        "",
                        {}
                    )
                self.graph_editor.load(yaml_data=parsed_yaml)
                loaded_name = self.normalize_name(self.graph_editor.graph.name)
                new_log = self.action_logger.append_status(
                    current_log,
                    "Discarded unsaved changes and opened "
                    f"{self.action_logger.quote_value(queued_filename)}."
                )
                for warning in self.get_runtime_validation_warnings():
                    new_log = self.action_logger.append_status(new_log, warning)
                return (
                    new_log,
                    self.get_fresh_graph_component(),
                    False,
                    loaded_name,
                    False,
                    "",
                    {}
                )
            raise PreventUpdate

        @self.callback(
            Output("action-status", "value", allow_duplicate=True),
            Output("download-yaml", "data", allow_duplicate=True),
            Input("download-graph", "n_clicks"),
            State("action-status", "value"),
            State("current-document", "data"),
            prevent_initial_call=True
        )
        def on_download_graph(
            download_graph_clicks: int,
            current_log: str | None,
            current_document: str | None
        ) -> tuple[str, object]:
            if not download_graph_clicks:
                raise PreventUpdate
            download_name = self.get_filename(current_document)
            new_log = current_log
            for warning in self.get_runtime_validation_warnings():
                new_log = self.action_logger.append_status(new_log, warning)
            return (
                self.action_logger.append_status(
                    new_log,
                    "Saved a copy as "
                    f"{self.action_logger.quote_value(download_name)}."
                ),
                dcc.send_string(
                    self.graph_editor.export_yaml_text(),
                    download_name
                )
            )

        @self.callback(
            Output("action-status", "value", allow_duplicate=True),
            Output("graph-container", "children", allow_duplicate=True),
            Output("unsaved-changes", "data", allow_duplicate=True),
            Output("current-document", "data", allow_duplicate=True),
            Output("confirm-unsaved-work", "displayed", allow_duplicate=True),
            Output("confirm-unsaved-work", "message", allow_duplicate=True),
            Output("pending-action", "data", allow_duplicate=True),
            Output("pending-upload", "data", allow_duplicate=True),
            Input("new-graph", "n_clicks"),
            State("action-status", "value"),
            State("unsaved-changes", "data"),
            prevent_initial_call=True
        )
        def on_new_graph(
            new_graph_clicks: int,
            current_log: str | None,
            unsaved_changes: bool
        ) -> tuple[object, object, object, object, bool, object, str, dict]:
            if not new_graph_clicks:
                raise PreventUpdate
            if unsaved_changes:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    True,
                    "You have unsaved changes. Start a new graph anyway?",
                    self.PENDING_ACTION_NEW,
                    {}
                )
            self.graph_editor.load()
            return (
                self.action_logger.append_status(
                    current_log,
                    "Started a new dialogue graph."
                ),
                self.get_fresh_graph_component(),
                False,
                self.normalize_name(self.graph_editor.graph.name),
                False,
                no_update,
                "",
                {}
            )

        @self.callback(
            Output("dialogue-editor", "elements", allow_duplicate=True),
            Output("action-status", "value", allow_duplicate=True),
            Output("unsaved-changes", "data", allow_duplicate=True),
            Input("save-add-edge", "n_clicks"),
            State("new-edge-from", "value"),
            State("new-edge-to", "value"),
            State("new-edge-text", "value"),
            State("new-edge-predicates", "value"),
            State("new-edge-effects", "value"),
            State("action-status", "value"),
            prevent_initial_call=True
        )
        def on_save_add_edge(
            save_add_edge_clicks: int,
            new_edge_from: str | None,
            new_edge_to: str | None,
            new_edge_text: str | None,
            new_edge_predicates_text: str | None,
            new_edge_effects_text: str | None,
            current_log: str | None
        ) -> tuple[object, str, bool]:
            if not save_add_edge_clicks:
                raise PreventUpdate
            if not new_edge_from or not new_edge_from.strip():
                return (
                    no_update,
                    self.action_logger.append_status(
                        current_log,
                        "Could not create a Player node because Source "
                        "is required. Enter an NPC node ID in Source and "
                        "save again."
                    ),
                    True
                )
            try:
                new_edge_predicates = self.parse_predicates(
                    new_edge_predicates_text
                )
                new_edge_effects = self.parse_effects(new_edge_effects_text)
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
            except ValueError as exception:
                return (
                    no_update,
                    self.action_logger.append_status(
                        current_log,
                        "Could not create a Player node because "
                        f"{exception}. Fix Predicates/Effects and save "
                        "again."
                    ),
                    True
                )
            except VertexNotFoundError as exception:
                endpoint_name = exception.field_name or "Source/Target"
                return (
                    no_update,
                    self.action_logger.append_status(
                        current_log,
                        "Could not create a Player node because "
                        f"{endpoint_name} must be an existing NPC node ID. "
                        f"Enter a valid NPC node ID in {endpoint_name} and "
                        "save again."
                    ),
                    True
                )
            new_log = self.action_logger.append_status(
                current_log,
                self.action_logger.build_create_log(
                    "Player node",
                    new_edge_name,
                    self.action_logger.get_player_log_fields(new_edge_name)
                )
            )
            if normalized_to_vertex is None:
                new_edge = self.graph_editor.graph.edge_dict[new_edge_name]
                auto_created_npc = new_edge.to_vertex
                new_log = self.action_logger.append_status(
                    new_log,
                    self.action_logger.build_create_log(
                        "NPC node",
                        auto_created_npc,
                        self.action_logger.get_npc_log_fields(
                            auto_created_npc
                        )
                    )
                )
            return (self.get_elements(), new_log, True)

        @self.callback(
            Output("dialogue-editor", "elements", allow_duplicate=True),
            Output("action-status", "value", allow_duplicate=True),
            Output("unsaved-changes", "data", allow_duplicate=True),
            Input("save-add-vertex", "n_clicks"),
            State("new-vertex-text", "value"),
            State("new-vertex-effects", "value"),
            State("action-status", "value"),
            prevent_initial_call=True
        )
        def on_save_add_vertex(
            save_add_vertex_clicks: int,
            new_vertex_text: str | None,
            new_vertex_effects_text: str | None,
            current_log: str | None
        ) -> tuple[object, str, object]:
            if not save_add_vertex_clicks or not new_vertex_text:
                raise PreventUpdate
            try:
                new_vertex_effects = self.parse_effects(
                    new_vertex_effects_text
                )
            except ValueError as exception:
                return (
                    no_update,
                    self.action_logger.append_status(
                        current_log,
                        "Could not create an NPC node because "
                        f"{exception}. Fix the Effects field and save "
                        "again."
                    ),
                    True
                )
            new_vertex_name = self.add_vertex(
                new_vertex_text, new_vertex_effects
            )
            create_log = self.action_logger.build_create_log(
                "NPC node",
                new_vertex_name,
                self.action_logger.get_npc_log_fields(new_vertex_name)
            )
            return (
                self.get_elements(),
                self.action_logger.append_status(current_log, create_log),
                True
            )

        @self.callback(
            Output("dialogue-editor", "elements", allow_duplicate=True),
            Output("action-status", "value", allow_duplicate=True),
            Output("unsaved-changes", "data", allow_duplicate=True),
            Input("save-edit-node", "n_clicks"),
            State("dialogue-editor", "selectedNodeData"),
            State("edit-text", "value"),
            State("edit-predicates", "value"),
            State("edit-effects", "value"),
            State("edit-from-vertex", "value"),
            State("edit-to-vertex", "value"),
            State("action-status", "value"),
            prevent_initial_call=True
        )
        def on_save_edit_node(
            save_edit_clicks: int,
            selected_nodes: list[dict] | None,
            edit_text: str | None,
            edit_predicates_text: str | None,
            edit_effects_text: str | None,
            edit_from_vertex: str | None,
            edit_to_vertex: str | None,
            current_log: str | None
        ) -> tuple[object, str, object]:
            if not save_edit_clicks or not selected_nodes:
                raise PreventUpdate
            node_id = selected_nodes[0].get("id")
            if not node_id:
                raise PreventUpdate
            node_type, before_fields = self.action_logger.get_node_log_fields(
                node_id,
                include_empty=False
            )
            try:
                predicates = self.parse_predicates(edit_predicates_text)
                effects = self.parse_effects(edit_effects_text)
            except ValueError as exception:
                return (
                    no_update,
                    self.action_logger.append_status(
                        current_log,
                        f"Could not save changes for {node_type} "
                        f"{self.action_logger.quote_value(node_id)} "
                        f"because {exception}. Fix the invalid field "
                        "and save again."
                    ),
                    True
                )
            was_updated = self.update_node(
                node_id, edit_text or "", predicates, effects
            )
            endpoint_warnings = []
            endpoint_updated = False
            if node_id in self.graph_editor.graph.edge_dict:
                endpoint_updated, endpoint_warnings = (
                    self.update_edge_endpoints(
                        node_id, edit_from_vertex, edit_to_vertex
                    )
                )
            was_anything_updated = was_updated or endpoint_updated
            if not was_anything_updated and not endpoint_warnings:
                raise PreventUpdate
            new_log = current_log
            if was_anything_updated:
                _, after_fields = self.action_logger.get_node_log_fields(
                    node_id,
                    include_empty=False
                )
                new_log = self.action_logger.append_status(
                    new_log,
                    self.action_logger.build_update_log(
                        node_type,
                        node_id,
                        before_fields,
                        after_fields
                    )
                )
            for warning in endpoint_warnings:
                new_log = self.action_logger.append_status(new_log, warning)
            return (
                self.get_elements() if was_anything_updated else no_update,
                new_log,
                True if was_anything_updated else no_update
            )

        @self.callback(
            Output("action-status", "value", allow_duplicate=True),
            Output("unsaved-changes", "data", allow_duplicate=True),
            Output("current-document", "data", allow_duplicate=True),
            Input("save-name", "n_clicks"),
            State("action-status", "value"),
            State("document-name", "value"),
            prevent_initial_call=True
        )
        def on_save_name(
            save_name_clicks: int,
            current_log: str | None,
            document_name: str | None
        ) -> tuple[str, bool, str]:
            if not save_name_clicks:
                raise PreventUpdate
            normalized = self.normalize_name(document_name)
            self.graph_editor.edit_name(normalized)
            return (
                self.action_logger.append_status(
                    current_log,
                    "Saved NPC name as "
                    f"{self.action_logger.quote_value(normalized)}."
                ),
                True,
                normalized
            )

        @self.callback(
            Output("action-status", "value", allow_duplicate=True),
            Output("graph-container", "children", allow_duplicate=True),
            Output("unsaved-changes", "data", allow_duplicate=True),
            Output("current-document", "data", allow_duplicate=True),
            Output("confirm-unsaved-work", "displayed", allow_duplicate=True),
            Output("confirm-unsaved-work", "message", allow_duplicate=True),
            Output("pending-action", "data", allow_duplicate=True),
            Output("pending-upload", "data", allow_duplicate=True),
            Input("upload-graph", "contents"),
            State("upload-graph", "filename"),
            State("action-status", "value"),
            State("unsaved-changes", "data"),
            prevent_initial_call=True
        )
        def on_upload_graph(
            upload_contents: str | None,
            upload_filename: str | None,
            current_log: str | None,
            unsaved_changes: bool
        ) -> tuple[object, object, object, object, bool, object, str, dict]:
            if not upload_contents:
                raise PreventUpdate
            if unsaved_changes:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    True,
                    "You have unsaved changes. Upload and replace anyway?",
                    self.PENDING_ACTION_UPLOAD,
                    {
                        "contents": upload_contents,
                        "filename": upload_filename or "Untitled"
                    }
                )
            try:
                parsed_yaml = self.parse_uploaded_yaml(upload_contents)
            except ValueError as exception:
                return (
                    self.action_logger.append_status(
                        current_log, str(exception)
                    ),
                    no_update,
                    no_update,
                    no_update,
                    False,
                    no_update,
                    "",
                    {}
                )
            self.graph_editor.load(yaml_data=parsed_yaml)
            loaded_name = self.normalize_name(self.graph_editor.graph.name)
            quoted_value = upload_filename or loaded_name
            new_log = self.action_logger.append_status(
                current_log,
                "Opened "
                f"{self.action_logger.quote_value(quoted_value)}."
            )
            for warning in self.get_runtime_validation_warnings():
                new_log = self.action_logger.append_status(new_log, warning)
            return (
                new_log,
                self.get_fresh_graph_component(),
                False,
                loaded_name,
                False,
                no_update,
                "",
                {}
            )

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
            Output("edit-predicates-container", "style"),
            Output("edit-from-vertex-container", "style"),
            Output("edit-to-vertex-container", "style"),
            Input("dialogue-editor", "selectedNodeData")
        )
        def show_hide_edge_only_fields(
            selected_nodes: list[dict] | None
        ) -> tuple[dict, dict, dict]:
            if not selected_nodes:
                return (
                    {"display": "none"},
                    {"display": "none"},
                    {"display": "none"}
                )
            node_id = selected_nodes[0].get("id")
            if not node_id or node_id in self.graph_editor.graph.vertex_dict:
                return (
                    {"display": "none"},
                    {"display": "none"},
                    {"display": "none"}
                )
            return (
                {"display": "block"},
                {"display": "block"},
                {"display": "block"}
            )

        @self.callback(
            Output("document-name", "value"),
            Input("current-document", "data")
        )
        def sync_document_name(current_document: str | None) -> str:
            return self.normalize_name(current_document)

        @self.callback(
            Output("add-edge-modal", "style"),
            Input("open-add-edge-modal", "n_clicks"),
            Input("cancel-add-edge", "n_clicks"),
            Input("save-add-edge", "n_clicks"),
            State("add-edge-modal", "style"),
            prevent_initial_call=True
        )
        def toggle_add_edge_modal(
            open_clicks: int, 
            cancel_clicks: int, 
            save_clicks: int, 
            current_style: dict | None
        ) -> dict[str, str | int]:
            if not ctx.triggered:
                return current_style or get_modal_overlay_style(False)
            triggered_id = ctx.triggered_id
            if triggered_id == "open-add-edge-modal":
                return get_modal_overlay_style(True)
            if triggered_id in ["cancel-add-edge", "save-add-edge"]:
                return get_modal_overlay_style(False)
            return current_style or get_modal_overlay_style(False)
        
        @self.callback(
            Output("add-vertex-modal", "style"),
            Input("open-add-vertex-modal", "n_clicks"),
            Input("cancel-add-vertex", "n_clicks"),
            Input("save-add-vertex", "n_clicks"),
            State("add-vertex-modal", "style"),
            prevent_initial_call=True
        )
        def toggle_add_vertex_modal(
            open_clicks: int, 
            cancel_clicks: int, 
            save_clicks: int, 
            current_style: dict | None
        ) -> dict[str, str | int]:
            if not ctx.triggered:
                return current_style or get_modal_overlay_style(False)
            triggered_id = ctx.triggered_id
            if triggered_id == "open-add-vertex-modal":
                return get_modal_overlay_style(True)
            if triggered_id in ["cancel-add-vertex", "save-add-vertex"]:
                return get_modal_overlay_style(False)
            return current_style or get_modal_overlay_style(False)
        
        @self.callback(
            Output("delete-cascade", "style"),
            Output("delete-cascade", "value"),
            Input("dialogue-editor", "selectedNodeData")
        )
        def toggle_cascade_delete(
            selected_nodes: list[dict] | None
        ) -> tuple[dict, list]:
            if not selected_nodes:
                is_vertex = False
            else:
                node_id = selected_nodes[0].get("id")
                is_vertex = (
                    node_id is not None
                    and node_id in self.graph_editor.graph.vertex_dict
                )
            if is_vertex:
                return (
                    {
                        "marginBottom": "16px", 
                        "color": "#e5e7eb", 
                        "display": "block"
                    },
                    []
                )
            return (
                {"display": "none"},
                []
            )

        @self.callback(
            Output("delete-node-modal", "style"),
            Input("open-delete-modal", "n_clicks"),
            Input("cancel-delete-node-modal", "n_clicks"),
            Input("confirm-delete-node-modal", "n_clicks"),
            State("delete-node-modal", "style"),
            State("dialogue-editor", "selectedNodeData"),
            prevent_initial_call=True
        )
        def toggle_delete_modal(
            open_clicks: int,
            cancel_clicks: int,
            confirm_clicks: int,
            current_style: dict | None,
            selected_nodes: list[dict] | None
        ) -> dict[str, str | int]:
            if not ctx.triggered:
                return current_style or get_modal_overlay_style(False)
            triggered_id = ctx.triggered_id
            if triggered_id == "open-delete-modal" and selected_nodes:
                return get_modal_overlay_style(True)
            if triggered_id in [
                "cancel-delete-node-modal", "confirm-delete-node-modal"
            ]:
                return get_modal_overlay_style(False)
            return current_style or get_modal_overlay_style(False)
        
        @self.callback(
            Output("open-edit-modal", "disabled"),
            Output("open-edit-modal", "style"),
            Output("open-delete-modal", "disabled"),
            Output("open-delete-modal", "style"),
            Input("dialogue-editor", "selectedNodeData")
        )
        def toggle_edit_delete_buttons(
            selected_nodes: list[dict] | None
        ) -> tuple[bool, dict, bool, dict]:
            edit_base_style = {
                "width": "100%",
                "padding": "10px",
                "marginBottom": "8px",
                "border": "1px solid #666",
                "borderRadius": "4px"
            }
            delete_base_style = {
                "width": "100%",
                "padding": "10px",
                "marginBottom": "8px",
                "borderRadius": "4px"
            }
            if not selected_nodes:
                return (
                    True, 
                    {
                        **edit_base_style,
                        "backgroundColor": "#374151",
                        "color": "#6b7280",
                        "cursor": "not-allowed",
                        "opacity": 0.5
                    },
                    True,
                    {
                        **delete_base_style,
                        "backgroundColor": "#4b1c1c",
                        "color": "#6b7280",
                        "border": "1px solid #7f1d1d",
                        "cursor": "not-allowed",
                        "opacity": 0.5
                    }
                )
            return (
                False, 
                {
                    **edit_base_style,
                    "backgroundColor": "#4b5563",
                    "color": "#e6e6e6",
                    "cursor": "pointer"
                },
                False,
                {
                    **delete_base_style,
                    "backgroundColor": "#7f1d1d",
                    "color": "#e6e6e6",
                    "border": "1px solid #c53030",
                    "cursor": "pointer"
                }
            )

        @self.callback(
            Output("edit-node-modal", "style"),
            Input("open-edit-modal", "n_clicks"),
            Input("cancel-edit-node", "n_clicks"),
            Input("save-edit-node", "n_clicks"),
            State("edit-node-modal", "style"),
            State("dialogue-editor", "selectedNodeData"),
            prevent_initial_call=True
        )
        def toggle_edit_modal(
            open_clicks: int,
            cancel_clicks: int,
            save_clicks: int,
            current_style: dict | None,
            selected_nodes: list[dict] | None
        ) -> dict[str, str | int]:
            if not ctx.triggered:
                return current_style or get_modal_overlay_style(False)
            triggered_id = ctx.triggered_id
            if triggered_id == "open-edit-modal" and selected_nodes:
                return get_modal_overlay_style(True)
            if triggered_id in ["cancel-edit-node", "save-edit-node"]:
                return get_modal_overlay_style(False)
            return current_style or get_modal_overlay_style(False)
        
        @self.callback(
            Output("selected-node-display", "children"),
            Input("dialogue-editor", "selectedNodeData")
        )
        def update_selected_node_display(
            selected_nodes: list[dict] | None
        ) -> str:
            if not selected_nodes:
                return "None"
            node_id = selected_nodes[0].get("id", "None")
            return node_id

    def remove_node(self, node_id: str, cascade_delete: bool = False) -> bool:
        """Remove a vertex or edge by node id.

        Args:
            node_id (str): Vertex or edge identifier.
            cascade_delete (bool): Whether to cascade when removing a vertex.

        Returns:
            bool: "True" when a node was removed, otherwise "False".
        """
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
        """Validate and update edge enpoint fields from edit input.

        Args:
            node_id (str): Edge identifier.
            new_from_vertex (str | None): Candidate source vertex id.
            new_to_vertex (str | None): Candidate target vertex id.

        Returns:
            tuple[bool, list[str]]: Update flag and validation warnings.
        """
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
                    "Could not update Source for Player node "
                    f"{self.action_logger.quote_value(node_id)} "
                    "because NPC node "
                    f"{self.action_logger.quote_value(candidate_from_vertex)} "
                    "does not exist. Enter an existing NPC node ID in Source "
                    "and save again."
                )
        elif edge.from_vertex == self.MISSING_VERTEX:
            pass
        else:
            warnings.append(
                "Could not update Source for Player node "
                f"{self.action_logger.quote_value(node_id)} because "
                "Source cannot be empty. Enter an existing NPC node ID in "
                "Source and save again."
            )
        if candidate_to_vertex:
            if candidate_to_vertex in self.graph_editor.graph.vertex_dict:
                if edge.to_vertex != candidate_to_vertex:
                    self.graph_editor.edit_to_vertex(
                        node_id, candidate_to_vertex
                    )
                    was_updated = True
            else:
                warnings.append(
                    "Could not update Target for Player node "
                    f"{self.action_logger.quote_value(node_id)} "
                    "because NPC node "
                    f"{self.action_logger.quote_value(candidate_to_vertex)} "
                    "does not exist. Enter an existing NPC node ID in Target "
                    "and save again."
                )
        elif edge.to_vertex == self.MISSING_VERTEX:
            pass
        else:
            warnings.append(
                "Could not update Target for Player node "
                f"{self.action_logger.quote_value(node_id)} because "
                "Target cannot be empty. Enter an existing NPC node ID in "
                "Target and save again."
            )
        return was_updated, warnings

    def update_node(
        self, 
        node_id: str, 
        new_text: str, 
        new_predicates: list[dict[str, str | int]] | None,
        new_effects: list[dict[str, str | int]] | None
    ) -> bool:
        """Update node text, predicates, and effects when changed.

        Args:
            node_id (str): Vertex or edge identifier.
            new_text (str): New dialogue text.
            new_predicates (list[dict[str, str | int]] | None): Predicates.
            new_effects (list[dict[str, str | int]] | None): Effects.

        Returns:
            bool: "True" when at least one field changed.
        """
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
    """Launch the local Dash dialogue editor application."""
    open_url("http://localhost:8050")
    app = App()
    app.run()

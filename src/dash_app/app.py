from base64 import b64decode
from binascii import Error as BinasciiError
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
from dash.exceptions import PreventUpdate
from dash_cytoscape import load_extra_layouts
from flask import request
from os import PathLike, _exit
from re import sub
from threading import Timer
from typing import Any
from webbrowser import open as open_url
from yaml import YAMLError, safe_load

from dash_app.constants import (
    CascadeValue,
    ElementId,
    FormType,
    HISTORY_LIMIT,
    MenuItemId,
    PendingAction,
    PickField
)
from dash_app.layout import (
    build_log_children,
    get_bottom_panel_style,
    get_center_panel,
    get_graph_component,
    get_index_string,
    get_left_panel,
    get_project_metadata,
    get_right_panel,
    get_shortcuts_overlay,
    get_unsaved_work_modal,
    get_upload_graph
)
from dash_app.logger import Logger
from dash_app.messages import (
    BUTTON_CANCEL,
    BUTTON_CONFIRM_DELETE,
    BUTTON_SAVE,
    CONFIRM_QUIT,
    CONFIRM_UNSAVED_NEW,
    CONFIRM_UNSAVED_QUIT,
    CONFIRM_UNSAVED_UPLOAD,
    DEFAULT_DOCUMENT_NAME,
    DEFAULT_NODE_DISPLAY,
    DIRTY_MARKER,
    ERROR_ADD_NPC_INVALID_FIELD,
    ERROR_ADD_PLAYER_ENDPOINT,
    ERROR_ADD_PLAYER_INVALID_FIELD,
    ERROR_ADD_PLAYER_INVALID_SOURCE,
    ERROR_ADD_PLAYER_SOURCE_REQUIRED,
    ERROR_DELETE_MISSING_NODE,
    ERROR_DELETE_START_VERTEX,
    ERROR_INVALID_EFFECT,
    ERROR_INVALID_PREDICATE,
    ERROR_SAVE_INVALID_FIELD,
    ERROR_SAVE_MISSING_NODE,
    ERROR_UPDATE_ENDPOINT_EMPTY,
    ERROR_UPDATE_ENDPOINT_MISSING,
    ERROR_UPLOAD_INVALID_DATA,
    ERROR_UPLOAD_INVALID_YAML,
    ERROR_UPLOAD_NO_DATA,
    ERROR_UPLOAD_NO_PENDING,
    ERROR_UPLOAD_NOT_DICT,
    ERROR_UPLOAD_NOT_UTF8,
    FIELD_SOURCE,
    FIELD_SOURCE_OR_TARGET,
    FIELD_TARGET,
    LABEL_CASCADE_DELETE,
    LABEL_DOCUMENT,
    LABEL_SELECTED_NODE,
    MENU_DELETE_NODE,
    MENU_EDIT_NODE,
    NODE_TYPE_NPC,
    NODE_TYPE_PLAYER,
    STATUS_DISCARD_NEW,
    STATUS_DISCARD_OPENED,
    STATUS_DISCARD_QUIT,
    STATUS_NEW_GRAPH,
    STATUS_NO_CHANGES,
    STATUS_NOTHING_TO_REDO,
    STATUS_NOTHING_TO_UNDO,
    STATUS_OPENED,
    STATUS_PICK_MODE,
    STATUS_QUIT,
    STATUS_READY,
    STATUS_REDO,
    STATUS_RUNTIME_VALIDATION_HEADER,
    STATUS_RUNTIME_VALIDATION_LINE,
    STATUS_SAVED_COPY,
    STATUS_SAVED_NAME,
    STATUS_UNDO,
    STATUS_UNRESOLVED_CONNECTIONS,
    TITLE_ADD_NPC,
    TITLE_ADD_PLAYER,
    TITLE_DELETE_NODE,
    TITLE_EDIT_NODE,
    TITLE_FORM,
    TOOLTIP_ADD_PLAYER_NO_NPC,
    TOOLTIP_ADD_PLAYER_ENABLED,
    TOOLTIP_DELETE_DISABLED,
    TOOLTIP_DELETE_ENABLED,
    TOOLTIP_EDIT_DISABLED,
    TOOLTIP_EDIT_ENABLED,
    TOOLTIP_MENU_ADD_NPC,
    TOOLTIP_MENU_ADD_PLAYER,
    TOOLTIP_MENU_ADD_PLAYER_FROM_NPC,
    TOOLTIP_MENU_CANCEL,
    TOOLTIP_MENU_DELETE,
    TOOLTIP_MENU_EDIT
)
from dash_app.theme import (
    COLOR_TEXT,
    get_close_button_style,
    get_danger_button_style,
    get_panel_button_danger_disabled_style,
    get_panel_button_danger_style,
    get_panel_button_disabled_style,
    get_panel_button_enabled_style,
    get_primary_button_style,
    get_toolbar_button_disabled_style,
    get_toolbar_button_style,
    SERVER_SHUTDOWN_DELAY_SECONDS,
    SERVER_URL
)
from dialogue_editor.graph_editor import (
    GraphEditor, VertexCannotBeDeletedError, VertexNotFoundError
)
from dialogue_model.codecs import (
    convert_effect_to_text, 
    convert_predicate_to_text, 
    convert_text_to_effect, 
    convert_text_to_predicate
)
from dialogue_model.constants import MISSING_VERTEX, START_VERTEX
from dialogue_validator.graph_validator import collect_validation_errors
from dialogue_viewer.cytoscape_adapter import CytoscapeAdapter

class App(Dash):
    """Dash application wrapper for dialogue graph editing."""

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
        self.reset_history()
        load_extra_layouts()
        author, version = get_project_metadata()
        initial_name = self.normalize_name(self.graph_editor.graph.name)
        initial_log_entries = self.action_logger.append_status(
            None, STATUS_READY
        )
        self.layout = html.Div(
            [
                get_left_panel(initial_name, author, version),
                get_center_panel(self.get_elements(), self.get_context_menu()),
                get_right_panel(),
                dcc.Store(id=ElementId.UNSAVED_CHANGES, data=False),
                dcc.Store(id=ElementId.CURRENT_DOCUMENT, data=initial_name),
                dcc.Store(id=ElementId.PENDING_ACTION, data=""),
                dcc.Store(id=ElementId.ACTION_LOG, data=initial_log_entries),
                dcc.Store(id=ElementId.PENDING_UPLOAD, data={}),
                dcc.Store(id=ElementId.QUIT_SIGNAL, data=0),
                dcc.Store(id=ElementId.SELECTED_NODE_ID, data=None),
                dcc.Store(id=ElementId.BOTTOM_PANEL_VISIBLE, data=False),
                dcc.Store(id=ElementId.BOTTOM_PANEL_FORM_TYPE, data=""),
                dcc.Store(id=ElementId.PICK_MODE_ACTIVE, data=False),
                dcc.Store(id=ElementId.PICK_MODE_FIELD, data=""),
                dcc.Store(id=ElementId.SHORTCUTS_HELP_VISIBLE, data=False),
                dcc.Store(id=ElementId.CONFIRM_UNSAVED_VISIBLE, data=False),
                dcc.Store(
                    id=ElementId.UNDO_REDO_STATE, 
                    data=self.get_undo_redo_state()
                ),
                dcc.Download(id=ElementId.DOWNLOAD_YAML),
                get_unsaved_work_modal(),
                html.Div(
                    id=ElementId.QUIT_CLIENT_TRIGGER, 
                    style={"display": "none"}
                ),
                html.Div(
                    id=ElementId.SHORTCUT_LISTENER_DUMMY,
                    style={"display": "none"}
                ),
                get_shortcuts_overlay()
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

    def build_context_menu_selection(
        self,
        elements: list[dict[str, Any]] | None,
        element_id: str
    ) -> list[dict[str, Any]]:
        """Select one node and explicitly deselect all other elements.

        Args:
            elements (list[dict[str, Any]] | None): Current Cytoscape elements.
            element_id (str): Node id selected through the context menu.

        Returns: 
            list[dict[str, Any]]: Updated Cytoscape elements with the target
                node selected.
        """
        if not elements:
            return []
        selected_elements = []
        for element in elements:
            updated_element = dict(element)
            if (
                element_id 
                and updated_element.get("data", {}).get("id") == element_id
            ):
                updated_element["selected"] = True
            else:
                updated_element["selected"] = False
            selected_elements.append(updated_element)
        return selected_elements

    def capture_snapshot(
        self,
        selected_node_id: str | None,
        document_name: str | None,
        label: str
    ) -> dict[str, Any]:
        """Build a restorable snapshot of the current editor state.

        Args:
            selected_node_id (str | None): Node selected when the snapshot
                is taken, restored on undo/redo.
            document_name (str | None): Document name shown for this state.
            label (str): Description of the action that produced this state,
                echoed by undo/redo log messages.

        Returns:
            dict[str, Any]: Snapshot mapping consumed by restore_snapshot.
        """
        return {
            "yaml": self.graph_editor.export_yaml_text(),
            "next_vertex_index": self.graph_editor.next_vertex_index,
            "next_edge_index": self.graph_editor.next_edge_index,
            "selected_node_id": selected_node_id,
            "document_name": document_name,
            "label": label
        }

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

    def get_add_player_button_state(
        self
    ) -> tuple[bool, dict[str, str | int], str]:
        """Build disabled state, style, and tooltip for Add Player button.

        Returns:
            tuple[bool, dict[str, str | int], str]: Disabled flag, style,
                and tooltip text.
        """
        has_vertices = bool(self.graph_editor.graph.vertex_dict)
        if not has_vertices:
            return (
                True,
                get_panel_button_disabled_style(),
                TOOLTIP_ADD_PLAYER_NO_NPC
            )
        return (
            False,
            get_panel_button_enabled_style(),
            TOOLTIP_ADD_PLAYER_ENABLED
        )

    def get_context_action_panel_outputs(
        self,
        menu_item_id: str,
        element_id: str | None,
        current_log: list[dict[str, str]] | None
    ) -> tuple[
        list[dict[str, str]] | Any,
        dict[str, str],
        bool,
        str,
        str,
        str,
        str,
        str,
        str,
        str,
        list[str],
        bool,
        str,
        str,
        dict[str, str],
        str,
        dict[str, str]
    ]:
        """Translate a context menu action into bottom panel state.

        Args:
            menu_item_id (str): Identifier of the clicked context menu item.
            element_id (str | None): Node id associated with the menu click.
            current_log (list[dict[str, str]] | None): Current action log
                entries.

        Returns:
            tuple[list[dict[str, str]] | Any, dict[str, str], bool, str, 
            str, str, str, str, str, str, list[str], bool, str, str, 
            dict[str, str], str, dict[str, str]]: Action log entries 
                followed by bottom panel outputs in callback order.

        Raises:
            PreventUpdate: If no action should be performed.
        """
        default_save_button_style = get_primary_button_style()
        delete_save_button_style = get_danger_button_style()
        close_button_style = get_close_button_style()
        if menu_item_id == MenuItemId.ADD_NPC:
            return (
                no_update,
                get_bottom_panel_style(True),
                True,
                FormType.ADD_VERTEX,
                TITLE_ADD_NPC,
                "",
                "",
                "",
                "",
                "",
                [],
                False,
                "",
                BUTTON_SAVE,
                default_save_button_style,
                BUTTON_CANCEL,
                close_button_style
            )
        if menu_item_id == MenuItemId.ADD_PLAYER:
            return (
                no_update,
                get_bottom_panel_style(True),
                True,
                FormType.ADD_EDGE,
                TITLE_ADD_PLAYER,
                "",
                "",
                "",
                "",
                "",
                [],
                False,
                "",
                BUTTON_SAVE,
                default_save_button_style,
                BUTTON_CANCEL,
                close_button_style
            )
        if menu_item_id == MenuItemId.ADD_PLAYER_DIALOGUE:
            if (
                not element_id 
                or element_id in self.graph_editor.graph.edge_dict
            ):
                return (
                    self.action_logger.append_status(
                        current_log, ERROR_ADD_PLAYER_INVALID_SOURCE
                    ),
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update
                )
            return (
                no_update,
                get_bottom_panel_style(True),
                True,
                FormType.ADD_EDGE,
                TITLE_ADD_PLAYER,
                "",
                element_id or "",
                "",
                "",
                "",
                [],
                False,
                "",
                BUTTON_SAVE,
                default_save_button_style,
                BUTTON_CANCEL,
                close_button_style
            )
        if menu_item_id == MenuItemId.EDIT_NODE and element_id:
            node_text = self.get_node_text(element_id)
            predicates_text = self.get_node_predicates(element_id)
            effects_text = self.get_node_effects(element_id)
            edit_from_vertex, edit_to_vertex = (
                self.get_edge_endpoints_for_edit(element_id)
            )
            is_edge = element_id in self.graph_editor.graph.edge_dict
            return (
                no_update,
                get_bottom_panel_style(True),
                True,
                FormType.EDIT_EDGE if is_edge else FormType.EDIT_VERTEX,
                TITLE_EDIT_NODE,
                node_text or "",
                edit_from_vertex,
                edit_to_vertex,
                predicates_text,
                effects_text,
                [],
                False,
                "",
                BUTTON_SAVE,
                default_save_button_style,
                BUTTON_CANCEL,
                close_button_style
            )
        if menu_item_id == MenuItemId.DELETE_NODE and element_id:
            if element_id == START_VERTEX:
                return (
                    self.action_logger.append_status(
                        current_log,
                        ERROR_DELETE_START_VERTEX.format(
                            node_id=self.action_logger.quote_value(
                                START_VERTEX
                            )
                        )
                    ),
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update
                )
            return (
                no_update,
                get_bottom_panel_style(True),
                True,
                FormType.DELETE,
                TITLE_DELETE_NODE,
                "",
                "",
                "",
                "",
                "",
                [],
                False,
                "",
                BUTTON_CONFIRM_DELETE,
                delete_save_button_style,
                BUTTON_CANCEL,
                close_button_style
            )
        raise PreventUpdate

    def get_context_menu(self) -> list[dict[str, str | list[str]]]:
        """Build the right click context menu for the graph.

        The menu is defined once and never changes during a session. Each
        item uses availableOn to scope visibility to the correct target
        type. 

        Returns:
            list[dict[str, str | list[str]]]: Context menu item mappings.
        """
        return [
            {
                "id": MenuItemId.EDIT_NODE,
                "label": MENU_EDIT_NODE,
                "tooltipText": TOOLTIP_MENU_EDIT,
                "availableOn": ["node"]
            },
            {
                "id": MenuItemId.ADD_PLAYER_DIALOGUE,
                "label": TITLE_ADD_PLAYER,
                "tooltipText": TOOLTIP_MENU_ADD_PLAYER_FROM_NPC,
                "availableOn": ["node"]
            },
            {
                "id": MenuItemId.DELETE_NODE,
                "label": MENU_DELETE_NODE,
                "tooltipText": TOOLTIP_MENU_DELETE,
                "availableOn": ["node"]
            },
            {
                "id": MenuItemId.ADD_NPC,
                "label": TITLE_ADD_NPC,
                "tooltipText": TOOLTIP_MENU_ADD_NPC,
                "availableOn": ["canvas", "edge"]
            },
            {
                "id": MenuItemId.ADD_PLAYER,
                "label": TITLE_ADD_PLAYER,
                "tooltipText": TOOLTIP_MENU_ADD_PLAYER,
                "availableOn": ["canvas", "edge"]
            },
            {
                "id": MenuItemId.CANCEL,
                "label": BUTTON_CANCEL,
                "tooltipText": TOOLTIP_MENU_CANCEL,
                "availableOn": ["canvas", "edge", "node"]
            }
        ]

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
                LABEL_SELECTED_NODE.format(node_id=DEFAULT_NODE_DISPLAY),
                [
                    {
                        "label": LABEL_CASCADE_DELETE, 
                        "value": CascadeValue.CASCADE, 
                        "disabled": False
                    }
                ],
                current_delete_cascade or []
            )
        node_id = selected_nodes[0].get("id", DEFAULT_NODE_DISPLAY)
        is_edge = node_id in self.graph_editor.graph.edge_dict
        options = [
            {
                "label": LABEL_CASCADE_DELETE, 
                "value": CascadeValue.CASCADE, 
                "disabled": is_edge
            }
        ]
        value = [] if is_edge else (current_delete_cascade or [])
        return (LABEL_SELECTED_NODE.format(node_id=node_id), options, value)

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
            "" if edge.from_vertex == MISSING_VERTEX else edge.from_vertex
        )
        to_vertex = (
            "" if edge.to_vertex == MISSING_VERTEX else edge.to_vertex
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
            self.get_elements(), 
            str(self.graph_render_count), 
            self.get_context_menu()
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
            STATUS_RUNTIME_VALIDATION_HEADER.format(count=len(errors)),
            *[
                STATUS_RUNTIME_VALIDATION_LINE.format(error=error)
                for error in errors
            ]
        ]
        return warning_lines

    def get_undo_redo_state(self) -> dict[str, bool]:
        """Return whether undo and redo are currently available.

        Returns:
            dict[str, bool]: Mapping with "can_undo" and "can_redo" flags
                derived from the history cursor position.
        """
        return {
            "can_undo": self.history_cursor > 0,
            "can_redo": self.history_cursor < len(self.history) - 1
        }

    def normalize_name(self, name: str | None) -> str:
        """Normalize an NPC name to a non-empty display value.

        Args:
            name (str | None): NPC name.

        Returns:
            str: Stripped name, or "Untitled" when empty.
        """
        normalized = (name or "").strip()
        return normalized if normalized else DEFAULT_DOCUMENT_NAME

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
                    ERROR_INVALID_EFFECT.format(
                        line_number=line_number, line=stripped_line
                    )
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
                    ERROR_INVALID_PREDICATE.format(
                        line_number=line_number, line=stripped_line
                    )
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
            raise ValueError(ERROR_UPLOAD_NO_DATA)
        _, encoded_content = upload_contents.split(",", 1)
        try:
            raw_bytes = b64decode(encoded_content, validate=True)
        except BinasciiError as e:
            raise ValueError(ERROR_UPLOAD_INVALID_DATA) from e
        try:
            decoded_text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(ERROR_UPLOAD_NOT_UTF8) from e
        try:
            parsed_yaml = safe_load(decoded_text) or {}
        except YAMLError as e:
            raise ValueError(ERROR_UPLOAD_INVALID_YAML) from e
        if not isinstance(parsed_yaml, dict):
            raise ValueError(ERROR_UPLOAD_NOT_DICT)
        return parsed_yaml

    def record_history(
        self,
        log_entries: list[dict[str, str]] | None,
        selected_node_id: str | None,
        document_name: str | None
    ) -> dict[str, bool]:
        """Capture a new snapshot when the graph changed since the last one.

        Args:
            log_entries (list[dict[str, str]] | None): Current action log.
            selected_node_id (str | None): Currently selected node.
            document_name (str | None): Current document name.

        Returns:
            dict[str, bool]: Updated undo/redo availability.
        """
        current_yaml = self.graph_editor.export_yaml_text()
        if current_yaml == self.history[self.history_cursor]["yaml"]:
            return self.get_undo_redo_state()
        label = ""
        if log_entries:
            label = str(log_entries[-1].get("message", "")).split("\n")[0]
        self.history = self.history[: self.history_cursor+1]
        self.history.append(
            self.capture_snapshot(selected_node_id, document_name, label)
        )
        self.history_cursor += 1
        self.trim_history()
        return self.get_undo_redo_state()

    def register_callbacks(self) -> None:
        """Register all Dash callbacks for graph editing actions."""
        self.clientside_callback(
            """
            function(quitSignal) {
                if (!quitSignal) {
                    return "";
                }
                window.setTimeout(function() {
                    window.close();
                }, 0);
                return "";
            }
            """,
            Output(ElementId.QUIT_CLIENT_TRIGGER, "children"),
            Input(ElementId.QUIT_SIGNAL, "data"),
            prevent_initial_call=True
        )

        self.clientside_callback(
            """
            function(bottomPanelVisible, pickModeActive, formType,
                     helpVisible, confirmVisible) {
                if (!window.dmShortcuts) {
                    window.dmShortcuts = {installed: false, state: {}};
                }
                window.dmShortcuts.state = {
                    bottomPanelVisible: !!bottomPanelVisible,
                    pickModeActive: !!pickModeActive,
                    formType: formType || "",
                    helpVisible: !!helpVisible,
                    confirmVisible: !!confirmVisible
                };
                if (window.dmShortcuts.installed) {
                    return "";
                }
                window.dmShortcuts.installed = true;
                var setProps = function(id, props) {
                    if (window.dash_clientside
                        && window.dash_clientside.set_props) {
                        window.dash_clientside.set_props(id, props);
                    }
                };
                var clickById = function(id) {
                    var el = document.getElementById(id);
                    if (el) { el.click(); }
                };
                var isEditableTarget = function() {
                    var el = document.activeElement;
                    if (!el) { return false; }
                    var tag = el.tagName;
                    return (
                        tag === "INPUT" || tag === "TEXTAREA"
                        || el.isContentEditable
                    );
                };
                var getCy = function() {
                    var container = document.getElementById(
                        "dialogue-editor"
                    );
                    if (!container || !container._cyreg
                        || !container._cyreg.cy) {
                        return null;
                    }
                    return container._cyreg.cy;
                };
                var arrowKeys = {
                    ArrowUp: true,
                    ArrowDown: true,
                    ArrowLeft: true,
                    ArrowRight: true
                };
                var recenterIfOffscreen = function(cy, node) {
                    var extent = cy.extent();
                    var position = node.position();
                    var outside = (
                        position.x < extent.x1 || position.x > extent.x2
                        || position.y < extent.y1 || position.y > extent.y2
                    );
                    if (outside) {
                        cy.animate({center: {eles: node}}, {duration: 150});
                    }
                };
                var selectOnly = function(cy, previous, node) {
                    cy.batch(function() {
                        if (previous) { previous.unselect(); }
                        node.select();
                    });
                    recenterIfOffscreen(cy, node);
                };
                var selectNearestVertexToCenter = function(cy) {
                    var vertices = cy.nodes().filter(function(node) {
                        return !node.data("is_edge_node");
                    });
                    if (vertices.length === 0) { return; }
                    var extent = cy.extent();
                    var centerX = (extent.x1 + extent.x2) / 2;
                    var centerY = (extent.y1 + extent.y2) / 2;
                    var best = null;
                    var bestDistance = Infinity;
                    vertices.forEach(function(node) {
                        var position = node.position();
                        var distance = Math.hypot(
                            position.x - centerX, position.y - centerY
                        );
                        if (distance < bestDistance) {
                            bestDistance = distance;
                            best = node;
                        }
                    });
                    if (best) { selectOnly(cy, null, best); }
                };
                var findVerticalNeighbor = function(cy, source, goingUp) {
                    var origin = source.position();
                    var tolerance = computeRowTolerance(cy);
                    var pickFrom = function(nodes) {
                        var candidates = [];
                        nodes.forEach(function(node) {
                            if (node.id() === source.id()) { return; }
                            var position = node.position();
                            var forward = goingUp
                            ? -(position.y - origin.y)
                            : (position.y - origin.y);
                            if (forward <= tolerance) { return; }
                            candidates.push({
                                node: node,
                                forward: forward,
                                dx: Math.abs(position.x - origin.x),
                                x: position.x
                            });
                        });
                        if (candidates.length === 0) { return null; }
                        var nearestForward = Infinity;
                        candidates.forEach(function(candidate) {
                            if (candidate.forward < nearestForward) {
                                nearestForward = candidate.forward;
                            }
                        });
                        var best = null;
                        candidates.forEach(function(candidate) {
                            if (candidate.forward - nearestForward > tolerance) {
                                return;
                            }
                            if (best === null
                                || candidate.dx < best.dx - 1e-9
                                || (Math.abs(candidate.dx - best.dx) <= 1e-9
                                    && candidate.x < best.x)) {
                                best = candidate;
                            }
                        });
                        return best ? best.node : null;
                    };
                    var connected = pickFrom(source.neighborhood().nodes());
                    return connected !== null
                        ? connected
                        : pickFrom(cy.nodes());
                };
                var computeRowTolerance = function(cy) {
                    var ys = cy.nodes().map(function(node) {
                        return node.position().y;
                    });
                    ys.sort(function(a, b) { return a - b; });
                    var minGap = Infinity;
                    for (var i = 1; i < ys.length; i++) {
                        var gap = ys[i] - ys[i - 1];
                        if (gap > 1e-6 && gap < minGap) { minGap = gap; }
                    }
                    return isFinite(minGap) ? minGap / 2 : Infinity;
                };
                var findRowNeighbor = function(cy, source, goingRight) {
                    var origin = source.position();
                    var tolerance = computeRowTolerance(cy);
                    var members = [];
                    cy.nodes().forEach(function(node) {
                        if (Math.abs(node.position().y - origin.y)
                            <= tolerance) {
                            members.push(node);
                        }
                    });
                    if (members.length <= 1) { return null; }
                    members.sort(function(a, b) {
                        return a.position().x - b.position().x;
                    });
                    var index = -1;
                    for (var i = 0; i < members.length; i++) {
                        if (members[i].id() === source.id()) {
                            index = i;
                            break;
                        }
                    }
                    if (index === -1) { return null; }
                    var count = members.length;
                    var nextIndex = goingRight
                        ? (index + 1) % count
                        : (index - 1 + count) % count;
                    return members[nextIndex];
                };
                var navigateSelection = function(direction) {
                    var cy = getCy();
                    if (!cy) { return; }
                    var selected = cy.nodes(":selected");
                    if (selected.length === 0) {
                        selectNearestVertexToCenter(cy);
                        return;
                    }
                    var source = selected[0];
                    var target = null;
                    if (direction === "ArrowUp") {
                        target = findVerticalNeighbor(cy, source, true);
                    } else if (direction === "ArrowDown") {
                        target = findVerticalNeighbor(cy, source, false);
                    } else if (direction === "ArrowRight") {
                        target = findRowNeighbor(cy, source, true);
                    } else if (direction === "ArrowLeft") {
                        target = findRowNeighbor(cy, source, false);
                    }
                    if (target) { selectOnly(cy, source, target); }
                };
                document.addEventListener("keydown", function(event) {
                    var state = window.dmShortcuts.state || {};
                    var key = event.key;
                    if (state.confirmVisible) {
                        if (key === "Enter") {
                            event.preventDefault();
                            clickById("confirm-unsaved-confirm");
                        } else if (key === "Escape") {
                            event.preventDefault();
                            clickById("confirm-unsaved-cancel");
                        }
                        return;
                    }
                    if (key === "Escape") {
                        if (state.helpVisible) {
                            setProps(
                                "shortcuts-help-visible", {data: false}
                            );
                            return;
                        }
                        if (state.pickModeActive) {
                            setProps("pick-mode-active", {data: false});
                            setProps("pick-mode-field", {data: ""});
                            return;
                        }
                        if (state.bottomPanelVisible) {
                            clickById("bottom-panel-close");
                            return;
                        }
                        return;
                    }
                    if (key === "?" && state.helpVisible) {
                        event.preventDefault();
                        setProps("shortcuts-help-visible", {data: false});
                        return;
                    }
                    if (state.helpVisible) {
                        return;
                    }
                    if (state.bottomPanelVisible) {
                        if (event.ctrlKey && !event.metaKey
                            && !event.altKey && key === "Enter") {
                            event.preventDefault();
                            clickById("bottom-panel-save");
                            return;
                        }
                        if (state.formType === "delete" && key === "Enter") {
                            event.preventDefault();
                            clickById("bottom-panel-save");
                        }
                        return;
                    }
                    if (isEditableTarget()) {
                        return;
                    }
                    if (event.ctrlKey && event.shiftKey
                        && !event.metaKey && !event.altKey
                        && key.toLowerCase() === "z") {
                        event.preventDefault();
                        clickById("redo-action");
                        return;
                    }
                    if (event.ctrlKey && !event.metaKey
                        && !event.altKey && !event.shiftKey) {
                        var lowered = key.toLowerCase();
                        if (lowered === "n") {
                            event.preventDefault();
                            clickById("new-graph");
                            return;
                        }
                        if (lowered === "o") {
                            event.preventDefault();
                            clickById("upload-graph-button");
                            return;
                        }
                        if (lowered === "s") {
                            event.preventDefault();
                            clickById("download-graph");
                            return;
                        }
                        if (lowered === "q") {
                            event.preventDefault();
                            clickById("quit-editor");
                            return;
                        }
                        if (lowered === "z") {
                            event.preventDefault();
                            clickById("undo-action");
                            return;
                        }
                        if (lowered === "y") {
                            event.preventDefault();
                            clickById("redo-action");
                            return;
                        }
                        return;
                    }
                    if (event.ctrlKey || event.metaKey || event.altKey) {
                        return;
                    }
                    if (key === "n" || key === "N") {
                        clickById("open-add-vertex-modal");
                    } else if (key === "p" || key === "P") {
                        clickById("open-add-edge-modal");
                    } else if (key === "e" || key === "E") {
                        clickById("open-edit-modal");
                    } else if (key === "Delete" || key === "Backspace") {
                        event.preventDefault();
                        clickById("open-delete-modal");
                    } else if (arrowKeys.hasOwnProperty(key)) {
                        event.preventDefault();
                        navigateSelection(key);
                    } else if (key === "?") {
                        event.preventDefault();
                        setProps("shortcuts-help-visible", {data: true});
                    }
                });
                return "";
            }
            """,
            Output(ElementId.SHORTCUT_LISTENER_DUMMY, "children"),
            Input(ElementId.BOTTOM_PANEL_VISIBLE, "data"),
            Input(ElementId.PICK_MODE_ACTIVE, "data"),
            Input(ElementId.BOTTOM_PANEL_FORM_TYPE, "data"),
            Input(ElementId.SHORTCUTS_HELP_VISIBLE, "data"),
            Input(ElementId.CONFIRM_UNSAVED_VISIBLE, "data")
        )

        self.clientside_callback(
            """
            function(helpVisible) {
                return {
                    "display": helpVisible ? "flex" : "none",
                    "position": "fixed",
                    "top": "0",
                    "left": "0",
                    "right": "0",
                    "bottom": "0",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "backgroundColor": "rgba(0, 0, 0, 0.6)",
                    "zIndex": "1000"
                };
            }
            """,
            Output(ElementId.SHORTCUTS_OVERLAY, "style"),
            Input(ElementId.SHORTCUTS_HELP_VISIBLE, "data")
        )

        self.clientside_callback(
            """
            function(confirmVisible) {
                return {
                    "display": confirmVisible ? "flex" : "none",
                    "position": "fixed",
                    "top": "0",
                    "left": "0",
                    "right": "0",
                    "bottom": "0",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "backgroundColor": "rgba(0, 0, 0, 0.6)",
                    "zIndex": "1000"
                };
            }
            """,
            Output(ElementId.CONFIRM_UNSAVED_WORK, "style"),
            Input(ElementId.CONFIRM_UNSAVED_VISIBLE, "data")
        )

        self.clientside_callback(
            """
            function(openClicks, closeClicks) {
                var context = window.dash_clientside.callback_context;
                var triggered = context ? context.triggered : [];
                if (!triggered || triggered.length === 0) {
                    return window.dash_clientside.no_update;
                }
                var triggeredId = triggered[0].prop_id.split(".")[0];
                if (triggeredId === "open-shortcuts-help") {
                    return true;
                }
                if (triggeredId === "shortcuts-help-close") {
                    return false;
                }
                return window.dash_clientside.no_update;
            }
            """,
            Output(ElementId.SHORTCUTS_HELP_VISIBLE, "data"),
            Input(ElementId.OPEN_SHORTCUTS_HELP, "n_clicks"),
            Input(ElementId.SHORTCUTS_HELP_CLOSE, "n_clicks"),
            prevent_initial_call=True
        )

        @self.callback(
            Output(ElementId.PICK_MODE_ACTIVE, "data"),
            Output(ElementId.PICK_MODE_FIELD, "data"),
            Input(ElementId.BOTTOM_FORM_PICK_SOURCE, "n_clicks"),
            Input(ElementId.BOTTOM_FORM_PICK_TARGET, "n_clicks"),
            State(ElementId.PICK_MODE_ACTIVE, "data"),
            prevent_initial_call=True
        )
        def activate_pick_mode(
            pick_source_clicks: int,
            pick_target_clicks: int,
            is_active: bool
        ) -> tuple[bool, str]:
            if not ctx.triggered:
                raise PreventUpdate
            triggered_id = ctx.triggered_id
            if triggered_id == ElementId.BOTTOM_FORM_PICK_SOURCE:
                return True, PickField.SOURCE
            if triggered_id == ElementId.BOTTOM_FORM_PICK_TARGET:
                return True, PickField.TARGET
            raise PreventUpdate

        @self.callback(
            Output(ElementId.DIALOGUE_EDITOR, "elements", allow_duplicate=True),
            Input(ElementId.DIALOGUE_EDITOR, "selectedNodeData"),
            State(ElementId.DIALOGUE_EDITOR, "elements"),
            prevent_initial_call=True
        )
        def enforce_single_selection(
            selected_nodes: list[dict[str, Any]] | None,
            elements: list[dict[str, Any]] | None
        ) -> list[dict[str, Any]]:
            if not elements:
                raise PreventUpdate
            selected_ids_in_elements = [
                element.get("data", {}).get("id", "")
                for element in elements
                if element.get("selected") is True
            ]
            if not selected_nodes:
                if not selected_ids_in_elements:
                    raise PreventUpdate
                return self.build_context_menu_selection(elements, "")
            last_selected_id = selected_nodes[-1].get("id", "")
            if not last_selected_id:
                raise PreventUpdate
            if selected_ids_in_elements == [last_selected_id]:
                raise PreventUpdate
            return self.build_context_menu_selection(
                elements, last_selected_id
            )

        @self.callback(
            Output(ElementId.BOTTOM_PANEL, "style"),
            Output(ElementId.BOTTOM_PANEL_VISIBLE, "data"),
            Output(ElementId.BOTTOM_PANEL_FORM_TYPE, "data"),
            Output(ElementId.BOTTOM_PANEL_TITLE, "children"),
            Output(ElementId.BOTTOM_FORM_DIALOGUE, "value"),
            Output(ElementId.BOTTOM_FORM_SOURCE, "value"),
            Output(ElementId.BOTTOM_FORM_TARGET, "value"),
            Output(ElementId.BOTTOM_FORM_PREDICATES, "value"),
            Output(ElementId.BOTTOM_FORM_EFFECTS, "value"),
            Output(ElementId.BOTTOM_FORM_CASCADE, "value"),
            Output(ElementId.PICK_MODE_ACTIVE, "data"),
            Output(ElementId.PICK_MODE_FIELD, "data"),
            Output(ElementId.BOTTOM_PANEL_SAVE, "children"),
            Output(ElementId.BOTTOM_PANEL_SAVE, "style"),
            Output(ElementId.BOTTOM_PANEL_CLOSE, "children"),
            Output(ElementId.BOTTOM_PANEL_CLOSE, "style"),
            Output(ElementId.SELECTED_NODE_ID, "data", allow_duplicate=True),
            Input(ElementId.BOTTOM_PANEL_CLOSE, "n_clicks"),
            Input(ElementId.BOTTOM_PANEL_SAVE, "n_clicks"),
            Input(ElementId.OPEN_ADD_EDGE_MODAL, "n_clicks"),
            Input(ElementId.OPEN_ADD_VERTEX_MODAL, "n_clicks"),
            Input(ElementId.OPEN_EDIT_MODAL, "n_clicks"),
            Input(ElementId.OPEN_DELETE_MODAL, "n_clicks"),
            State(ElementId.BOTTOM_PANEL_VISIBLE, "data"),
            State(ElementId.DIALOGUE_EDITOR, "selectedNodeData"),
            prevent_initial_call=True
        )
        def manage_bottom_panel(
            close_clicks: int,
            save_clicks: int,
            open_edge_clicks: int,
            open_vertex_clicks: int,
            open_edit_clicks: int,
            open_delete_clicks: int,
            is_visible: bool,
            selected_nodes: list[dict] | None
        ) -> tuple[
            dict[str, str],
            bool,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            list,
            bool,
            str,
            str,
            dict[str, str],
            str,
            dict[str, str],
            str | None
        ]:
            if not ctx.triggered:
                raise PreventUpdate
            default_save_button_style = get_primary_button_style()
            delete_save_button_style = get_danger_button_style()
            close_button_style = get_close_button_style()
            triggered_id = ctx.triggered_id
            if triggered_id == ElementId.BOTTOM_PANEL_CLOSE:
                return (
                    get_bottom_panel_style(False),
                    False,
                    "",
                    TITLE_FORM,
                    "",
                    "",
                    "",
                    "",
                    "",
                    [],
                    False,
                    "",
                    BUTTON_SAVE,
                    default_save_button_style,
                    BUTTON_CANCEL,
                    close_button_style,
                    None
                )
            if triggered_id == ElementId.BOTTOM_PANEL_SAVE:
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    False,
                    "",
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    no_update
                )
            if triggered_id == ElementId.OPEN_ADD_EDGE_MODAL:
                if not self.graph_editor.graph.vertex_dict:
                    raise PreventUpdate

                return (
                    get_bottom_panel_style(True),
                    True,
                    FormType.ADD_EDGE,
                    TITLE_ADD_PLAYER,
                    "",
                    (
                        selected_nodes[0].get("id", "")
                        if (
                            selected_nodes
                            and selected_nodes[0].get("id", "")
                            in self.graph_editor.graph.vertex_dict
                        )
                        else ""
                    ),
                    "",
                    "",
                    "",
                    [],
                    False,
                    "",
                    BUTTON_SAVE,
                    default_save_button_style,
                    BUTTON_CANCEL,
                    close_button_style,
                    None
                )
            if triggered_id == ElementId.OPEN_ADD_VERTEX_MODAL:
                return (
                    get_bottom_panel_style(True),
                    True,
                    FormType.ADD_VERTEX,
                    TITLE_ADD_NPC,
                    "",
                    "",
                    "",
                    "",
                    "",
                    [],
                    False,
                    "",
                    BUTTON_SAVE,
                    default_save_button_style,
                    BUTTON_CANCEL,
                    close_button_style,
                    None
                )
            if triggered_id == ElementId.OPEN_EDIT_MODAL:
                if not selected_nodes:
                    raise PreventUpdate
                node_id = selected_nodes[0].get("id", "")
                if not node_id:
                    raise PreventUpdate
                node_text = self.get_node_text(node_id)
                predicates_text = self.get_node_predicates(node_id)
                effects_text = self.get_node_effects(node_id)
                edit_from_vertex, edit_to_vertex = (
                    self.get_edge_endpoints_for_edit(node_id)
                )
                is_edge = node_id in self.graph_editor.graph.edge_dict
                form_type = (
                    FormType.EDIT_EDGE if is_edge else FormType.EDIT_VERTEX
                )
                title = TITLE_EDIT_NODE
                return (
                    get_bottom_panel_style(True),
                    True,
                    form_type,
                    title,
                    node_text or "",
                    edit_from_vertex,
                    edit_to_vertex,
                    predicates_text,
                    effects_text,
                    [],
                    False,
                    "",
                    BUTTON_SAVE,
                    default_save_button_style,
                    BUTTON_CANCEL,
                    close_button_style,
                    node_id
                )
            if triggered_id == ElementId.OPEN_DELETE_MODAL:
                if not selected_nodes:
                    raise PreventUpdate
                return (
                    get_bottom_panel_style(True),
                    True,
                    FormType.DELETE,
                    TITLE_DELETE_NODE,
                    "",
                    "",
                    "",
                    "",
                    "",
                    [],
                    False,
                    "",
                    BUTTON_CONFIRM_DELETE,
                    delete_save_button_style,
                    BUTTON_CANCEL,
                    close_button_style,
                    selected_nodes[0].get("id", "")
                )
            raise PreventUpdate

        @self.callback(
            Output(ElementId.BOTTOM_FORM_DIALOGUE_CONTAINER, "style"),
            Output(ElementId.BOTTOM_FORM_EFFECTS_CONTAINER, "style"),
            Output(ElementId.BOTTOM_FORM_SOURCE_CONTAINER, "style"),
            Output(ElementId.BOTTOM_FORM_TARGET_CONTAINER, "style"),
            Output(ElementId.BOTTOM_FORM_PREDICATES_CONTAINER, "style"),
            Output(ElementId.BOTTOM_FORM_CASCADE_CONTAINER, "style"),
            Output(ElementId.BOTTOM_FORM_DELETE_MESSAGE_CONTAINER, "style"),
            Input(ElementId.BOTTOM_PANEL_FORM_TYPE, "data")
        )
        def manage_bottom_panel_fields(
            form_type: str
        ) -> tuple[dict, dict, dict, dict, dict, dict, dict]:
            hidden_style = {"display": "none"}
            dialogue_visible = {"marginBottom": "12px"}
            source_visible = {
                "flex": "1", 
                "minWidth": "280px", 
                "marginRight": "8px"
            }
            target_visible = {"flex": "1", "minWidth": "280px"}
            predicates_visible = {
                "flex": "1", 
                "minWidth": "300px", 
                "marginRight": "8px"
            }
            effects_visible = {"flex": "1", "minWidth": "300px"}
            if form_type in (FormType.ADD_EDGE, FormType.EDIT_EDGE):
                return (
                    dialogue_visible,
                    effects_visible,
                    source_visible,
                    target_visible,
                    predicates_visible,
                    hidden_style,
                    hidden_style
                )
            if form_type in (FormType.ADD_VERTEX, FormType.EDIT_VERTEX):
                return (
                    dialogue_visible,
                    effects_visible,
                    hidden_style,
                    hidden_style,
                    hidden_style,
                    hidden_style,
                    hidden_style
                )
            if form_type == FormType.DELETE:
                return (
                    hidden_style,
                    hidden_style,
                    hidden_style,
                    hidden_style,
                    hidden_style,
                    {"display": "block"},
                    {
                        "display": "block",
                        "marginBottom": "12px",
                        "color": COLOR_TEXT
                    }
                )
            return (hidden_style,) * 7

        @self.callback(
            Output(ElementId.BOTTOM_PANEL, "style", allow_duplicate=True),
            Input(ElementId.PICK_MODE_ACTIVE, "data"),
            Input(ElementId.BOTTOM_PANEL_VISIBLE, "data"),
            State(ElementId.BOTTOM_PANEL, "style"),
            prevent_initial_call=True
        )
        def manage_bottom_panel_graying(
            pick_mode_active: bool,
            bottom_panel_visible: bool,
            bottom_panel_style: dict[str, str] | None
        ) -> dict[str, str]:
            style = dict(bottom_panel_style or {})
            style["display"] = "block" if bottom_panel_visible else "none"
            if pick_mode_active:
                style["opacity"] = "0.5"
                style["pointerEvents"] = "none"
            else:
                style.pop("opacity", None)
                style.pop("pointerEvents", None)
            return style

        @self.callback(
            Output(ElementId.GRAPH_CONTAINER, "style"),
            Input(ElementId.PICK_MODE_ACTIVE, "data"),
            Input(ElementId.BOTTOM_PANEL_VISIBLE, "data"),
            prevent_initial_call=True
        )
        def manage_graph_graying(
            pick_mode_active: bool,
            bottom_panel_visible: bool
        ) -> dict[str, str | int]:
            base_style = {"flex": "1", "minHeight": 0}
            if pick_mode_active:
                return base_style
            elif bottom_panel_visible:
                return {
                    **base_style,
                    "opacity": "0.5"
                }
            else:
                return base_style

        @self.callback(
            Output(ElementId.DIALOGUE_EDITOR, "autoungrabify"),
            Output(ElementId.DIALOGUE_EDITOR, "autounselectify"),
            Input(ElementId.BOTTOM_PANEL_VISIBLE, "data"),
            Input(ElementId.PICK_MODE_ACTIVE, "data"),
            prevent_initial_call=True
        )
        def manage_graph_interactions(
            bottom_panel_visible: bool,
            pick_mode_active: bool
        ) -> tuple[bool, bool]:
            lock_graph_interactions = (
                bottom_panel_visible and not pick_mode_active
            )
            return lock_graph_interactions, lock_graph_interactions

        @self.callback(
            Output(ElementId.UNDO_ACTION, "disabled"),
            Output(ElementId.UNDO_ACTION, "style"),
            Output(ElementId.REDO_ACTION, "disabled"),
            Output(ElementId.REDO_ACTION, "style"),
            Input(ElementId.UNDO_REDO_STATE, "data")
        )
        def manage_undo_redo_buttons(
            undo_redo_state: dict[str, bool] | None
        ) -> tuple[bool, dict[str, str], bool, dict[str, str]]:
            state = undo_redo_state or {}
            can_undo = bool(state.get("can_undo"))
            can_redo = bool(state.get("can_redo"))
            undo_style = (
                get_toolbar_button_style() if can_undo
                else get_toolbar_button_disabled_style()
            )
            redo_style = (
                get_toolbar_button_style() if can_redo
                else get_toolbar_button_disabled_style()
            )
            return not can_undo, undo_style, not can_redo, redo_style

        @self.callback(
            Output(ElementId.DIALOGUE_EDITOR, "elements", allow_duplicate=True),
            Output(ElementId.ACTION_LOG, "data", allow_duplicate=True),
            Output(ElementId.UNSAVED_CHANGES, "data", allow_duplicate=True),
            Output(ElementId.BOTTOM_PANEL, "style", allow_duplicate=True),
            Output(ElementId.BOTTOM_PANEL_VISIBLE, "data", allow_duplicate=True),
            Output(ElementId.BOTTOM_FORM_DIALOGUE, "value", allow_duplicate=True),
            Output(ElementId.BOTTOM_FORM_SOURCE, "value", allow_duplicate=True),
            Output(ElementId.BOTTOM_FORM_TARGET, "value", allow_duplicate=True),
            Output(ElementId.BOTTOM_FORM_PREDICATES, "value", allow_duplicate=True),
            Output(ElementId.BOTTOM_FORM_EFFECTS, "value", allow_duplicate=True),
            Output(ElementId.BOTTOM_FORM_CASCADE, "value", allow_duplicate=True),
            Input(ElementId.BOTTOM_PANEL_SAVE, "n_clicks"),
            State(ElementId.BOTTOM_PANEL_FORM_TYPE, "data"),
            State(ElementId.DIALOGUE_EDITOR, "selectedNodeData"),
            State(ElementId.BOTTOM_FORM_DIALOGUE, "value"),
            State(ElementId.BOTTOM_FORM_SOURCE, "value"),
            State(ElementId.BOTTOM_FORM_TARGET, "value"),
            State(ElementId.BOTTOM_FORM_PREDICATES, "value"),
            State(ElementId.BOTTOM_FORM_EFFECTS, "value"),
            State(ElementId.BOTTOM_FORM_CASCADE, "value"),
            State(ElementId.SELECTED_NODE_ID, "data"),
            State(ElementId.ACTION_LOG, "data"),
            prevent_initial_call=True
        )
        def on_bottom_panel_save(
            save_clicks: int,
            form_type: str,
            selected_nodes: list[dict] | None,
            form_dialogue: str | None,
            form_source: str | None,
            form_target: str | None,
            form_predicates: str | None,
            form_effects: str | None,
            form_cascade: list[str] | None,
            selected_node_id: str | None,
            current_log: list[dict[str, str]] | None
        ) -> tuple[
            object, str, bool, dict, bool, str, str, str, str, str, list
        ]:
            if not save_clicks:
                raise PreventUpdate
            resolved_selected_nodes = selected_nodes
            if selected_node_id:
                resolved_selected_nodes = [{"id": selected_node_id}]
            if form_type == FormType.ADD_EDGE:
                if not form_source or not form_source.strip():
                    return (
                        no_update,
                        self.action_logger.append_status(
                            current_log, ERROR_ADD_PLAYER_SOURCE_REQUIRED
                        ),
                        True,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update
                    )
                try:
                    new_edge_predicates = self.parse_predicates(
                        form_predicates
                    )
                    new_edge_effects = self.parse_effects(form_effects)
                    normalized_to_vertex = (
                        form_target.strip()
                        if form_target and form_target.strip()
                        else None
                    )
                    new_edge_name = self.add_edge(
                        form_source.strip(),
                        normalized_to_vertex,
                        form_dialogue,
                        new_edge_predicates,
                        new_edge_effects
                    )
                except ValueError as exception:
                    return (
                        no_update,
                        self.action_logger.append_status(
                            current_log, ERROR_ADD_PLAYER_INVALID_FIELD(
                                reason=exception
                            )
                        ),
                        True,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update
                    )
                except VertexNotFoundError as exception:
                    endpoint_name = (
                        exception.field_name or FIELD_SOURCE_OR_TARGET
                    )
                    return (
                        no_update,
                        self.action_logger.append_status(
                            current_log, ERROR_ADD_PLAYER_ENDPOINT(
                                endpoint=endpoint_name
                            )
                        ),
                        True,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update
                    )
                create_lines = [
                    self.action_logger.build_create_log(
                        NODE_TYPE_PLAYER,
                        new_edge_name,
                        self.action_logger.get_player_log_fields(new_edge_name)
                    )
                ]
                if normalized_to_vertex is None:
                    new_edge = self.graph_editor.graph.edge_dict[new_edge_name]
                    auto_created_npc = new_edge.to_vertex
                    create_lines.append(
                        self.action_logger.build_create_log(
                            NODE_TYPE_NPC,
                            auto_created_npc,
                            self.action_logger.get_npc_log_fields(
                                auto_created_npc
                            )
                        )
                    )
                new_log = self.action_logger.append_grouped_status(
                    current_log, create_lines
                )
                return (
                    self.get_elements(),
                    new_log,
                    True,
                    get_bottom_panel_style(False),
                    False,
                    "",
                    "",
                    "",
                    "",
                    "",
                    []
                )
            if form_type == FormType.ADD_VERTEX:
                if not form_dialogue:
                    raise PreventUpdate
                try:
                    new_vertex_effects = self.parse_effects(form_effects)
                except ValueError as exception:
                    return (
                        no_update,
                        self.action_logger.append_status(
                            current_log, ERROR_ADD_NPC_INVALID_FIELD(
                                reason=exception
                            )
                        ),
                        True,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update
                    )
                new_vertex_name = self.add_vertex(
                    form_dialogue, new_vertex_effects
                )
                create_log = self.action_logger.build_create_log(
                    NODE_TYPE_NPC,
                    new_vertex_name,
                    self.action_logger.get_npc_log_fields(new_vertex_name)
                )
                return (
                    self.get_elements(),
                    self.action_logger.append_status(current_log, create_log),
                    True,
                    get_bottom_panel_style(False),
                    False,
                    "",
                    "",
                    "",
                    "",
                    "",
                    []
                )
            if form_type in [FormType.EDIT_EDGE, FormType.EDIT_VERTEX]:
                if not resolved_selected_nodes:
                    raise PreventUpdate
                node_id = resolved_selected_nodes[0].get("id", "")
                if not node_id:
                    raise PreventUpdate
                node_type, before_fields = (
                    self.action_logger.get_node_log_fields(
                        node_id, include_empty=False
                    )
                )
                try:
                    predicates = self.parse_predicates(form_predicates)
                    effects = self.parse_effects(form_effects)
                except ValueError as exception:
                    return (
                        no_update,
                        self.action_logger.append_status(
                            current_log, ERROR_SAVE_INVALID_FIELD.format(
                                node_type=node_type,
                                node_id=self.action_logger.quote_value(
                                    node_id
                                ),
                                reason=exception
                            )
                        ),
                        True,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update
                    )
                node_exists = (
                    node_id in self.graph_editor.graph.vertex_dict
                    or node_id in self.graph_editor.graph.edge_dict
                )
                if not node_exists:
                    return (
                        no_update,
                        self.action_logger.append_status(
                            current_log, ERROR_SAVE_MISSING_NODE.format(
                                node_type=node_type,
                                node_id=self.action_logger.quote_value(node_id)
                            )
                        ),
                        True,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update
                    )
                was_updated = self.update_node(
                    node_id, form_dialogue or "", predicates, effects
                )
                if form_type == FormType.EDIT_EDGE:
                    from_vertex_str = (
                        form_source.strip() if form_source else ""
                    )
                    to_vertex_str = (
                        form_target.strip() if form_target else ""
                    )
                    was_updated_endpoints, endpoint_warnings = (
                        self.update_edge_endpoints(
                            node_id, 
                            from_vertex_str or None, 
                            to_vertex_str or None
                        )
                    )
                    if endpoint_warnings:
                        new_log = self.action_logger.append_grouped_status(
                            current_log, endpoint_warnings
                        )
                        anything_saved = was_updated or was_updated_endpoints
                        return (
                            (
                                self.get_elements() 
                                if anything_saved else no_update
                            ),
                            new_log,
                            True if anything_saved else no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update,
                            no_update
                        )
                    was_updated = was_updated or was_updated_endpoints
                if not was_updated:
                    return (
                        no_update,
                        self.action_logger.append_status(
                            current_log, STATUS_NO_CHANGES.format(
                                node_type=node_type,
                                node_id=self.action_logger.quote_value(node_id)
                            )
                        ),
                        no_update,
                        get_bottom_panel_style(False),
                        False,
                        "",
                        "",
                        "",
                        "",
                        "",
                        []
                    )
                after_fields = self.action_logger.get_node_log_fields(
                    node_id, include_empty=False
                )[1]
                update_log = self.action_logger.build_update_log(
                    node_type, node_id, before_fields, after_fields
                )
                return (
                    self.get_elements(),
                    self.action_logger.append_status(current_log, update_log),
                    True,
                    get_bottom_panel_style(False),
                    False,
                    "",
                    "",
                    "",
                    "",
                    "",
                    []
                )
            if form_type == FormType.DELETE:
                if not resolved_selected_nodes:
                    raise PreventUpdate
                node_id = resolved_selected_nodes[0].get("id", "")
                if not node_id:
                    raise PreventUpdate
                cascade_delete_enabled = (
                    CascadeValue.CASCADE in (form_cascade or [])
                )
                was_edge_delete = node_id in self.graph_editor.graph.edge_dict
                was_vertex_delete = (
                    node_id in self.graph_editor.graph.vertex_dict
                )
                delete_messages = []
                if was_vertex_delete and cascade_delete_enabled:
                    delete_messages.append(
                        self.action_logger.build_delete_log(
                            NODE_TYPE_NPC,
                            node_id,
                            self.action_logger.get_npc_log_fields(
                                node_id, include_empty=True
                            )
                        )
                    )
                if was_edge_delete:
                    delete_messages.append(
                        self.action_logger.build_delete_log(
                            NODE_TYPE_PLAYER,
                            node_id,
                            self.action_logger.get_player_log_fields(
                                node_id, include_empty=True
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
                                NODE_TYPE_PLAYER,
                                edge_name,
                                self.action_logger.get_player_log_fields(
                                    edge_name, include_empty=True
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
                    was_removed = self.remove_node(
                        node_id, cascade_delete_enabled
                    )
                except VertexCannotBeDeletedError:
                    return (
                        no_update,
                        self.action_logger.append_status(
                            current_log, ERROR_DELETE_START_VERTEX.format(
                                node_id=self.action_logger.quote_value(node_id)
                            )
                        ),
                        True,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update
                    )
                if not was_removed:
                    return (
                        no_update,
                        self.action_logger.append_status(
                            current_log, ERROR_DELETE_MISSING_NODE.format(
                                node_id=self.action_logger.quote_value(node_id)
                            )
                        ),
                        True,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update
                    )
                new_log = self.action_logger.append_grouped_status(
                    current_log, delete_messages
                )
                if was_vertex_delete and not cascade_delete_enabled:
                    npc_delete_message = self.action_logger.build_delete_log(
                        NODE_TYPE_NPC,
                        node_id,
                        npc_log_fields_before_delete
                    ).removesuffix(".")
                    new_log = self.action_logger.append_status(
                        new_log, STATUS_UNRESOLVED_CONNECTIONS.format(
                            delete_message=npc_delete_message,
                            count=unresolved_connections_created
                        )
                    )
                return (
                    self.get_elements(),
                    new_log,
                    True,
                    get_bottom_panel_style(False),
                    False,
                    "",
                    "",
                    "",
                    "",
                    "",
                    []
                )
            raise PreventUpdate

        @self.callback(
            Output(ElementId.CONFIRM_UNSAVED_VISIBLE, "data", allow_duplicate=True),
            Output(ElementId.PENDING_ACTION, "data", allow_duplicate=True),
            Output(ElementId.PENDING_UPLOAD, "data", allow_duplicate=True),
            Input(ElementId.CONFIRM_UNSAVED_CANCEL, "n_clicks"),
            prevent_initial_call=True
        )
        def on_confirm_unsaved_cancel(
            confirm_unsaved_cancel_clicks: int
        ) -> tuple[bool, str, dict]:
            if not confirm_unsaved_cancel_clicks:
                raise PreventUpdate
            return False, "", {}

        @self.callback(
            Output(ElementId.ACTION_LOG, "data", allow_duplicate=True),
            Output(ElementId.GRAPH_CONTAINER, "children", allow_duplicate=True),
            Output(ElementId.UNSAVED_CHANGES, "data", allow_duplicate=True),
            Output(ElementId.CURRENT_DOCUMENT, "data", allow_duplicate=True),
            Output(ElementId.CONFIRM_UNSAVED_VISIBLE, "data", allow_duplicate=True),
            Output(ElementId.PENDING_ACTION, "data", allow_duplicate=True),
            Output(ElementId.PENDING_UPLOAD, "data", allow_duplicate=True),
            Output(ElementId.QUIT_SIGNAL, "data", allow_duplicate=True),
            Input(ElementId.CONFIRM_UNSAVED_CONFIRM, "n_clicks"),
            State(ElementId.PENDING_ACTION, "data"),
            State(ElementId.PENDING_UPLOAD, "data"),
            State(ElementId.ACTION_LOG, "data"),
            State(ElementId.QUIT_SIGNAL, "data"),
            State(ElementId.UNSAVED_CHANGES, "data"),
            prevent_initial_call=True
        )
        def on_confirm_unsaved_submit(
            confirm_unsaved_submit_clicks: int,
            pending_action: str | None,
            pending_upload: dict | None,
            current_log: list[dict[str, str]] | None,
            quit_signal: int | None,
            unsaved_changes: bool,
        ) -> tuple[object, object, object, object, bool, str, dict, object]:
            if not confirm_unsaved_submit_clicks:
                raise PreventUpdate
            if pending_action == PendingAction.NEW:
                self.graph_editor.load()
                self.reset_history()
                return (
                    self.action_logger.append_status(
                        current_log, STATUS_DISCARD_NEW
                    ),
                    self.get_fresh_graph_component(),
                    False,
                    self.normalize_name(self.graph_editor.graph.name),
                    False,
                    "",
                    {},
                    no_update
                )
            if pending_action == PendingAction.UPLOAD:
                queued_upload = pending_upload or {}
                queued_contents = queued_upload.get("contents")
                queued_filename = (
                    queued_upload.get("filename") or DEFAULT_DOCUMENT_NAME
                )
                if not queued_contents:
                    return (
                        self.action_logger.append_status(
                            current_log, ERROR_UPLOAD_NO_PENDING
                        ),
                        no_update,
                        no_update,
                        no_update,
                        False,
                        "",
                        {},
                        no_update
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
                        {},
                        no_update
                    )
                self.graph_editor.load(yaml_data=parsed_yaml)
                self.reset_history()
                loaded_name = self.normalize_name(self.graph_editor.graph.name)
                new_log = self.action_logger.append_grouped_status(
                    current_log,
                    self.get_runtime_validation_warnings()
                )
                new_log = self.action_logger.append_status(
                    new_log, STATUS_DISCARD_OPENED.format(
                        filename=self.action_logger.quote_value(
                            queued_filename
                        )
                    )
                )
                return (
                    new_log,
                    self.get_fresh_graph_component(),
                    False,
                    loaded_name,
                    False,
                    "",
                    {},
                    no_update
                )
            if pending_action == PendingAction.QUIT:
                self.request_app_shutdown()
                return (
                    self.action_logger.append_status(
                        current_log,
                        STATUS_DISCARD_QUIT if unsaved_changes else STATUS_QUIT
                    ),
                    no_update,
                    no_update,
                    no_update,
                    False,
                    "",
                    {},
                    (quit_signal or 0) + 1
                )
            raise PreventUpdate

        @self.callback(
            Output(ElementId.ACTION_LOG, "data", allow_duplicate=True),
            Output(ElementId.DOWNLOAD_YAML, "data", allow_duplicate=True),
            Output(ElementId.UNSAVED_CHANGES, "data", allow_duplicate=True),
            Input(ElementId.DOWNLOAD_GRAPH, "n_clicks"),
            State(ElementId.ACTION_LOG, "data"),
            State(ElementId.CURRENT_DOCUMENT, "data"),
            prevent_initial_call=True
        )
        def on_download_graph(
            download_graph_clicks: int,
            current_log: list[dict[str, str]] | None,
            current_document: str | None
        ) -> tuple[str, object, bool]:
            if not download_graph_clicks:
                raise PreventUpdate
            download_name = self.get_filename(current_document)
            new_log = self.action_logger.append_grouped_status(
                current_log, self.get_runtime_validation_warnings()
            )
            return (
                self.action_logger.append_status(
                    new_log, STATUS_SAVED_COPY.format(
                        filename=self.action_logger.quote_value(download_name)
                    )
                ),
                dcc.send_string(
                    self.graph_editor.export_yaml_text(), download_name
                ),
                False
            )

        @self.callback(
            Output(ElementId.BOTTOM_FORM_SOURCE, "value"),
            Output(ElementId.BOTTOM_FORM_TARGET, "value"),
            Output(ElementId.PICK_MODE_ACTIVE, "data", allow_duplicate=True),
            Output(ElementId.PICK_MODE_FIELD, "data", allow_duplicate=True),
            Output(ElementId.ACTION_LOG, "data", allow_duplicate=True),
            Input(ElementId.DIALOGUE_EDITOR, "tapNodeData"),
            State(ElementId.PICK_MODE_ACTIVE, "data"),
            State(ElementId.PICK_MODE_FIELD, "data"),
            State(ElementId.BOTTOM_FORM_SOURCE, "value"),
            State(ElementId.BOTTOM_FORM_TARGET, "value"),
            State(ElementId.ACTION_LOG, "data"),
            prevent_initial_call=True
        )
        def on_graph_click_during_pick_mode(
            tapped_node: dict | None,
            pick_mode_active: bool,
            pick_field: str,
            current_source: str | None,
            current_target: str | None,
            current_log: list[dict[str, str]] | None
        ) -> tuple[str, str, bool, str, Any]:
            if not pick_mode_active or not tapped_node:
                raise PreventUpdate
            node_id = tapped_node.get("id", "")
            if not node_id:
                raise PreventUpdate
            if tapped_node.get("is_edge_node", False):
                field_label = (
                    FIELD_SOURCE 
                    if pick_field == PickField.SOURCE else FIELD_TARGET
                )
                return (
                    no_update,
                    no_update,
                    no_update,
                    no_update,
                    self.action_logger.append_status(
                        current_log, STATUS_PICK_MODE.format(
                            field_label=field_label
                        )
                    )
                )
            if pick_field == PickField.SOURCE:
                return (
                    node_id,
                    current_target or "",
                    False,
                    "",
                    no_update
                )
            if pick_field == PickField.TARGET:
                return (
                    current_source or "",
                    node_id,
                    False,
                    "",
                    no_update
                )
            raise PreventUpdate

        @self.callback(
            Output(ElementId.ACTION_LOG, "data", allow_duplicate=True),
            Output(ElementId.GRAPH_CONTAINER, "children", allow_duplicate=True),
            Output(ElementId.UNSAVED_CHANGES, "data", allow_duplicate=True),
            Output(ElementId.CURRENT_DOCUMENT, "data", allow_duplicate=True),
            Output(ElementId.CONFIRM_UNSAVED_VISIBLE, "data", allow_duplicate=True),
            Output(ElementId.CONFIRM_UNSAVED_MESSAGE, "children", allow_duplicate=True),
            Output(ElementId.PENDING_ACTION, "data", allow_duplicate=True),
            Output(ElementId.PENDING_UPLOAD, "data", allow_duplicate=True),
            Input(ElementId.NEW_GRAPH, "n_clicks"),
            State(ElementId.ACTION_LOG, "data"),
            State(ElementId.UNSAVED_CHANGES, "data"),
            prevent_initial_call=True
        )
        def on_new_graph(
            new_graph_clicks: int,
            current_log: list[dict[str, str]] | None,
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
                    CONFIRM_UNSAVED_NEW,
                    PendingAction.NEW,
                    {}
                )
            self.graph_editor.load()
            self.reset_history()
            return (
                self.action_logger.append_status(
                    current_log, STATUS_NEW_GRAPH
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
            Output(ElementId.CONFIRM_UNSAVED_VISIBLE, "data", allow_duplicate=True),
            Output(ElementId.CONFIRM_UNSAVED_MESSAGE, "children", allow_duplicate=True),
            Output(ElementId.PENDING_ACTION, "data", allow_duplicate=True),
            Output(ElementId.PENDING_UPLOAD, "data", allow_duplicate=True),
            Input(ElementId.QUIT_EDITOR, "n_clicks"),
            State(ElementId.UNSAVED_CHANGES, "data"),
            prevent_initial_call=True
        )
        def on_quit_editor(
            quit_editor_clicks: int,
            unsaved_changes: bool
        ) -> tuple[bool, str, str, dict]:
            if not quit_editor_clicks:
                raise PreventUpdate
            return (
                True,
                CONFIRM_UNSAVED_QUIT if unsaved_changes else CONFIRM_QUIT,
                PendingAction.QUIT,
                {}
            )

        @self.callback(
            Output(ElementId.DIALOGUE_EDITOR, "elements", allow_duplicate=True),
            Output(ElementId.ACTION_LOG, "data", allow_duplicate=True),
            Output(ElementId.UNSAVED_CHANGES, "data", allow_duplicate=True),
            Output(ElementId.CURRENT_DOCUMENT, "data", allow_duplicate=True),
            Output(ElementId.SELECTED_NODE_ID, "data", allow_duplicate=True),
            Input(ElementId.REDO_ACTION, "n_clicks"),
            State(ElementId.ACTION_LOG, "data"),
            prevent_initial_call=True
        )
        def on_redo(
            redo_clicks: int,
            current_log: list[dict[str, str]] | None
        ) -> tuple[object, object, object, object, object]:
            if not redo_clicks:
                raise PreventUpdate
            if self.history_cursor >= len(self.history) - 1:
                return (
                    no_update,
                    self.action_logger.append_status(
                        current_log, STATUS_NOTHING_TO_REDO
                    ),
                    no_update,
                    no_update,
                    no_update
                )
            snapshot = self.restore_snapshot(self.history_cursor+1)
            elements = self.build_context_menu_selection(
                self.get_elements(), snapshot["selected_node_id"] or ""
            )
            return (
                elements,
                self.action_logger.append_status(
                    current_log, STATUS_REDO.format(action=snapshot["label"])
                ),
                self.history_cursor != self.clean_cursor,
                snapshot["document_name"],
                snapshot["selected_node_id"]
            )

        @self.callback(
            Output(ElementId.ACTION_LOG, "data", allow_duplicate=True),
            Output(ElementId.UNSAVED_CHANGES, "data", allow_duplicate=True),
            Output(ElementId.CURRENT_DOCUMENT, "data", allow_duplicate=True),
            Input(ElementId.SAVE_NAME, "n_clicks"),
            State(ElementId.ACTION_LOG, "data"),
            State(ElementId.DOCUMENT_NAME, "value"),
            prevent_initial_call=True
        )
        def on_save_name(
            save_name_clicks: int,
            current_log: list[dict[str, str]] | None,
            document_name: str | None
        ) -> tuple[str, bool, str]:
            if not save_name_clicks:
                raise PreventUpdate
            normalized = self.normalize_name(document_name)
            self.graph_editor.edit_name(normalized)
            return (
                self.action_logger.append_status(
                    current_log, STATUS_SAVED_NAME.format(
                        name=self.action_logger.quote_value(normalized)
                    )
                ),
                True,
                normalized
            )

        @self.callback(
            Output(ElementId.DIALOGUE_EDITOR, "elements", allow_duplicate=True),
            Output(ElementId.ACTION_LOG, "data", allow_duplicate=True),
            Output(ElementId.UNSAVED_CHANGES, "data", allow_duplicate=True),
            Output(ElementId.CURRENT_DOCUMENT, "data", allow_duplicate=True),
            Output(ElementId.SELECTED_NODE_ID, "data", allow_duplicate=True),
            Input(ElementId.UNDO_ACTION, "n_clicks"),
            State(ElementId.ACTION_LOG, "data"),
            prevent_initial_call=True
        )
        def on_undo(
            undo_clicks: int,
            current_log: list[dict[str, str]] | None
        ) -> tuple[object, object, object, object, object]:
            if not undo_clicks:
                raise PreventUpdate
            if self.history_cursor <= 0:
                return (
                    no_update,
                    self.action_logger.append_status(
                        current_log, STATUS_NOTHING_TO_UNDO
                    ),
                    no_update,
                    no_update,
                    no_update
                )
            undone_label = self.history[self.history_cursor]["label"]
            snapshot = self.restore_snapshot(self.history_cursor-1)
            elements = self.build_context_menu_selection(
                self.get_elements(), snapshot["selected_node_id"] or ""
            )
            return (
                elements,
                self.action_logger.append_status(
                    current_log, STATUS_UNDO.format(action=undone_label)
                ),
                self.history_cursor != self.clean_cursor,
                snapshot["document_name"],
                snapshot["selected_node_id"]
            )

        @self.callback(
            Output(ElementId.ACTION_LOG, "data", allow_duplicate=True),
            Output(ElementId.GRAPH_CONTAINER, "children", allow_duplicate=True),
            Output(ElementId.UNSAVED_CHANGES, "data", allow_duplicate=True),
            Output(ElementId.CURRENT_DOCUMENT, "data", allow_duplicate=True),
            Output(ElementId.CONFIRM_UNSAVED_VISIBLE, "data", allow_duplicate=True),
            Output(ElementId.CONFIRM_UNSAVED_MESSAGE, "children", allow_duplicate=True),
            Output(ElementId.PENDING_ACTION, "data", allow_duplicate=True),
            Output(ElementId.PENDING_UPLOAD, "data", allow_duplicate=True),
            Input(ElementId.UPLOAD_GRAPH, "contents"),
            State(ElementId.UPLOAD_GRAPH, "filename"),
            State(ElementId.ACTION_LOG, "data"),
            State(ElementId.UNSAVED_CHANGES, "data"),
            prevent_initial_call=True
        )
        def on_upload_graph(
            upload_contents: str | None,
            upload_filename: str | None,
            current_log: list[dict[str, str]] | None,
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
                    CONFIRM_UNSAVED_UPLOAD,
                    PendingAction.UPLOAD,
                    {
                        "contents": upload_contents,
                        "filename": upload_filename or DEFAULT_DOCUMENT_NAME
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
            self.reset_history()
            loaded_name = self.normalize_name(self.graph_editor.graph.name)
            quoted_value = upload_filename or loaded_name
            new_log = self.action_logger.append_grouped_status(
                current_log,
                self.get_runtime_validation_warnings()
            )
            new_log = self.action_logger.append_status(
                new_log, STATUS_OPENED.format(
                    filename=self.action_logger.quote_value(quoted_value)
                )
            )
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
            Output(ElementId.DIALOGUE_EDITOR, "elements", allow_duplicate=True),
            Output(ElementId.SELECTED_NODE_ID, "data", allow_duplicate=True),
            Output(ElementId.ACTION_LOG, "data", allow_duplicate=True),
            Output(ElementId.BOTTOM_PANEL, "style", allow_duplicate=True),
            Output(ElementId.BOTTOM_PANEL_VISIBLE, "data", allow_duplicate=True),
            Output(ElementId.BOTTOM_PANEL_FORM_TYPE, "data", allow_duplicate=True),
            Output(ElementId.BOTTOM_PANEL_TITLE, "children", allow_duplicate=True),
            Output(ElementId.BOTTOM_FORM_DIALOGUE, "value", allow_duplicate=True),
            Output(ElementId.BOTTOM_FORM_SOURCE, "value", allow_duplicate=True),
            Output(ElementId.BOTTOM_FORM_TARGET, "value", allow_duplicate=True),
            Output(ElementId.BOTTOM_FORM_PREDICATES, "value", allow_duplicate=True),
            Output(ElementId.BOTTOM_FORM_EFFECTS, "value", allow_duplicate=True),
            Output(ElementId.BOTTOM_FORM_CASCADE, "value", allow_duplicate=True),
            Output(ElementId.PICK_MODE_ACTIVE, "data", allow_duplicate=True),
            Output(ElementId.PICK_MODE_FIELD, "data", allow_duplicate=True),
            Output(ElementId.BOTTOM_PANEL_SAVE, "children", allow_duplicate=True),
            Output(ElementId.BOTTOM_PANEL_SAVE, "style", allow_duplicate=True),
            Output(ElementId.BOTTOM_PANEL_CLOSE, "children", allow_duplicate=True),
            Output(ElementId.BOTTOM_PANEL_CLOSE, "style", allow_duplicate=True),
            Input(ElementId.DIALOGUE_EDITOR, "contextMenuData"),
            State(ElementId.DIALOGUE_EDITOR, "elements"),
            State(ElementId.ACTION_LOG, "data"),
            prevent_initial_call=True
        )
        def open_bottom_panel_from_context_menu(
            context_menu_data: dict | None,
            elements: list[dict[str, Any]] | None,
            current_log: list[dict[str, str]] | None
        ) -> tuple[
            list[dict[str, Any]],
            str | None,
            str,
            dict[str, str],
            bool,
            str,
            str,
            str,
            str,
            str,
            str,
            list[str],
            bool,
            str,
            str,
            dict[str, str],
            str,
            dict[str, str]
        ]:
            if not context_menu_data:
                raise PreventUpdate
            menu_item_id = context_menu_data.get("menuItemId", "")
            if menu_item_id == "cancel":
                raise PreventUpdate
            element_id = context_menu_data.get("elementId") or ""
            selected_elements = no_update
            selected_node_id = no_update
            if element_id:
                selected_elements = self.build_context_menu_selection(
                    elements, element_id
                )
                selected_node_id = element_id
            panel_outputs = self.get_context_action_panel_outputs(
                menu_item_id, element_id or None, current_log
            )
            return (selected_elements, selected_node_id, *panel_outputs)

        @self.callback(
            Output(ElementId.UNDO_REDO_STATE, "data"),
            Input(ElementId.ACTION_LOG, "data"),
            State(ElementId.SELECTED_NODE_ID, "data"),
            State(ElementId.CURRENT_DOCUMENT, "data"),
            prevent_initial_call=True
        )
        def refresh_history(
            log_entries: list[dict[str, str]] | None,
            selected_node_id: str | None,
            current_document: str | None
        ) -> dict[str, bool]:
            return self.record_history(
                log_entries, selected_node_id, current_document
            )

        @self.callback(
            Output(ElementId.ACTION_LOG_DISPLAY, "children"),
            Input(ElementId.ACTION_LOG, "data")
        )
        def render_action_log(
            log_entries: list[dict[str, str]] | None
        ) -> list[html.Div]:
            return build_log_children(log_entries)

        @self.callback(
            Output(ElementId.CURRENT_DOCUMENT_LABEL, "children"),
            Input(ElementId.CURRENT_DOCUMENT, "data"),
            Input(ElementId.UNSAVED_CHANGES, "data")
        )
        def render_document_label(
            current_document: str | None,
            unsaved_changes: bool
        ) -> str:
            document_name = self.get_filename(current_document)
            dirty_marker = DIRTY_MARKER if unsaved_changes else ""
            return LABEL_DOCUMENT.format(name=f"{document_name}{dirty_marker}")

        @self.callback(
            Output(ElementId.UPLOAD_GRAPH_CONTAINER, "children"),
            Input(ElementId.ACTION_LOG, "data"),
            prevent_initial_call=True
        )
        def reset_upload_contents_after_actions(
            action_log: list[dict[str, str]] | None
        ) -> dcc.Upload:
            return get_upload_graph()

        @self.callback(
            Output(ElementId.DIALOGUE_EDITOR, "elements", allow_duplicate=True),
            Input(ElementId.DIALOGUE_EDITOR, "contextMenuData"),
            State(ElementId.DIALOGUE_EDITOR, "elements"),
            prevent_initial_call=True
        )
        def select_context_menu_target(
            context_menu_data: dict | None,
            elements: list[dict] | None
        ) -> list[dict]:
            if not context_menu_data:
                raise PreventUpdate
            if context_menu_data.get("menuItemId") == "cancel":
                raise PreventUpdate
            element_id = context_menu_data.get("elementId") or ""
            if not element_id:
                raise PreventUpdate
            return self.build_context_menu_selection(elements, element_id)

        @self.callback(
            Output(ElementId.DOCUMENT_NAME, "value"),
            Input(ElementId.CURRENT_DOCUMENT, "data")
        )
        def sync_document_name(current_document: str | None) -> str:
            return self.normalize_name(current_document)

        @self.callback(
            Output(ElementId.OPEN_ADD_EDGE_MODAL, "disabled"),
            Output(ElementId.OPEN_ADD_EDGE_MODAL, "style"),
            Output(ElementId.OPEN_ADD_EDGE_TOOLTIP, "title"),
            Input(ElementId.DIALOGUE_EDITOR, "elements")
        )
        def toggle_add_player_button(
            elements: list[dict] | None
        ) -> tuple[bool, dict[str, str | int], str]:
            return self.get_add_player_button_state()
        
        @self.callback(
            Output(ElementId.OPEN_EDIT_MODAL, "disabled"),
            Output(ElementId.OPEN_EDIT_MODAL, "style"),
            Output(ElementId.OPEN_EDIT_TOOLTIP, "title"),
            Output(ElementId.OPEN_DELETE_MODAL, "disabled"),
            Output(ElementId.OPEN_DELETE_MODAL, "style"),
            Output(ElementId.OPEN_DELETE_TOOLTIP, "title"),
            Input(ElementId.DIALOGUE_EDITOR, "selectedNodeData")
        )
        def toggle_edit_delete_buttons(
            selected_nodes: list[dict] | None
        ) -> tuple[bool, dict, str, bool, dict, str]:
            if not selected_nodes:
                return (
                    True,
                    get_panel_button_disabled_style(),
                    TOOLTIP_EDIT_DISABLED,
                    True,
                    get_panel_button_danger_disabled_style(),
                    TOOLTIP_DELETE_DISABLED
                )
            return (
                False,
                get_panel_button_enabled_style(),
                TOOLTIP_EDIT_ENABLED,
                False,
                get_panel_button_danger_style(),
                TOOLTIP_DELETE_ENABLED
            )

        @self.callback(
            Output(ElementId.DIALOGUE_EDITOR, "contextMenu"),
            Input(ElementId.PICK_MODE_ACTIVE, "data"),
            Input(ElementId.BOTTOM_PANEL_VISIBLE, "data"),
            prevent_initial_call=True
        )
        def update_context_menu(
            pick_mode_active: bool,
            bottom_panel_visible: bool
        ) -> list[dict[str, str | list[str]]]:
            if pick_mode_active or bottom_panel_visible:
                return []
            return self.get_context_menu()
        
        @self.callback(
            Output(ElementId.SELECTED_NODE_DISPLAY, "children"),
            Input(ElementId.DIALOGUE_EDITOR, "selectedNodeData")
        )
        def update_selected_node_display(
            selected_nodes: list[dict] | None
        ) -> str:
            if not selected_nodes:
                return DEFAULT_NODE_DISPLAY
            node_id = selected_nodes[0].get("id", DEFAULT_NODE_DISPLAY)
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

    def request_app_shutdown(self) -> None:
        """Stop the server after the current callback response is sent."""
        shutdown_server = request.environ.get("werkzeug.server.shutdown")
        if shutdown_server:
            Timer(SERVER_SHUTDOWN_DELAY_SECONDS, shutdown_server).start()
            return
        Timer(SERVER_SHUTDOWN_DELAY_SECONDS, _exit, args=(0,)).start()

    def reset_history(self) -> None:
        """Reset undo history to a single snapshot of the current graph."""
        document_name = self.normalize_name(self.graph_editor.graph.name)
        self.history = [
            self.capture_snapshot(None, document_name, STATUS_READY)
        ]
        self.history_cursor = 0
        self.clean_cursor = 0

    def restore_snapshot(self, index: int) -> dict[str, Any]:
        """Load the graph state stored in a history snapshot.

        Args:
            index (int): History index to restore.

        Returns:
            dict[str, Any]: The restored snapshot, whose selection and
                document name callers apply to the corresponding stores.
        """
        snapshot = self.history[index]
        self.graph_editor.load(yaml_data=safe_load(snapshot["yaml"]))
        self.graph_editor.next_vertex_index = snapshot["next_vertex_index"]
        self.graph_editor.next_edge_index = snapshot["next_edge_index"]
        self.history_cursor = index
        return snapshot

    def trim_history(self) -> None:
        """Bound history length to HISTORY_LIMIT, dropping oldest snapshots."""
        overflow = len(self.history) - HISTORY_LIMIT
        if overflow <= 0:
            return
        self.history = self.history[overflow:]
        self.history_cursor -= overflow
        self.clean_cursor -= overflow
        if self.clean_cursor < 0:
            self.clean_cursor = -1

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
                    ERROR_UPDATE_ENDPOINT_MISSING.format(
                        field=FIELD_SOURCE,
                        node_id=self.action_logger.quote_value(node_id),
                        vertex_id=self.action_logger.quote_value(
                            candidate_from_vertex
                        )
                    )
                )
        elif edge.from_vertex == MISSING_VERTEX:
            pass
        else:
            warnings.append(
                ERROR_UPDATE_ENDPOINT_EMPTY.format(
                    field=FIELD_SOURCE,
                    node_id=self.action_logger.quote_value(node_id)
                )
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
                    ERROR_UPDATE_ENDPOINT_MISSING.format(
                        field=FIELD_TARGET,
                        node_id=self.action_logger.quote_value(node_id),
                        vertex_id=self.action_logger.quote_value(
                            candidate_to_vertex
                        )
                    )
                )
        elif edge.to_vertex == MISSING_VERTEX:
            pass
        else:
            warnings.append(
                ERROR_UPDATE_ENDPOINT_EMPTY.format(
                    field=FIELD_TARGET,
                    node_id=self.action_logger.quote_value(node_id)
                )
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
    open_url(SERVER_URL)
    app = App()
    app.run()

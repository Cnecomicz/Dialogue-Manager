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

from dash_app.layout import (
    get_bottom_panel_style,
    get_center_panel,
    get_graph_component,
    get_index_string,
    get_left_panel,
    get_project_metadata,
    get_right_panel,
    get_shortcuts_overlay,
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
    PENDING_ACTION_QUIT = "quit"
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
                get_center_panel(self.get_elements(), self.get_context_menu()),
                get_right_panel(),
                dcc.Store(id="unsaved-changes", data=False),
                dcc.Store(id="current-document", data=initial_name),
                dcc.Store(id="pending-action", data=""),
                dcc.Store(id="pending-upload", data={}),
                dcc.Store(id="quit-signal", data=0),
                dcc.Store(id="selected-node-id", data=None),
                dcc.Store(id="bottom-panel-visible", data=False),
                dcc.Store(id="bottom-panel-form-type", data=""),
                dcc.Store(id="pick-mode-active", data=False),
                dcc.Store(id="pick-mode-field", data=""),
                dcc.Store(id="shortcuts-help-visible", data=False),
                dcc.Download(id="download-yaml"),
                dcc.ConfirmDialog(
                    id="confirm-unsaved-work",
                    message="You have unsaved changes. Continue?"
                ),
                html.Div(id="quit-client-trigger", style={"display": "none"}),
                html.Div(
                    id="shortcut-listener-dummy", style={"display": "none"}
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
        base_style = {
            "width": "100%",
            "padding": "10px",
            "marginBottom": "8px",
            "border": "1px solid #666",
            "borderRadius": "4px"
        }
        has_vertices = bool(self.graph_editor.graph.vertex_dict)
        if not has_vertices:
            return (
                True,
                {
                    **base_style,
                    "backgroundColor": "#374151",
                    "color": "#6b7280",
                    "cursor": "not-allowed",
                    "opacity": 0.5
                },
                "Create at least one NPC node first."
            )
        return (
            False,
            {
                **base_style,
                "backgroundColor": "#4b5563",
                "color": "#e6e6e6",
                "cursor": "pointer"
            },
            "Create a player choice linking two NPC nodes (P)"
        )

    def get_context_action_panel_outputs(
        self,
        menu_item_id: str,
        element_id: str | None,
        current_log: str | None
    ) -> tuple[
        str | Any,
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
            current_log (str | None): Current action-status log text.

        Returns:
            tuple[str | Any, dict[str, str], bool, str, str, str, str, str,
            str, str, list[str], bool, str, str, dict[str, str], str,
            dict[str, str]]: Action-status text followed by bottom panel
                outputs in callback order.

        Raises:
            PreventUpdate: If no action should be performed.
        """
        default_save_button_style = {
            "padding": "8px 14px",
            "backgroundColor": "#4b5563",
            "color": "#e6e6e6",
            "border": "1px solid #666",
            "borderRadius": "4px",
            "cursor": "pointer"
        }
        delete_save_button_style = {
            "padding": "8px 14px",
            "backgroundColor": "#7f1d1d",
            "color": "#e6e6e6",
            "border": "1px solid #c53030",
            "borderRadius": "4px",
            "cursor": "pointer"
        }
        close_button_style = {
            "padding": "8px 14px",
            "backgroundColor": "#333",
            "color": "#e6e6e6",
            "border": "1px solid #555",
            "borderRadius": "4px",
            "cursor": "pointer"
        }
        if menu_item_id == "add-npc":
            return (
                no_update,
                get_bottom_panel_style(True),
                True,
                "add-vertex",
                "Add NPC Dialogue",
                "",
                "",
                "",
                "",
                "",
                [],
                False,
                "",
                "Save",
                default_save_button_style,
                "Cancel",
                close_button_style
            )
        if menu_item_id == "add-player":
            return (
                no_update,
                get_bottom_panel_style(True),
                True,
                "add-edge",
                "Add Player Dialogue",
                "",
                "",
                "",
                "",
                "",
                [],
                False,
                "",
                "Save",
                default_save_button_style,
                "Cancel",
                close_button_style
            )
        if menu_item_id == "add-player-dialogue":
            if (
                not element_id 
                or element_id in self.graph_editor.graph.edge_dict
            ):
                return (
                    self.action_logger.append_status(
                        current_log,
                        "Could not create a Player node from this selection "
                        "because the source must be an NPC node."
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
                "add-edge",
                "Add Player Dialogue",
                "",
                element_id or "",
                "",
                "",
                "",
                [],
                False,
                "",
                "Save",
                default_save_button_style,
                "Cancel",
                close_button_style
            )
        if menu_item_id == "edit-node" and element_id:
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
                "edit-edge" if is_edge else "edit-vertex",
                "Edit Node",
                node_text or "",
                edit_from_vertex,
                edit_to_vertex,
                predicates_text,
                effects_text,
                [],
                False,
                "",
                "Save",
                default_save_button_style,
                "Cancel",
                close_button_style
            )
        if menu_item_id == "delete-node" and element_id:
            if element_id == "vertex_0":
                return (
                    self.action_logger.append_status(
                        current_log,
                        'You could not delete NPC node "vertex_0" because '
                        "the first NPC node cannot be deleted."
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
                "delete",
                "Delete Node",
                "",
                "",
                "",
                "",
                "",
                [],
                False,
                "",
                "Confirm Delete",
                delete_save_button_style,
                "Cancel",
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
                "id": "edit-node",
                "label": "Edit Selected Node",
                "tooltipText": "Open edit form",
                "availableOn": ["node"]
            },
            {
                "id": "add-player-dialogue",
                "label": "Add Player Dialogue",
                "tooltipText": "Create a Player node from this NPC node",
                "availableOn": ["node"]
            },
            {
                "id": "delete-node",
                "label": "Delete Selected Node",
                "tooltipText": "Open delete confirmation",
                "availableOn": ["node"]
            },
            {
                "id": "add-npc",
                "label": "Add NPC Dialogue",
                "tooltipText": "Add a new NPC node",
                "availableOn": ["canvas", "edge"]
            },
            {
                "id": "add-player",
                "label": "Add Player Dialogue",
                "tooltipText": "Add a new Player node",
                "availableOn": ["canvas", "edge"]
            },
            {
                "id": "cancel",
                "label": "Cancel",
                "tooltipText": "Close menu",
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
            Output("quit-client-trigger", "children"),
            Input("quit-signal", "data"),
            prevent_initial_call=True
        )

        self.clientside_callback(
            """
            function(bottomPanelVisible, pickModeActive, formType,
                     helpVisible) {
                if (!window.dmShortcuts) {
                    window.dmShortcuts = {installed: false, state: {}};
                }
                window.dmShortcuts.state = {
                    bottomPanelVisible: !!bottomPanelVisible,
                    pickModeActive: !!pickModeActive,
                    formType: formType || "",
                    helpVisible: !!helpVisible
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
                var openFileDialog = function() {
                    var input = document.querySelector(
                        "#upload-graph input[type=file]"
                    );
                    if (input) { input.click(); }
                };
                document.addEventListener("keydown", function(event) {
                    var state = window.dmShortcuts.state || {};
                    var key = event.key;
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
                        if (state.formType === "delete" && key === "Enter") {
                            event.preventDefault();
                            clickById("bottom-panel-save");
                        }
                        return;
                    }
                    if (isEditableTarget()) {
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
                            openFileDialog();
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
            Output("shortcut-listener-dummy", "children"),
            Input("bottom-panel-visible", "data"),
            Input("pick-mode-active", "data"),
            Input("bottom-panel-form-type", "data"),
            Input("shortcuts-help-visible", "data")
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
            Output("shortcuts-overlay", "style"),
            Input("shortcuts-help-visible", "data")
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
            Output("shortcuts-help-visible", "data"),
            Input("open-shortcuts-help", "n_clicks"),
            Input("shortcuts-help-close", "n_clicks"),
            prevent_initial_call=True
        )

        @self.callback(
            Output("pick-mode-active", "data"),
            Output("pick-mode-field", "data"),
            Input("bottom-form-pick-source", "n_clicks"),
            Input("bottom-form-pick-target", "n_clicks"),
            State("pick-mode-active", "data"),
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
            if triggered_id == "bottom-form-pick-source":
                return True, "source"
            if triggered_id == "bottom-form-pick-target":
                return True, "target"
            raise PreventUpdate

        @self.callback(
            Output("dialogue-editor", "elements", allow_duplicate=True),
            Input("dialogue-editor", "selectedNodeData"),
            State("dialogue-editor", "elements"),
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
            Output("bottom-panel", "style"),
            Output("bottom-panel-visible", "data"),
            Output("bottom-panel-form-type", "data"),
            Output("bottom-panel-title", "children"),
            Output("bottom-form-dialogue", "value"),
            Output("bottom-form-source", "value"),
            Output("bottom-form-target", "value"),
            Output("bottom-form-predicates", "value"),
            Output("bottom-form-effects", "value"),
            Output("bottom-form-cascade", "value"),
            Output("pick-mode-active", "data"),
            Output("pick-mode-field", "data"),
            Output("bottom-panel-save", "children"),
            Output("bottom-panel-save", "style"),
            Output("bottom-panel-close", "children"),
            Output("bottom-panel-close", "style"),
            Input("bottom-panel-close", "n_clicks"),
            Input("bottom-panel-save", "n_clicks"),
            Input("open-add-edge-modal", "n_clicks"),
            Input("open-add-vertex-modal", "n_clicks"),
            Input("open-edit-modal", "n_clicks"),
            Input("open-delete-modal", "n_clicks"),
            State("bottom-panel-visible", "data"),
            State("dialogue-editor", "selectedNodeData"),
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
            dict[str, str]
        ]:
            if not ctx.triggered:
                raise PreventUpdate
            default_save_button_style = {
                "padding": "8px 14px",
                "backgroundColor": "#4b5563",
                "color": "#e6e6e6",
                "border": "1px solid #666",
                "borderRadius": "4px",
                "cursor": "pointer"
            }
            delete_save_button_style = {
                "padding": "8px 14px",
                "backgroundColor": "#7f1d1d",
                "color": "#e6e6e6",
                "border": "1px solid #c53030",
                "borderRadius": "4px",
                "cursor": "pointer"
            }
            close_button_style = {
                "padding": "8px 14px",
                "backgroundColor": "#333",
                "color": "#e6e6e6",
                "border": "1px solid #555",
                "borderRadius": "4px",
                "cursor": "pointer"
            }
            triggered_id = ctx.triggered_id
            if triggered_id == "bottom-panel-close":
                return (
                    get_bottom_panel_style(False),
                    False,
                    "",
                    "Form",
                    "",
                    "",
                    "",
                    "",
                    "",
                    [],
                    False,
                    "",
                    "Save",
                    default_save_button_style,
                    "Cancel",
                    close_button_style
                )
            if triggered_id == "bottom-panel-save":
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
                    no_update
                )
            if triggered_id == "open-add-edge-modal":
                if not self.graph_editor.graph.vertex_dict:
                    raise PreventUpdate

                return (
                    get_bottom_panel_style(True),
                    True,
                    "add-edge",
                    "Add Player Dialogue",
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
                    "Save",
                    default_save_button_style,
                    "Cancel",
                    close_button_style
                )
            if triggered_id == "open-add-vertex-modal":
                return (
                    get_bottom_panel_style(True),
                    True,
                    "add-vertex",
                    "Add NPC Dialogue",
                    "",
                    "",
                    "",
                    "",
                    "",
                    [],
                    False,
                    "",
                    "Save",
                    default_save_button_style,
                    "Cancel",
                    close_button_style
                )
            if triggered_id == "open-edit-modal":
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
                form_type = "edit-edge" if is_edge else "edit-vertex"
                title = "Edit Node"
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
                    "Save",
                    default_save_button_style,
                    "Cancel",
                    close_button_style
                )
            if triggered_id == "open-delete-modal":
                if not selected_nodes:
                    raise PreventUpdate
                return (
                    get_bottom_panel_style(True),
                    True,
                    "delete",
                    "Delete Node",
                    "",
                    "",
                    "",
                    "",
                    "",
                    [],
                    False,
                    "",
                    "Confirm Delete",
                    delete_save_button_style,
                    "Cancel",
                    close_button_style
                )
            raise PreventUpdate

        @self.callback(
            Output("bottom-form-dialogue-container", "style"),
            Output("bottom-form-effects-container", "style"),
            Output("bottom-form-source-container", "style"),
            Output("bottom-form-target-container", "style"),
            Output("bottom-form-predicates-container", "style"),
            Output("bottom-form-cascade-container", "style"),
            Output("bottom-form-delete-message-container", "style"),
            Input("bottom-panel-form-type", "data")
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
            if form_type in ("add-edge", "edit-edge"):
                return (
                    dialogue_visible,
                    effects_visible,
                    source_visible,
                    target_visible,
                    predicates_visible,
                    hidden_style,
                    hidden_style
                )
            if form_type in ("add-vertex", "edit-vertex"):
                return (
                    dialogue_visible,
                    effects_visible,
                    hidden_style,
                    hidden_style,
                    hidden_style,
                    hidden_style,
                    hidden_style
                )
            if form_type == "delete":
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
                        "color": "#e6e6e6"
                    }
                )
            return (hidden_style,) * 7

        @self.callback(
            Output("bottom-panel", "style", allow_duplicate=True),
            Input("pick-mode-active", "data"),
            State("bottom-panel", "style"),
            prevent_initial_call=True
        )
        def manage_bottom_panel_graying(
            pick_mode_active: bool,
            bottom_panel_style: dict[str, str] | None
        ) -> dict[str, str]:
            style = dict(bottom_panel_style or {})
            if pick_mode_active:
                style["opacity"] = "0.5"
                style["pointerEvents"] = "none"
            else:
                style.pop("opacity", None)
                style.pop("pointerEvents", None)
            return style

        @self.callback(
            Output("graph-container", "style"),
            Input("pick-mode-active", "data"),
            Input("bottom-panel-visible", "data"),
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
            Output("dialogue-editor", "autoungrabify"),
            Output("dialogue-editor", "autounselectify"),
            Input("bottom-panel-visible", "data"),
            Input("pick-mode-active", "data"),
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
            Output("dialogue-editor", "elements", allow_duplicate=True),
            Output("action-status", "value", allow_duplicate=True),
            Output("unsaved-changes", "data", allow_duplicate=True),
            Output("bottom-panel", "style", allow_duplicate=True),
            Output("bottom-panel-visible", "data", allow_duplicate=True),
            Output("bottom-form-dialogue", "value", allow_duplicate=True),
            Output("bottom-form-source", "value", allow_duplicate=True),
            Output("bottom-form-target", "value", allow_duplicate=True),
            Output("bottom-form-predicates", "value", allow_duplicate=True),
            Output("bottom-form-effects", "value", allow_duplicate=True),
            Output("bottom-form-cascade", "value", allow_duplicate=True),
            Input("bottom-panel-save", "n_clicks"),
            State("bottom-panel-form-type", "data"),
            State("dialogue-editor", "selectedNodeData"),
            State("bottom-form-dialogue", "value"),
            State("bottom-form-source", "value"),
            State("bottom-form-target", "value"),
            State("bottom-form-predicates", "value"),
            State("bottom-form-effects", "value"),
            State("bottom-form-cascade", "value"),
            State("selected-node-id", "data"),
            State("action-status", "value"),
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
            current_log: str | None
        ) -> tuple[
            object, str, bool, dict, bool, str, str, str, str, str, list
        ]:
            if not save_clicks:
                raise PreventUpdate
            resolved_selected_nodes = selected_nodes
            if selected_node_id and not resolved_selected_nodes:
                resolved_selected_nodes = [{"id": selected_node_id}]
            if form_type == "add-edge":
                if not form_source or not form_source.strip():
                    return (
                        no_update,
                        self.action_logger.append_status(
                            current_log,
                            "Could not create a Player node because Source "
                            "is required. Enter an NPC node ID in Source "
                            "and save again."
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
                            current_log,
                            "Could not create a Player node because "
                            f"{exception}. Fix Predicates/Effects and save "
                            "again."
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
                    endpoint_name = exception.field_name or "Source/Target"
                    return (
                        no_update,
                        self.action_logger.append_status(
                            current_log,
                            "Could not create a Player node because "
                            f"{endpoint_name} must be an existing NPC node "
                            "ID. Enter a valid NPC node ID in "
                            f"{endpoint_name} and save again."
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
            if form_type == "add-vertex":
                if not form_dialogue:
                    raise PreventUpdate
                try:
                    new_vertex_effects = self.parse_effects(form_effects)
                except ValueError as exception:
                    return (
                        no_update,
                        self.action_logger.append_status(
                            current_log,
                            "Could not create an NPC node because "
                            f"{exception}. Fix the Effects field and save "
                            "again."
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
                    "NPC node",
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
            if form_type in ["edit-edge", "edit-vertex"]:
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
                            current_log,
                            f"Could not save changes for {node_type} "
                            f"{self.action_logger.quote_value(node_id)} "
                            f"because {exception}. Fix the invalid field "
                            "and save again."
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
                if not was_updated:
                    return (
                        no_update,
                        self.action_logger.append_status(
                            current_log,
                            f"Could not save changes for {node_type} "
                            f"{self.action_logger.quote_value(node_id)} "
                            "because it no longer exists. Select a current "
                            "node and try again."
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
                if form_type == "edit-edge":
                    try:
                        from_vertex_str = (
                            form_source.strip() if form_source else ""
                        )
                        to_vertex_str = (
                            form_target.strip() if form_target else ""
                        )
                        was_updated = self.graph_editor.update_edge_endpoints(
                            node_id, 
                            from_vertex_str or None, 
                            to_vertex_str or None
                        )
                    except VertexNotFoundError as exception:
                        endpoint_name = exception.field_name or "Source/Target"
                        return (
                            no_update,
                            self.action_logger.append_status(
                                current_log,
                                "Could not update Player node "
                                f"{self.action_logger.quote_value(node_id)} "
                                f"because {endpoint_name} must be an existing "
                                "NPC node ID. Enter a valid NPC node ID "
                                f"in {endpoint_name} and save again."
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
            if form_type == "delete":
                if not resolved_selected_nodes:
                    raise PreventUpdate
                node_id = resolved_selected_nodes[0].get("id", "")
                if not node_id:
                    raise PreventUpdate
                cascade_delete_enabled = "cascade" in (form_cascade or [])
                was_edge_delete = node_id in self.graph_editor.graph.edge_dict
                was_vertex_delete = (
                    node_id in self.graph_editor.graph.vertex_dict
                )
                delete_messages = []
                if was_vertex_delete and cascade_delete_enabled:
                    delete_messages.append(
                        self.action_logger.build_delete_log(
                            "NPC node",
                            node_id,
                            self.action_logger.get_npc_log_fields(
                                node_id, include_empty=True
                            )
                        )
                    )
                if was_edge_delete:
                    delete_messages.append(
                        self.action_logger.build_delete_log(
                            "Player node",
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
                                "Player node",
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
                            current_log,
                            "You could not delete NPC node "
                            f"{self.action_logger.quote_value(node_id)} "
                            "because the first NPC node cannot be deleted."
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
                            current_log,
                            "Could not delete "
                            f"{self.action_logger.quote_value(node_id)} "
                            "because it no longer exists. Select a current "
                            "node and try again."
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
                new_log = self.action_logger.append_statuses(
                    current_log, delete_messages
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
            Output("quit-signal", "data", allow_duplicate=True),
            Input("confirm-unsaved-work", "submit_n_clicks"),
            State("pending-action", "data"),
            State("pending-upload", "data"),
            State("action-status", "value"),
            State("quit-signal", "data"),
            prevent_initial_call=True
        )
        def on_confirm_unsaved_submit(
            confirm_unsaved_submit_clicks: int,
            pending_action: str | None,
            pending_upload: dict | None,
            current_log: str | None,
            quit_signal: int | None
        ) -> tuple[object, object, object, object, bool, str, dict, object]:
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
                    {},
                    no_update
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
                    {},
                    no_update
                )
            if pending_action == self.PENDING_ACTION_QUIT:
                self.request_app_shutdown()
                return (
                    self.action_logger.append_status(
                        current_log,
                        "Discarded unsaved changes and quit the dialogue "
                        "editor session."
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
            Output("bottom-form-source", "value"),
            Output("bottom-form-target", "value"),
            Output("pick-mode-active", "data", allow_duplicate=True),
            Output("pick-mode-field", "data", allow_duplicate=True),
            Input("dialogue-editor", "tapNodeData"),
            State("pick-mode-active", "data"),
            State("pick-mode-field", "data"),
            State("bottom-form-source", "value"),
            State("bottom-form-target", "value"),
            prevent_initial_call=True
        )
        def on_graph_click_during_pick_mode(
            tapped_node: dict | None,
            pick_mode_active: bool,
            pick_field: str,
            current_source: str | None,
            current_target: str | None
        ) -> tuple[str, str, bool, str]:
            if not pick_mode_active or not tapped_node:
                raise PreventUpdate
            node_id = tapped_node.get("id", "")
            if not node_id:
                raise PreventUpdate
            if pick_field == "source":
                return (
                    node_id,
                    current_target or "",
                    False,
                    ""
                )
            if pick_field == "target":
                return (
                    current_source or "",
                    node_id,
                    False,
                    ""
                )
            raise PreventUpdate

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
            Output("confirm-unsaved-work", "displayed", allow_duplicate=True),
            Output("confirm-unsaved-work", "message", allow_duplicate=True),
            Output("pending-action", "data", allow_duplicate=True),
            Output("pending-upload", "data", allow_duplicate=True),
            Output("action-status", "value", allow_duplicate=True),
            Output("quit-signal", "data", allow_duplicate=True),
            Input("quit-editor", "n_clicks"),
            State("unsaved-changes", "data"),
            State("action-status", "value"),
            State("quit-signal", "data"),
            prevent_initial_call=True
        )
        def on_quit_editor(
            quit_editor_clicks: int,
            unsaved_changes: bool,
            current_log: str | None,
            quit_signal: int | None
        ) -> tuple[bool, object, str, dict, object, object]:
            if not quit_editor_clicks:
                raise PreventUpdate
            if unsaved_changes:
                return (
                    True,
                    "You have unsaved changes. Quit anyway?",
                    self.PENDING_ACTION_QUIT,
                    {},
                    no_update,
                    no_update
                )
            self.request_app_shutdown()
            return (
                False,
                no_update,
                "",
                {},
                self.action_logger.append_status(
                    current_log,
                    "Quit the dialogue editor session."
                ),
                (quit_signal or 0) + 1
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
            Output("dialogue-editor", "elements", allow_duplicate=True),
            Output("selected-node-id", "data", allow_duplicate=True),
            Output("action-status", "value", allow_duplicate=True),
            Output("bottom-panel", "style", allow_duplicate=True),
            Output("bottom-panel-visible", "data", allow_duplicate=True),
            Output("bottom-panel-form-type", "data", allow_duplicate=True),
            Output("bottom-panel-title", "children", allow_duplicate=True),
            Output("bottom-form-dialogue", "value", allow_duplicate=True),
            Output("bottom-form-source", "value", allow_duplicate=True),
            Output("bottom-form-target", "value", allow_duplicate=True),
            Output("bottom-form-predicates", "value", allow_duplicate=True),
            Output("bottom-form-effects", "value", allow_duplicate=True),
            Output("bottom-form-cascade", "value", allow_duplicate=True),
            Output("pick-mode-active", "data", allow_duplicate=True),
            Output("pick-mode-field", "data", allow_duplicate=True),
            Output("bottom-panel-save", "children", allow_duplicate=True),
            Output("bottom-panel-save", "style", allow_duplicate=True),
            Output("bottom-panel-close", "children", allow_duplicate=True),
            Output("bottom-panel-close", "style", allow_duplicate=True),
            Input("dialogue-editor", "contextMenuData"),
            State("dialogue-editor", "elements"),
            State("action-status", "value"),
            prevent_initial_call=True
        )
        def open_bottom_panel_from_context_menu(
            context_menu_data: dict | None,
            elements: list[dict[str, Any]] | None,
            current_log: str | None
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
            Output("dialogue-editor", "elements", allow_duplicate=True),
            Input("dialogue-editor", "contextMenuData"),
            State("dialogue-editor", "elements"),
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
            Output("document-name", "value"),
            Input("current-document", "data")
        )
        def sync_document_name(current_document: str | None) -> str:
            return self.normalize_name(current_document)

        @self.callback(
            Output("open-add-edge-modal", "disabled"),
            Output("open-add-edge-modal", "style"),
            Output("open-add-edge-tooltip", "title"),
            Input("dialogue-editor", "elements")
        )
        def toggle_add_player_button(
            elements: list[dict] | None
        ) -> tuple[bool, dict[str, str | int], str]:
            return self.get_add_player_button_state()
        
        @self.callback(
            Output("open-edit-modal", "disabled"),
            Output("open-edit-modal", "style"),
            Output("open-edit-tooltip", "title"),
            Output("open-delete-modal", "disabled"),
            Output("open-delete-modal", "style"),
            Output("open-delete-tooltip", "title"),
            Input("dialogue-editor", "selectedNodeData")
        )
        def toggle_edit_delete_buttons(
            selected_nodes: list[dict] | None
        ) -> tuple[bool, dict, str, bool, dict, str]:
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
                    "Select a node to edit.",
                    True,
                    {
                        **delete_base_style,
                        "backgroundColor": "#4b1c1c",
                        "color": "#6b7280",
                        "border": "1px solid #7f1d1d",
                        "cursor": "not-allowed",
                        "opacity": 0.5
                    },
                    "Select a node to delete."
                )
            return (
                False, 
                {
                    **edit_base_style,
                    "backgroundColor": "#4b5563",
                    "color": "#e6e6e6",
                    "cursor": "pointer"
                },
                "Edit the selected node's text, effects, and predicates (E)",
                False,
                {
                    **delete_base_style,
                    "backgroundColor": "#7f1d1d",
                    "color": "#e6e6e6",
                    "border": "1px solid #c53030",
                    "cursor": "pointer"
                },
                "Remove the selected node from the graph (Delete / Backspace)"
            )

        @self.callback(
            Output("dialogue-editor", "contextMenu"),
            Input("pick-mode-active", "data"),
            Input("bottom-panel-visible", "data"),
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

    def request_app_shutdown(self) -> None:
        """Stop the server after the current callback response is sent."""
        shutdown_server = request.environ.get("werkzeug.server.shutdown")
        if shutdown_server:
            Timer(0.1, shutdown_server).start()
            return
        Timer(0.1, _exit, args=(0,)).start()

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

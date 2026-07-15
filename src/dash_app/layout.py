from dash import dcc, html
from dash_cytoscape import Cytoscape
from datetime import datetime
from pathlib import Path
from tomllib import load as toml_load

from dash_app.constants import CascadeValue, ElementId
from dash_app.messages import (
    BUTTON_CANCEL,
    BUTTON_CLOSE,
    BUTTON_CONFIRM,
    BUTTON_NEW,
    BUTTON_OPEN,
    BUTTON_QUIT,
    BUTTON_REDO,
    BUTTON_SAVE,
    BUTTON_SELECT_FROM_GRAPH,
    BUTTON_SHORTCUTS,
    BUTTON_UNDO,
    CONFIRM_DELETE_NODE_QUESTION,
    CONFIRM_UNSAVED_CONTINUE,
    DEFAULT_DOCUMENT_NAME,
    DEFAULT_NODE_DISPLAY,
    HEADER_LOG,
    HEADER_NPC_NAME,
    HEADER_SELECTED_NODE,
    LABEL_CASCADE_OPTION,
    LABEL_DIALOGUE,
    LABEL_DOCUMENT,
    LABEL_EFFECTS,
    LABEL_PREDICATES,
    LABEL_SOURCE_NPC,
    LABEL_TARGET_NPC,
    MENU_DELETE_NODE,
    MENU_EDIT_NODE,
    PLACEHOLDER_EFFECTS,
    PLACEHOLDER_NPC_NAME,
    PLACEHOLDER_PREDICATES,
    PLACEHOLDER_SOURCE_NPC,
    PLACEHOLDER_TARGET_NPC,
    SHORTCUTS_HELP,
    SHORTCUTS_HELP_FOOTER,
    TITLE_ADD_NPC,
    TITLE_ADD_PLAYER,
    TITLE_DIALOGUE_EDITOR,
    TITLE_FORM,
    TITLE_KEYBOARD_SHORTCUTS,
    TOOLTIP_ADD_NPC_BUTTON,
    TOOLTIP_NEW,
    TOOLTIP_OPEN,
    TOOLTIP_QUIT,
    TOOLTIP_REDO,
    TOOLTIP_SAVE_COPY,
    TOOLTIP_SHORTCUTS,
    TOOLTIP_UNDO
)
from dash_app.theme import (
    COLOR_DANGER_BG,
    COLOR_DANGER_BORDER,
    COLOR_DARK_BG,
    COLOR_DELETE_HIGHLIGHT,
    COLOR_INPUT_BG,
    COLOR_INPUT_BORDER,
    COLOR_INPUT_TEXT,
    COLOR_LOG_ROW_BORDER,
    COLOR_PANEL_ALT_BG,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_PRIMARY_BG,
    COLOR_ROW_BORDER,
    COLOR_SELECT_HIGHLIGHT,
    COLOR_TEXT,
    COLOR_TEXT_DOCUMENT,
    COLOR_TEXT_LIGHT,
    COLOR_TEXT_MUTED,
    FONT_SIZE_BASE,
    FONT_SIZE_H1,
    FONT_SIZE_H2,
    FONT_SIZE_LG,
    FONT_SIZE_TITLE,
    FONT_SIZE_XS,
    get_close_button_style,
    get_input_style,
    get_key_badge_style,
    get_label_style,
    get_panel_button_danger_style,
    get_panel_button_enabled_style,
    get_pick_button_style,
    get_primary_button_style,
    get_textarea_style,
    get_toolbar_button_disabled_style,
    get_toolbar_button_style,
    PANEL_WIDTH,
    RADIUS,
    RADIUS_LG,
    thin_border
)
from dialogue_viewer.theme import (
    COLOR_BACKGROUND,
    COLOR_EDGE_LINE,
    COLOR_EDGE_NODE_FILL,
    COLOR_FONT,
    COLOR_NODE_BORDER,
    COLOR_START_VERTEX_BORDER,
    COLOR_START_VERTEX_FILL,
    COLOR_VERTEX_FILL
)

def build_log_children(entries: list[dict[str, str]] | None) -> list[html.Div]:
    """Build log row components from entries in reverse-chronological order.

    Args:
        entries (list[dict[str, str]] | None): Structured log entries.

    Returns:
        list: Log row components, newest first.
    """
    if not entries:
        return []
    return [get_log_row(entry) for entry in reversed(entries)]

def format_log_timestamp(timestamp: str) -> str:
    """Format an ISO timestamp as a standard hr:min:sec time.

    Args:
        timestamp (str): ISO 8601 timestamp string.

    Returns:
        str: Time formatted as "HH:MM:SS", or an empty string if invalid.
    """
    if not timestamp:
        return ""
    try:
        return datetime.fromisoformat(timestamp).strftime("%H:%M:%S")
    except ValueError:
        return ""

def get_bottom_panel() -> html.Div:
    """Build the bottom panel for form editing with flexible field layout.

    Returns:
        html.Div: Bottom panel component containing all form fields.
    """
    primary_button_style = get_primary_button_style()
    secondary_button_style = get_close_button_style()
    return html.Div(
        [
            html.Div(
                [
                    html.H2(
                        TITLE_FORM,
                        id=ElementId.BOTTOM_PANEL_TITLE,
                        style={
                            "margin": "0",
                            "fontSize": FONT_SIZE_TITLE,
                            "color": COLOR_TEXT,
                            "flex": "1"
                        }
                    ),
                    html.Div(
                        [
                            html.Button(
                                BUTTON_SAVE,
                                id=ElementId.BOTTOM_PANEL_SAVE,
                                n_clicks=0,
                                style=primary_button_style
                            ),
                            html.Button(
                                BUTTON_CANCEL,
                                id=ElementId.BOTTOM_PANEL_CLOSE,
                                n_clicks=0,
                                style=secondary_button_style
                            )
                        ],
                        style={"display": "flex", "gap": "8px"}
                    )
                ],
                style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "marginBottom": "16px",
                    "paddingBottom": "12px",
                    "borderBottom": thin_border(COLOR_PANEL_BORDER)
                }
            ),
            html.Div(
                [
                    html.Label(LABEL_DIALOGUE, style=get_label_style()),
                    dcc.Textarea(
                        id=ElementId.BOTTOM_FORM_DIALOGUE,
                        placeholder=LABEL_DIALOGUE,
                        style=get_textarea_style("100px")
                    )
                ],
                id=ElementId.BOTTOM_FORM_DIALOGUE_CONTAINER,
                style={"marginBottom": "12px"}
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label(
                                LABEL_SOURCE_NPC, style=get_label_style()
                            ),
                            html.Div(
                                [
                                    dcc.Input(
                                        id=ElementId.BOTTOM_FORM_SOURCE,
                                        type="text",
                                        placeholder=PLACEHOLDER_SOURCE_NPC,
                                        style={
                                            **get_input_style(),
                                            "flex": "1",
                                            "minWidth": "150px"
                                        }
                                    ),
                                    html.Button(
                                        BUTTON_SELECT_FROM_GRAPH,
                                        id=ElementId.BOTTOM_FORM_PICK_SOURCE,
                                        n_clicks=0,
                                        style=get_pick_button_style()
                                    )
                                ],
                                style={
                                    "display": "flex", 
                                    "gap": "4px", 
                                    "alignItems": "flex-end"
                                }
                            )
                        ],
                        style={
                            "flex": "1",
                            "minWidth": "280px",
                            "marginRight": "8px"
                        },
                        id=ElementId.BOTTOM_FORM_SOURCE_CONTAINER
                    ),
                    html.Div(
                        [
                            html.Label(
                                LABEL_TARGET_NPC, style=get_label_style()
                            ),
                            html.Div(
                                [
                                    dcc.Input(
                                        id=ElementId.BOTTOM_FORM_TARGET,
                                        type="text",
                                        placeholder=PLACEHOLDER_TARGET_NPC,
                                        style={
                                            **get_input_style(),
                                            "flex": "1",
                                            "minWidth": "150px"
                                        }
                                    ),
                                    html.Button(
                                        BUTTON_SELECT_FROM_GRAPH,
                                        id=ElementId.BOTTOM_FORM_PICK_TARGET,
                                        n_clicks=0,
                                        style=get_pick_button_style()
                                    )
                                ],
                                style={
                                    "display": "flex",
                                    "gap": "4px",
                                    "alignItems": "flex-end"
                                }
                            )
                        ],
                        style={
                            "flex": "1",
                            "minWidth": "280px"
                        },
                        id=ElementId.BOTTOM_FORM_TARGET_CONTAINER
                    )
                ],
                style={
                    "display": "flex",
                    "gap": "8px",
                    "marginBottom": "12px",
                    "flexWrap": "wrap"
                }
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label(
                                LABEL_PREDICATES, 
                                style=get_label_style()
                            ),
                            dcc.Textarea(
                                id=ElementId.BOTTOM_FORM_PREDICATES,
                                placeholder=PLACEHOLDER_PREDICATES,
                                style=get_textarea_style("70px")
                            )
                        ],
                        id=ElementId.BOTTOM_FORM_PREDICATES_CONTAINER,
                        style={
                            "flex": "1", 
                            "minWidth": "300px", 
                            "marginRight": "8px"
                        }
                    ),
                    html.Div(
                        [
                            html.Label(LABEL_EFFECTS, style=get_label_style()),
                            dcc.Textarea(
                                id=ElementId.BOTTOM_FORM_EFFECTS,
                                placeholder=PLACEHOLDER_EFFECTS,
                                style=get_textarea_style("70px")
                            )
                        ],
                        id=ElementId.BOTTOM_FORM_EFFECTS_CONTAINER,
                        style={"flex": "1", "minWidth": "300px"}
                    )
                ],
                style={
                    "display": "flex",
                    "gap": "8px",
                    "marginBottom": "12px",
                    "flexWrap": "wrap"
                }
            ),
            html.Div(
                [
                    html.Div(
                        CONFIRM_DELETE_NODE_QUESTION,
                        id=ElementId.BOTTOM_FORM_DELETE_MESSAGE_CONTAINER,
                        style={
                            "display": "none",
                            "marginBottom": "12px",
                            "color": COLOR_TEXT
                        }
                    ),
                    html.Div(
                        [
                            dcc.Checklist(
                                id=ElementId.BOTTOM_FORM_CASCADE,
                                options=[
                                    {
                                        "label": LABEL_CASCADE_OPTION,
                                        "value": CascadeValue.CASCADE
                                    }
                                ],
                                value=[],
                                labelStyle={"color": COLOR_TEXT_LIGHT},
                                style={"color": COLOR_TEXT_LIGHT}
                            )
                        ]
                    )
                ],
                id=ElementId.BOTTOM_FORM_CASCADE_CONTAINER,
                style={"display": "none"}
            )
        ],
        id=ElementId.BOTTOM_PANEL,
        style=get_bottom_panel_style(False)
    )

def get_bottom_panel_style(is_open: bool) -> dict[str, str | int]:
    """Return style for the bottom panel while preserving fixed placement.

    Args:
        is_open (bool): Whether the panel is visible.

    Returns:
        dict[str, str | int]: Style mapping for bottom panel container.
    """
    return {
        "display": "block" if is_open else "none",
        "position": "absolute",
        "bottom": "0",
        "left": "0",
        "right": "0",
        "backgroundColor": COLOR_PANEL_ALT_BG,
        "borderTop": thin_border(COLOR_PANEL_BORDER),
        "padding": "16px",
        "boxSizing": "border-box",
        "maxHeight": "45vh",
        "overflowY": "auto",
        "zIndex": "999",
        "boxShadow": "0 -4px 12px rgba(0, 0, 0, 0.3)"
    }

def get_center_panel(
    initial_elements: list,
    context_menu: list[dict[str, str | list[str]]] | None = None
) -> html.Div:
    """Build the center graph panel with Cytoscape visualization.

    Args:
        initial_elements (list): Initial Cytoscape graph elements.
        context_menu (list[dict[str, str | list[str]]] | None): Context menu
            items passed to the Cytoscape component.

    Returns:
        html.Div: Center panel component.
    """
    return html.Div(
        [
            get_header(),
            html.Div(
                [
                    html.Div(
                        get_graph_component(initial_elements, context_menu),
                        id=ElementId.GRAPH_CONTAINER,
                        style={"flex": "1", "minHeight": 0}
                    ),
                    get_bottom_panel()
                ],
                style={
                    "flex": "1",
                    "minHeight": 0,
                    "display": "flex",
                    "flexDirection": "column",
                    "position": "relative",
                    "overflow": "hidden"
                }
            )
        ],
        style={
            "flex": "1",
            "minWidth": 0,
            "height": "100%",
            "display": "flex",
            "flexDirection": "column"
        }
    )

def get_cytoscape_stylesheet() -> list[dict[str, str | dict[str, str | int]]]:
    """Return the Cytoscape stylesheet for graph rendering.

    Returns:
        list[dict[str, str | dict[str, str | int]]]: Cytoscape style rules.
    """
    return [
        {
            "selector": "node",
            "style": {
                "shape": "round-rectangle",
                "background-color": COLOR_VERTEX_FILL,
                "border-color": COLOR_NODE_BORDER,
                "border-width": 2,
                "color": COLOR_FONT,
                "font-family": "Helvetica",
                "font-size": "12px",
                "label": "data(label)",
                "text-valign": "center",
                "text-halign": "center",
                "text-wrap": "wrap",
                "text-max-width": 240,
                "min-width": 80,
                "min-height": 40,
                "width": "label",
                "height": "label",
                "padding": "20px"
            }
        },
        {
            "selector": "edge",
            "style": {
                "line-color": COLOR_EDGE_LINE,
                "target-arrow-color": COLOR_EDGE_LINE,
                "target-arrow-shape": "triangle",
                "color": COLOR_FONT,
                "curve-style": "bezier"
            }
        },
        {
            "selector": "node:selected",
            "style": {
                "border-color": COLOR_SELECT_HIGHLIGHT,
                "border-width": 4
            }
        },
        {
            "selector": "[?is_edge_node]",
            "style": {
                "shape": "ellipse",
                "background-color": COLOR_EDGE_NODE_FILL,
                "padding": "30px"
            }
        },
        {
            "selector": "[?is_start_vertex]",
            "style": {
                "border-color": COLOR_START_VERTEX_BORDER,
                "border-width": 3,
                "background-color": COLOR_START_VERTEX_FILL,
                "font-weight": "bold"
            }
        },
        {
            "selector": "[?is_start_vertex]:selected",
            "style": {
                "border-color": COLOR_SELECT_HIGHLIGHT,
                "border-width": 4
            }
        },
        {
            "selector": "[?has_missing_endpoint]",
            "style": {
                "border-color": COLOR_DELETE_HIGHLIGHT,
                "border-width": 4,
                "background-color": COLOR_DANGER_BG
            }
        },
        {
            "selector": "[?has_missing_endpoint]:selected",
            "style": {
                "border-color": COLOR_SELECT_HIGHLIGHT,
                "border-width": 6
            }
        }
    ]

def get_edit_section() -> list:
    """Build the selected node display.

    Returns:
        list: Dash components showing currently selected node.
    """
    return [
        html.H3(HEADER_SELECTED_NODE),
        html.Div(
            DEFAULT_NODE_DISPLAY,
            id=ElementId.SELECTED_NODE_DISPLAY,
            style={
                "padding": "8px",
                "marginBottom": "12px",
                "backgroundColor": COLOR_DARK_BG,
                "border": thin_border(COLOR_PRIMARY_BG),
                "borderRadius": RADIUS,
                "color": COLOR_TEXT_LIGHT,
                "fontSize": FONT_SIZE_BASE
            }
        )
    ]

def get_graph_component(
    elements: list, 
    key: str | None = None, 
    context_menu: list[dict[str, str | list[str]]] | None = None
) -> html.Div:
    """ Build the Cytoscape graph wrapped in a keyed container.

    The key is placed on the wrapping Div (dash_cytoscape rejects unknown
    props such as "key"). Changing the key forces React to remount the 
    wrapper and, with it, a fresh Cytoscape instance. This fully resets
    selection and render state when an entirely new graph is loaded
    (New/Open), so nodes whose ids are shared across graphs (e.g. the
    mandatory vertex_0) do not retain selection from a prior graph.

    Args:
        elements (list): Cytoscape graph elements.
        key (str | None): React key on the wrapper. Change to force remount.
        context_menu (list[dict[str, str | list[str]]] | None): Context menu
            items passed through to Cytoscape.

    Returns:
        html.Div: The keyed wrapper containing the graph component.
    """
    return html.Div(
        Cytoscape(
            id=ElementId.DIALOGUE_EDITOR,
            layout={"name": "dagre", "rankDir": "TB"},
            clearOnUnhover=True,
            style={
                "width": "100%",
                "height": "100%",
                "backgroundColor": COLOR_BACKGROUND
            },
            elements=elements,
            contextMenu=context_menu or [],
            stylesheet=get_cytoscape_stylesheet()
        ),
        key=key,
        style={"width": "100%", "height": "100%"}
    )

def get_header() -> html.Div:
    """Build the top toolbar for graph-level actions.

    Returns:
        html.Div: Header component with new/open/save controls.
    """
    button_style = get_toolbar_button_style()
    return html.Div(
        [
            html.Button(
                BUTTON_NEW,
                id=ElementId.NEW_GRAPH,
                n_clicks=0,
                title=TOOLTIP_NEW,
                style=button_style
            ),
            html.Div(
                get_upload_graph(button_style),
                id=ElementId.UPLOAD_GRAPH_CONTAINER,
                style={"display": "inline-block"}
            ),
            html.Button(
                BUTTON_SAVE,
                id=ElementId.DOWNLOAD_GRAPH,
                n_clicks=0,
                title=TOOLTIP_SAVE_COPY,
                style=button_style
            ),
            html.Button(
                BUTTON_UNDO,
                id=ElementId.UNDO_ACTION,
                n_clicks=0,
                title=TOOLTIP_UNDO,
                disabled=True,
                style=get_toolbar_button_disabled_style()
            ),
            html.Button(
                BUTTON_REDO,
                id=ElementId.REDO_ACTION,
                n_clicks=0,
                title=TOOLTIP_REDO,
                disabled=True,
                style=get_toolbar_button_disabled_style()
            ),
            html.Div(
                LABEL_DOCUMENT.format(name=DEFAULT_DOCUMENT_NAME),
                id=ElementId.CURRENT_DOCUMENT_LABEL,
                style={
                    "fontSize": FONT_SIZE_LG,
                    "color": COLOR_TEXT_DOCUMENT,
                    "marginLeft": "8px"
                }
            ),
            html.Div(style={"flex": "1"}),
            html.Button(
                BUTTON_SHORTCUTS,
                id=ElementId.OPEN_SHORTCUTS_HELP,
                n_clicks=0,
                title=TOOLTIP_SHORTCUTS,
                style=button_style
            ),
            html.Button(
                BUTTON_QUIT,
                id=ElementId.QUIT_EDITOR,
                n_clicks=0,
                title=TOOLTIP_QUIT,
                style={
                    **button_style,
                    "backgroundColor": COLOR_DANGER_BG,
                    "border": thin_border(COLOR_DANGER_BORDER)
                }
            )
        ],
        style={
            "display": "flex",
            "justifyContent": "flex-start",
            "alignItems": "center",
            "gap": "8px",
            "whiteSpace": "nowrap",
            "overflow": "hidden",
            "backgroundColor": COLOR_PANEL_BG,
            "borderBottom": thin_border(COLOR_PANEL_BORDER),
            "flexShrink": 0,
            "padding": "8px 10px"
        }
    )

def get_index_string() -> str:
    """Return the custom Dash HTML template.

    Returns:
        str: Full HTML template string used by Dash.
    """
    return """
        <!DOCTYPE html>
        <html>
            <head>
                {%metas%}
                <title>{%title%}</title>
                {%favicon%}
                {%css%}
                <style>
                    html, body, #react-entry-point {
                        margin: 0;
                        padding: 0;
                        width: 100%;
                        height: 100%;
                        overflow: hidden;
                        background-color: """ + COLOR_PANEL_BG + """;
                    }
                    .cy-context-menus-cxt-menu,
                    .cy-context-menus-cxt-menuitem,
                    .custom-menu-item {
                        min-width: 220px !important;
                        width: max-content !important;
                        white-space: nowrap !important;
                        padding-left: 12px !important;
                        padding-right: 12px !important;
                        box-sizing: border-box !important;
                    }
                </style>
            </head>
            <body>
                {%app_entry%}
                <footer>
                    {%config%}
                    {%scripts%}
                    {%renderer%}
                </footer>
            </body>
        </html>
    """

def get_left_panel(initial_name: str, author: str, version: str) -> html.Div:
    """Build the left sidebar panel with title, controls, and action buttons.

    Args:
        initial_name (str): Initial value for the NPC name input.
        author (str): Author name read from pyproject.toml.
        version (str): Version string read from pyproject.toml.

    Returns:
        html.Div: Left panel component.
    """
    subtitle_parts = [
        part for part in [author, f"v{version}" if version else ""] 
        if part
    ]
    subtitle = " \u00b7 ".join(subtitle_parts)
    return html.Div(
        [
            html.H1(
                TITLE_DIALOGUE_EDITOR,
                style={
                    "marginTop": "0",
                    "marginBottom": "4px",
                    "color": COLOR_TEXT,
                    "fontSize": FONT_SIZE_H1,
                    "fontWeight": "bold"
                }
            ),
            html.P(
                subtitle,
                style={
                    "marginTop": "0",
                    "marginBottom": "20px",
                    "color": COLOR_TEXT_MUTED,
                    "fontSize": FONT_SIZE_XS
                }
            ),
            html.Hr(style={"margin": "16px 0"}),
            *get_name_section(initial_name),
            html.Hr(style={"margin": "16px 0"}),
            *get_edit_section(),
            html.Hr(style={"margin": "16px 0"}),
            html.Button(
                TITLE_ADD_NPC,
                id=ElementId.OPEN_ADD_VERTEX_MODAL,
                n_clicks=0,
                title=TOOLTIP_ADD_NPC_BUTTON,
                style=get_panel_button_enabled_style()
            ),
            html.Div(
                html.Button(
                    TITLE_ADD_PLAYER,
                    id=ElementId.OPEN_ADD_EDGE_MODAL,
                    n_clicks=0,
                    style=get_panel_button_enabled_style()
                ),
                id=ElementId.OPEN_ADD_EDGE_TOOLTIP,
                title="",
                style={"display": "block"}
            ),
            html.Div(
                html.Button(
                    MENU_EDIT_NODE,
                    id=ElementId.OPEN_EDIT_MODAL,
                    n_clicks=0,
                    style=get_panel_button_enabled_style()
                ),
                id=ElementId.OPEN_EDIT_TOOLTIP,
                title="",
                style={"display": "block"}
            ),
            html.Div(
                html.Button(
                    MENU_DELETE_NODE,
                    id=ElementId.OPEN_DELETE_MODAL,
                    n_clicks=0,
                    style=get_panel_button_danger_style()
                ),
                id=ElementId.OPEN_DELETE_TOOLTIP,
                title="",
                style={"display": "block"}
            )
        ],
        style={
            "width": PANEL_WIDTH,
            "flexShrink": 0,
            "boxSizing": "border-box",
            "padding": "12px",
            "paddingBottom": "24px",
            "backgroundColor": COLOR_PANEL_BG,
            "color": COLOR_TEXT,
            "borderRight": thin_border(COLOR_PANEL_BORDER),
            "overflowY": "auto",
            "height": "100vh"
        }
    )

def get_log_row(entry: dict[str, str]) -> html.Div:
    """Build a single log row with a timestamp and message.

    Args:
        entry (dict[str, str]): Structured log entry.

    Returns:
        html.Div: Row component displaying the entry.
    """
    return html.Div(
        [
            html.Span(
                format_log_timestamp(entry.get("timestamp", "")),
                style={
                    "color": COLOR_TEXT_MUTED,
                    "fontFamily": "monospace",
                    "fontSize": FONT_SIZE_XS,
                    "marginRight": "8px",
                    "flexShrink": 0
                }
            ),
            html.Span(
                entry.get("message", ""),
                style={"whiteSpace": "pre-wrap", "flex": "1"}
            )
        ],
        style={
            "display": "flex",
            "alignItems": "baseline",
            "paddingBottom": "6px",
            "borderBottom": thin_border(COLOR_LOG_ROW_BORDER)
        }
    )

def get_modal_backdrop_style(is_open: bool) -> dict[str, str | int]:
    """Return style for a centered modal backdrop overlay.

    Args:
        is_open (bool): Whether the overlay is visible.

    Returns:
        dict[str, str | int]: Style mapping for the overlay container.
    """
    return {
        "display": "flex" if is_open else "none",
        "position": "fixed",
        "top": "0",
        "left": "0",
        "right": "0",
        "bottom": "0",
        "alignItems": "center",
        "justifyContent": "center",
        "backgroundColor": "rgba(0, 0, 0, 0.6)",
        "zIndex": "1000"
    }

def get_name_section(initial_value: str = DEFAULT_DOCUMENT_NAME) -> list:
    """Build the sidebar controls for editing NPC name.

    Args:
        initial_value (str): Initial text for the name input.

    Returns:
        list: Dash components for name editing controls.
    """
    return [
        html.H3(HEADER_NPC_NAME),
        dcc.Input(
            id=ElementId.DOCUMENT_NAME,
            type="text",
            value=initial_value,
            placeholder=PLACEHOLDER_NPC_NAME,
            style={
                "width": "100%",
                "marginBottom": "12px",
                "backgroundColor": COLOR_INPUT_BG,
                "color": COLOR_INPUT_TEXT,
                "caretColor": COLOR_INPUT_TEXT,
                "border": thin_border(COLOR_INPUT_BORDER),
                "fontSize": FONT_SIZE_BASE,
                "opacity": 1
            }
        ),
        html.Button(BUTTON_SAVE, id=ElementId.SAVE_NAME, n_clicks=0)
    ]

def get_project_metadata() -> tuple[str, str]:
    """Get author name and version from pyproject.toml.

    Returns:
        tuple[str, str]: (author, version) strings, empty if unavailable.
    """
    toml_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    try:
        with open(toml_path, "rb") as f:
            data = toml_load(f)
        project = data.get("project", {})
        version = project.get("version", "")
        authors = project.get("authors", [])
        author = authors[0].get("name", "") if authors else ""
        return author, version
    except (FileNotFoundError, KeyError, IndexError):
        return "", ""

def get_right_panel() -> html.Div:
    """Build the right sidebar panel containing the action log.

    Returns:
        html.Div: Right panel component.
    """
    return html.Div(
        [
            html.H3(HEADER_LOG, style={"marginTop": "0"}),
            html.Div(
                id=ElementId.ACTION_LOG_DISPLAY,
                style={
                    "width": "100%",
                    "flex": "1",
                    "fontSize": FONT_SIZE_BASE,
                    "backgroundColor": COLOR_DARK_BG,
                    "color": COLOR_TEXT_LIGHT,
                    "border": thin_border(COLOR_PRIMARY_BG),
                    "padding": "8px",
                    "overflowY": "auto",
                    "boxSizing": "border-box",
                    "display": "flex",
                    "flexDirection": "column",
                    "gap": "8px",
                    "maskImage": (
                        "linear-gradient(to bottom, rgba(0, 0, 0, 1) 0%, "
                        "rgba(0, 0, 0, 0.3) 100%)"
                    ),
                    "WebKitMaskImage": (
                        "linear-gradient(to bottom, rgba(0, 0, 0, 1) 0%, "
                        "rgba(0, 0, 0, 0.3) 100%)"
                    )
                }
            )
        ],
        style={
            "width": PANEL_WIDTH,
            "flexShrink": 0,
            "boxSizing": "border-box",
            "padding": "12px",
            "paddingBottom": "24px",
            "backgroundColor": COLOR_PANEL_BG,
            "color": COLOR_TEXT,
            "borderLeft": thin_border(COLOR_PANEL_BORDER),
            "display": "flex",
            "flexDirection": "column",
            "height": "100vh"
        }
    )

def get_shortcuts_overlay() -> html.Div:
    """Build the modal overlay that lists all keyboard shortcuts.

    Returns:
        html.Div: Full screen overlay component listing keyboard shortcuts.
    """
    shortcuts = SHORTCUTS_HELP
    key_style = get_key_badge_style()
    row_style = {
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center",
        "gap": "16px",
        "padding": "8px 0",
        "borderBottom": thin_border(COLOR_ROW_BORDER)
    }
    rows = [
        html.Div(
            [
                html.Span(description, style={"color": COLOR_TEXT}),
                html.Span(keys, style=key_style)
            ],
            style=row_style
        )
        for description, keys in shortcuts
    ]
    return html.Div(
        html.Div(
            [
                html.Div(
                    [
                        html.H2(
                            TITLE_KEYBOARD_SHORTCUTS,
                            style={
                                "margin": "0",
                                "fontSize": FONT_SIZE_H2,
                                "color": COLOR_TEXT,
                                "flex": "1"
                            }
                        ),
                        html.Button(
                            BUTTON_CLOSE,
                            id=ElementId.SHORTCUTS_HELP_CLOSE,
                            n_clicks=0,
                            style=get_close_button_style()
                        )
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "center",
                        "marginBottom": "12px",
                        "paddingBottom": "12px",
                        "borderBottom": thin_border(COLOR_PANEL_BORDER)
                    }
                ),
                *rows,
                html.P(
                    SHORTCUTS_HELP_FOOTER,
                    style={
                        "marginTop": "16px",
                        "marginBottom": "0",
                        "color": COLOR_TEXT_MUTED,
                        "fontSize": FONT_SIZE_XS
                    }
                )
            ],
            style={
                "width": "min(480px, 90vw)",
                "maxHeight": "80vh",
                "overflowY": "auto",
                "backgroundColor": COLOR_PANEL_ALT_BG,
                "border": thin_border(COLOR_PANEL_BORDER),
                "borderRadius": RADIUS_LG,
                "padding": "20px",
                "boxSizing": "border-box",
                "boxShadow": "0 8px 32px rgba(0, 0, 0, 0.5)"
            }
        ),
        id=ElementId.SHORTCUTS_OVERLAY,
        style=get_modal_backdrop_style(False)
    )

def get_unsaved_work_modal() -> html.Div:
    """Build the confirmation modal for unsaved-work actions.

    Returns:
        html.Div: Full screen overlay containing the confirmation dialog.
    """
    return html.Div(
        html.Div(
            [
                html.Div(
                    CONFIRM_UNSAVED_CONTINUE,
                    id=ElementId.CONFIRM_UNSAVED_MESSAGE,
                    style={
                        "color": COLOR_TEXT,
                        "fontSize": FONT_SIZE_LG,
                        "marginBottom": "20px"
                    }
                ),
                html.Div(
                    [
                        html.Button(
                            BUTTON_CANCEL,
                            id=ElementId.CONFIRM_UNSAVED_CANCEL,
                            n_clicks=0,
                            style=get_close_button_style()
                        ),
                        html.Button(
                            BUTTON_CONFIRM,
                            id=ElementId.CONFIRM_UNSAVED_CONFIRM,
                            n_clicks=0,
                            style=get_primary_button_style()
                        )
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "flex-end",
                        "gap": "8px"
                    }
                )
            ],
            style={
                "width": "min(420px, 90vw)",
                "backgroundColor": COLOR_PANEL_ALT_BG,
                "border": thin_border(COLOR_PANEL_BORDER),
                "borderRadius": RADIUS_LG,
                "padding": "20px",
                "boxSizing": "border-box",
                "boxShadow": "0 8px 32px rgba(0, 0, 0, 0.5)"
            }
        ),
        id=ElementId.CONFIRM_UNSAVED_WORK,
        style=get_modal_backdrop_style(False)
    )

def get_upload_graph(
    button_style: dict[str, str | int] | None = None
) -> dcc.Upload:
    """Build the upload control used to load graph yaml files.

    Args:
        button_style (dict[str, str | int] | None): Optional style mapping
            for the Open button.

    Returns:
        dcc.Upload: Dash upload component for yaml files.
    """
    resolved_button_style = button_style or get_toolbar_button_style()
    return dcc.Upload(
        id=ElementId.UPLOAD_GRAPH,
        children=html.Button(
            BUTTON_OPEN,
            id=ElementId.UPLOAD_GRAPH_BUTTON,
            n_clicks=0,
            title=TOOLTIP_OPEN,
            style=resolved_button_style
        ),
        multiple=False,
        style={"display": "inline-block"}
    )
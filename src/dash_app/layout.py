from dash import dcc, html
from dash_cytoscape import Cytoscape
from pathlib import Path
from tomllib import load as toml_load

def get_bottom_panel() -> html.Div:
    """Build the bottom panel for form editing with flexible field layout.

    Returns:
        html.Div: Bottom panel component containing all form fields.
    """
    primary_button_style = {
        "padding": "8px 14px",
        "backgroundColor": "#4b5563",
        "color": "#e6e6e6",
        "border": "1px solid #666",
        "borderRadius": "4px",
        "cursor": "pointer"
    }
    secondary_button_style = {
        "padding": "8px 14px",
        "backgroundColor": "#333",
        "color": "#e6e6e6",
        "border": "1px solid #555",
        "borderRadius": "4px",
        "cursor": "pointer"
    }
    return html.Div(
        [
            html.Div(
                [
                    html.H2(
                        "Form",
                        id="bottom-panel-title",
                        style={
                            "margin": "0",
                            "fontSize": "18px",
                            "color": "#e6e6e6",
                            "flex": "1"
                        }
                    ),
                    html.Div(
                        [
                            html.Button(
                                "Save",
                                id="bottom-panel-save",
                                n_clicks=0,
                                style=primary_button_style
                            ),
                            html.Button(
                                "Cancel",
                                id="bottom-panel-close",
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
                    "borderBottom": "1px solid #444"
                }
            ),
            html.Div(
                [
                    html.Label("Dialogue", style=get_label_style()),
                    dcc.Textarea(
                        id="bottom-form-dialogue",
                        placeholder="Dialogue",
                        style=get_textarea_style("100px")
                    )
                ],
                id="bottom-form-dialogue-container",
                style={"marginBottom": "12px"}
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label(
                                "Source NPC Node", style=get_label_style()
                            ),
                            html.Div(
                                [
                                    dcc.Input(
                                        id="bottom-form-source",
                                        type="text",
                                        placeholder="Source NPC node",
                                        style={
                                            **get_input_style(),
                                            "flex": "1",
                                            "minWidth": "150px"
                                        }
                                    ),
                                    html.Button(
                                        "Select From Graph",
                                        id="bottom-form-pick-source",
                                        n_clicks=0,
                                        style={
                                            "padding": "6px 10px",
                                            "backgroundColor": "#5a6370",
                                            "color": "#e6e6e6",
                                            "border": "1px solid #777",
                                            "borderRadius": "4px",
                                            "cursor": "pointer",
                                            "fontSize": "12px",
                                            "marginLeft": "8px"
                                        }
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
                        id="bottom-form-source-container"
                    ),
                    html.Div(
                        [
                            html.Label(
                                "Target NPC Node", style=get_label_style()
                            ),
                            html.Div(
                                [
                                    dcc.Input(
                                        id="bottom-form-target",
                                        type="text",
                                        placeholder="Target NPC node",
                                        style={
                                            **get_input_style(),
                                            "flex": "1",
                                            "minWidth": "150px"
                                        }
                                    ),
                                    html.Button(
                                        "Select From Graph",
                                        id="bottom-form-pick-target",
                                        n_clicks=0,
                                        style={
                                            "padding": "6px 10px",
                                            "backgroundColor": "#5a6370",
                                            "color": "#e6e6e6",
                                            "border": "1px solid #777",
                                            "borderRadius": "4px",
                                            "cursor": "pointer",
                                            "fontSize": "12px",
                                            "marginLeft": "8px"
                                        }
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
                        id="bottom-form-target-container"
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
                            html.Label("Predicates", style=get_label_style()),
                            dcc.Textarea(
                                id="bottom-form-predicates",
                                placeholder="Predicates (one per line)",
                                style=get_textarea_style("70px")
                            )
                        ],
                        id="bottom-form-predicates-container",
                        style={
                            "flex": "1", 
                            "minWidth": "300px", 
                            "marginRight": "8px"
                        }
                    ),
                    html.Div(
                        [
                            html.Label("Effects", style=get_label_style()),
                            dcc.Textarea(
                                id="bottom-form-effects",
                                placeholder="Effects (one per line)",
                                style=get_textarea_style("70px")
                            )
                        ],
                        id="bottom-form-effects-container",
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
                        "Are you sure you want to delete the selected node?",
                        id="bottom-form-delete-message-container",
                        style={
                            "display": "none",
                            "marginBottom": "12px",
                            "color": "#e6e6e6"
                        }
                    ),
                    html.Div(
                        [
                            dcc.Checklist(
                                id="bottom-form-cascade",
                                options=[
                                    {
                                        "label": (
                                            "Delete all connected player "
                                            "nodes? If you do not, you may "
                                            "need to repair unresolved "
                                            "connections."
                                        ),
                                        "value": "cascade"
                                    }
                                ],
                                value=[],
                                labelStyle={"color": "#e5e7eb"},
                                style={"color": "#e5e7eb"}
                            )
                        ]
                    )
                ],
                id="bottom-form-cascade-container",
                style={"display": "none"}
            )
        ],
        id="bottom-panel",
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
        "backgroundColor": "#252d35",
        "borderTop": "1px solid #444",
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
                        id="graph-container",
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
                "background-color": "#a36a2a",
                "border-color": "#aaaaaa",
                "border-width": 2,
                "color": "#e6e6e6",
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
                "line-color": "#cccccc",
                "target-arrow-color": "#cccccc",
                "target-arrow-shape": "triangle",
                "color": "#e6e6e6",
                "curve-style": "bezier"
            }
        },
        {
            "selector": "node:selected",
            "style": {
                "border-color": "#fbbf24",
                "border-width": 4
            }
        },
        {
            "selector": "[?is_edge_node]",
            "style": {
                "shape": "ellipse",
                "background-color": "#336699",
                "padding": "30px"
            }
        },
        {
            "selector": "[?is_start_vertex]",
            "style": {
                "border-color": "#d6c29b",
                "border-width": 3,
                "background-color": "#a84a07",
                "font-weight": "bold"
            }
        },
        {
            "selector": "[?is_start_vertex]:selected",
            "style": {
                "border-color": "#fbbf24",
                "border-width": 4
            }
        },
        {
            "selector": "[?has_missing_endpoint]",
            "style": {
                "border-color": "#ef4444",
                "border-width": 4,
                "background-color": "#7f1d1d"
            }
        },
        {
            "selector": "[?has_missing_endpoint]:selected",
            "style": {
                "border-color": "#fbbf24",
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
        html.H3("Selected Node"),
        html.Div(
            "None",
            id="selected-node-display",
            style={
                "padding": "8px",
                "marginBottom": "12px",
                "backgroundColor": "#111827",
                "border": "1px solid #4b5563",
                "borderRadius": "4px",
                "color": "#e5e7eb",
                "fontSize": "14px"
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
            id="dialogue-editor",
            layout={"name": "dagre", "rankDir": "TB"},
            clearOnUnhover=True,
            style={
                "width": "100%",
                "height": "100%",
                "backgroundColor": "#303841"
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
    button_style = {
        "padding": "8px 14px",
        "fontSize": "16px",
        "backgroundColor": "#374151",
        "color": "#e5e7eb",
        "border": "1px solid #4b5563",
        "borderRadius": "4px",
        "cursor": "pointer"
    }
    return html.Div(
        [
            html.Button(
                "New",
                id="new-graph",
                n_clicks=0,
                style=button_style
            ),
            html.Div(
                get_upload_graph(button_style),
                id="upload-graph-container",
                style={"display": "inline-block"}
            ),
            html.Button(
                "Save",
                id="download-graph",
                n_clicks=0,
                style=button_style
            ),
            html.Div(
                "Document: Untitled",
                id="current-document-label",
                style={
                    "fontSize": "16px",
                    "color": "#d1d5db",
                    "marginLeft": "8px"
                }
            ),
            html.Div(style={"flex": "1"}),
            html.Button(
                "Quit",
                id="quit-editor",
                n_clicks=0,
                style={
                    **button_style,
                    "backgroundColor": "#7f1d1d",
                    "border": "1px solid #c53030"
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
            "backgroundColor": "#1f252b",
            "borderBottom": "1px solid #444",
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
                        background-color: #1f252b;
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

def get_input_style() -> dict[str, str | int]:
    """Return consistent styling for text input fields.

    Returns:
        dict[str, str | int]: Inline style for inputs.
    """
    return {
        "width": "100%",
        "backgroundColor": "#ffffff",
        "color": "#111827",
        "caretColor": "#111827",
        "border": "1px solid #9ca3af",
        "fontSize": "14px",
        "padding": "6px 8px",
        "boxSizing": "border-box"
    }

def get_label_style() -> dict[str, str | int]:
    """Return consistent styling for form labels.

    Returns:
        dict[str, str | int]: Inline style for labels.
    """
    return {
        "fontWeight": "bold",
        "marginBottom": "4px",
        "marginTop": "12px",
        "color": "#e5e7eb",
        "fontSize": "14px"
    }

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
                "Dialogue Editor",
                style={
                    "marginTop": "0",
                    "marginBottom": "4px",
                    "color": "#e6e6e6",
                    "fontSize": "24px",
                    "fontWeight": "bold"
                }
            ),
            html.P(
                subtitle,
                style={
                    "marginTop": "0",
                    "marginBottom": "20px",
                    "color": "#9ca3af",
                    "fontSize": "12px"
                }
            ),
            html.Hr(style={"margin": "16px 0"}),
            *get_name_section(initial_name),
            html.Hr(style={"margin": "16px 0"}),
            *get_edit_section(),
            html.Hr(style={"margin": "16px 0"}),
            html.Button(
                "Add NPC Dialogue",
                id="open-add-vertex-modal",
                n_clicks=0,
                style={
                    "width": "100%",
                    "padding": "10px",
                    "marginBottom": "8px",
                    "backgroundColor": "#4b5563",
                    "color": "#e6e6e6",
                    "border": "1px solid #666",
                    "borderRadius": "4px",
                    "cursor": "pointer"
                }
            ),
            html.Div(
                html.Button(
                    "Add Player Dialogue",
                    id="open-add-edge-modal",
                    n_clicks=0,
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "marginBottom": "8px",
                        "backgroundColor": "#4b5563",
                        "color": "#e6e6e6",
                        "border": "1px solid #666",
                        "borderRadius": "4px",
                        "cursor": "pointer"
                    }
                ),
                id="open-add-edge-tooltip",
                title="",
                style={"display": "block"}
            ),
            html.Div(
                html.Button(
                    "Edit Selected Node",
                    id="open-edit-modal",
                    n_clicks=0,
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "marginBottom": "8px",
                        "backgroundColor": "#4b5563",
                        "color": "#e6e6e6",
                        "border": "1px solid #666",
                        "borderRadius": "4px",
                        "cursor": "pointer"
                    }
                ),
                id="open-edit-tooltip",
                title="",
                style={"display": "block"}
            ),
            html.Div(
                html.Button(
                    "Delete Selected Node",
                    id="open-delete-modal",
                    n_clicks=0,
                    style={
                        "width": "100%",
                        "padding": "10px",
                        "marginBottom": "8px",
                        "backgroundColor": "#7f1d1d",
                        "color": "#e6e6e6",
                        "border": "1px solid #c53030",
                        "borderRadius": "4px",
                        "cursor": "pointer"
                    }
                ),
                id="open-delete-tooltip",
                title="",
                style={"display": "block"}
            )
        ],
        style={
            "width": "320px",
            "flexShrink": 0,
            "boxSizing": "border-box",
            "padding": "12px",
            "paddingBottom": "24px",
            "backgroundColor": "1f252b",
            "color": "#e6e6e6",
            "borderRight": "1px solid #444",
            "overflowY": "auto",
            "height": "100vh"
        }
    )

def get_log() -> list:
    """Build the sidebar log section.

    Returns:
        list: Dash components that display action logs.
    """
    return [
        html.H3("Log"),
        dcc.Textarea(
            value="Ready.",
            id="action-status",
            readOnly=True,
            style={
                "width": "100%",
                "height": "70px",
                "marginTop": "12px",
                "fontSize": "14px",
                "backgroundColor": "#111827",
                "color": "#e5e7eb",
                "border": "1px solid #4b5563",
                "padding": "8px",
                "resize": "none",
                "overflowY": "auto",
                "whiteSpace": "pre-wrap"
            }
        ),
        html.Div(
            id="action-status-scroll-trigger", 
            style={"display": "none"}
        )
    ]

def get_name_section(initial_value: str = "Untitled") -> list:
    """Build the sidebar controls for editing NPC name.

    Args:
        initial_value (str): Initial text for the name input.

    Returns:
        list: Dash components for name editing controls.
    """
    return [
        html.H3("NPC Name"),
        dcc.Input(
            id="document-name",
            type="text",
            value=initial_value,
            placeholder="NPC name",
            style={
                "width": "100%",
                "marginBottom": "12px",
                "backgroundColor": "#ffffff",
                "color": "#111827",
                "caretColor": "#111827",
                "border": "1px solid #9ca3af",
                "fontSize": "14px",
                "opacity": 1
            }
        ),
        html.Button("Save", id="save-name", n_clicks=0)
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
            html.H3("Log", style={"marginTop": "0"}),
            dcc.Textarea(
                value="Ready.",
                id="action-status",
                readOnly=True,
                style={
                    "width": "100%",
                    "flex": "1",
                    "fontSize": "14px",
                    "backgroundColor": "#111827",
                    "color": "#e5e7eb",
                    "border": "1px solid #4b5563",
                    "padding": "8px",
                    "resize": "none",
                    "overflowY": "auto",
                    "whiteSpace": "pre-wrap",
                    "boxSizing": "border-box"
                }
            ),
            html.Div(
                id="action-status-scroll-trigger",
                style={"display": "none"}
            )
        ],
        style={
            "width": "320px",
            "flexShrink": 0,
            "boxSizing": "border-box",
            "padding": "12px",
            "paddingBottom": "24px",
            "backgroundColor": "#1f252b",
            "color": "#e6e6e6",
            "borderLeft": "1px solid #444",
            "display": "flex",
            "flexDirection": "column",
            "height": "100vh"
        }
    )

def get_textarea_style(height: str = "auto") -> dict[str, str | int]:
    """Return consistent styling for textarea fields.

    Args:
        height (str): Height of textarea (default "auto").

    Returns:
        dict[str, str | int]: Inline style for textareas.
    """
    return {
        "width": "100%",
        "height": height,
        "backgroundColor": "#ffffff",
        "color": "#111827",
        "caretColor": "#111827",
        "border": "1px solid #9ca3af",
        "fontSize": "14px",
        "padding": "6px 8px",
        "resize": "none",
        "overflowY": "auto",
        "boxSizing": "border-box"
    }

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
    resolved_button_style = button_style or {
        "padding": "8px 14px",
        "fontSize": "16px",
        "backgroundColor": "#374151",
        "color": "#e5e7eb",
        "border": "1px solid #4b5563",
        "borderRadius": "4px",
        "cursor": "pointer"
    }
    return dcc.Upload(
        id="upload-graph",
        children=html.Button(
            "Open",
            id="upload-graph-button",
            n_clicks=0,
            style=resolved_button_style
        ),
        multiple=False,
        style={"display": "inline-block"}
    )
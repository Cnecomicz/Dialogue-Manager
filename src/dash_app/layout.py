from dash import dcc, html
from dash_cytoscape import Cytoscape

def get_add_edge_modal() -> html.Div:
    """Build the complete Add Edge modal.

    Returns:
        html.Div: Modal overlay div for adding edges.
    """
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Add Player Dialogue", style={"color": "#e6e6e6"}),
                    html.Div(
                        get_add_edge_modal_content(),
                        style={"marginBottom": "16px"}
                    ),
                    html.Div(
                        [
                            html.Button(
                                "Save",
                                id="save-add-edge",
                                n_clicks=0,
                                style={
                                    "marginRight": "8px",
                                    "padding": "8px 16px",
                                    "backgroundColor": "#4b5563",
                                    "color": "#e6e6e6",
                                    "border": "1px solid #666",
                                    "borderRadius": "4px",
                                    "cursor": "pointer"
                                }
                            ),
                            html.Button(
                                "Cancel",
                                id="cancel-add-edge",
                                n_clicks=0,
                                style={
                                    "padding": "8px 16px",
                                    "backgroundColor": "#333",
                                    "color": "#e6e6e6",
                                    "border": "1px solid #555",
                                    "borderRadius": "4px",
                                    "cursor": "pointer"
                                }
                            )
                        ]
                    )
                ],
                style=get_modal_card_style()
            )
        ],
        id="add-edge-modal",
        style=get_modal_overlay_style(False)
    )

def get_add_edge_modal_content() -> list:
    """Build form content for adding a player edge (used in modal).

    Returns:
        list: Dash components for edge creation form.
    """
    return [
        html.Label("Dialogue", style=get_label_style()),
        dcc.Textarea(
            id="new-edge-text",
            placeholder="Dialogue",
            style=get_textarea_style()
        ),
        html.Label("Source NPC Node", style=get_label_style()),
        dcc.Input(
            id="new-edge-from",
            type="text",
            placeholder="Source NPC node",
            style=get_input_style()
        ),
        html.Label("Target NPC Node", style=get_label_style()),
        dcc.Input(
            id="new-edge-to",
            type="text",
            placeholder="Target NPC node",
            style=get_input_style()
        ),
        html.Label("Predicates", style=get_label_style()),
        dcc.Textarea(
            id="new-edge-predicates",
            placeholder="Predicates (one per line)",
            style=get_textarea_style("70px")
        ),
        html.Label("Effects", style=get_label_style()),
        dcc.Textarea(
            id="new-edge-effects",
            placeholder="Effects (one per line)",
            style=get_textarea_style("70px")
        )
    ]

# def get_add_edge_section() -> list:
#     """Build the sidebar controls for adding a player edge.

#     Returns:
#         list: Dash components for edge creation controls.
#     """
#     return [
#         html.H3("Add player node"),
#         *get_add_edge_modal_content(),
#         html.Button("Save", id="add-edge", n_clicks=0)
#     ]

def get_add_vertex_modal() -> html.Div:
    """ Build the complete Add Vertex modal.

    Returns:
        html.Div: Modal overlay div for adding vertices.
    """
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Add NPC Dialogue", style={"color": "#e6e6e6"}),
                    html.Div(
                        get_add_vertex_modal_content(),
                        style={"marginBottom": "16px"}
                    ),
                    html.Div(
                        [
                            html.Button(
                                "Save",
                                id="save-add-vertex",
                                n_clicks=0,
                                style={
                                    "marginRight": "8px",
                                    "padding": "8px 16px",
                                    "backgroundColor": "#4b5563",
                                    "color": "#e6e6e6",
                                    "border": "1px solid #666",
                                    "borderRadius": "4px",
                                    "cursor": "pointer"
                                }
                            ),
                            html.Button(
                                "Cancel",
                                id="cancel-add-vertex",
                                n_clicks=0,
                                style={
                                    "padding": "8px 16px",
                                    "backgroundColor": "#333",
                                    "color": "#e6e6e6",
                                    "border": "1px solid #555",
                                    "borderRadius": "4px",
                                    "cursor": "pointer"
                                }
                            )
                        ]
                    )
                ],
                style=get_modal_card_style()
            )
        ],
        id="add-vertex-modal",
        style=get_modal_overlay_style(False)
    )

def get_add_vertex_modal_content() -> list:
    """Build form content for adding an NPC vertex (used in modal).

    Returns:
        list: Dash components for vertex creation form.
    """
    return [
        html.Label("Dialogue", style=get_label_style()),
        dcc.Textarea(
            id="new-vertex-text",
            placeholder="Dialogue",
            style=get_textarea_style()
        ),
        html.Label("Effects", style=get_label_style()),
        dcc.Textarea(
            id="new-vertex-effects",
            placeholder="Effects (one per line)",
            style=get_textarea_style("70px")
        )
    ]

# def get_add_vertex_section() -> list:
#     """Build the sidebar controls for adding an NPC vertex.

#     Returns:
#         list: Dash components for vertex creation controls.
#     """
#     return [
#         html.H3("Add NPC node"),
#         dcc.Textarea(
#             id="new-vertex-text",
#             placeholder="NPC dialogue",
#             style={
#                 "width": "100%",
#                 "backgroundColor": "#ffffff",
#                 "color": "#111827",
#                 "caretColor": "#111827",
#                 "border": "1px solid #9ca3af",
#                 "fontSize": "14px",
#                 "opacity": 1
#             }
#         ),
#         dcc.Textarea(
#             id="new-vertex-effects",
#             placeholder="Effects (one per line)",
#             style={
#                 "width": "100%",
#                 "height": "70px",
#                 "marginTop": "12px",
#                 "marginBottom": "12px",
#                 "fontSize": "14px",
#                 "backgroundColor": "#ffffff",
#                 "color": "#111827",
#                 "border": "1px solid #9ca3af",
#                 "resize": "vertical"
#             }
#         ),
#         html.Button("Save", id="add-vertex", n_clicks=0)
#     ]

def get_center_panel(initial_elements: list) -> html.Div:
    """Build the center graph panel with Cytoscape visualization.

    Args:
        initial_elements (list): Initial Cytoscape graph elements.

    Returns:
        html.Div: Center panel component.
    """
    return html.Div(
        [
            get_header(),
            html.Div(
                Cytoscape(
                    id="dialogue-editor",
                    layout={"name": "dagre", "rankDir": "TB"},
                    style={
                        "width": "100%",
                        "height": "100%",
                        "backgroundColor": "#303841"
                    },
                    elements=initial_elements,
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

def get_delete_confirmation_modal_content() -> list:
    """Build content for delete confirmation modal.

    Returns: 
        list: Dash components for delete confirmation.
    """
    return [
        html.Div(
            "Are you sure you want to delete the selected node?",
            style={
                "marginBottom": "16px",
                "color": "#e6e6e6"
            }
        ),
        dcc.Checklist(
            id="delete-cascade",
            options=[
                {
                    "label": (
                        "Delete all connected player nodes? If you do not, "
                        "you may need to repair unresolved connections."
                    ), 
                    "value": "cascade"
                }
            ],
            value=[],
            labelStyle={"color": "#e5e7eb"},
            style={
                "marginBottom": "16px",
                "color": "#e5e7eb"
            }
        )
    ]

def get_delete_node_modal() -> html.Div:
    """Build the complete Delete Node modal.

    Returns:
        html.Div: Modal overlay div for deleting nodes.
    """
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Delete Node", style={"color": "#e6e6e6"}),
                    html.Div(
                        get_delete_confirmation_modal_content(),
                        style={"marginBottom": "16px"},
                        id="delete-modal-content-container"
                    ),
                    html.Div(
                        [
                            html.Button(
                                "Confirm Delete",
                                id="confirm-delete-node-modal",
                                n_clicks=0,
                                style={
                                    "marginRight": "8px",
                                    "padding": "8px 16px",
                                    "backgroundColor": "#7f1d1d",
                                    "color": "#e6e6e6",
                                    "border": "1px solid #c53030",
                                    "borderRadius": "4px",
                                    "cursor": "pointer"
                                }
                            ),
                            html.Button(
                                "Cancel",
                                id="cancel-delete-node-modal",
                                n_clicks=0,
                                style={
                                    "padding": "8px 16px",
                                    "backgroundColor": "#333",
                                    "color": "#e6e6e6",
                                    "border": "1px solid #555",
                                    "borderRadius": "4px",
                                    "cursor": "pointer"
                                }
                            )
                        ]
                    )
                ],
                style=get_modal_card_style()
            )
        ],
        id="delete-node-modal",
        style=get_modal_overlay_style(False)
    )

# def get_delete_section() -> list:
#     """Build the sidebar controls for deleting a selected node.

#     Returns:
#         list: Dash components for delete controls.
#     """
#     return [
#         html.H3("Delete selected node"),
#         html.Div(
#             "Selected node: None", 
#             id="delete-selected-node-display"
#         ),
#         html.Button("Delete", id="delete-node", n_clicks=0)
#     ]

def get_edit_node_modal() -> html.Div:
    """Build the complete Edit Node modal.

    Returns:
        html.Div: Modal overlay div for editing nodes.
    """
    return html.Div(
        [
            html.Div(
                [
                    html.H2("Edit Node", style={"color": "#e6e6e6"}),
                    html.Div(
                        get_edit_node_modal_content(),
                        style={"marginBottom": "16px"},
                        id="edit-modal-content-container"
                    ),
                    html.Div(
                        [
                            html.Button(
                                "Save",
                                id="save-edit-node",
                                n_clicks=0,
                                style={
                                    "marginRight": "8px",
                                    "padding": "8px 16px",
                                    "backgroundColor": "#4b5563",
                                    "color": "#e6e6e6",
                                    "border": "1px solid #666",
                                    "borderRadius": "4px",
                                    "cursor": "pointer"
                                }
                            ),
                            html.Button(
                                "Cancel",
                                id="cancel-edit-node",
                                n_clicks=0,
                                style={
                                    "padding": "8px 16px",
                                    "backgroundColor": "#333",
                                    "color": "#e6e6e6",
                                    "border": "1px solid #555",
                                    "borderRadius": "4px",
                                    "cursor": "pointer"
                                }
                            )
                        ]
                    )
                ],
                style=get_modal_card_style()
            )
        ],
        id="edit-node-modal",
        style=get_modal_overlay_style(False)
    )

def get_edit_node_modal_content() -> list:
    """Build form content for editing a node (used in modal).

    Returns:
        list: Dash components for node edit form.
    """
    return [
        html.Label("Dialogue", style=get_label_style()),
        dcc.Textarea(
            id="edit-text",
            placeholder="Dialogue",
            style=get_textarea_style()
        ),
        html.Div(
            [
                html.Label("Source NPC Node", style=get_label_style()),
                dcc.Input(
                    id="edit-from-vertex",
                    type="text",
                    placeholder="Source NPC node",
                    style=get_input_style()
                )
            ],
            id="edit-from-vertex-container"
        ),
        html.Div(
            [
                html.Label("Target NPC Node", style=get_label_style()),
                dcc.Input(
                    id="edit-to-vertex",
                    type="text",
                    placeholder="Target NPC node",
                    style=get_input_style()
                ),
            ],
            id="edit-to-vertex-container"
        ),
        html.Div(
            [
                html.Label("Predicates", style=get_label_style()),
                dcc.Textarea(
                    id="edit-predicates",
                    placeholder="Predicates (one per line)",
                    style=get_textarea_style("70px")
                ),
            ],
            id="edit-predicates-container"
        ),
        html.Label("Effects", style=get_label_style()),
        dcc.Textarea(
            id="edit-effects",
            placeholder="Effects (one per line)",
            style=get_textarea_style("70px")
        )
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

def get_header() -> html.Div:
    """Build the top toolbar for graph-level actions.

    Returns:
        html.Div: Header component with new/open/save controls.
    """
    return html.Div(
        [
            html.Button(
                "New",
                id="new-graph",
                n_clicks=0
            ),
            html.Div(
                get_upload_graph(),
                id="upload-graph-container",
                style={"display": "inline-block"}
            ),
            html.Button(
                "Save",
                id="download-graph",
                n_clicks=0
            ),
            html.Div(
                "Document: Untitled",
                id="current-document-label",
                style={
                    "fontSize": "14px",
                    "color": "#d1d5db",
                    "marginLeft": "8px"
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
            "flexShrink": 0
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

def get_modal_card_style() -> dict[str, str | int]:
    """Return shared card styling for modal-like dialogs.

    Returns:
        dict[str, str | int]: Inline style for modal cards.
    """
    return {
        "width": "min(520px, 100%)",
        "maxHeight": "calc(100vh - 48px)",
        "overflowY": "auto",
        "padding": "16px",
        "backgroundColor": "#252d35",
        "border": "1px solid #444",
        "borderRadius": "8px",
        "boxShadow": "0 12px 32px rgba(0, 0, 0, 0.35)"
    }

def get_modal_overlay_style(is_open: bool) -> dict[str, str | int]:
    """Return the overlay style for modal-like dialogs.

    Args:
        is_open (bool): Whether the overlay should be visible.

    Returns:
        dict[str, str | int]: Dash inline style mapping.
    """
    return {
        "position": "fixed",
        "inset": 0,
        "display": "flex" if is_open else "none",
        "alignItems": "center",
        "justifyContent": "center",
        "backgroundColor": "rgba(15, 23, 42, 0.55)",
        "zIndex": 1000,
        "padding": "24px",
        "boxSizing": "border-box"
    }

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
        "resize": "vertical",
        "boxSizing": "border-box"
    }

def get_upload_graph() -> dcc.Upload:
    """Build the upload control used to load graph yaml files.

    Returns:
        dcc.Upload: Dash upload component for yaml files.
    """
    return dcc.Upload(
        id="upload-graph",
        children=html.Button(
            "Open",
            id="upload-graph-button",
            n_clicks=0
        ),
        multiple=False,
        style={"display": "inline-block"}
    )
from dash import dcc, html

def get_add_edge_section() -> list:
    """Build the sidebar controls for adding a player edge.

    Returns:
        list: Dash components for edge creation controls.
    """
    return [
        html.H3("Add player node"),
        dcc.Input(
            id="new-edge-from",
            type="text",
            placeholder="Prior NPC node (required)",
            style={
                "width": "100%",
                "backgroundColor": "#ffffff",
                "color": "#111827",
                "caretColor": "#111827",
                "border": "1px solid #9ca3af",
                "fontSize": "14px",
                "opacity": 1
            }
        ),
        dcc.Input(
            id="new-edge-to",
            type="text",
            placeholder="Next NPC node",
            style={
                "width": "100%",
                "marginTop": "12px",
                "backgroundColor": "#ffffff",
                "color": "#111827",
                "caretColor": "#111827",
                "border": "1px solid #9ca3af",
                "fontSize": "14px",
                "opacity": 1
            }
        ),
        dcc.Textarea(
            id="new-edge-text",
            placeholder="Player dialogue",
            style={
                "width": "100%",
                "marginTop": "12px",
                "backgroundColor": "#ffffff",
                "color": "#111827",
                "caretColor": "#111827",
                "border": "1px solid #9ca3af",
                "fontSize": "14px",
                "opacity": 1
            }
        ),
        dcc.Textarea(
            id="new-edge-predicates",
            placeholder="Predicates (one per line)",
            style={
                "width": "100%",
                "height": "70px",
                "marginTop": "12px",
                "fontSize": "14px",
                "backgroundColor": "#ffffff",
                "color": "#111827",
                "border": "1px solid #9ca3af",
                "resize": "vertical"
            }
        ),
        dcc.Textarea(
            id="new-edge-effects",
            placeholder="Effects (one per line)",
            style={
                "width": "100%",
                "height": "70px",
                "marginTop": "12px",
                "marginBottom": "12px",
                "fontSize": "14px",
                "backgroundColor": "#ffffff",
                "color": "#111827",
                "border": "1px solid #9ca3af",
                "resize": "vertical"
            }
        ),
        html.Button("Save", id="add-edge", n_clicks=0)
    ]

def get_add_vertex_section() -> list:
    """Build the sidebar controls for adding an NPC vertex.

    Returns:
        list: Dash components for vertex creation controls.
    """
    return [
        html.H3("Add NPC node"),
        dcc.Textarea(
            id="new-vertex-text",
            placeholder="NPC dialogue",
            style={
                "width": "100%",
                "backgroundColor": "#ffffff",
                "color": "#111827",
                "caretColor": "#111827",
                "border": "1px solid #9ca3af",
                "fontSize": "14px",
                "opacity": 1
            }
        ),
        dcc.Textarea(
            id="new-vertex-effects",
            placeholder="Effects (one per line)",
            style={
                "width": "100%",
                "height": "70px",
                "marginTop": "12px",
                "marginBottom": "12px",
                "fontSize": "14px",
                "backgroundColor": "#ffffff",
                "color": "#111827",
                "border": "1px solid #9ca3af",
                "resize": "vertical"
            }
        ),
        html.Button("Save", id="add-vertex", n_clicks=0)
    ]

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

def get_delete_section() -> list:
    """Build the sidebar controls for deleting a selected node.

    Returns:
        list: Dash components for delete controls.
    """
    return [
        html.H3("Delete selected node"),
        html.Div(
            "Selected node: None", 
            id="delete-selected-node-display"
        ),
        dcc.Checklist(
            id="delete-cascade",
            options=[{"label": "Cascade delete", "value": "cascade"}],
            value=[],
            labelStyle={"color": "#e5e7eb"},
            style={
                "marginTop": "12px",
                "marginBottom": "12px",
                "color": "#e5e7eb"
            }
        ),
        html.Button("Delete", id="delete-node", n_clicks=0),
        dcc.ConfirmDialog(
            id="confirm-delete-node",
            message="Are you sure you want to delete the selected node?"
        )
    ]

def get_edit_section() -> list:
    """Build the sidebar controls for editing a selected node.

    Returns:
        list: Dash components for edit controls.
    """
    return [
        html.H3("Edit selected node"),
        html.Div(
            "Selected node: None",
            id="selected-node-display"
        ),
        dcc.Textarea(
            id="edit-text",
            placeholder="Edit dialogue",
            style={
                "width": "100%",
                "backgroundColor": "#ffffff",
                "color": "#111827",
                "caretColor": "#111827",
                "border": "1px solid #9ca3af",
                "fontSize": "14px",
                "opacity": 1
            }
        ),
        dcc.Textarea(
            id="edit-predicates",
            placeholder="Edit predicates (one per line)",
            style={
                "width": "100%",
                "height": "70px",
                "marginTop": "12px",
                "fontSize": "14px",
                "backgroundColor": "#ffffff",
                "color": "#111827",
                "border": "1px solid #9ca3af",
                "resize": "vertical"
            }
        ),
        dcc.Textarea(
            id="edit-effects",
            placeholder="Edit effects (one per line)",
            style={
                "width": "100%",
                "height": "70px",
                "marginTop": "12px",
                "fontSize": "14px",
                "backgroundColor": "#ffffff",
                "color": "#111827",
                "border": "1px solid #9ca3af",
                "resize": "vertical"
            }
        ),
        dcc.Input(
            id="edit-from-vertex",
            type="text",
            placeholder="Edit from vertex",
            style={
                "width": "100%",
                "marginTop": "12px",
                "backgroundColor": "#ffffff",
                "color": "#111827",
                "caretColor": "#111827",
                "border": "1px solid #9ca3af",
                "fontSize": "14px",
                "opacity": 1
            }
        ),
        dcc.Input(
            id="edit-to-vertex",
            type="text",
            placeholder="Edit to vertex",
            style={
                "width": "100%",
                "marginTop": "12px",
                "marginBottom": "12px",
                "backgroundColor": "#ffffff",
                "color": "#111827",
                "caretColor": "#111827",
                "border": "1px solid #9ca3af",
                "fontSize": "14px",
                "opacity": 1
            }
        ),
        html.Button("Save", id="save-text", n_clicks=0)
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
        html.H3("NPC name"),
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
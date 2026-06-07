from dash import dcc, html

def get_add_edge_button() -> list:
    return [
        html.H3("Add edge"),
        dcc.Input(
            id="new-edge-from",
            type="text",
            placeholder="From vertex (required)",
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
            placeholder="To vertex",
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
            id="new-edge-text",
            type="text",
            placeholder="Edge text",
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
            placeholder="Predicates (optional, one per line)",
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
            placeholder="Effects (optional, one per line)",
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
        html.Button("Add edge", id="add-edge", n_clicks=0)
    ]

def get_add_vertex_button() -> list:
    return [
        html.H3("Add vertex"),
        dcc.Input(
            id="new-vertex-text",
            type="text",
            placeholder="Vertex text",
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
            placeholder="Effects (optional, one per line)",
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
        html.Button("Add vertex", id="add-vertex", n_clicks=0)
    ]

def get_cytoscape_stylesheet() -> list[dict[str, str | dict[str, str | int]]]:
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
        }
    ]

def get_edit_button() -> list:
    return [
        html.H3("Edit selected node"),
        html.Div(
            "Selected node: None",
            id="selected-node-display"
        ),
        dcc.Input(
            id="edit-text",
            type="text",
            placeholder="Enter new text for selected node",
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
            placeholder="Enter predicates, one per line",
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
            placeholder="Enter effects, one per line",
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
        html.Button("Save", id="save-text", n_clicks=0)
    ]

def get_log() -> list:
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
from enum import StrEnum

class ElementId(StrEnum):
    """Enumerate the DOM identifiers for Dash components and state stores.

    Centralizing these identifiers keeps every callback wiring
    (Output/Input/State), layout id assignment, and ctx.triggered_id comparison
    referring to a single source of truth, which prevents drift between
    the layout and the callbacks. Because StrEnum members are plain strings,
    each member is interchangeable with its literal id across the Dash
    component tree, the callback graph, and the dcc.Store json boundary.

    Note:
        The JavaScript clientside_callback blobs reference these same ids
        as inline string literals; those literals are intentionally left
        in place because they live inside opaque JavaScript source strings.
    """

    ACTION_LOG = "action-log"
    ACTION_LOG_DISPLAY = "action-log-display"
    BOTTOM_FORM_CASCADE = "bottom-form-cascade"
    BOTTOM_FORM_CASCADE_CONTAINER = "bottom-form-cascade-container"
    BOTTOM_FORM_DELETE_MESSAGE_CONTAINER = "bottom-form-delete-message-container"
    BOTTOM_FORM_DIALOGUE = "bottom-form-dialogue"
    BOTTOM_FORM_DIALOGUE_CONTAINER = "bottom-form-dialogue-container"
    BOTTOM_FORM_EFFECTS = "bottom-form-effects"
    BOTTOM_FORM_EFFECTS_CONTAINER = "bottom-form-effects-container"
    BOTTOM_FORM_PICK_SOURCE = "bottom-form-pick-source"
    BOTTOM_FORM_PICK_TARGET = "bottom-form-pick-target"
    BOTTOM_FORM_PREDICATES = "bottom-form-predicates"
    BOTTOM_FORM_PREDICATES_CONTAINER = "bottom-form-predicates-container"
    BOTTOM_FORM_SOURCE = "bottom-form-source"
    BOTTOM_FORM_SOURCE_CONTAINER = "bottom-form-source-container"
    BOTTOM_FORM_TARGET = "bottom-form-target"
    BOTTOM_FORM_TARGET_CONTAINER = "bottom-form-target-container"
    BOTTOM_PANEL = "bottom-panel"
    BOTTOM_PANEL_CLOSE = "bottom-panel-close"
    BOTTOM_PANEL_FORM_TYPE = "bottom-panel-form-type"
    BOTTOM_PANEL_SAVE = "bottom-panel-save"
    BOTTOM_PANEL_TITLE = "bottom-panel-title"
    BOTTOM_PANEL_VISIBLE = "bottom-panel-visible"
    CONFIRM_UNSAVED_WORK = "confirm-unsaved-work"
    CURRENT_DOCUMENT = "current-document"
    CURRENT_DOCUMENT_LABEL = "current-document-label"
    DIALOGUE_EDITOR = "dialogue-editor"
    DOCUMENT_NAME = "document-name"
    DOWNLOAD_GRAPH = "download-graph"
    DOWNLOAD_YAML = "download-yaml"
    GRAPH_CONTAINER = "graph-container"
    NEW_GRAPH = "new-graph"
    OPEN_ADD_EDGE_MODAL = "open-add-edge-modal"
    OPEN_ADD_EDGE_TOOLTIP = "open-add-edge-tooltip"
    OPEN_ADD_VERTEX_MODAL = "open-add-vertex-modal"
    OPEN_DELETE_MODAL = "open-delete-modal"
    OPEN_DELETE_TOOLTIP = "open-delete-tooltip"
    OPEN_EDIT_MODAL = "open-edit-modal"
    OPEN_EDIT_TOOLTIP = "open-edit-tooltip"
    OPEN_SHORTCUTS_HELP = "open-shortcuts-help"
    PENDING_ACTION = "pending-action"
    PENDING_UPLOAD = "pending-upload"
    PICK_MODE_ACTIVE = "pick-mode-active"
    PICK_MODE_FIELD = "pick-mode-field"
    QUIT_CLIENT_TRIGGER = "quit-client-trigger"
    QUIT_EDITOR = "quit-editor"
    QUIT_SIGNAL = "quit-signal"
    SAVE_NAME = "save-name"
    SELECTED_NODE_DISPLAY = "selected-node-display"
    SELECTED_NODE_ID = "selected-node-id"
    SHORTCUT_LISTENER_DUMMY = "shortcut-listener-dummy"
    SHORTCUTS_HELP_CLOSE = "shortcuts-help-close"
    SHORTCUTS_HELP_VISIBLE = "shortcuts-help-visible"
    SHORTCUTS_OVERLAY = "shortcuts-overlay"
    UNSAVED_CHANGES = "unsaved-changes"
    UPLOAD_GRAPH = "upload-graph"
    UPLOAD_GRAPH_BUTTON = "upload-graph-button"
    UPLOAD_GRAPH_CONTAINER = "upload-graph-container"
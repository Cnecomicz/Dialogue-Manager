from dialogue_editor.messages import FIELD_SOURCE, FIELD_TARGET

BUTTON_CANCEL = "Cancel"
BUTTON_CLOSE = "Close"
BUTTON_CONFIRM = "Confirm"
BUTTON_CONFIRM_DELETE = "Confirm Delete"
BUTTON_NEW = "New"
BUTTON_OPEN = "Open"
BUTTON_QUIT = "Quit"
BUTTON_REDO = "Redo"
BUTTON_SAVE = "Save"
BUTTON_SELECT_FROM_GRAPH = "Select From Graph"
BUTTON_SHORTCUTS = "Shortcuts"
BUTTON_UNDO = "Undo"
CONFIRM_DELETE_NODE_QUESTION = (
    "Are you sure you want to delete the selected node?"
)
CONFIRM_QUIT = "Are you sure you want to quit?"
CONFIRM_UNSAVED_CONTINUE = (
    "You have unsaved changes. Are you sure you want to continue?"
)
CONFIRM_UNSAVED_NEW = (
    "You have unsaved changes. Are you sure you want to start a new graph?"
)
CONFIRM_UNSAVED_QUIT = (
    "You have unsaved changes. Are you sure you want to quit?"
)
CONFIRM_UNSAVED_UPLOAD = (
    "You have unsaved changes. Are you sure you want to open a file and "
    "replace the current graph?"
)
DEFAULT_DOCUMENT_NAME = "Untitled"
DEFAULT_NODE_DISPLAY = "None"
DIRTY_MARKER = " *"
ERROR_ADD_NPC_INVALID_FIELD = (
    "Could not create an NPC node because {reason}. Fix the Effects field "
    "and try again."
)
ERROR_ADD_PLAYER_ENDPOINT = (
    "Could not create a Player node because {endpoint} must be an existing "
    "NPC node ID. Enter a valid NPC node ID in {endpoint} and try again."
)
ERROR_ADD_PLAYER_INVALID_FIELD = (
    "Could not create a Player node because {reason}. Fix Predicates/Effects "
    "and save again."
)
ERROR_ADD_PLAYER_INVALID_SOURCE = (
    "Could not create a Player node from this selection because the "
    f"{FIELD_SOURCE} must be an NPC node."
)
ERROR_ADD_PLAYER_SOURCE_REQUIRED = (
    f"Could not create a Player node because {FIELD_SOURCE} is required. "
    f"Enter an NPC node ID in {FIELD_SOURCE} and try again."
)
ERROR_DELETE_MISSING_NODE = (
    "Could not delete {node_id} because it no longer exists. Select a current "
    "node and try again."
)
ERROR_DELETE_START_VERTEX = (
    "Could not delete NPC node {node_id} because the starting NPC node cannot "
    "be deleted."
)
ERROR_INVALID_EFFECT = "Invalid effect on line {line_number}: {line}"
ERROR_INVALID_PREDICATE = "Invalid predicate on line {line_number}: {line}"
ERROR_SAVE_INVALID_FIELD = (
    "Could not save changes for {node_type} {node_id} because {reason}. "
    "Fix the invalid field and try again."
)
ERROR_SAVE_MISSING_NODE = (
    "Could not save changes for {node_type} {node_id} because it no longer "
    "exists. Select a current node and try again."
)
ERROR_UPDATE_ENDPOINT_EMPTY = (
    "Could not update {field} for Player node {node_id} because {field} "
    "cannot be empty. Enter an existing NPC node ID in {field} and try "
    "again."
)
ERROR_UPDATE_ENDPOINT_MISSING = (
    "Could not update {field} for Player node {node_id} because NPC node "
    "{vertex_name} does not exist. Enter an existing NPC node ID in {field} "
    "and try again."
)
ERROR_UPLOAD_INVALID_DATA = (
    "Could not open the file because the upload data is invalid. Select "
    "a different file and try again."
)
ERROR_UPLOAD_INVALID_YAML = (
    "Could not open the file because the yaml format is invalid. Select "
    "a different file and try again."
)
ERROR_UPLOAD_NO_DATA = (
    "Could not open the file because no file data was received. Select the "
    "file and try again."
)
ERROR_UPLOAD_NO_PENDING = (
    "Could not open the file because no pending file data was found. Select "
    "a different file and try again."
)
ERROR_UPLOAD_NOT_DICT = (
    "Could not open the file because the top level must be a dictionary. "
    "Select a different file with yaml keys name, vertices, and edges."
)
ERROR_UPLOAD_NOT_UTF8 = (
    "Could not open the file because it is not UTF-8 text. Select a different "
    "file and try again."
)
FIELD_SOURCE_OR_TARGET = f"{FIELD_SOURCE}/{FIELD_TARGET}"
HEADER_LOG = "Log"
HEADER_NPC_NAME = "NPC Name"
HEADER_SELECTED_NODE = "Selected Node"
LABEL_CASCADE_DELETE = "Cascade delete"
LABEL_CASCADE_OPTION = (
    "Delete all connected player nodes? If you do not, you may need to "
    "repair unresolved connections."
)
LABEL_DIALOGUE = "Dialogue"
LABEL_DOCUMENT = "Document: {name}"
LABEL_EFFECTS = "Effects"
LABEL_PREDICATES = "Predicates"
LABEL_SELECTED_NODE = "Selected node: {node_id}"
LABEL_SOURCE_NPC = f"{FIELD_SOURCE} NPC Node"
LABEL_TARGET_NPC = f"{FIELD_TARGET} NPC Node"
LOG_CHANGE = "{field} changed from {old_value} to {new_value}"
LOG_CREATE = "Created {node_type} {node_value}"
LOG_DELETE = "Deleted {node_type} {node_value}"
LOG_FIELD_SEPARATOR = "; "
LOG_FIELDS_PREFIX = " with "
LOG_UPDATE = "Updated {node_type} {node_value}"
MENU_DELETE_NODE = "Delete Selected Node"
MENU_EDIT_NODE = "Edit Selected Node"
NODE_TYPE_NODE = "Node"
NODE_TYPE_NPC = "NPC node"
NODE_TYPE_PLAYER = "Player node"
PLACEHOLDER_EFFECTS = "Effects (one per line)"
PLACEHOLDER_NPC_NAME = "NPC name"
PLACEHOLDER_PREDICATES = "Predicates (one per line)"
PLACEHOLDER_SOURCE_NPC = f"{FIELD_SOURCE} NPC node"
PLACEHOLDER_TARGET_NPC = f"{FIELD_TARGET} NPC node"
SHORTCUTS_HELP = [
    ("New graph", "Ctrl+N"),
    ("Open a graph", "Ctrl+O"),
    ("Save a copy", "Ctrl+S"),
    ("Undo", "Ctrl+Z"),
    ("Redo", "Ctrl+Y / Ctrl+Shift+Z"),
    ("Quit the editor", "Ctrl+Q"),
    ("Add NPC dialogue", "N"),
    ("Add Player dialogue", "P"),
    ("Edit selected node", "E"),
    ("Delete selected node", "Delete / Backspace"),
    ("Navigate between nodes", "\u2190 \u2191 \u2192 \u2193"),
    ("Confirm selection or save an open form", "Ctrl+Enter"),
    ("Cancel, close panel, or exit node picking", "Esc"),
    ("Show this help", "?")
]
SHORTCUTS_HELP_FOOTER = (
    "Shortcuts work while the graph is in focus and you are not typing in "
    "a text field. Shortcuts are not guaranteed to work on all devices."
)
STATUS_DISCARD_NEW = (
    "Discarded unsaved changes and started a new dialogue graph."
)
STATUS_DISCARD_OPENED = "Discarded unsaved changes and opened {filename}."
STATUS_DISCARD_QUIT = "Discarded unsaved changes and quit the dialogue editor."
STATUS_NEW_GRAPH = "Started a new dialogue graph."
STATUS_NO_CHANGES = "No changes were made to {node_type} {node_id}."
STATUS_NOTHING_TO_REDO = "Nothing to redo."
STATUS_NOTHING_TO_UNDO = "Nothing to undo."
STATUS_OPENED = "Opened {filename}."
STATUS_PICK_MODE = (
    "Pick mode: {field_label} must be an NPC node. Click an NPC node to "
    "select it."
)
STATUS_QUIT = "Quit the dialogue editor."
STATUS_READY = "Ready."
STATUS_REDO = "Redid: {action}"
STATUS_SAVED_COPY = "Saved a copy as {filename}."
STATUS_SAVED_NAME = "Saved NPC name as {name}."
STATUS_UNDO = "Undid: {action}"
STATUS_UNRESOLVED_CONNECTIONS = (
    "{delete_message}. {count} unresolved connections were left behind. "
    f"Open each affected Player node and set {FIELD_SOURCE_OR_TARGET} to "
    "a valid NPC node."
)
TITLE_ADD_NPC = "Add NPC Dialogue"
TITLE_ADD_PLAYER = "Add Player Dialogue"
TITLE_DELETE_NODE = "Delete Node"
TITLE_DIALOGUE_EDITOR = "Dialogue Editor"
TITLE_EDIT_NODE = "Edit Node"
TITLE_FORM = "Form"
TITLE_KEYBOARD_SHORTCUTS = "Keyboard Shortcuts"
TOOLTIP_ADD_NPC_BUTTON = "Create a new NPC dialogue node (N)"
TOOLTIP_ADD_PLAYER_ENABLED = "Create a player choice linking two NPC nodes (P)"
TOOLTIP_ADD_PLAYER_NO_NPC = "Create at least one NPC node first."
TOOLTIP_DELETE_DISABLED = "Select a node to delete."
TOOLTIP_DELETE_ENABLED = (
    "Remove the selected node from the graph (Delete / Backspace)"
)
TOOLTIP_EDIT_DISABLED = "Select a node to edit."
TOOLTIP_EDIT_ENABLED = (
    "Edit the selected node's text, effects, and predicates (E)"
)
TOOLTIP_MENU_ADD_NPC = "Add a new NPC node"
TOOLTIP_MENU_ADD_PLAYER = "Add a new Player node"
TOOLTIP_MENU_ADD_PLAYER_FROM_NPC = "Create a Player node from this NPC node"
TOOLTIP_MENU_CANCEL = "Close menu"
TOOLTIP_MENU_DELETE = "Open delete confirmation"
TOOLTIP_MENU_EDIT = "Open edit form"
TOOLTIP_NEW = "Start a new empty graph (Ctrl+N)"
TOOLTIP_OPEN = "Open a graph from a yaml file (Ctrl+O)"
TOOLTIP_QUIT = "Close the editor (Ctrl+Q)"
TOOLTIP_REDO = "Redo the last undone change (Ctrl+Y / Ctrl+Shift+Z)"
TOOLTIP_SAVE_COPY = "Download a copy of this graph as yaml (Ctrl+S)"
TOOLTIP_SHORTCUTS = "Show all keyboard shortcuts (?)"
TOOLTIP_UNDO = "Undo the last change (Ctrl+Z)"
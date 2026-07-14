from enum import StrEnum

class CascadeValue(StrEnum):
    """Enumerate the cascade-delete checklist values."""

    CASCADE = "cascade"

class FormType(StrEnum):
    """Enumerate the bottom-panel form types."""

    ADD_EDGE = "add-edge"
    ADD_VERTEX = "add-vertex"
    DELETE = "delete"
    EDIT_EDGE = "edit-edge"
    EDIT_VERTEX = "edit-vertex"

class MenuItemId(StrEnum):
    """Enumerate the right click context menu item identifiers."""

    ADD_NPC = "add-npc"
    ADD_PLAYER = "add-player"
    ADD_PLAYER_DIALOGUE = "add-player-dialogue"
    CANCEL = "cancel"
    DELETE_NODE = "delete-node"
    EDIT_NODE = "edit-node"

class PendingAction(StrEnum):
    """Enumerate the deferred actions awaiting unsaved work confirmation."""

    NEW = "new"
    QUIT = "quit"
    UPLOAD = "upload"

class PickField(StrEnum):
    """Enumerate the pick mode endpoint fields."""

    SOURCE = "source"
    TARGET = "target"
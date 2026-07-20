from typing import Any, Protocol, runtime_checkable

from dialogue_navigator.messages import MSG_UNRESOLVED_PATH

class GameStatePathError(Exception):
    """Raised when a dotted game state path cannot be resolved.

    Attributes:
        path (str): The full path that failed to resolve.
        missing_attr (str): The path segment that could not be resolved.
    """

    def __init__(self, path: str, missing_attr: str, root: object) -> None:
        """Initialize the error with the failing path and context.

        Args:
            path (str): Full dotted path being resolved.
            missing_atr (str): Segment that failed.
            root (object): Root game state object the path was resolved
                against.
        """
        self.path = path
        self.missing_attr = missing_attr
        super().__init__(
            MSG_UNRESOLVED_PATH.format(
                path=path,
                missing_attr=missing_attr,
                root_type=type(root).__name__
            )
        )

@runtime_checkable
class StateAccessor(Protocol):
    """Read/write game state values addressed by paths.

    This is the port the navigator depends on. Supply the default
    AttributeStateAccessor for plain attribute based state, or implement
    this protocol to adapt any other storage (dictionaries, an entity component
    system, etc).

    Implementations must raise GameStatePathError when a path cannot be
    resolved.
    """

    def get(self, path: str) -> Any:
        """Resolve and return the value at a path.

        Args:
            path (str): Path to get value at.

        Returns:
            Any: Resolved value.

        Raises:
            GameStatePathError: If the path cannot be resolved.
        """
        ...

    def set(self, path: str, value: Any) -> None:
        """Assign a value at a path.

        Args:
            path (str): Path to set value to.
            value (Any): Value to assign.

        Raises:
            GameStatePathError: If the path cannot be resolved.
        """
        ...

class AttributeStateAccessor:
    """Default accessor that reads/writes path as object attributes.

    Attributes:
        root (object): Root game state object paths are resolved against.
    """

    def __init__(self, root: object) -> None:
        """Initialize the accessor with a root game state object.

        Args:
            root (object): Object whose attribute tree matches the paths
                used by the graph's predicates and effects.
        """
        self.root = root

    def __repr__(self) -> str:
        """Return a debug representation of this accessor.

        Returns:
            str: String representation of this accessor.
        """
        return f"<AttributeStateAccessor root={type(self.root).__name__}>"

    def get(self, path: str) -> Any:
        """Resolve an attribute path from the root object.

        Args:
            path (str): Path to get value at.

        Returns:
            Any: Resolved nested attribute value.

        Raises:
            GameStatePathError: If any segment of the path is missing.
        """
        obj = self.root
        for attr in path.split("."):
            try:
                obj = getattr(obj, attr)
            except AttributeError as error:
                raise GameStatePathError(path, attr, self.root) from error
        return obj

    def set(self, path: str, value: Any) -> None:
        """Set an attribute path on the root object.

        Args:
            path (str): Path to set value to.
            value (Any): Value to assign.

        Raises:
            GameStatePathError: If any parent segment of the path is missing.
        """
        attrs = path.split(".")
        obj = self.root
        for attr in attrs[:-1]:
            try:
                obj = getattr(obj, attr)
            except AttributeError as error:
                raise GameStatePathError(path, attr, self. root) from error
        setattr(obj, attrs[-1], value)
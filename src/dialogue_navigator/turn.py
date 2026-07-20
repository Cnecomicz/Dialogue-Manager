from dataclasses import dataclass

@dataclass(frozen=True)
class Option:
    """Represent a single selectable player choice for the current turn.

    Attributes:
        edge (str): Edge identifier to pass to GraphNavigator.select() or
            GraphNavigator.respond_with().
        text (str): Player choice text, with placeholders already evaluated.
    """

    edge: str
    text: str

@dataclass(frozen=True)
class Turn:
    """Represent one dialogue turn as presented to the game engine.

    Attributes:
        vertex (str): Current vertex identifier.
        text (str): NPC line for the current vertex, with placeholders already
            evaluated.
        options (list[Option]): Currently selectable player choices in
            declaration order.
        is_over (bool): True when no options remain.
    """

    vertex: str
    text: str
    options: list[Option]
    is_over: bool
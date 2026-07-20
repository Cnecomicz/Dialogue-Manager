# Dialogue Manager

A Python toolkit for building, editing, navigating, and visualizing branching
dialogue graphs for video games. This is intended to support my current
game development but has been built standalone in order to contain its scope 
and to allow anyone willing to use my conventions to adopt it for their 
own purposes.

It includes:

* A dialogue model which standardizes dialogue graphs, tracking the text,
    predicates, and effects per each vertex or edge, and saves/loads into
    yaml.
* A runtime graph navigator API that traverses dialogue graphs, getting
    NPC and player text, getting player options filtered by game state 
    predicates, and setting game state effects upon node entry.
* A Dash + Cytoscape visual editor with underlying editor API for creating
    and mutating graphs. 
* A Graphviz renderer for static svg output.

## Features

* Load/save dialogue graphs as yaml
* Represent NPC lines as vertices and player choices as edges
* Attach effects (game state consequences of dialogue choices) to vertices 
    and edges
* Attach predicates (game state conditions upon which an option is available) 
    to edges 
* Parse plain text predicate/effect expressions to and from structured data
* Navigate a graph at runtime, providing NPC lines and available player 
    choices while handling predicates, effects, and game state dependent
    variable text
* Visualize and edit graphs interactively in the browser
* Render graphs to svg for docs and design review

## Installation

This project requires Python 3.11 or newer.

Using the static svg render requires [Graphviz](https://graphviz.org) installed 
on your system.

After downloading this project off of 
[https://github.com/Cnecomicz/dialogue](https://github.com/Cnecomicz/dialogue), 
install it in the terminal using pip:

```
pip install -e .
```

This project depends on the preexisting python packages dash, dash-cytoscape, 
graphviz, and PyYAML.

You can also install this project with additional development tools:

```
pip install -e ".[dev]"
```

The additional dev dependencies are pytest, pytest-cov, pytest-testmon, 
and pytest-xdist, and are used for running the pytest suite.

## Quick start

### Dialogue editor

Launch the visual dialogue editor with `dialogue-editor`. This starts a 
local Dash app and opens http://localhost:8050. 

#### Shortcuts

Keyboard shortcuts can be performed in the dialogue editor when the graph
UI is in focus (i.e., not during text field editing).

Shortcuts are designed to work on Safari in macOS. Other browers/platforms
may experience a collision with built in browser/system level shortcuts.

| Shortcut | Action |
| --- | --- |
| `Ctrl+N` | Start a new empty graph |
| `Ctrl+O` | Open a graph |
| `Ctrl+S` | Save a copy of the graph |
| `Ctrl+Z` | Undo the last change |
| `Ctrl+Y / Ctrl+Shift+Z` | Redo the last undone change |
| `Ctrl+Q` | Quit the editor |
| `N` | Add an NPC dialogue node |
| `P` | Add a Player dialogue node |
| `E` | Edit the selected node |
| `Delete` / `Backspace` | Delete the selected node |
| `Arrow keys` | Move the selection to the next node |
| `Ctrl+Enter` | Confirm selection or save an open form |
| `Esc` | Cancel |
| `?` | Show the keyboard shortcut help overlay |

Shortcuts can be viewed in the UI by pressing `?` or by hovering over any
button.

### Dialogue renderer

Render a dialogue graph to svg with `dialogue-render <path>`, for example
`dialogue-render data/alice_dialogue_graph.yaml`. An svg is generated in
the same directory as the source file.

### Dialogue validator

Check a dialogue graph for runtime validity with `dialogue-validate <path>`,
for example `dialogue-validate data/alice_dialogue_graph.yaml`. It prints
a success line when the graph is valid, or a validation report when it is
not.

### In game dialogue management API

Use the `GraphNavigator` API to handle presenting, filtering, and selecting
dialogue options in your game engine. See a minimal working example 
[below](#programmatic-usage-mwe).

### Test suite

With dev dependencies installed, run the test suite with `./run_tests.sh`. 
This attempts to optimize which tests run using testmon. To override this, 
use `COVERAGE=1 ./run_tests.sh`.

## Dialogue model yaml format

A graph has this top-level shape:

* name: NPC name
* vertices: map of vertex_name -> vertex object. A vertex object has:
    * text, representing the NPC dialogue, and 
    * optionally effects, representing game state changes that occur upon 
        entering this vertex.
* edges: map of edge_name -> edge object. An edge object has:
    * from, representing the source vertex,
    * to, representing the target vertex,
    * text, representing  the player dialogue,
    * optionally predicates, representing game state conditions that must 
        be true for the edge to be available, and
    * optionally effects, representing game state changes that occur upon
        selecting this edge.

Example:

```
name: Zeke

vertices:
    vertex_0:
        text: "Hello world."
        effects: []
    vertex_1:
        text: "Here you go. You have purchased {flags.flower_count} flowers."
        effects:
            - {type: "modify_list", target: "player.inventory", method: "append", value: "Flower"}
            - {type: "modify_list", target: "zeke.inventory", method: "remove", value: "Flower"}
            - {type: "modify_value", target: "flags.flower_count", delta: 1}

edges:
    edge_0:
        from: "vertex_0"
        to: "vertex_1"
        text: "Here is 1 gold. Can I have a flower?"
        predicates:
            - {type: "check_value", path: "player.gold", op: ">=", value: 1}
            - {type: "check_list", path: "zeke.inventory", op: "in", value: "Flower"}
        effects:
            - {type: "modify_value", target: "player.gold", delta: -1}
```

For a larger example, see 
[data/alice_dialogue_graph.yaml](data/alice_dialogue_graph.yaml). 

The editor supports Python-esque text forms of effects and predicates. These
forms are parsed and converted into the above standardized yaml examples.
This availability exists to support the browser based `dialogue-editor`
where users can key predicates or effects by hand for a given vertex/edge;
it is not mandatory if manually editing yaml files or directly calling
`GraphEditor` methods outside of `dialogue-editor`. The following outlines
the conversion between forms.

### Effects:

* Modifying a list: `player.inventory.append(Flower)` <-> 
    `{type: "modify_list", target: "player.inventory", method: "append", value: "Flower"}`
* Modifying a value: `player.gold = player.gold-1` <-> 
    `{type: "modify_value", target: "player.gold", delta: -1}`

### Predicates:

* Checking a value: `player.gold >= 1` <-> 
    `{type: "check_value", path: "player.gold", op: ">=", value: 1}`
* Checking list membership: `Flower in zeke.inventory` <-> 
    `{type: "check_list", path: "zeke.inventory", op: "in", value: "Flower"}`

## Graph validation

A dialogue graph is runtime-valid when it satisfies every guarantee below.
The editor deliberately tolerates invalid graphs while working (logging 
warnings rather than blocking), but the runtime navigator requires a valid
graph.

Structural guarantees:

* The start vertex `vertex_0` exists.
* No edge endpoint is left unresolved (`__MISSING__`).
* Every edge endpoint references an existing vertex.
* Every vertex is reachable from `vertex_0` (along directed edges).
* The graph is a single connected component.

Well-formedness guarantees:

* Each effect type is supported, and `modify_list` effects use supported
    list methods.
* Each predicate type is supported.
* Each effect/predicate contains the keys required per that type.
* Each vertex/edge has text with no empty or nested placeholder braces `{}`.

Validation can be done in the command line with `dialogue-validate <path>`
or programmatically by importing functionality from the `dialogue_validator`
package.

## Programmatic game engine usage MWE:

This is a minimal working example of how the runtime dialogue navigator
could be used in a game engine. A game loop presents each turn, maps player
input to one of the available options, and advances until the conversation
is over.

```
from dialogue_model.graph import Graph
from dialogue_navigator.graph_navigator import GraphNavigator

graph = Graph("data/alice_dialogue_graph.yaml")

class MWEPlayer:
    def __init__(self):
        self.gold = 2
        self.inventory = []

class MWEAlice:
    def __init__(self):
        self.inventory = ["Flower", "Flower"]

class MWEGameState:
    def __init__(self):
        self.player = MWEPlayer()
        self.alice = MWEAlice()

def render_turn(turn):
    print(f"Alice: {turn.text}")
    for index, option in enumerate(turn.options):
        print(f"  [{index}] {option.text}")

graph_navigator = GraphNavigator(graph, game_state=MWEGameState())

turn = graph_navigator.get_current_turn()
while not turn.is_over:
    render_turn(turn)
    choice = turn.options[0] # Supposing the player always chooses option 0
    turn = graph_navigator.respond_with(choice.edge)
render_turn(turn)
```

In expected use cases, `GraphNavigator` will handle all mechanical aspects
of dialogue navigation (replacing text placeholder variables with their
values, filtering available edges to only ones with predicates satisfied,
and applying effects when an edge is selected). A typical user of
`GraphNavigator` need only be aware of:
* `get_current_turn()` to return a `Turn` object,
* `select(edge_name)` to commit a choice of edge player response, and
* `respond_with(edge_name)`, which is syntactic sugar for `select(edge_name)`
    followed by `get_current_turn()`. 

Note that validation automatically occurs when instantiating a
`GraphNavigator` and so need not be explicitly invoked. The game engine
is not expected to edit a `Graph` in any way; changes in dialogue availability
should occur by changing game state values that predicates will then check 
against, and therefore a single validation check on creation should suffice.

## Game state contract

The navigator resolves paths such as `player.gold` and `alice.inventory`,
used by predicates, effects, and text placeholders, against a game state
object that your engine owns. The dialogue project deliberately does not
define a game state class; this can be anything, as long as its attribute
tree matches the paths your graph uses. In the MWE above, `player.gold`
resolves because `MWEGameState` has a `player` attribute whose value has
a `gold` attribute.

By default, `GraphNavigator(graph, game_state, accessor)` wraps `game_state`
in an `AttributeStateAccessor` which reads and writes those paths as ordinary
object attributes. If your state is not stored as plain attributes (for
instance, it is a dictionary, an entity component system, etc), pass a custom
`accessor` instead:

```
from dialogue_navigator.state_accessor import StateAccessor

class MyAccessor:
    def get(self, path):
        ...
    def set(self, path, value):
        ...

graph_navigator = GraphNavigator(graph, accessor=MyAccessor())
```

## Package Layout

### dash_app

Browser-based visual editor.

### dialogue_editor

`GraphEditor` mutation and persistence API. Used by the Dash + Cytoscape app, 
with public access to methods as well.

### dialogue_model

`Graph`, `Vertex`, and `Edge` classes. Codecs for converting/parsing between 
yaml and python syntax.

### dialogue_navigator

`GraphNavigator` runtime edge validation and effect processing. Handles
complete dialogue turn life cycle with `Turn` and `Option` classes. Provides
an accessor seam to handle any engine's game state managers.

### dialogue_validator

`GraphValidator` validity API. Used by `GraphNavigator`, with public access
to methods as well.

### dialogue_viewer

`GraphViewer` class, a static svg renderer.

## Behavior notes

`GraphEditor` and consequently the `dialogue-editor` browser app handle vertex
deletion with an optional `cascade_delete` parameter, defaulting to `False`.
When `True`, removing a vertex removes all connected edges. When `False`,
removing a vertex orphans all edges having that vertex as its source or 
target, flagging the from and to keys as `__MISSING__`.

Graphs begin at `vertex_0`, which cannot be deleted.

## Editor log messages

The log in `dialogue-editor` is intended to be a user-facing history of 
changes made in the UI.

The editor uses these terms in the log:

* NPC node: A dialogue node spoken by the NPC (represented by a vertex in
    the dialogue model).
* Player node: A dialogue option spoken by the player (represented by an
    edge in the dialogue model).

### What gets logged

* Creating nodes: Click Add NPC Dialogue or Add Player Dialogue, enter data, 
    and click Save. Logs the node id and any nonempty saved fields.
* Editing nodes: Select a node, click Edit Selected Node, change data, and 
    click Save. Logs any old values and their corresponding updated values.
* Deleting nodes: Select a node, click Delete Selected Node, and click Confirm
    Delete. Logs the deleted node id and any nonempty fields.
* Cascade delete: Click the checkbox to delete all connected player nodes 
    before clicking Confirm Delete when deleting an NPC node. Logs one line 
    for the deleted NPC node and one line for each Player node.
* Non-cascade delete: Leave the checkbox unselected before clicking Confirm
    Delete. Logs the deletion and flags the number of unresolved connections 
    of Source/Target NPC nodes that need to be addressed.
* New/Open/Save/Undo/Redo: Click the corresponding buttons in the header 
    of the user interface. Logs outcomes and filenames when relevant.
* Validation and parsing failures: Logs plain-language explanations with
    direct guidance on how to resolve.

## Console scripts

`dialogue-editor` launches the Dash browser editor.

`dialogue-render <path>` renders a yaml graph to svg in the same directory
as the source file.

`dialogue-validate <path>` checks a yaml graph for runtime validity and
prints a status report.

(With dev dependencies) `./run_tests.sh` runs an optimized pytest suite.
To force all tests to run, use `COVERAGE=1 ./run_tests.sh`.
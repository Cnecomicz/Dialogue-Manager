# Dialogue Manager

A Python toolkit for building, editing, navigating, and visualizing branching
dialogue graphs for video games. This is intended to support my current
game development but has been built standalone in order to contain its scope 
and to allow anyone willing to use my conventions to adopt it for their 
own purposes.

It includes:

* A dialogue model which standardizes dialogue graphs, tracking the text,
predicates, and effects per each vertex or edge, and saves/loads into yaml.
* A runtime graph navigator API that traverses dialogue graphs, getting
NPC and player text, filtering player options by game state predicates, 
and setting game state effects upon node entry.
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
choices while handling predicates and effects
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

Install with development tools:

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

### Test suite

With dev dependencies installed, run the test suite with `./run_tests.sh`. 
This attempts to optimize which tests run using testmon. To override this, 
use `COVERAGE=1 ./run_tests.sh`.

### In game dialogue management API

Use the `GraphNavigator` API to handle presenting, filtering, and selecting
dialogue options in your game engine. See a minimal working example 
[below](#programmatic-usage-mwe).

## Dialogue model yaml format

A graph has this top-level shape:

* name: NPC name
* vertices: map of vertex_name -> vertex object. A vertex object has text,
representing the NPC dialogue, and optionally effects, representing game
state changes that occur upon entering this vertex.
* edges: map of edge_name -> edge object. An edge object has from, representing
the source vertex, to, representing the target vertex, text, representing 
the player dialogue, optionally predicates, representing game state conditions
that must be true for the edge to be available, and optionally effects,
representing game state changes that occur upon selecting this edge.

Example:

```
name: Zeke

vertices:
    vertex_0:
        text: "Hello world."
        effects: []
    vertex_1:
        text: "Here you go."
        effects:
            - {type: "modify_list", target: "player.inventory", method: "append", value: "Flower"}

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

The editor supports text forms for effects and predicates that are parsed 
into the above yaml examples. These forms are used in the editor to key 
predicates or effects by hand for a given vertex/edge.

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

## Programmatic usage MWE:

This is a sample of how the runtime dialogue navigator will be used in the
game engine:

```
from dialogue_model.graph import Graph
from dialogue_navigator.graph_navigator import GraphNavigator, InvalidEdgeError

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

graph_navigator = GraphNavigator(graph, MWEGameState())

current_turn = graph_navigator.get_current_turn()
print("Alice says:")
for vertex_name, vertex_text in current_turn["vertex_text"].items():
    print(f"{vertex_text} ({vertex_name})")
print("Your options:")
for edge_name, edge_text in current_turn["edge_texts"].items():
    print(f"{edge_text} ({edge_name})")

try:
    graph_navigator.select("edge_0")
except InvalidEdgeError as exception:
    print(exception)

current_turn = graph_navigator.get_current_turn()
print("Alice then says:")
for vertex_name, vertex_text in current_turn["vertex_text"].items():
    print(f"{vertex_text} ({vertex_name})")
print("Your options now:")
for edge_name, edge_text in current_turn["edge_texts"].items():
    print(f"{edge_text} ({edge_name})")

```

## Package Layout

### dash_app

Browser-based visual editor.

### dialogue_editor

GraphEditor mutation and persistence API. Used by the Dash + Cytoscape app, 
with public access to methods as well.

### dialogue_model

Graph, Vertex, and Edge classes. Codecs for converting/parsing between yaml
and python syntax.

### dialogue_navigator

GraphNavigator runtime edge validation and effect processing. Handles complete
dialogue turn life cycle. 

## Behavior notes

GraphEditor and consequently the `dialogue-editor` browser app handle vertex
deletion with an optional `cascade_delete` parameter, defaulting to `False`.
When `True`, removing a vertex removes all connected edges. When `False`,
removing a vertex orphans all edges having that vertex as its source or 
target, flagging the from and to keys as `__MISSING__`.

Graphs begin at vertex_0, which cannot be deleted.

## Editor log messages

The Log in `dialogue-editor` is intended to be a user-facing history of 
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
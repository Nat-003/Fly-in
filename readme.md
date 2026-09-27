*This project has been created as part of the 42 curriculum by nappasam.*



# Fly-in

A drone-routing simulator: it moves a fleet of drones from a **start** zone to an **end** zone across a network of connected zones, in as few simulation turns as possible, while respecting movement costs, zone/connection capacities, and special zone types.

---

## Description

Beneath the drone theme, Fly-in is a **multi-agent pathfinding and flow-scheduling problem on a graph**. Given a map file describing a network of zones and the connections between them, plus a number of drones, the program routes every drone from the single start zone to the single end zone and prints, turn by turn, where each drone moves — aiming to minimise the total number of turns.

The problem has two distinct layers, solved by different parts of the code:

1. **Pathfinding** — discovering good routes through the graph, weighted by how many turns each zone costs to enter.
2. **Scheduling / simulation** — marching the drones along those routes turn by turn, never violating a zone's or a connection's capacity, and pipelining them so they don't queue single-file when they don't have to.

The map format supports four zone types (`normal`, `priority`, `restricted`, `blocked`), per-zone capacities (`max_drones`), per-connection capacities (`max_link_capacity`), and optional colours used by the visual output. `restricted` zones are special: reaching one costs **two turns**, during which the drone occupies the connection mid-flight and must land on the next turn.

The program is written in **Python 3.10+**, is fully object-oriented, and uses **no graph libraries** — the graph model, Dijkstra search, and simulation are all hand-written (only `heapq` from the standard library is used as a plain container).

---

## Instructions

### Requirements
- Python **3.10 or later**
- `make` (to use the provided targets)
- `flake8` and `mypy` for linting (installed by `make install`)

### Setup
```sh
make install      # installs flake8 + mypy
```

### Running
The program takes a map file as its single argument:
```sh
python3 main.py maps/easy/01_linear_path.txt
```

Or via the Makefile, which runs a default map you can override:
```sh
make run                                   # runs the default map
make run MAP=maps/easy/02_simple_fork.txt  # runs a specific map
```

### Other Makefile targets
| Target | What it does |
|---|---|
| `make install` | Install the dev dependencies (flake8, mypy). |
| `make run` | Run the simulator on `$(MAP)` (override with `MAP=path`). |
| `make debug` | Run the program under Python's debugger (`pdb`). |
| `make lint` | Run `flake8 .` and `mypy` with the subject's mandated flags. |
| `make lint-strict` | Run `flake8 .` and `mypy . --strict`. |
| `make clean` | Remove caches and bytecode (`__pycache__`, `.mypy_cache`, `*.pyc`). |

### Map file format
```
nb_drones: 5

start_hub: start 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]

connection: start-roof1
connection: corridorA-goal [max_link_capacity=2]
```
- First line: `nb_drones: <positive integer>`.
- Zones: `start_hub:` / `end_hub:` / `hub:` followed by `<name> <x> <y>` and optional `[metadata]`.
- Metadata keys: `zone=<normal|priority|restricted|blocked>`, `color=<word>`, `max_drones=<n>` (zones), `max_link_capacity=<n>` (connections). All optional; tags may appear in any order.
- Connections: `connection: <name1>-<name2>` (bidirectional; zone names may not contain dashes or spaces).
- Lines starting with `#` are comments.

Malformed maps stop the program with an error message identifying the offending line and its cause.

---

## Algorithm and implementation strategy

The program is built as a small pipeline of single-responsibility classes.

### 1. Parsing → the graph model (`Parser`, `Zone`, `Connection`, `Graph`)
The parser reads the map line by line and builds the graph **incrementally**. Validation is layered by how much context each check needs:
- **Line-level** (in the parser): is the prefix known, are the coordinates integers, is the metadata well-formed?
- **Object-level** (in constructors): is the zone type one of the four legal values, are capacities positive?
- **Whole-map** (in `Graph`): exactly one start and one end, unique zone names, no duplicate connections, every connection's endpoints already defined.

The graph stores zones in a dict and uses an **adjacency list** (`dict[str, list[Connection]]`). Connections are bidirectional and stored on both endpoints. A `normalized_key()` (the two zone names, sorted) is used to reject duplicate edges such as `a-b` / `b-a`.

### 2. Pathfinding (`Pathfinder`)
Routes are found with a hand-written **weighted Dijkstra**. Each zone's `movement_cost()` is its weight (`restricted` = 2, everything else = 1), so the search naturally prefers `priority`/`normal` routes over `restricted` ones and never enters `blocked` zones. A monotonically increasing counter is pushed into each heap entry (`(cost, counter, node)`) so that zones are never compared directly when costs tie.

**Multiple paths** are produced by a *penalise-and-repeat* strategy (a simplified Yen's algorithm): find the cheapest path, then add a large penalty to the **intermediate** zones of that path (never the start or end, which every path shares) and search again. Because the just-used zones are now expensive, the next search is pushed onto a different route. This repeats until no new path is found. This yields several good routes without requiring them to be perfectly disjoint — the simulation engine handles any overlap.

### 3. Assigning drones to paths (`Simulation.create_drones`)
Splitting drones evenly across paths would be wrong, because paths differ in length: a short path can cycle drones through faster than a long one. Instead the assignment is **greedy by estimated finish time**: each drone is given the path that minimises `path_length + (drones already assigned to that path)`. This front-loads short paths and lightly loads long ones, so all paths finish at roughly the same turn. Each `Drone` stores its **own** path, which is why introducing multiple paths required no change to the turn engine.

### 4. The turn engine (`Simulation.take_turn`)
Each turn is resolved in a strict **plan-then-commit** design, in four phases, so that all moves are decided from the turn's *starting* state before any of them are applied:

1. **Land arrivals** — drones mid-flight toward a restricted zone tick down and land, joining their destination zone.
2. **Project occupancy** — build a projected occupancy per zone and per connection, reserving the destinations of drones still in transit.
3. **Plan** — process drones **furthest-along first**, so a drone leaving a zone frees it for the drone behind *in the same turn* (this is what pipelines the fleet instead of a single-file crawl). A move is allowed only if both the destination zone and the connection have projected room. Moves into a restricted zone are recorded as two-turn **launches**; all others as normal moves.
4. **Commit** — apply **all departures first, then all arrivals**, so that a move which depends on another drone vacating a zone (including a launch on a different list) never sees the zone as briefly full.

Zone-capacity, connection-capacity, the start/end exceptions (uncapped), and the "restricted drone must land next turn, cannot wait on the connection" rule all fall out of this projection-based design.

---

## Visual representation

The simulator provides a **coloured terminal** visual. After each turn it prints two things:

1. The official movement line in the required format — `D<id>-<zone>` for a normal move, or `D<id>-<connection>` for a drone still in flight toward a restricted zone — space-separated, one line per turn.
2. A `--- ZONES ---` panel showing the state of every zone that turn:

```
Turn 3 | D1-path_a D4-junction
--- ZONES ---
  start        remaining: 0
  junction     D2 D3 D4
  path_a       D1
  path_b       .
  goal         delivered: 1/4
```

Each row shows a zone's live contents: the drones currently in it (`D1 D2`), any drone flying toward it (`-> D3`), a `.` when empty, `remaining: N` on the start zone, and `delivered: N/total` on the end zone. Zone **names are coloured** according to each zone's `color` field, translated to ANSI escape codes at display time through a name→code table with a plain-text fallback for colours that aren't recognised (the spec allows any colour word, so unknown ones simply render uncoloured rather than failing).

**Why it helps:** the panel makes the simulation legible at a glance — you can watch a zone fill and drain, see when a corridor is idle, and confirm that drones are actually being distributed across parallel paths rather than queueing on one. It made a real routing issue visible during development (an unused branch showing as permanently empty), which is exactly the kind of insight the movement line alone hides.

---

## Example input and output

**Input** — `maps/easy/02_simple_fork.txt` (4 drones, a fork with two parallel branches):
```
nb_drones: 4

start_hub: start 0 1 [color=green]
hub: junction 1 1 [color=yellow]
hub: path_a 2 0 [color=blue]
hub: path_b 2 2 [color=blue]
end_hub: goal 3 1 [color=red]

connection: start-junction
connection: junction-path_a
connection: junction-path_b
connection: path_a-goal
connection: path_b-goal
```

**Output** (movement lines; the coloured zone panel is printed after each line in the terminal):
```
D1-junction D2-junction D3-junction
D1-path_a D4-junction
D1-goal D2-path_a
D2-goal D3-path_a
D3-goal D4-path_a
D4-goal
number of turn 6
```

Both branches (`path_a` and `path_b`) are used, so the fleet flows in parallel instead of single-file.

---

## Performance

On the provided maps, every drone is delivered and every reference turn-target (subject §VII.7) is met:

| Map | Drones | Turns | Target |
|---|---|---|---|
| Easy — linear_path | 2 | 4 | ≤ 6 |
| Easy — simple_fork | 4 | 4 | ≤ 8 |
| Easy — basic_capacity | 4 | 4 | ≤ 6 |
| Medium — dead_end_trap | 5 | 8 | ≤ 12 |
| Medium — circular_loop | 6 | 15 | ≤ 15 |
| Medium — priority_puzzle | 5 | 7 | ≤ 12 |
| Hard — maze_nightmare | 8 | 13 | ≤ 30 |
| Hard — capacity_hell | 12 | 16 | ≤ 35 |
| Hard — ultimate_challenge | 15 | 28 | ≤ 45 |

The optional challenger map (*the_impossible_dream*, 25 drones) is solved but does not currently beat the optional 45-turn reference record.

---

## Resources

References consulted for the concepts behind the project:
- Dijkstra's shortest-path algorithm — weighted graph traversal.
- Yen's algorithm / k-shortest-paths — the idea behind the penalise-and-repeat multi-path search.
- The **lem-in** problem (42 curriculum) — the classic ant-farm flow-scheduling problem this project is modelled on, and the source of the greedy path-assignment idea.
- Python `heapq` documentation — the priority queue used by Dijkstra.
- ANSI escape codes — terminal colour output.

### How AI was used
AI (Claude) was used as a **tutor and reviewer**, not a code generator. Specifically:
- **Concept explanation and design guidance** — talking through the four-phase turn engine, the restricted-zone two-turn transit, the plan-then-commit commit ordering, the penalise-and-repeat multi-path idea, and the greedy assignment strategy *before* writing them.
- **Code review** — running my drafts against the sample maps, pointing out bugs (e.g. a double-move after landing, a commit-ordering crash, a departure-credit placement error, an f-string quote-nesting issue) and explaining *why* they were wrong so I could fix them myself.
- **Documentation** — help drafting this README and the project's internal handoff notes.

Every algorithm and design decision was worked through and understood before being implemented; the code was written and debugged by me, with AI used to explain concepts, catch mistakes, and verify behaviour against the real map files.

# Maze Runner

A Python project for exploring classical search algorithms in maze environments. Use the graphical interface to choose a maze, problem, and algorithm, or run searches from the command line.

## Requirements

- Python 3
- Tkinter for the graphical interface (usually included with standard Python installations)

The project uses only Python's standard library; no `pip install` step is required.

## Run the graphical interface

From the project directory:

```powershell
python gui.py
```

Choose a maze, problem, and search algorithm in the window, then select **Run**. Use **Compare all** to compare supported algorithms. Press **Space** to skip an animation.

## Run from the command line

```powershell
# List available mazes
python runner.py --list

# Run breadth-first search on the default maze
python runner.py

# Run depth-first search on maze_small
python runner.py --maze maze_small --algorithm dfs

# Solve a keys problem using A* and the keyhunt heuristic
python runner.py --maze keys_small --problem keys --algorithm astar --heuristic keyhunt

# Compare algorithms
python runner.py --maze maze_medium --compare

# Print statistics without opening a window
python runner.py --maze maze_medium --algorithm bfs --quiet

# Show all command-line options
python runner.py --help
```

The short algorithm names are `right`, `dfs`, `bfs`, `dls`, `ids`, `ucs`, `gbfs`, and `astar`. For depth-limited search, pass a limit with `--depth`.

## Project layout

- `gui.py` — graphical interface for selecting mazes and running or comparing searches
- `runner.py` — command-line runner and search orchestration
- `search.py` — search algorithm implementations
- `problems.py`, `griever_hole.py` — maze and key-collection problem definitions
- `heuristics.py` — heuristics for informed search
- `maze.py`, `display.py`, `util.py` — maze loading, display, and shared utilities
- `mazes/` — included maze layouts
- `reports.pdf` — project report

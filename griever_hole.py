"""
griever_hole.py
---------------
Questions 8 and 9: escaping through the Griever Hole.

The Griever Hole only opens after the runners have entered the escape code.
The pieces of the code (marked K in the maze) are scattered through the
corridors. Thomas has to pick up ALL of them, in any order, and then reach the
exit E. Picking up a piece happens automatically when he steps onto its cell.

Try it once you are done:
    python runner.py -l keys_small -p keys -a bfs
    python runner.py -l keys_medium -p keys -a astar -H keyhunt
"""

import util
from problems import SearchProblem, mazeDistance


class KeyHuntProblem(SearchProblem):
    """
    Q8: Collect every code piece, then reach the exit.

    You choose the state representation, with two requirements:
      1. A state must be HASHABLE (tuples, frozensets, ints, strings... but
         not lists, sets or dicts), because your search keeps them in sets.
      2. A state must be a TUPLE whose FIRST element is Thomas's (row, col)
         position. The display and the grader read state[0].

    Keep the state small: store only what you need to know to decide what
    happens next. Do NOT put the whole maze in the state.
    """

    def __init__(self, maze):
        self.maze = maze
        self.startPosition = maze.start
        self.keys = tuple(maze.keys)      # positions of all code pieces
        self.exit = maze.exit
        self.heuristicInfo = {}           # scratch space for your heuristic
        # Bookkeeping for the display and the grader. Do not touch.
        self._expanded = 0
        self._expandedOrder = []
        "*** YOUR CODE HERE (optional: set up anything else you need) ***"

    def getStartState(self):
        """Returns the start state, a tuple (startPosition, ...)."""
        # State = (position, pieces still to collect). The ORDER in which the
        # earlier pieces were picked up does not change what can happen next,
        # so a frozenset of the remaining pieces is all we need to remember.
        remaining = frozenset(self.keys)
        # Just in case a piece lies on the start cell: it is already collected.
        remaining = remaining - {self.startPosition}
        return (self.startPosition, remaining)

    def isGoalState(self, state):
        """True when every code piece has been collected AND Thomas is at the exit."""
        position, remaining = state
        return position == self.exit and len(remaining) == 0

    def getSuccessors(self, state):
        """
        Returns a list of (successor, action, stepCost) triples.

        Use self.maze.neighbors(position), which gives the legal
        (action, nextPosition) pairs in North, South, East, West order, and
        self.maze.cost(nextPosition) for the step cost.
        """
        # Bookkeeping. Keep these two lines.
        self._expanded += 1
        self._expandedOrder.append(state[0])

        successors = []
        position, remaining = state
        for action, nextPosition in self.maze.neighbors(position):
            # Stepping onto a piece picks it up automatically.
            if nextPosition in remaining:
                nextRemaining = remaining - {nextPosition}
            else:
                nextRemaining = remaining
            nextState = (nextPosition, nextRemaining)
            successors.append((nextState, action, self.maze.cost(nextPosition)))
        return successors

    # --- Provided: you do not need to change anything below -------------
    def getCostOfActions(self, actions):
        """Total step cost of a sequence of actions (inf if it hits a wall)."""
        import maze as mazeModule
        if actions is None:
            return float('inf')
        pos = self.startPosition
        total = 0
        for action in actions:
            dr, dc = mazeModule.DELTA[action]
            pos = (pos[0] + dr, pos[1] + dc)
            if self.maze.isWall(pos):
                return float('inf')
            total += self.maze.cost(pos)
        return total

    def positionOf(self, state):
        return state[0]

    def expandedPositions(self):
        return list(self._expandedOrder)


def keyHuntHeuristic(state, problem):
    """
    Q9: A heuristic for KeyHuntProblem.

    It must be CONSISTENT (and therefore admissible): for every state s and
    successor s' reached with step cost c,  h(s) <= c + h(s'),  and h must be
    0 at goal states. The grader checks this.

    The more informed (larger) your heuristic is while staying consistent,
    the fewer states A* expands and the more points you earn.

    Useful tools:
      * problem.keys, problem.exit, and whatever your state stores
      * mazeDistance(pos1, pos2, problem.maze, problem.heuristicInfo) gives
        the true number of steps between two cells, and caches the result
      * util.manhattanDistance(pos1, pos2)
    """
    position, remaining = state

    def distance(a, b):
        return mazeDistance(a, b, problem.maze, problem.heuristicInfo)

    # No pieces left: all that remains is the walk to the exit.
    if len(remaining) == 0:
        return distance(position, problem.exit)

    # Part 1: Thomas must at least walk to the nearest remaining piece.
    toNearestPiece = min(distance(position, key) for key in remaining)

    # Part 2: after that he still has to link up every remaining piece and
    # the exit. No walk can do that in fewer steps than the minimum spanning
    # tree of those points. The tree only depends on which pieces remain, so
    # it is computed once per set of pieces and remembered.
    cacheKey = ('spanningTree', remaining)
    if cacheKey not in problem.heuristicInfo:
        points = list(remaining) + [problem.exit]
        problem.heuristicInfo[cacheKey] = spanningTreeLength(points, distance)

    return toNearestPiece + problem.heuristicInfo[cacheKey]


def spanningTreeLength(points, distance):
    """
    Total length of the minimum spanning tree that connects 'points', where
    distance(a, b) is the length of the edge between two points.

    This is Prim's algorithm: start the tree from one point and keep adding
    the point that is cheapest to attach, until every point is in the tree.
    """
    inTree = [points[0]]
    notInTree = points[1:]
    total = 0

    while notInTree:
        bestPoint = None
        bestDistance = float('inf')
        for candidate in notInTree:
            for member in inTree:
                d = distance(member, candidate)
                if d < bestDistance:
                    bestDistance = d
                    bestPoint = candidate

        # Every point left is unreachable (walled off): no finite tree exists.
        if bestPoint is None:
            return float('inf')

        total += bestDistance
        inTree.append(bestPoint)
        notInTree.remove(bestPoint)

    return total

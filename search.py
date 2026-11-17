"""
search.py
---------
THE MAZE RUNNER — Mini Project 1: Classical Search

This is where you implement the search algorithms (Questions 1–7).

Every algorithm receives a SearchProblem (see problems.py) and must return a
LIST OF ACTIONS that leads from the start state to a goal state, e.g.
['South', 'South', 'East']. Return [] if the start state is already a goal.

Conventions the grader relies on (please read — they matter!):

  * Use the fringe containers from util.py (Stack, Queue, PriorityQueue).
  * Calling problem.getSuccessors(state) counts as EXPANDING that state.
    Call it exactly once per expanded state, and never for a state you only
    generated.
  * Goal test when a state is POPPED from the fringe (just before you would
    expand it), not when it is pushed. (For BFS the grader also accepts
    the "early" goal test done when a state is generated.)
  * Push successors in the order getSuccessors returns them.
  * Q1, Q2, Q5, Q6, Q7 are GRAPH searches: keep a set of already-expanded
    states and never expand the same state twice.
"""

import util
from util import Stack, Queue, PriorityQueue, CUTOFF
from heuristics import nullHeuristic


# ----------------------------------------------------------------------
# Q0 (worked example, not graded): always go right
# ----------------------------------------------------------------------
def alwaysRightSearch(problem):
    """
    Not a real search: the runner keeps stepping right ('East') until he
    reaches the goal. If a wall blocks the way east, he is stuck and gives up
    (returns None). It shows you how to use the problem's methods. Try it:
        python runner.py -l maze_tiny -a right     (escapes)
        python runner.py -l maze_small -a right       (walks into a wall)
    """
    state = problem.getStartState()
    actions = []
    while not problem.isGoalState(state):
        successors = problem.getSuccessors(state)   # list of (next, action, cost)
        east = [s for s in successors if s[1] == 'East']
        if not east:
            return None   # a wall straight ahead: the doors close with him inside
        nextState, action, stepCost = east[0]
        actions.append(action)
        state = nextState
    return actions


# ----------------------------------------------------------------------
# Q1: Depth-First Search
# ----------------------------------------------------------------------
def depthFirstSearch(problem):
    """
    Search the deepest nodes in the search tree first (graph search).

    To get started, try printing:
        print("Start:", problem.getStartState())
        print("Is the start a goal?", problem.isGoalState(problem.getStartState()))
        print("Start's successors:", problem.getSuccessors(problem.getStartState()))

    Hint: a fringe entry can hold more than a state. Storing
    (state, actionsSoFar) is an easy way to remember how you got there.
    """
    fringe = Stack()
    fringe.push((problem.getStartState(), []))
    expanded = set()

    while not fringe.isEmpty():
        state, actions = fringe.pop()

        if problem.isGoalState(state):
            return actions

        if state not in expanded:
            expanded.add(state)
            for successor, action, stepCost in problem.getSuccessors(state):
                fringe.push((successor, actions + [action]))

    # The fringe ran out before a goal was found: there is no solution.
    return None


# ----------------------------------------------------------------------
# Q2: Breadth-First Search
# ----------------------------------------------------------------------
def breadthFirstSearch(problem):
    """Search the shallowest nodes in the search tree first (graph search)."""
    fringe = Queue()
    fringe.push((problem.getStartState(), []))
    expanded = set()

    while not fringe.isEmpty():
        state, actions = fringe.pop()

        if problem.isGoalState(state):
            return actions

        if state not in expanded:
            expanded.add(state)
            for successor, action, stepCost in problem.getSuccessors(state):
                fringe.push((successor, actions + [action]))

    return None


# ----------------------------------------------------------------------
# Q3: Depth-Limited Search
# ----------------------------------------------------------------------
def depthLimitedSearch(problem, limit):
    """
    Depth-first search that never goes deeper than 'limit' actions.

    Return value:
      * a list of at most 'limit' actions that reaches a goal, or
      * CUTOFF (from util) if no goal was found but the search was stopped
        by the depth limit somewhere, so a deeper solution may exist, or
      * None if no goal was found and the limit was never reached, which
        proves there is no solution at all.

    The start state is at depth 0. A state at depth == limit may be goal
    tested but must not be expanded.

    Do NOT use a global explored set here (think about why that can make the
    search miss a solution that fits within the limit). Instead, avoid cycles
    by not revisiting a state that is already on the current path.
    """
    # A negative limit does not even allow the start state to be looked at.
    if limit is None or limit < 0:
        return CUTOFF

    def recursiveDLS(state, depth, onPath):
        """
        Search below 'state', which sits at 'depth'. 'onPath' is the set of
        states on the path from the start down to 'state' (inclusive).
        Returns a list of actions, CUTOFF or None, just like the outer function.
        """
        if problem.isGoalState(state):
            return []

        # At the limit a state may be goal tested (above) but not expanded.
        if depth == limit:
            return CUTOFF

        cutoffHappened = False
        for successor, action, stepCost in problem.getSuccessors(state):
            # Going back to a state already on this path would be a cycle.
            if successor in onPath:
                continue

            onPath.add(successor)
            result = recursiveDLS(successor, depth + 1, onPath)
            onPath.remove(successor)

            if result is CUTOFF:
                cutoffHappened = True
            elif result is not None:
                return [action] + result

        if cutoffHappened:
            return CUTOFF
        return None

    start = problem.getStartState()
    return recursiveDLS(start, 0, {start})


# ----------------------------------------------------------------------
# Q4: Iterative Deepening Search
# ----------------------------------------------------------------------
def iterativeDeepeningSearch(problem, maxDepth=10000):
    """
    Run depthLimitedSearch with limit = 0, 1, 2, ... until it finds a
    solution. Return that solution, or None if the problem has no solution
    (or none within maxDepth).
    """
    for limit in range(maxDepth + 1):
        result = depthLimitedSearch(problem, limit)
        # A list means a solution; None means no solution exists at any depth.
        if result is not CUTOFF:
            return result

    # Still cut off at maxDepth: give up.
    return None


# ----------------------------------------------------------------------
# Helper shared by Q5, Q6 and Q7
# ----------------------------------------------------------------------
def priorityGraphSearch(problem, priorityFunction):
    """
    Graph search with a PriorityQueue as the fringe. UCS, Greedy and A* are
    all this same loop; they only differ in the number used to order the
    fringe, which is priorityFunction(costSoFar, state).

    A state can sit in the fringe several times (once for every way it was
    reached). The copy with the lowest priority is popped first and expanded;
    the others are skipped when they are popped later.
    """
    start = problem.getStartState()
    fringe = PriorityQueue()
    fringe.push((start, [], 0), priorityFunction(0, start))
    expanded = set()

    while not fringe.isEmpty():
        state, actions, costSoFar = fringe.pop()

        if problem.isGoalState(state):
            return actions

        if state not in expanded:
            expanded.add(state)
            for successor, action, stepCost in problem.getSuccessors(state):
                newCost = costSoFar + stepCost
                priority = priorityFunction(newCost, successor)
                fringe.push((successor, actions + [action], newCost), priority)

    return None


# ----------------------------------------------------------------------
# Q5: Uniform-Cost Search
# ----------------------------------------------------------------------
def uniformCostSearch(problem):
    """Search the node of least total path cost g(n) first (graph search)."""
    def pathCost(costSoFar, state):
        return costSoFar

    return priorityGraphSearch(problem, pathCost)


# ----------------------------------------------------------------------
# Q6: Greedy Best-First Search
# ----------------------------------------------------------------------
def greedyBestFirstSearch(problem, heuristic=nullHeuristic):
    """
    Search the node that SEEMS closest to the goal first, i.e. the one with
    the lowest heuristic(state, problem) value (graph search).
    """
    def estimateOnly(costSoFar, state):
        return heuristic(state, problem)

    return priorityGraphSearch(problem, estimateOnly)


# ----------------------------------------------------------------------
# Q7: A* Search
# ----------------------------------------------------------------------
def aStarSearch(problem, heuristic=nullHeuristic):
    """
    Search the node with the lowest f(n) = g(n) + heuristic(n) first
    (graph search).
    """
    def costPlusEstimate(costSoFar, state):
        return costSoFar + heuristic(state, problem)

    return priorityGraphSearch(problem, costPlusEstimate)


# Abbreviations
always_right = alwaysRightSearch
dfs = depthFirstSearch
bfs = breadthFirstSearch
dls = depthLimitedSearch
ids = iterativeDeepeningSearch
ucs = uniformCostSearch
gbfs = greedyBestFirstSearch
astar = aStarSearch

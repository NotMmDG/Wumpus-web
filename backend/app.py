from flask import Flask, jsonify, request
from flask_cors import CORS
from game.world import World
from game.agent import Agent
from game.logic import get_best_move

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

world = World(size=5)
agent = Agent(world)

def get_best_move_and_reason(visible_grid, agent_pos):
    """
    Returns (best_move, best_reason) where best_move is [row, col] and best_reason is a string explanation.
    """
    from collections import deque

    rows = len(visible_grid)
    cols = len(visible_grid[0]) if rows > 0 else 0
    directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]

    visited = set()
    safe = set()
    risky = set()
    dangerous = set()

    # 1. Mark visited cells
    for r in range(rows):
        for c in range(cols):
            cell = visible_grid[r][c]
            if cell != "unknown":
                visited.add((r, c))
                if cell in ("pit", "wumpus"):
                    dangerous.add((r, c))

    # 2. Deduce safe/risky/dangerous for unknown cells
    for r in range(rows):
        for c in range(cols):
            if visible_grid[r][c] != "unknown":
                continue
            neighbor_percepts = []
            has_white_neighbor = False
            all_neighbors_breeze_or_stench = True
            has_visited_neighbor = False
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) in visited:
                    has_visited_neighbor = True
                    neighbor_cell = visible_grid[nr][nc]
                    neighbor_percepts.append(neighbor_cell)
                    if neighbor_cell not in ("pit", "wumpus", "gold") and "breeze" not in neighbor_cell and "stench" not in neighbor_cell:
                        has_white_neighbor = True
                    if "breeze" not in neighbor_cell and "stench" not in neighbor_cell:
                        all_neighbors_breeze_or_stench = False
            if not has_visited_neighbor:
                continue
            if has_white_neighbor:
                safe.add((r, c))
            elif all_neighbors_breeze_or_stench:
                dangerous.add((r, c))
            elif any("breeze" in n or "stench" in n for n in neighbor_percepts):
                risky.add((r, c))

    risky = risky - safe - dangerous

    r, c = agent_pos
    unvisited_neighbors = []
    visited_neighbors = []
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            if visible_grid[nr][nc] == "unknown":
                unvisited_neighbors.append((nr, nc))
            elif (nr, nc) in visited and visible_grid[nr][nc] not in ("pit", "wumpus"):
                visited_neighbors.append((nr, nc))

    all_unvisited_not_safe = all((nbr not in safe) for nbr in unvisited_neighbors) if unvisited_neighbors else False

    prev_cell = None
    if hasattr(agent, "move_history") and agent.move_history and len(agent.move_history) > 1:
        prev_label = agent.move_history[-2][0]
        cols_labels = ['A', 'B', 'C', 'D', 'E'][:cols]
        col = cols_labels.index(prev_label[0])
        row = int(prev_label[1:]) - 1
        prev_cell = (row, col)

    best_move = None
    best_reason = ""
    # Try to explain the logic for the best move
    if all_unvisited_not_safe and visited_neighbors:
        if len(visited_neighbors) == 1 and prev_cell and visited_neighbors[0] == prev_cell:
            all_dangerous = True
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    cell = visible_grid[nr][nc]
                    if cell not in ("pit", "wumpus") and (nr, nc) != prev_cell:
                        all_dangerous = False
                        break
            if all_dangerous:
                best_move = list(prev_cell)
                best_reason = (
                    f"All unvisited neighbors are not marked safe and only one visited neighbor exists, "
                    f"which is the previous cell ({prev_cell}). All other neighbors are dangerous, so the best move is to return to the previous cell."
                )
        else:
            for nbr in visited_neighbors:
                if prev_cell is None or nbr != prev_cell:
                    best_move = list(nbr)
                    best_reason = (
                        f"All unvisited neighbors are not marked safe. There are multiple visited neighbors. "
                        f"Choosing a visited neighbor ({nbr}) that is not the previous cell to avoid danger."
                    )
                    break

    if best_move is None:
        # BFS to find shortest path to an unvisited safe cell
        queue = deque()
        queue.append((tuple(agent_pos), []))
        explored = set()
        while queue:
            (r0, c0), path = queue.popleft()
            if (r0, c0) in explored:
                continue
            explored.add((r0, c0))
            if (r0, c0) in safe and visible_grid[r0][c0] == "unknown":
                if path:
                    best_move = list(path[0])
                    best_reason = (
                        f"Found a path to an unvisited safe cell at {path[-1]}. "
                        f"The first step towards it is {path[0]}. Safe cells are deduced from neighbors with no breeze or stench."
                    )
                else:
                    best_move = [r0, c0]
                    best_reason = (
                        f"Current cell is an unvisited safe cell. Staying in place."
                    )
                break
            for dr, dc in directions:
                nr, nc = r0 + dr, c0 + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    if (nr, nc) in dangerous:
                        continue
                    if (nr, nc) not in explored:
                        queue.append(((nr, nc), path + [(nr, nc)]))

    if best_move is None:
        # If no unvisited safe cell, try risky unknown cells (but not definite pits/wumpus)
        queue = deque()
        queue.append((tuple(agent_pos), []))
        explored = set()
        while queue:
            (r0, c0), path = queue.popleft()
            if (r0, c0) in explored:
                continue
            explored.add((r0, c0))
            if (r0, c0) in risky and visible_grid[r0][c0] == "unknown":
                if path:
                    best_move = list(path[0])
                    best_reason = (
                        f"No unvisited safe cells found. "
                        f"Found a path to a risky cell at {path[-1]}, which is not definitely dangerous but may have some risk. "
                        f"The first step towards it is {path[0]}."
                    )
                else:
                    best_move = [r0, c0]
                    best_reason = (
                        f"No unvisited safe cells found. Current cell is a risky cell."
                    )
                break
            for dr, dc in directions:
                nr, nc = r0 + dr, c0 + dc
                if 0 <= nr < rows and 0 <= nc < cols:
                    if (nr, nc) in dangerous:
                        continue
                    if (nr, nc) not in explored:
                        queue.append(((nr, nc), path + [(nr, nc)]))

    if best_move is None:
        best_move = list(agent_pos)
        best_reason = (
            f"No safe or risky moves found. Staying in place."
        )

    return best_move, best_reason

def label_from_pos(pos, cols=5):
    col_labels = ['A', 'B', 'C', 'D', 'E'][:cols]
    row, col = pos
    return f"{col_labels[col]}{row+1}"

def build_response(move_reason=""):
    # Add persistent percepts for all visited cells
    cell_percepts = {
        f"{r},{c}": percepts
        for (r, c), percepts in world.visited_percepts.items()
    }
    return {
        "visible_grid": world.get_visible_grid(),
        "agent_pos": agent.pos,
        "board_labels": {
            "cols": ['A', 'B', 'C', 'D', 'E'][:world.size],
            "rows": list(range(1, world.size + 1))
        },
        "percepts": world.get_percepts(agent.pos),
        "game_over": agent.game_over,
        "move_reason": move_reason,
        "move_history": agent.move_history,
        "cell_percepts": cell_percepts  # <-- Add this line
    }

@app.route("/api/init", methods=["GET"])
def init_game():
    world.reset()
    agent.reset()
    
    # Make sure agent and world track the agent position consistently
    world.agent_pos = agent.pos  # or use whichever you have
    
    return jsonify(build_response(move_reason="Game started"))

@app.route("/api/next-move", methods=["POST"])
def next_move():
    if agent.game_over:
        return jsonify(build_response(move_reason="Game already over"))

    # Save current state for best move calculation
    visible_grid = world.get_visible_grid()
    agent_pos = agent.pos.copy()
    cols = world.size

    # Get best move and reason before making the move
    best_move, best_reason = get_best_move_and_reason(visible_grid, agent_pos)
    best_move_label = label_from_pos(best_move, cols)
    best_move_detail = f"Best move at this position: {best_move_label}. Reason: {best_reason}"

    # Call make_move to update the game state internally
    move_result = agent.make_move()  # auto move

    # Try to get move_reason if agent.make_move() returns dict or object with 'move_reason'
    move_reason = ""
    chosen_move_label = label_from_pos(agent.pos, cols)
    if isinstance(move_result, dict):
        move_reason = move_result.get("move_reason", "")
    elif hasattr(move_result, "move_reason"):
        move_reason = getattr(move_result, "move_reason", "")
    else:
        move_reason = "Agent performed auto move"

    # Compare chosen move to best move
    if agent.pos == best_move:
        explanation = (
            f"Auto-move chosen: {chosen_move_label}. This is the best move according to the agent's knowledge. "
            f"Reason for best move: {best_reason}"
        )
    else:
        explanation = (
            f"Auto-move chosen: {chosen_move_label}. This is NOT the best move according to the agent's knowledge. "
            f"The best move would have been {best_move_label}. "
            f"Reason for best move: {best_reason}. "
            f"Reason for chosen move: {move_reason}"
        )

    return jsonify(build_response(move_reason=explanation))

@app.route("/api/manual-move", methods=["POST"])
def manual_move():
    data = request.get_json()
    move = data.get("move")

    if agent.game_over:
        return jsonify(build_response(move_reason="Game already over"))

    if not move or not isinstance(move, list) or len(move) != 2:
        return jsonify({"error": "Invalid move format"}), 400

    # Save current state for best move calculation
    visible_grid = world.get_visible_grid()
    agent_pos = agent.pos.copy()
    cols = world.size

    # Get best move and reason before making the move
    best_move, best_reason = get_best_move_and_reason(visible_grid, agent_pos)
    best_move_label = label_from_pos(best_move, cols)
    best_move_detail = f"Best move at this position: {best_move_label}. Reason: {best_reason}"

    # Call make_move with manual_pos to update game state
    move_result = agent.make_move(manual_pos=tuple(move))

    move_reason = ""
    chosen_move_label = label_from_pos(move, cols)
    if isinstance(move_result, dict):
        move_reason = move_result.get("move_reason", "")
    elif hasattr(move_result, "move_reason"):
        move_reason = getattr(move_result, "move_reason", "")
    else:
        move_reason = f"Agent manually moved to {move}"

    # Compare chosen move to best move
    if list(move) == best_move:
        explanation = (
            f"Manual move chosen: {chosen_move_label}. This is the best move according to the agent's knowledge. "
            f"Reason for best move: {best_reason}"
        )
    else:
        explanation = (
            f"Manual move chosen: {chosen_move_label}. This is NOT the best move according to the agent's knowledge. "
            f"The best move would have been {best_move_label}. "
            f"Reason for best move: {best_reason}. "
            f"Reason for chosen move: {move_reason}"
        )

    return jsonify(build_response(move_reason=explanation))

@app.route('/api/preview-best-move', methods=['POST'])
def preview_best_move():
    data = request.get_json()
    visible_grid = data.get('visibleGrid')
    agent_pos = data.get('agentPos')

    if not visible_grid or not agent_pos:
        return jsonify({"error": "Missing visibleGrid or agentPos"}), 400

    best_move, best_reason = get_best_move_and_reason(visible_grid, agent_pos)
    return jsonify({"best_move": best_move, "reason": best_reason})

if __name__ == "__main__":
    app.run(debug=True)

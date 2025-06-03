def get_best_move(visible_grid, agent_pos):
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
    # The following block is only relevant if you want to use move_history for best move logic
    # Remove or adapt as needed if you want to keep logic.py independent of agent state

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
                return list(prev_cell)
        else:
            for nbr in visited_neighbors:
                if prev_cell is None or nbr != prev_cell:
                    return list(nbr)

    # BFS to find shortest path to an unvisited safe cell
    queue = deque()
    queue.append((tuple(agent_pos), []))
    explored = set()
    while queue:
        (r, c), path = queue.popleft()
        if (r, c) in explored:
            continue
        explored.add((r, c))
        if (r, c) in safe and visible_grid[r][c] == "unknown":
            if path:
                return list(path[0])
            else:
                return [r, c]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if (nr, nc) in dangerous:
                    continue
                if (nr, nc) not in explored:
                    queue.append(((nr, nc), path + [(nr, nc)]))

    # If no unvisited safe cell, try risky unknown cells (but not definite pits/wumpus)
    queue = deque()
    queue.append((tuple(agent_pos), []))
    explored = set()
    while queue:
        (r, c), path = queue.popleft()
        if (r, c) in explored:
            continue
        explored.add((r, c))
        if (r, c) in risky and visible_grid[r][c] == "unknown":
            if path:
                return list(path[0])
            else:
                return [r, c]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if (nr, nc) in dangerous:
                    continue
                if (nr, nc) not in explored:
                    queue.append(((nr, nc), path + [(nr, nc)]))

    return list(agent_pos)

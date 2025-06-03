import random
from flask import current_app
from game.logic import get_best_move

class Agent:
    def __init__(self, world):
        self.world = world
        self.pos = [0, 0]
        self.visited = set()
        self.visited.add(tuple(self.pos))
        self.game_over = False
        self.move_history = []

    def get_percepts(self, pos):
        return self.world.get_percepts(pos)
    
    def reset(self):
        self.pos = [0, 0]
        self.visited = set()
        self.visited.add(tuple(self.pos))
        self.game_over = False
        self.move_history = []
        self.world.agent_pos = self.pos
        self.world.visited = set()
        self.world.visited.add(tuple(self.pos))
        # Sync all agent's visited cells to world's visited_percepts
        self.world.visited_percepts = {}
        for pos in self.visited:
            self.world.visited_percepts[pos] = self.world.get_percepts(pos)

    def _is_adjacent(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        return max(abs(r1 - r2), abs(c1 - c2)) == 1

    def choose_best_move(self):
        r, c = self.pos
        visible_grid = self.world.get_visible_grid()

        directions = [
            (r-1, c), (r+1, c), (r, c-1), (r, c+1),
            (r-1, c-1), (r-1, c+1), (r+1, c-1), (r+1, c+1)
        ]
        valid_moves = [(nr, nc) for nr, nc in directions if 0 <= nr < self.world.size and 0 <= nc < self.world.size]

        unvisited_safe = []
        visited_safe = []

        for nr, nc in valid_moves:
            cell = visible_grid[nr][nc]
            if cell in ["pit", "wumpus"]:
                continue  # dangerous
            if (nr, nc) not in self.visited:
                unvisited_safe.append((nr, nc))
            else:
                visited_safe.append((nr, nc))

        if unvisited_safe:
            reason = f"Chose unvisited safe/unknown square from {unvisited_safe}."
            return random.choice(unvisited_safe), reason
        elif visited_safe:
            reason = f"No new safe squares, revisiting visited {visited_safe}."
            return random.choice(visited_safe), reason
        else:
            return None, "No safe or known options available."

    def make_move(self, manual_pos=None):
        if self.game_over:
            return self._build_response("Game over.")

        if manual_pos:
            # Validate manual move
            if not (0 <= manual_pos[0] < self.world.size and 0 <= manual_pos[1] < self.world.size):
                return self._build_response("Invalid manual move: out of bounds.")
            
            if not self._is_adjacent(self.pos, manual_pos):
                return self._build_response("Invalid manual move: must move to a neighboring cell.")
            
            next_pos = manual_pos
            reason = f"Manual move to {self._pos_to_label(next_pos)}."
        else:
            # Always use the backend's best move logic for auto-move
            visible_grid = self.world.get_visible_grid()
            agent_pos = self.pos
            best_move = get_best_move(visible_grid, agent_pos)
            if not best_move or best_move == list(agent_pos):
                self.game_over = True
                return self._build_response("No safe moves left. Game over.")
            next_pos = tuple(best_move)
            reason = f"Auto-move chosen to {self._pos_to_label(next_pos)}. Reason: Used best move logic from backend."

        self.pos = list(next_pos)
        self.visited.add(tuple(self.pos))
        self.world.agent_pos = self.pos
        self.world.visited.add(tuple(self.pos))

        cell = self.world.grid[self.pos[0]][self.pos[1]]
        percepts = self.world.get_percepts(self.pos)

        if cell == "pit":
            self.game_over = True
            reason += " Fell into a pit. 💀"
        elif cell == "wumpus":
            self.game_over = True
            reason += " Eaten by the Wumpus! 🐉"
        elif cell == "gold":
            self.game_over = True
            reason += " Found the gold! 🏆"

        # Store move label + reason in history for readability
        self.move_history.append((self._pos_to_label(self.pos), reason))

        return self._build_response(reason)

    def _build_response(self, reason):
        # Sync all agent's visited cells to world's visited_percepts
        for pos in self.visited:
            self.world.visited_percepts[pos] = self.world.get_percepts(pos)
        string_cell_percepts = {f"{r},{c}": percepts for (r, c), percepts in self.world.visited_percepts.items()}
        return {
            "visible_grid": self.world.get_visible_grid(),
            "agent_pos": self.pos,
            "percepts": self.world.get_percepts(self.pos),
            "move_reason": reason,
            "game_over": self.game_over,
            "move_history": self.move_history,
            "board_labels": self._generate_board_labels(),
            "cell_percepts": string_cell_percepts
        }

    def _generate_board_labels(self):
        cols = ['A', 'B', 'C', 'D', 'E'][:self.world.size]
        rows = list(range(1, self.world.size + 1))
        return {'cols': cols, 'rows': rows}

    def _pos_to_label(self, pos):
        cols = ['A', 'B', 'C', 'D', 'E'][:self.world.size]
        row_label = str(pos[0] + 1)
        col_label = cols[pos[1]]
        return f"{col_label}{row_label}"

import random

class World:
    def __init__(self, size=5, pit_count=3, wumpus_count=1, gold_count=1):
        self.size = size
        self.pit_count = pit_count
        self.wumpus_count = wumpus_count
        self.gold_count = gold_count
        self.reset()

    def to_dict(self):
        return {
            'size': self.size,
            'wumpus_positions': list(self.wumpus_positions),
            'gold_positions': list(self.gold_positions),
            'agent_position': self.agent_pos,
            'pits': list(self.pits),
        }

    def reset(self):
        self.grid = [["empty" for _ in range(self.size)] for _ in range(self.size)]

        # Place multiple wumpuses
        self.wumpus_positions = set()
        while len(self.wumpus_positions) < self.wumpus_count:
            pos = (random.randint(0, self.size - 1), random.randint(0, self.size - 1))
            if pos != (0, 0) and pos not in self.wumpus_positions:
                self.wumpus_positions.add(pos)
                self.grid[pos[0]][pos[1]] = "wumpus"

        # Place multiple golds
        self.gold_positions = set()
        while len(self.gold_positions) < self.gold_count:
            pos = (random.randint(0, self.size - 1), random.randint(0, self.size - 1))
            if pos != (0, 0) and pos not in self.wumpus_positions and pos not in self.gold_positions:
                self.gold_positions.add(pos)
                self.grid[pos[0]][pos[1]] = "gold"

        # Place multiple pits
        self.pits = set()
        while len(self.pits) < self.pit_count:
            pos = (random.randint(0, self.size - 1), random.randint(0, self.size - 1))
            if pos != (0, 0) and pos not in self.wumpus_positions and pos not in self.gold_positions and pos not in self.pits:
                self.pits.add(pos)
                self.grid[pos[0]][pos[1]] = "pit"

        self.agent_pos = [0, 0]
        self.grid[0][0] = "empty"
        self.visited = set()
        self.visited.add((0, 0))
        self.visited_percepts = {}
        self.visited_percepts[(0, 0)] = self.get_percepts((0, 0))

    def place_entities(self, entity, count):
        placed = 0
        while placed < count:
            r = random.randint(0, self.size - 1)
            c = random.randint(0, self.size - 1)
            # Avoid start cell and no overlapping entities
            if (r, c) == (0, 0):
                continue
            if self.grid[r][c] == "empty":
                self.grid[r][c] = entity
                placed += 1

    def in_bounds(self, r, c):
        return 0 <= r < self.size and 0 <= c < self.size

    def get_percepts(self, pos):
        """
        Return list of percepts at given position:
        - 'breeze' if adjacent to pit
        - 'stench' if adjacent to wumpus
        """
        r, c = pos
        percepts = []

        # Adjacent (including diagonals) cells to check
        neighbors = [
            (r-1, c), (r+1, c), (r, c-1), (r, c+1),
            (r-1, c-1), (r-1, c+1), (r+1, c-1), (r+1, c+1)
        ]

        for nr, nc in neighbors:
            if self.in_bounds(nr, nc):
                if self.grid[nr][nc] == "pit" and "breeze" not in percepts:
                    percepts.append("breeze")
                if self.grid[nr][nc] == "wumpus" and "stench" not in percepts:
                    percepts.append("stench")

        # Include percepts of the current cell
        if self.grid[r][c] == "pit" and "breeze" not in percepts:
            percepts.append("breeze")
        if self.grid[r][c] == "wumpus" and "stench" not in percepts:
            percepts.append("stench")

        return percepts

    def get_visible_grid(self):
        """
        Returns a grid for display where:
        - visited cells show actual content or perceptual info (breeze, stench)
        - others show 'unknown'
        """
        visible_grid = []
        for r in range(self.size):
            row = []
            for c in range(self.size):
                if (r, c) in self.visited:
                    # Prioritize actual content over percepts if available
                    if self.grid[r][c] != "empty":
                        row.append(self.grid[r][c])
                    else:
                        percepts = self.visited_percepts.get((r, c), [])
                        if percepts:
                            row.append("+".join(percepts))  # e.g., "breeze+stench"
                        else:
                            row.append("empty")  # or some other default
                else:
                    row.append("unknown")
            visible_grid.append(row)
        return visible_grid

    def move_agent(self, new_pos):
        """
        Move agent to new_pos, update visited cells.
        Returns:
          - cell content at new_pos
          - percepts at new_pos
        """
        r, c = new_pos
        if not self.in_bounds(r, c):
            raise ValueError("Move out of bounds")

        self.agent_pos = [r, c]
        self.visited.add((r, c))

        cell = self.grid[r][c]
        percepts = self.get_percepts((r, c))

        # Always update visited_percepts for every visited cell
        self.visited_percepts[(r, c)] = percepts

        return cell, percepts

    def is_safe(self, pos):
        """
        Returns True if cell at pos is safe (no pit or wumpus)
        """
        r, c = pos
        if not self.in_bounds(r, c):
            return False
        cell = self.grid[r][c]
        return cell not in ("pit", "wumpus")

    def print_debug(self):
        """
        For console debug: prints entire grid with entity chars
        """
        symbol_map = {
            "empty": ".",
            "pit": "P",
            "wumpus": "W",
            "gold": "G"
        }
        for r in range(self.size):
            row_str = ""
            for c in range(self.size):
                if (r, c) == tuple(self.agent_pos):
                    row_str += "A "
                else:
                    row_str += symbol_map.get(self.grid[r][c], "?") + " "
            print(row_str)

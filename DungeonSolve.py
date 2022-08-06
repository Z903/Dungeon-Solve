import collections, copy, itertools, json

class State():
    def __init__(self, rows, cols, mons, trea, **kwarg):
        self.rows = rows
        self.cols = cols
        self.board = list()
        self.treaure = trea
        self.monsters = mons
        
        # The number of cols is the width
        self.width = len(self.cols)
        self.height = len(self.rows)

        for _ in range(2): self.board.append(["X"] * (self.width + 4))
        for _ in range(self.height): self.board.append(["X","X"] + ["."] * self.width + ["X","X"])
        for _ in range(2): self.board.append(["X"] * (self.width + 4))

        for m in mons:
            self.board[m[1] + 2][m[0] + 2] = "O"
        for t in trea:
            self.board[t[1] + 2][t[0] + 2] = "T"

    def clone(self):
        c = copy.copy(self)
        c.board = copy.deepcopy(self.board)
        return c

    def transposed(self):
        return list(map(list, zip(*self.board)))

    def show(self):
        print("." + "".join(str(x) for x in self.cols))
        for r in range(self.height):
            print("{}{}".format(self.rows[r], "".join(str(x) for x in self.board[r + 2][2:-2])))
        print("")

    def check_treasure_early(self, treaure):
        x = treaure[0] + 2
        y = treaure[1] + 2

        def a(x,y):
            if self.board[y - 1][x - 1] not in (".", "T"): return False
            if self.board[y - 0][x - 1] not in (".", "T"): return False
            if self.board[y + 1][x - 1] not in (".", "T"): return False
            if self.board[y - 1][x - 0] not in (".", "T"): return False
            if self.board[y - 0][x - 0] not in (".", "T"): return False
            if self.board[y + 1][x - 0] not in (".", "T"): return False
            if self.board[y - 1][x + 1] not in (".", "T"): return False
            if self.board[y - 0][x + 1] not in (".", "T"): return False
            if self.board[y + 1][x + 1] not in (".", "T"): return False
            return True
    
        result = set()
        for (ox,oy) in [(-1,-1), (-1,0), (-1,1),(0,-1), (0,0), (0,1),(1,-1), (1,0), (1,1)]:
            if a(x + ox, y + oy):
                result.add((x + ox, y + oy))
        return result

    def count_hallways(self):
        # Make a set of all empty spaces
        hall_positions = set()
        for row in range(2, self.width + 2):
            for col in range(2, self.height + 2):
                if self.board[row][col] == ".":
                    hall_positions.add((row, col))

        # Remove all connected hallway tiles from hall_positions recursively
        def removeIsland(pos):
            if pos in hall_positions:
                hall_positions.remove(pos)
                for neighbourPos in ((-1, 0),(1, 0),(0, -1),(0, 1)):
                    removeIsland((pos[0] + neighbourPos[0], pos[1] + neighbourPos[1]))
        
        # Count the number of seperated hallways
        result = 0
        while hall_positions:
            result += 1
            removeIsland(next(iter(hall_positions)))
        return result

    def check(self, row):
        """
        Check from 0 up to `row`
        """
        solved = True
  
        # Check each row
        for i in range(self.height):
            temp = sum(1 for x in self.board[i + 2] if x == "X") - 4
            if temp > self.rows[i]: return False
            if temp < self.rows[i]: solved = False
   
        # Check each col
        bt = self.transposed()
        for i in range(self.width):
            temp = sum(1 for x in bt[i + 2] if x == "X") - 4
            if temp > self.cols[i]: return False
            if temp < self.cols[i]: solved = False
    
        # Dead end check
        for y in range(2, row + 3):
            for x in range(2, self.width + 2):
                if self.board[y][x] == ".":
                    t = 0
                    if self.board[y - 1][x] == "X": t += 1
                    if self.board[y + 1][x] == "X": t += 1
                    if self.board[y][x - 1] == "X": t += 1
                    if self.board[y][x + 1] == "X": t += 1
                    if (t >= 3):
                        return False

        # Early treasure check
        treasures = list()
        for t in self.treaure:
            treasure = self.check_treasure_early(t)
            if treasure == set():
                return False
            treasures.append(treasure)

        treasure_tiles = set()
        for t in treasures:
            treasure_tiles = treasure_tiles.union(t)

        # Check for 2x2
        for y in range(3, row + 3):
            for x in range(3, self.width + 2):
                t = 0
                if self.board[y - 1][x - 0] == ".": t += 1
                if self.board[y - 1][x - 1] == ".": t += 1
                if self.board[y - 0][x - 0] == ".": t += 1
                if self.board[y - 0][x - 1] == ".": t += 1
                # exempt 2x2 areas in the treasure room
                if t == 4 and len(treasure_tiles.intersection({(x,y), (x-1,y), (x,y-1), (x-1,y-1)})) == 0:
                    return False

        # Check that monsters have an exit
        for m in self.monsters:
            x = m[0] + 2
            y = m[1] + 2
            if not any(self.board[y + ox][x - oy] == "." for ox,oy in [(-1,0), (1,0), (0,-1), (0,1)]):
                return False

        # If the board is partially solved return None
        if solved == False:
            return None

        # Checks below here requre the board to be complete

        # Check that monsters have 3 walls
        for m in self.monsters:
            x = m[0] + 2
            y = m[1] + 2
            if sum(self.board[y + ox][x - oy] == "X" for ox,oy in [(-1,0), (1,0), (0,-1), (0,1)]) != 3:
                return False

        # Check treasure room walls/exit
        for treasure in treasures:
            if len(treasure) != 1:
                return False
            t = next(iter(treasure))
            x = t[0]
            y = t[1]

            inner = collections.Counter(self.board[y + oy][x + ox] for ox,oy in [(-1,-1),(0,-1),(1,-1),(-1,0),(0,0),(1,0),(-1,1),(0,1),(1,1)])
            walls = collections.Counter(self.board[y + oy][x + ox] for ox,oy in [(-1,-2),(0,-2),(1,-2),(2,-1),(2,0),(2,1),(1,2),(0,2),(-1,2),(-2,1),(-2,0),(-2,-1)])

            if inner["."] != 8 or inner["T"] != 1 or walls["X"] != 11 or walls["."] != 1:
                return False

        # Check that all halls connect
        if self.count_hallways() != 1:
            return False

        # We have found a solution
        return True

    def solve(self, row = 0):
        if row >= self.height: return

        y = row + 2
        t = self.transposed()[2:-2]

        # Count number of walls in each col and if we could place a wall there record the index
        open_spaces = list(x for x,w,c in zip(
            range(2, self.width + 2),
            (sum(1 for w in z[2:-2] if w == "X") for z in t),
            self.cols
        ) if w < c and self.board[y][x] == ".")

        # Exit early if we would not be able to insert the required number of walls in this row
        if len(open_spaces) < self.rows[row]:
            return

        for s in itertools.combinations(open_spaces, self.rows[row]):

            # Set the selected open spaces to X
            for x in s:
                self.board[y][x] = "X"

            # Check board state
            ok = self.check(row)

            if ok == True:
                # We found a solution yield a clone
                yield self.clone()

            # Recurse to the next line
            if ok == None:
                for x in self.solve(row + 1):
                    # Yield solutions out
                    yield x
                    
            # Reset the selected open spaces to "."
            for x in s:
                self.board[y][x] = "."

puzzles = {}
with open("puzzles.json") as f:
    puzzles = json.load(f)["puzzles"]
for p in puzzles.values():
    print(p["name"] + "\n")
    state = State(**p)
    state.show()
    for solution in state.solve():
        solution.show()

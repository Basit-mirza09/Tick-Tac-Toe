"""
Tic-Tac-Toe with an unbeatable AI  (DSA Project)

Data structures used
--------------------
1. NON-LINEAR (custom-built): GameNode  -> game tree (each node = board state)
2. LINEAR     (custom-built): Stack     -> linked-list based stack for undo history
3. BUILT-IN   (Python)      : tuple     -> immutable board (also usable as dict key)
                              dict      -> cache (memoization) of evaluated positions

Run:   python tictactoe_ai.py          (play the game)
       python tictactoe_ai.py --test   (prove the AI never loses)
"""

import sys

EMPTY = " "
WIN_LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),   # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),   # columns
    (0, 4, 8), (2, 4, 6),              # diagonals
)


# ======================================================================
# LINEAR DATA STRUCTURE  ->  custom Stack (built with a linked list)
# ======================================================================
class StackNode:
    def __init__(self, data, next_node=None):
        self.data = data
        self.next = next_node


class Stack:
    """LIFO stack implemented from scratch using a singly linked list."""

    def __init__(self):
        self.top = None
        self.size = 0

    def push(self, data):
        self.top = StackNode(data, self.top)
        self.size += 1

    def pop(self):
        if self.is_empty():
            raise IndexError("pop from empty stack")
        data = self.top.data
        self.top = self.top.next
        self.size -= 1
        return data

    def peek(self):
        if self.is_empty():
            raise IndexError("peek from empty stack")
        return self.top.data

    def is_empty(self):
        return self.top is None

    def clear(self):
        self.top = None
        self.size = 0

    def __len__(self):
        return self.size

    def __iter__(self):
        current = self.top
        while current:
            yield current.data
            current = current.next


# ======================================================================
# BOARD HELPERS  (board is a TUPLE of 9 strings -> immutable)
# ======================================================================
def new_board():
    return (EMPTY,) * 9


def make_move(board, pos, player):
    """Return a NEW board (tuples cannot be changed in place)."""
    return board[:pos] + (player,) + board[pos + 1:]


def empty_cells(board):
    return [i for i, c in enumerate(board) if c == EMPTY]


def winner(board):
    for a, b, c in WIN_LINES:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return board[a]
    return None


def is_full(board):
    return EMPTY not in board


def other(player):
    return "O" if player == "X" else "X"


def print_board(board):
    def cell(i):
        return board[i] if board[i] != EMPTY else str(i + 1)

    print()
    for r in range(3):
        print(f" {cell(r*3)} | {cell(r*3+1)} | {cell(r*3+2)} ")
        if r < 2:
            print("---+---+---")
    print()


# ======================================================================
# NON-LINEAR DATA STRUCTURE  ->  custom Game Tree
# ======================================================================
class GameNode:
    """
    One node of the game tree.
      board    : the board state (tuple)
      player   : whose turn it is at this node
      move     : the cell (0-8) that was played to reach this node
      children : list of GameNode (one per possible next move)
      score    : minimax value of this node
    """

    __slots__ = ("board", "player", "move", "children", "score")

    def __init__(self, board, player, move=None):
        self.board = board
        self.player = player
        self.move = move
        self.children = []
        self.score = None

    def expand(self):
        """Create a child node for every empty cell."""
        for pos in empty_cells(self.board):
            child_board = make_move(self.board, pos, self.player)
            self.children.append(GameNode(child_board, other(self.player), pos))
        return self.children


# ======================================================================
# AI  ->  Minimax on the game tree + dict cache (memoization)
# ======================================================================
class MinimaxAI:
    def __init__(self, symbol):
        self.symbol = symbol                       # AI's letter
        self.cache = {}                            # dict: (board, player) -> score
        self.stats = {"nodes": 0, "cache_hits": 0}
        self.last_scores = {}                      # dict: cell -> score (for the UI)

    def _terminal_score(self, board):
        """Score for finished games. Faster wins / slower losses score better."""
        moves_played = 9 - len(empty_cells(board))
        w = winner(board)
        if w == self.symbol:
            return 10 - moves_played
        if w is not None:
            return -(10 - moves_played)
        return 0                                   # draw

    def minimax(self, node):
        key = (node.board, node.player)            # tuple used as dict key
        if key in self.cache:                      # already solved -> reuse
            self.stats["cache_hits"] += 1
            node.score = self.cache[key]
            return node.score

        self.stats["nodes"] += 1

        if winner(node.board) or is_full(node.board):
            node.score = self._terminal_score(node.board)
        else:
            node.expand()                          # grow the tree
            scores = [self.minimax(child) for child in node.children]
            node.score = max(scores) if node.player == self.symbol else min(scores)

        self.cache[key] = node.score
        return node.score

    def best_move(self, board):
        """Build the tree from the current board and return the best cell."""
        root = GameNode(board, self.symbol)
        root.expand()                              # root is always expanded
        for child in root.children:
            self.minimax(child)                    # cached children return fast
        self.last_scores = {c.move: c.score for c in root.children}
        best_child = max(root.children, key=lambda c: c.score)
        return best_child.move


# ======================================================================
# GAME LOOP
# ======================================================================
class Game:
    def __init__(self):
        self.board = new_board()
        self.history = Stack()                     # entries: (board_before, mover)
        self.human = "X"
        self.ai_symbol = "O"
        self.ai = MinimaxAI(self.ai_symbol)
        self.turn = "X"

    # ---------- setup ----------
    def choose_side(self):
        while True:
            ans = input("Do you want to go first (X)? [y/n]: ").strip().lower()
            if ans in ("y", "yes"):
                self.human, self.ai_symbol = "X", "O"
                break
            if ans in ("n", "no"):
                self.human, self.ai_symbol = "O", "X"
                break
            print("Please type y or n.")
        self.ai = MinimaxAI(self.ai_symbol)
        self.board = new_board()
        self.history.clear()
        self.turn = "X"

    # ---------- moves ----------
    def play(self, pos, mover):
        self.history.push((self.board, mover))     # save state BEFORE the move
        self.board = make_move(self.board, pos, mover)
        self.turn = other(mover)

    def human_moves_made(self):
        return any(mover == self.human for _, mover in self.history)

    def undo(self):
        """Undo the human's last move and everything played after it."""
        if not self.human_moves_made():
            print("Nothing to undo yet.")
            return False
        while not self.history.is_empty():
            board_before, mover = self.history.pop()
            self.board = board_before
            self.turn = mover
            if mover == self.human:
                break
        print("Last move undone.")
        return True

    def ai_turn(self):
        pos = self.ai.best_move(self.board)
        self.play(pos, self.ai_symbol)
        print(f"AI ({self.ai_symbol}) plays at {pos + 1}   "
              f"[tree nodes: {self.ai.stats['nodes']}, "
              f"cache hits: {self.ai.stats['cache_hits']}]")

    def human_turn(self):
        """Returns True if a move was played, False if undo/other command."""
        while True:
            raw = input(f"Your move ({self.human}) - cell 1-9, 'u' = undo, 'q' = quit: ").strip().lower()
            if raw == "q":
                print("Bye!")
                sys.exit(0)
            if raw == "u":
                self.undo()
                return False
            if not raw.isdigit() or not 1 <= int(raw) <= 9:
                print("Enter a number from 1 to 9.")
                continue
            pos = int(raw) - 1
            if self.board[pos] != EMPTY:
                print("That cell is already taken.")
                continue
            self.play(pos, self.human)
            return True

    # ---------- result ----------
    def game_over(self):
        w = winner(self.board)
        if w:
            print_board(self.board)
            print("You win!" if w == self.human else "AI wins!")
            return True
        if is_full(self.board):
            print_board(self.board)
            print("It's a draw!")
            return True
        return False

    def run(self):
        print("=" * 40)
        print("  TIC-TAC-TOE  vs  MINIMAX AI")
        print("=" * 40)
        self.choose_side()
        while True:
            print_board(self.board)
            if self.turn == self.ai_symbol:
                self.ai_turn()
            else:
                self.human_turn()
            if self.game_over():
                again = input("Play again? [y/n]: ").strip().lower()
                if again in ("y", "yes"):
                    self.choose_side()
                else:
                    print("Thanks for playing!")
                    return


# ======================================================================
# SELF TEST  ->  proves the AI can never lose
# ======================================================================
def exhaustive_test():
    total_games = 0
    for ai_symbol in ("X", "O"):
        human_symbol = other(ai_symbol)
        ai = MinimaxAI(ai_symbol)
        results = {"ai_wins": 0, "draws": 0, "human_wins": 0}

        def explore(board, player):
            if winner(board) or is_full(board):
                w = winner(board)
                if w == ai_symbol:
                    results["ai_wins"] += 1
                elif w == human_symbol:
                    results["human_wins"] += 1
                else:
                    results["draws"] += 1
                return
            if player == ai_symbol:
                explore(make_move(board, ai.best_move(board), player), other(player))
            else:
                for pos in empty_cells(board):          # try EVERY human move
                    explore(make_move(board, pos, player), other(player))

        explore(new_board(), "X")
        total = sum(results.values())
        total_games += total
        print(f"AI plays {ai_symbol}: {total} games -> {results}")
        assert results["human_wins"] == 0, "AI lost a game!"

    # Stack test
    s = Stack()
    for i in range(5):
        s.push(i)
    assert s.pop() == 4 and s.peek() == 3 and len(s) == 4
    s.clear()
    assert s.is_empty()

    print(f"\nAll tests passed. {total_games} games checked, human never won.")


if __name__ == "__main__":
    if "--test" in sys.argv:
        exhaustive_test()
    else:
        Game().run()

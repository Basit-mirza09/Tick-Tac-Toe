"""
Tic-Tac-Toe AI  -  Streamlit UI
Run:  streamlit run app.py

Game logic and data structures live in tictactoe_ai.py:
  * GameNode  (custom game tree)      * Stack (custom linked-list stack)
  * tuple board + dict cache (Python built-ins)
"""

import random

import streamlit as st

from tictactoe_ai import (
    EMPTY, WIN_LINES, MinimaxAI, Stack,
    empty_cells, is_full, make_move, new_board, other, winner,
)

st.set_page_config(page_title="Tic-Tac-Toe AI", page_icon="🎮", layout="centered")

# ----------------------------------------------------------------------
# STYLING
# ----------------------------------------------------------------------
CSS = """
<style>
#MainMenu, footer, header [data-testid="stToolbar"] {visibility: hidden;}
.stApp {background: radial-gradient(circle at 20% 0%, #1b2440 0%, #0b1020 55%);}
.block-container {padding-top: 2rem; max-width: 640px;}

.title {text-align:center; font-size:2.4rem; font-weight:800; letter-spacing:.5px;
        background: linear-gradient(90deg,#4cc9f0,#f72585); -webkit-background-clip:text;
        -webkit-text-fill-color:transparent; margin-bottom:0;}
.subtitle {text-align:center; color:#8d99ae; margin-bottom:1.2rem; font-size:.95rem;}

.score-row {display:flex; gap:12px; margin-bottom:14px;}
.score {flex:1; text-align:center; padding:10px 6px; border-radius:14px;
        background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.08);}
.score .n {font-size:1.7rem; font-weight:800; color:#fff; line-height:1.1;}
.score .l {font-size:.75rem; color:#8d99ae; text-transform:uppercase; letter-spacing:1px;}

.status {text-align:center; padding:12px; border-radius:14px; font-weight:700;
         font-size:1.05rem; margin-bottom:16px; border:1px solid rgba(255,255,255,.1);
         background:rgba(255,255,255,.05); color:#e5e9f0;}
.status.win  {background:rgba(46,204,113,.15); border-color:#2ecc71; color:#7dffb0;}
.status.lose {background:rgba(247,37,133,.15); border-color:#f72585; color:#ff8fc0;}
.status.draw {background:rgba(255,200,87,.13); border-color:#ffc857; color:#ffd98a;}

/* keep the 3x3 grid on mobile */
.st-key-board [data-testid="stHorizontalBlock"] {flex-wrap: nowrap !important; gap: 10px !important;}
.st-key-board [data-testid="stColumn"] {min-width: 0 !important; flex: 1 1 0 !important;}

/* board cells */
div[class*="st-key-cell_"] button {
    width:100%; aspect-ratio:1/1; height:auto; min-height:84px; border-radius:18px;
    background:linear-gradient(145deg,#18213b,#101730); border:2px solid #2a3a63;
    box-shadow:0 6px 18px rgba(0,0,0,.35); transition:all .15s ease; opacity:1 !important;
}
div[class*="st-key-cell_"] button p {font-size:3.2rem; font-weight:900; line-height:1; margin:0;}
div[class*="st-key-cell_"][class*="_E"] button:not(:disabled):hover {
    border-color:#4cc9f0; transform:translateY(-3px); box-shadow:0 10px 24px rgba(76,201,240,.25);}
div[class*="st-key-cell_"][class*="_E"] button:disabled {cursor:default;}
div[class*="st-key-cell_"][class*="_X"] button,
div[class*="st-key-cell_"][class*="_X"] button p {color:#4cc9f0 !important; text-shadow:0 0 14px rgba(76,201,240,.65);}
div[class*="st-key-cell_"][class*="_O"] button,
div[class*="st-key-cell_"][class*="_O"] button p {color:#f72585 !important; text-shadow:0 0 14px rgba(247,37,133,.65);}
div[class*="st-key-cell_"][class*="_win"] button {
    border-color:#ffc857 !important; background:linear-gradient(145deg,#3a3010,#241d08) !important;
    box-shadow:0 0 22px rgba(255,200,87,.45) !important;}

/* action buttons */
div[class*="st-key-act_"] button {border-radius:12px; font-weight:700; width:100%;}

.ds-card {padding:12px 14px; border-radius:12px; background:rgba(255,255,255,.05);
          border:1px solid rgba(255,255,255,.08); margin-bottom:10px; color:#d7dce6; font-size:.92rem;}
.ds-card b {color:#fff;}
.tag {display:inline-block; padding:2px 8px; border-radius:20px; font-size:.7rem; font-weight:700;
      margin-right:6px; background:#4cc9f0; color:#08111f;}
.tag.lin {background:#ffc857;} .tag.bi {background:#7dffb0;}
table.scores {border-collapse:collapse; margin:6px auto;}
table.scores td {width:64px; height:52px; text-align:center; border:1px solid rgba(255,255,255,.15);
                 color:#e5e9f0; font-weight:700; border-radius:6px;}
table.scores td.best {background:rgba(46,204,113,.25); color:#7dffb0;}
table.scores td.used {color:#6b7794; background:rgba(255,255,255,.04);}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ----------------------------------------------------------------------
# GAME STATE (kept in st.session_state)
# ----------------------------------------------------------------------
def start_game(human_symbol="X", difficulty="Hard"):
    s = st.session_state
    s.human = human_symbol
    s.ai_symbol = other(human_symbol)
    s.difficulty = difficulty
    s.ai = MinimaxAI(s.ai_symbol)              # fresh AI (fresh dict cache + tree stats)
    s.board = new_board()                      # tuple
    s.history = Stack()                        # custom linked-list stack
    s.turn = "X"
    s.over = False
    s.result = None                            # "win" | "lose" | "draw"
    s.last_ai_move = None
    s.used_minimax = False
    if s.ai_symbol == "X":                     # AI plays first
        ai_move()


def init_state():
    s = st.session_state
    if "board" not in s:
        s.scores = {"win": 0, "draw": 0, "lose": 0}
        s.side_choice = "X (go first)"
        s.diff_choice = "Hard"
        start_game("X", "Hard")


def play(pos, mover):
    s = st.session_state
    s.history.push((s.board, mover, pos))      # save state BEFORE the move
    s.board = make_move(s.board, pos, mover)
    s.turn = other(mover)


def check_finished():
    s = st.session_state
    w = winner(s.board)
    if w or is_full(s.board):
        s.over = True
        s.result = "draw" if not w else ("win" if w == s.human else "lose")
        s.scores[s.result] += 1


def ai_move():
    s = st.session_state
    empties = empty_cells(s.board)
    random_chance = {"Easy": 1.0, "Medium": 0.4, "Hard": 0.0}[s.difficulty]
    if random.random() < random_chance:
        pos, s.used_minimax = random.choice(empties), False
        s.ai.last_scores = {}
    else:
        pos, s.used_minimax = s.ai.best_move(s.board), True
    s.last_ai_move = pos
    play(pos, s.ai_symbol)


def click_cell(i):
    s = st.session_state
    if s.over or s.turn != s.human or s.board[i] != EMPTY:
        return
    play(i, s.human)
    check_finished()
    if not s.over:
        ai_move()
        check_finished()


def undo():
    """Pop the stack until the human's last move has been taken back."""
    s = st.session_state
    if s.over or not any(m == s.human for _, m, _ in s.history):
        return
    while not s.history.is_empty():
        board_before, mover, _ = s.history.pop()
        s.board, s.turn = board_before, mover
        if mover == s.human:
            break
    s.last_ai_move = None
    s.ai.last_scores = {}


def new_game():
    s = st.session_state
    start_game("X" if s.side_choice.startswith("X") else "O", s.diff_choice)


def reset_scores():
    st.session_state.scores = {"win": 0, "draw": 0, "lose": 0}


def winning_line():
    b = st.session_state.board
    for a, c, d in WIN_LINES:
        if b[a] != EMPTY and b[a] == b[c] == b[d]:
            return {a, c, d}
    return set()


# ----------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------
init_state()
S = st.session_state

with st.sidebar:
    st.header("⚙️ Settings")
    st.radio("You play as", ["X (go first)", "O (go second)"], key="side_choice")
    st.select_slider("AI difficulty", ["Easy", "Medium", "Hard"], key="diff_choice")
    st.caption("Settings apply when you press **New game**.")
    st.button("🔄 New game", on_click=new_game, use_container_width=True, type="primary")
    st.button("🧹 Reset scoreboard", on_click=reset_scores, use_container_width=True)
    st.divider()
    st.caption("DSA Project  •  Minimax AI\n\nCustom Tree + Custom Stack + tuple/dict")

st.markdown('<div class="title">TIC-TAC-TOE AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Can you beat the minimax algorithm?</div>', unsafe_allow_html=True)

tab_game, tab_ds = st.tabs(["🎮 Play", "🧠 Under the hood"])

# ---------------------------- PLAY TAB --------------------------------
with tab_game:
    sc = S.scores
    st.markdown(
        f"""<div class="score-row">
        <div class="score"><div class="n">{sc['win']}</div><div class="l">You ({S.human})</div></div>
        <div class="score"><div class="n">{sc['draw']}</div><div class="l">Draws</div></div>
        <div class="score"><div class="n">{sc['lose']}</div><div class="l">AI ({S.ai_symbol})</div></div>
        </div>""",
        unsafe_allow_html=True,
    )

    if S.over:
        msg = {"win": ("🎉 You win!", "win"), "lose": ("🤖 AI wins!", "lose"),
               "draw": ("🤝 It's a draw!", "draw")}[S.result]
        st.markdown(f'<div class="status {msg[1]}">{msg[0]}</div>', unsafe_allow_html=True)
    else:
        extra = f"  •  AI played cell {S.last_ai_move + 1}" if S.last_ai_move is not None else ""
        st.markdown(f'<div class="status">Your turn ({S.human}){extra}</div>', unsafe_allow_html=True)

    win_cells = winning_line()
    with st.container(key="board"):
        for r in range(3):
            cols = st.columns(3)
            for c in range(3):
                i = r * 3 + c
                sym = S.board[i]
                tag = sym if sym != EMPTY else "E"
                key = f"cell_{i}_{tag}" + ("_win" if i in win_cells else "")
                cols[c].button(
                    sym if sym != EMPTY else "\u00a0",
                    key=key,
                    on_click=click_cell,
                    args=(i,),
                    disabled=(sym != EMPTY or S.over or S.turn != S.human),
                    use_container_width=True,
                )

    st.write("")
    b1, b2 = st.columns(2)
    with b1:
        st.button("↩️ Undo move", key="act_undo", on_click=undo, use_container_width=True,
                  disabled=S.over or not any(m == S.human for _, m, _ in S.history))
    with b2:
        st.button("🔄 New game", key="act_new", on_click=new_game, use_container_width=True)

# ------------------------- UNDER THE HOOD TAB -------------------------
with tab_ds:
    st.markdown(
        """
        <div class="ds-card"><span class="tag">Non-linear</span><b>Game tree</b> (custom <code>GameNode</code> class).
        Every node is a board state; its children are all possible next moves. Minimax walks this tree.</div>
        <div class="ds-card"><span class="tag lin">Linear</span><b>Stack</b> (custom, linked-list based).
        Every move is pushed; <i>Undo</i> pops it (LIFO).</div>
        <div class="ds-card"><span class="tag bi">Built-in</span><b>tuple</b> = immutable board &nbsp;|&nbsp;
        <b>dict</b> = cache of already-solved positions (memoization).</div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("Live statistics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Stack size", len(S.history))
    m2.metric("Tree nodes", S.ai.stats["nodes"])
    m3.metric("Cache hits", S.ai.stats["cache_hits"])
    m4.metric("Dict entries", len(S.ai.cache))

    st.subheader("AI's last decision")
    scores = S.ai.last_scores
    if scores and S.used_minimax:
        best = max(scores.values())
        cells = ""
        for r in range(3):
            cells += "<tr>"
            for c in range(3):
                i = r * 3 + c
                if i in scores:
                    cls = "best" if scores[i] == best else ""
                    cells += f'<td class="{cls}">{scores[i]:+d}</td>'
                else:
                    cells += f'<td class="used">{S.board[i].strip() or "·"}</td>'
            cells += "</tr>"
        st.markdown(f'<table class="scores">{cells}</table>', unsafe_allow_html=True)
        st.caption("Minimax score of each cell the AI could play (green = chosen). "
                   "+ = good for AI, − = good for you, 0 = draw.")
    else:
        st.info("No minimax decision yet (AI hasn't moved, you undid, or Easy/Medium picked a random move).")

    st.subheader("Move stack (top → bottom)")
    if S.history.is_empty():
        st.caption("Stack is empty.")
    else:
        rows = [f"`{n}.` **{m}** played cell **{p + 1}**"
                for n, (_, m, p) in enumerate(S.history, start=1)]
        st.markdown("  \n".join(rows))

    with st.expander("How minimax works"):
        st.markdown(
            """
1. Build the game tree from the current board (each child = one possible move).
2. Leaf scores: AI win **+10**, human win **−10**, draw **0** (adjusted by depth so faster wins score higher).
3. On the AI's turn pick the **max** child, on your turn assume you pick the **min** child.
4. Before expanding a node, check the **dict cache**. If this `(board, player)` was already solved, reuse it.
5. The AI plays the child with the best score, so on **Hard** it never loses.
            """
        )

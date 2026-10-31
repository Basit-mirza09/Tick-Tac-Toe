# Tic-Tac-Toe AI (DSA Project)

## Run
    pip install -r requirements.txt
    streamlit run app.py

Terminal version:  python tictactoe_ai.py      Self-test: python tictactoe_ai.py --test

## Data structures
- Non-linear (custom): GameNode -> game tree used by minimax
- Linear (custom): Stack (linked list) -> move history / undo
- Built-in: tuple (board), dict (cache of solved positions)

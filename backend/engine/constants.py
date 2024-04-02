START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
# START_FEN = "1rbqk1nr/2pn1pp1/1p1bp3/p6p/QPP3P1/4pN1B/P2PKP1P/RNB4R w k - 0 11"
MAX_ROWS  = 8
MAX_COLS = 8

MAX_RANK = 8
MAX_FILE = 8
MIN_RANK = 1
MIN_FILE = 1

COLOR = {
    "BLACK": 'black',
    "WHITE": 'white'
}

PAWN_START = {
    "BLACK": 2,
    "WHITE": 7
}

ERROR_NO_POSITIONS_PROVIDED = (False, False, -1)
ERROR_NO_PIECE_TO_MOVE = (False, False, -2)
ERROR_MOVE_NOT_POSSIBLE = (False, False, -3)


SUCCESS_MOVE_MADE_NO_KILL = (True, False, 0)
SUCCESS_MOVE_MADE_WITH_KILL = (True, True, 0)
# START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
# START_FEN = "1rbqk1nr/2pn1pp1/1p1bp3/p6p/QPP3P1/4pN1B/P2PKP1P/RNB4R w k - 0 11"
START_FEN = "8/k7/2K5/1P6/8/8/8/8 b - - 0 40" # STALEMATE
START_FEN = "8/2P5/8/8/5k2/8/6p1/2K5 w - - 0 0" # PAWN PROMOTION
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



NO_MOVE_MADE = 0
MOVE_MADE = 1

NO_KILL = 2
KILL = 3

CHECK = 1
NO_CHECK = 0

CHECKMATE = 2
STALEMATE = 3

ERR_NO_POSITIONS = -1
ERR_NO_PIECE = -2 
ERR_ILLEGAL_MOVE = -3

ERROR_NO_POSITIONS_PROVIDED = (NO_MOVE_MADE, NO_KILL, ERR_NO_POSITIONS)
ERROR_NO_PIECE_TO_MOVE = (NO_MOVE_MADE, NO_KILL, ERR_NO_PIECE)
ERROR_MOVE_NOT_POSSIBLE = (NO_MOVE_MADE, NO_KILL, ERR_ILLEGAL_MOVE)


SUCCESS_MOVE_MADE_NO_KILL_NO_CHECK = (MOVE_MADE, NO_KILL, NO_CHECK)
SUCCESS_MOVE_MADE_NO_KILL_CHECK = (MOVE_MADE, NO_KILL, CHECK)
SUCCESS_MOVE_MADE_NO_KILL_CHECKMATE = (MOVE_MADE, NO_KILL, CHECKMATE)
SUCCESS_MOVE_MADE_NO_KILL_STALEMATE = (MOVE_MADE, NO_KILL, STALEMATE)
SUCCESS_MOVE_MADE_WITH_KILL_NO_CHECK = (MOVE_MADE, KILL, NO_CHECK)
SUCCESS_MOVE_MADE_WITH_KILL_CHECK = (MOVE_MADE, KILL, CHECK)
SUCCESS_MOVE_MADE_WITH_KILL_CHECKMATE = (MOVE_MADE, KILL, CHECKMATE)
SUCCESS_MOVE_MADE_WITH_KILL_STALEMATE = (MOVE_MADE, KILL, STALEMATE)

from abc import ABC
from engine.constants import *
import engine.fen_utils as fen_utils
from engine.piece import Piece
from pprint import pprint
from engine.pieces import *
import copy

class Board(ABC):
    def __init__(self, fen=START_FEN) -> None:
        super().__init__()
        self.fen = fen
        self.board = fen_utils.build_board_from_fen(fen)
        self.dead_pieces = {
            'black': [],
            'white': []
        }
        self.current_player = fen_utils.get_current_player(fen)
        self.halfmoves = fen_utils.get_halfmoves(fen)
        self.fullmoves = fen_utils.get_fullmoves(fen)
        self.castling_avalability = fen_utils.get_castling_avalability(fen)
        
        self.is_stalemate = False
        self.is_checkmate = False 

    def make_fen(self):
        active = "w" if self.current_player == COLOR["WHITE"] else "b"
        castling = ''.join(self.castling_avalability)
        en_passant = '-'

        rows = []
        for row in self.board:
            fen_row = ""
            for piece in row:
                fen_row += piece.get_name() if isinstance(piece, Piece) else 'X'
            rows.append(fen_row)

        fen = '/'.join(rows)

        placements = fen_utils.make_compact(fen)
        all_fen = [placements, active, castling, en_passant, str(self.halfmoves), str(self.fullmoves)]
        self.fen = ' '.join(all_fen)

        return self.fen

    def get_piece(self, piece_coords):
        rank, file = fen_utils.algebraic_to_coords(piece_coords)
        return self.board[rank - 1][file - 1]

    def get_pseudo_legal_moves(self, piece_coords):
        if self.is_stalemate or self.is_checkmate: return []
        rank, file = fen_utils.algebraic_to_coords(piece_coords)
        if not (1 <= rank <= 8 and 1 <= file <= 8):
            return None

        piece = self.board[rank - 1][file - 1]
        if not piece:
            return None

        all_paths = piece.get_possible_paths()
        valid_moves = []
        

        for path in all_paths:
            valid_path = []
            for r, f in path:
                if not (1 <= r <= 8 and 1 <= f <= 8):
                    break

                piece_at_pos = self.board[r - 1][f - 1]
                if piece_at_pos:
                    if piece_at_pos.get_color() == piece.get_color():
                        break
                    else:
                        if isinstance(piece, Pawn) and abs(piece.file - f) == 1:
                            if piece.can_move((r, f), is_capture=True):
                                valid_path.append((r, f))
                        elif not isinstance(piece, Pawn) or (isinstance(piece, Pawn) and abs(piece.file - f) == 1):
                            if piece.can_kill((r, f)):
                                valid_path.append((r, f))
                                break
                else:
                    if not isinstance(piece, Pawn) or (isinstance(piece, Pawn) and piece.file == f):
                        valid_path.append((r, f))

            valid_moves.extend(valid_path)

        if isinstance(piece, Pawn):
            final_valid_moves = []
            for move in valid_moves:
                r, f = move
                piece_at_target = self.board[r - 1][f - 1] if 1 <= r <= 8 and 1 <= f <= 8 else None
                if abs(piece.file - f) == 1 and piece_at_target and piece_at_target.get_color() != piece.get_color():
                    final_valid_moves.append(move)
                elif abs(piece.file - f) == 0 and not piece_at_target:
                    final_valid_moves.append(move)
            valid_moves = final_valid_moves

        return valid_moves
    
    def get_all_pseudo_legal_moves(self, player):
        moves = []
        for row in self.board:
            for piece in row:
                if not piece: continue 
                if piece.get_color() != player: continue
                moves.extend(self.get_pseudo_legal_moves(piece.get_algebraic_pos()))
        return moves 
    
    def deep_copy(self):
        copy_board = Board(self.fen)
        copy_board.board = copy.deepcopy(self.board)
        copy_board.current_player = self.current_player
        copy_board.halfmoves = self.halfmoves
        copy_board.fullmoves = self.fullmoves
        copy_board.castling_avalability = self.castling_avalability
        copy_board.dead_pieces = copy.deepcopy(self.dead_pieces)
        return copy_board

    def is_move_legal(self, from_pos, to_pos):
        board_copy = self.deep_copy()

        board_copy.move_piece(from_pos, to_pos, simulate=True)

        if board_copy.is_king_in_check(fen_utils.get_opposite_player(board_copy.current_player)):
            return False
        return True

    def get_legal_moves(self, piece_coords):
        legal_moves = []
        pseudo_legal_moves = self.get_pseudo_legal_moves(piece_coords)
        for rank, file in pseudo_legal_moves:
            to_algebraic = fen_utils.coords_to_algebraic(rank, file)
            if self.is_move_legal(piece_coords, to_algebraic):
                legal_moves.append((rank, file))
        return legal_moves
    
    def get_all_legal_moves(self, player):
        moves = []
        for row in self.board:
            for piece in row:
                if not piece: continue 
                if piece.get_color() != player: continue
                moves.extend(self.get_legal_moves(piece.get_algebraic_pos()))
        return moves 

    def is_king_in_check(self, player):
        king = self.get_king_location(player)
        all_possible_moves = self.get_all_pseudo_legal_moves(fen_utils.get_opposite_player(player))
        for move in all_possible_moves:
            if move == king:
                return True

        return False

    def get_king_location(self, player):
        for row in self.board:
            for piece in row:
                if not piece: continue 
                if piece.get_color() != player: continue 
                if piece.get_name().lower() == 'k':
                    return piece.rank, piece.file
        
        return -1, -1
    
    
    def move_piece(self, from_pos, to_pos, simulate=False):
        if not from_pos or not to_pos: return ERROR_NO_POSITIONS_PROVIDED

        from_pos = fen_utils.algebraic_to_coords(from_pos)
        to_pos = fen_utils.algebraic_to_coords(to_pos)

        from_rank, from_file = from_pos
        to_rank, to_file = to_pos

        piece = self.board[from_rank - 1][from_file - 1]

        if not piece: return ERROR_NO_PIECE_TO_MOVE
        
        if simulate:
            pseudo_legal_moves = self.get_pseudo_legal_moves(fen_utils.coords_to_algebraic(from_rank, from_file))
            if to_pos not in pseudo_legal_moves:
                return ERROR_MOVE_NOT_POSSIBLE
        else:
            possible_moves = self.get_legal_moves(fen_utils.coords_to_algebraic(from_rank, from_file))
            if to_pos not in possible_moves:
                return ERROR_MOVE_NOT_POSSIBLE

        piece_at_pos = self.board[to_rank - 1][to_file - 1]

        if piece.get_color() == COLOR["BLACK"]:
            self.fullmoves += 1

        if not piece_at_pos:
            self.board[from_rank - 1][from_file - 1] = None
            self.board[to_rank - 1][to_file - 1] = piece
            piece.update_position(to_rank, to_file)
            self.current_player = COLOR["WHITE"] if self.current_player == COLOR["BLACK"] else COLOR["BLACK"]
            self.fen = self.make_fen()
            
            if not simulate:
                if isinstance(piece, Pawn):
                    if self.try_pawn_promote(fen_utils.coords_to_algebraic(to_pos[0], to_pos[1]), do_it=False) == PAWN_CAN_PROMOTE:
                        return SUCCESS_MOVE_MADE_NO_KILL_PROMOTE_POSSIBLE
                    
                if self.is_game_over():
                    return SUCCESS_MOVE_MADE_NO_KILL_CHECKMATE if self.is_checkmate else SUCCESS_MOVE_MADE_NO_KILL_STALEMATE
                
                if self.is_king_in_check(self.current_player): return SUCCESS_MOVE_MADE_NO_KILL_CHECK
                
            return SUCCESS_MOVE_MADE_NO_KILL_NO_CHECK

        self.dead_pieces[piece_at_pos.get_color()].append(piece_at_pos)
        self.board[from_rank - 1][from_file - 1] = None
        self.board[to_rank - 1][to_file - 1] = piece
        piece.update_position(to_rank, to_file)
        self.current_player = COLOR["WHITE"] if self.current_player == COLOR["BLACK"] else COLOR["BLACK"]
        self.halfmoves += 1
        self.fen = self.make_fen()
        
        
        if not simulate:
            if isinstance(piece, Pawn):
                if self.try_pawn_promote(fen_utils.coords_to_algebraic(to_pos[0], to_pos[1]), do_it=False) == PAWN_CAN_PROMOTE:
                    return SUCCESS_MOVE_MADE_WTIH_KILL_PROMOTE_POSSIBLE
        
            if self.is_game_over():
                return SUCCESS_MOVE_MADE_WITH_KILL_CHECKMATE if self.is_checkmate else SUCCESS_MOVE_MADE_WITH_KILL_STALEMATE
            
            if self.is_king_in_check(self.current_player): return SUCCESS_MOVE_MADE_WITH_KILL_CHECK
            
        return SUCCESS_MOVE_MADE_WITH_KILL_NO_CHECK
    
    def is_game_over(self):
        all_legal_moves = self.get_all_legal_moves(self.current_player)
        if len(all_legal_moves) == 0 or self.are_only_kings_on_board():
            king_check = self.is_king_in_check(self.current_player)
            if king_check:
                self.is_checkmate = True 
            else:
                self.is_stalemate = True
                
        return self.is_stalemate or self.is_checkmate
    
    def are_only_kings_on_board(self):
        pieces = []
        for row in self.board:
            for piece in row:
                if piece: pieces.append(piece)
                
        are_kings_only = True
        for piece in pieces:
            if piece.get_name().lower() != "k":
                are_kings_only = False

        return are_kings_only    
    
    def try_pawn_promote(self, piece_coords, promote_to="queen", do_it=False):
        print("Testing if pawn at ", piece_coords, " can be promoted to ", promote_to)
        rank, file = fen_utils.algebraic_to_coords(piece_coords)
        piece = self.get_piece(piece_coords)
        final_rank = MAX_RANK if piece.get_color() == COLOR["BLACK"] else MIN_RANK 

        can_promote = rank == final_rank
        if not do_it: 
            if can_promote: return PAWN_CAN_PROMOTE
            else: return PAWN_CANNOT_PROMOTE  
       
        if can_promote:
            promoted_piece = self.make_promotion_piece(promote_to, rank, file, piece.get_color())
            self.board[rank - 1][file - 1] = promoted_piece  
            self.fen = self.make_fen()   
            if self.is_game_over():
                print(self.is_checkmate, self.is_stalemate)
                return SUCCESS_PAWN_PROMOTED_CHECKMATE if self.is_checkmate else SUCCESS_PAWN_PROMOTED_STALEMATE
            
            if self.is_king_in_check(self.current_player):
                print("checkl")
                
                return SUCCESS_PAWN_PROMOTED_CHECK
        return SUCCESS_PAWN_PROMOTED
        
    def make_promotion_piece(self, piece_type, rank, file, color):
        if piece_type == "queen":
            return Queen(rank, file, color)
        
        if piece_type == "rook":
            return Rook(rank, file, color)

        if piece_type == "knight":
            return Knight(rank, file, color)
        
        if piece_type == "bishop":
            return Bishop(rank, file, color)
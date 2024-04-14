from __future__ import annotations
import engine.constants as constants
import engine.fen_utils as fen_utils
from engine.piece import Piece
import engine.pieces as pieces
import copy
from engine.enpassant.EnPassantStatus import EnPassantStatus

from engine.Position import Position

from engine.player.BlackPlayer import BlackPlayer   
from engine.player.WhitePlayer import WhitePlayer   
from engine.player.Player import Player   

class Board():
    def __init__(self, fen=constants.START_FEN) -> None:
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
        self.castling_availability = fen_utils.get_castling_availability(fen)
        
        self.is_stalemate = False
        self.is_checkmate = False 
        self.king_in_check = None
        
        self.all_legal_moves = {
            constants.COLOR["BLACK"]: [],
            constants.COLOR["WHITE"]: []
        }
        
        self.en_passant = EnPassantStatus()

    def make_fen(self):
        active = "w" if isinstance(self.current_player, WhitePlayer) else "b"
        castling = ''.join(self.castling_availability) if len(self.castling_availability) > 0 else '-'

        en_passant = self.en_passant.eligible_square.algebraic if self.en_passant.available else '-'

        rows = []
        for rank in range(8):
            fen_row = ""
            empty_count = 0
            for file in range(8):
                position = Position(rank=rank + 1, file=file + 1)  
                piece = self.board[position.rank - 1][position.file - 1]  
                if isinstance(piece, Piece):
                    if empty_count > 0:
                        fen_row += str(empty_count)
                        empty_count = 0
                    fen_row += piece.get_name()
                else:
                    empty_count += 1
            if empty_count > 0:
                fen_row += str(empty_count)
            rows.append(fen_row)

        placements = '/'.join(rows)
        all_fen = [placements, active, castling, en_passant, str(self.halfmoves), str(self.fullmoves)]
        self.fen = ' '.join(all_fen)

        return self.fen

    def get_piece(self, position: Position):
        rank, file = position.rank, position.file
        return self.board[rank - 1][file - 1]
    
    def set_piece(self, position: Position, piece: Piece):
        rank, file = position.rank, position.file
        self.board[rank - 1][file - 1] = piece
    
    def clear_square(self, position: Position):
        self.set_piece(position, None)

    def get_pseudo_legal_moves(self, position: Position, log=False) -> list:
        
        if self.is_stalemate or self.is_checkmate: 
            return []
        
        piece = self.get_piece(position)
        if not piece:
            return []

        all_paths = piece.get_possible_paths()
        valid_moves = []
        
        for path in all_paths:
            
            valid_path = []
            
            for pos in path:
                if not pos.is_on_board():
                    break

                piece_at_pos = self.get_piece(pos)

                if piece_at_pos:
                    if piece_at_pos.get_color() != piece.get_color():
                        if piece.can_kill(pos):
                            valid_path.append(pos)
                    break
                        
                else:
                    if not self.king_in_check:
                        valid_moves.extend(self.get_castlable_moves(piece))
                    
                    if piece.can_move(pos):
                        valid_path.append(pos)
                    
                    if isinstance(piece, pieces.Pawn):
                        if self.en_passant.available and self.en_passant.pawn_color != piece.get_color():
                            possible = self.check_en_passant_possible_for_piece(piece)                                
                            if possible:
                                valid_moves.append(self.en_passant.eligible_square)

            valid_moves.extend(valid_path)
            
        return list(set(valid_moves))

    def get_all_pseudo_legal_moves(self, player: Player) -> list:
        moves = []
        for row in self.board:
            for piece in row:
                if not piece: 
                    continue 
                if piece.get_color() != player.color: 
                    continue
                moves.extend(self.get_pseudo_legal_moves(piece.position))
        return list(set(moves)) 
    
    def deep_copy_board(self):
        copy_board = Board()
        copy_board.board = [[None for _ in range(constants.MAX_FILE)] for _ in range(constants.MAX_RANK)]
        for r in range(constants.MAX_RANK):
            for c in range(constants.MAX_FILE):
                if self.board[r][c] is not None:
                    copy_board.board[r][c] = self.board[r][c].deep_copy()
        return copy_board
    
    def deep_copy(self) -> Board:
        copy_board = self.deep_copy_board()
        copy_board.fen = self.fen
        copy_board.current_player = self.current_player
        copy_board.halfmoves = self.halfmoves
        copy_board.fullmoves = self.fullmoves
        copy_board.castling_availability = self.castling_availability
        copy_board.dead_pieces = copy.deepcopy(self.dead_pieces)
        return copy_board

    def is_move_legal(self, from_pos: Position, to_pos: Position) -> bool:
        board_copy = self.deep_copy()
        board_copy.simulate_move(from_pos, to_pos)
        if board_copy.is_king_in_check(board_copy.current_player.opponent()):
            return False
        return True

    def simulate_move(self, from_pos: Position, to_pos: Position):
        self.move_piece(from_pos, to_pos, simulate=True)
        
    def get_legal_moves(self, position: Position, log=False) -> list:
        legal_moves = []
        pseudo_legal_moves = self.get_pseudo_legal_moves(position, log)
        for to_pos in pseudo_legal_moves:
            if self.is_move_legal(position, to_pos):
                legal_moves.append(to_pos)
        return list(set(legal_moves))
    
    def get_all_legal_moves(self, player: Player, log=False) -> list:
        moves = []
        for row in self.board:
            for piece in row:
                if not piece: 
                    continue 
                if piece.get_color() != player.color: 
                    continue
                moves.extend(self.get_legal_moves(piece.position, log))
        self.all_legal_moves[player.color] = moves
        return list(set(moves)) 

    def is_king_in_check(self, player: Player) -> bool:
        king = self.get_king_location(player)
        all_possible_moves = self.get_all_pseudo_legal_moves(player.opponent())
        for move in all_possible_moves:
            if move == king:
                self.king_in_check = player
                return True

        self.king_in_check = None
        return False

    def get_king_location(self, player: Player) -> Position:
        for row in self.board:
            for piece in row:
                if not piece: 
                    continue 
                if piece.get_color() != player.color: 
                    continue 
                if piece.get_name().lower() == 'k':
                    return piece.position
        
        return Position()
    
    def update_en_passant_status(self, from_pos: Position, to_pos: Position):
        from_rank, from_file = from_pos.rank, from_pos.file 
        to_rank, to_file = to_pos.rank, to_pos.file
        
        moved_piece = self.get_piece(to_pos)
        
        if isinstance(moved_piece, pieces.Pawn) and abs(to_rank - from_rank) == 2:
            eligible_square_rank = to_rank  + 1 if moved_piece.get_color() == constants.COLOR["WHITE"] else to_rank - 1
            eligible_square = Position(rank=eligible_square_rank, file=to_file)
            self.en_passant.set(eligible_square, to_pos, moved_piece.get_color())
        else:
            self.en_passant.clear()

    def check_en_passant_possible_for_piece(self, piece: Piece):
        piece_pos = piece.position
        rank, file = piece_pos.rank, piece_pos.file
        en_pass_position = self.en_passant.eligible_square
        en_pass_rank, en_pass_file = en_pass_position.rank, en_pass_position.file 
        
        if abs(rank - en_pass_rank) == 1 and abs(file - en_pass_file) == 1:
            if piece.get_color() == constants.COLOR["BLACK"]:
                return en_pass_rank > rank
            else:
                return rank > en_pass_rank
        else: 
            return False
    
    def move_piece(self, from_pos: Position, to_pos: Position, simulate=False):
        piece = self.get_piece(from_pos)
        piece_at_pos = self.get_piece(to_pos)

        if not piece: 
            return constants.ERROR_NO_PIECE_TO_MOVE
        
        if not simulate and not self.is_valid_move(from_pos, to_pos):
            return constants.ERROR_MOVE_NOT_POSSIBLE

        kill_status = constants.NO_KILL
        special_status = constants.NO_CHECK
        
        if not piece_at_pos:
            has_castled = self.check_for_castle(from_pos, to_pos)
            has_en_passant = self.check_for_en_passant(from_pos, to_pos)
                            
            if has_castled:
                special_status = constants.CASTLED

            if has_en_passant:
                kill_status = constants.KILL
            
        kill_status = self.move(from_pos, to_pos)
        self.update_board(from_pos, to_pos)
        
        special_status = self.post_move_checks(from_pos, to_pos) if not simulate else constants.NO_CHECK
        
        self.fen = self.make_fen()
        return kill_status, special_status
        
    def update_board(self, from_pos: Position, to_pos: Position):
        self.current_player = self.current_player.opponent()
        self.halfmoves += 1
        self.update_castling_availability()
        self.update_en_passant_status(from_pos, to_pos)
        
    def post_move_checks(self, from_pos: Position, to_pos: Position): 
        if self.try_pawn_promote(to_pos, do_it=False) == constants.PAWN_CAN_PROMOTE:
            return constants.PROMOTE_POSSIBLE
    
        if self.is_game_over():
            return constants.CHECKMATE if self.is_checkmate else constants.STALEMATE
        
        if self.is_king_in_check(self.current_player): 
            return constants.CHECK
        
        return constants.NO_CHECK
        
    def is_valid_move(self, from_pos: Position, to_pos: Position):
        possible_moves = self.get_pseudo_legal_moves(from_pos)
        if to_pos not in possible_moves:
            return False 
        return True
    
    def move(self, from_pos: Position, to_pos: Position):
        piece = self.get_piece(from_pos)
        self.clear_square(from_pos)
        killed_piece = self.get_piece(to_pos)
        self.set_piece(to_pos, piece)
        piece.update_position(to_pos)
        if killed_piece: 
            self.dead_pieces[killed_piece.get_color()].append(killed_piece)
            return constants.KILL
    
        return constants.NO_KILL
        
    def check_for_castle(self, from_pos: Position, to_pos: Position):
        piece = self.get_piece(from_pos)
        has_castled = False
        if isinstance(piece, pieces.King) and abs(to_pos.file - from_pos.file) > 1:
            has_castled = self.castle(piece, from_pos, to_pos)

        return has_castled  
    
    def check_for_en_passant(self, from_pos: Position, to_pos: Position):
        piece = self.get_piece(from_pos)
        
        if isinstance(piece, pieces.Pawn) and self.en_passant.available:
            if self.check_en_passant_possible_for_piece(piece):
                if to_pos == self.en_passant.eligible_square:
                    removed_pawn = self.get_piece(self.en_passant.target_pawn_position)
                    self.clear_square(self.en_passant.target_pawn_position)
                    self.dead_pieces[removed_pawn.get_color()].append(removed_pawn)
                    return True
                    
        return False
              
    def get_castlable_moves(self, piece):
        moves = []
            
        if isinstance(piece, pieces.King):
            if piece.get_color() == constants.COLOR["WHITE"]:
                if 'K' in self.castling_availability:
                    to_append = True
                    pieces_in_middle = ['f1', 'g1']
                    for p in pieces_in_middle:
                        r, f = fen_utils.algebraic_to_coords(p)
                        if self.board[r - 1][f - 1]:
                            to_append = False
                            break
                        if self.is_targeted_square(p):
                            to_append = False
                            break
                    if to_append: 
                            moves.append(Position(algebraic='g1'))
                if 'Q' in self.castling_availability:
                    to_append = True
                    pieces_in_middle = ['b1', 'c1', 'd1']
                    for p in pieces_in_middle:
                        r, f = fen_utils.algebraic_to_coords(p)
                        if self.board[r - 1][f - 1]:
                            to_append = False
                            break
                        if self.is_targeted_square(p):
                            to_append = False
                            break
                    if to_append: 
                        moves.append(Position(algebraic='c1'))
            elif piece.get_color() == constants.COLOR["BLACK"]:
                if 'k' in self.castling_availability:
                    to_append = True
                    pieces_in_middle = ['f8', 'g8']
                    for p in pieces_in_middle:
                        r, f = fen_utils.algebraic_to_coords(p)
                        if self.board[r - 1][f - 1]:
                            to_append = False
                            break
                        if self.is_targeted_square(p):
                            to_append = False
                            break
                    if to_append: 
                        moves.append(Position(algebraic='g8'))
                if 'q' in self.castling_availability:
                    to_append = True
                    pieces_in_middle = ['b8', 'c8', 'd8']
                    for p in pieces_in_middle:
                        r, f = fen_utils.algebraic_to_coords(p)
                        if self.board[r - 1][f - 1]:
                            to_append = False
                            break
                        if self.is_targeted_square(p):
                            to_append = False
                            break
                    if to_append: 
                            moves.append(Position(algebraic='c8'))
        return moves
    
    def is_targeted_square(self, position: Position):
        player = self.current_player.opponent()
        legal_moves = self.all_legal_moves[player.color]
        return position in legal_moves
    
    def castle(self, piece: Piece, from_pos: Position, to_pos: Position):
        
        if self.is_king_in_check(self.current_player):
            return False
        
        self.update_castling_availability()
        if not self.castling_availability:
            return False
        
        if to_pos.file > from_pos.file:
            castling = 'k' if piece.get_color() == constants.COLOR["BLACK"] else "K"
        elif from_pos.file > to_pos.file:
            castling = 'q' if piece.get_color() == constants.COLOR["BLACK"] else 'Q'
            
        if castling not in self.castling_availability:
            
            return False 
    
        if castling in 'kK':
            if castling == 'k': 
                pos1, pos2 = Position(algebraic='h8'), Position(algebraic='f8')
            else: 
                pos1, pos2 = Position(algebraic='h1'), Position(algebraic='f1')
        else:
            if castling == 'q': 
                pos1, pos2 = Position(algebraic='a8'), Position(algebraic='d8')
            else: 
                pos1, pos2 = Position(algebraic='a1'), Position(algebraic='d1')

        if pos1.is_on_board() and pos2.is_on_board():
            rook = self.get_piece(pos1)
            self.set_piece(pos2, rook)
            self.clear_square(pos1)
            rook.update_position(pos2)
            return True
        return False 
    
    def update_castling_availability(self):
        self.castling_availability = ''
        
        def is_rook_ready_for_castling(piece, expected_name):
            return piece is not None and piece.get_name() == expected_name and not piece.has_moved

        def is_king_ready_for_castling(piece, expected_name):
            return piece is not None and piece.get_name() == expected_name and not piece.has_moved
        
        if is_king_ready_for_castling(self.board[7][4], 'K'):
            if is_rook_ready_for_castling(self.board[7][0], 'R'):
                self.castling_availability += 'Q'
            if is_rook_ready_for_castling(self.board[7][7], 'R'):
                self.castling_availability += 'K'
        
        if is_king_ready_for_castling(self.board[0][4], 'k'):
            if is_rook_ready_for_castling(self.board[0][0], 'r'):
                self.castling_availability += 'q'
            if is_rook_ready_for_castling(self.board[0][7], 'r'):
                self.castling_availability += 'k'

    def is_game_over(self):
        
        if self.is_stalemate or self.is_checkmate:
            return True
        
        all_legal_moves = self.get_all_legal_moves(self.current_player, log=False)
        if len(all_legal_moves) == 0:
            if self.are_only_kings_on_board():
                self.is_stalemate = True
            
            else:
                king_in_check = self.is_king_in_check(self.current_player)
                if king_in_check:
                    self.is_checkmate = True
                else:
                    self.is_stalemate = True
                    
        return self.is_stalemate or self.is_checkmate
    
    def are_only_kings_on_board(self):
        pieces = []
        for row in self.board:
            for piece in row:
                if piece: 
                    pieces.append(piece)
                
        are_kings_only = True
        for piece in pieces:
            if piece.get_name().lower() != "k":
                are_kings_only = False

        return are_kings_only    
    
    def try_pawn_promote(self, position: Position, promote_to="queen", do_it=False):
        rank, file = position.rank, position.file
        piece = self.get_piece(position)
        
        if not isinstance(piece, pieces.Pawn):
            return constants.PAWN_CANNOT_PROMOTE
        
        final_rank = constants.MAX_RANK if piece.get_color() == constants.COLOR["BLACK"] else constants.MIN_RANK 

        can_promote = rank == final_rank
        if not do_it: 
            if can_promote: 
                return constants.PAWN_CAN_PROMOTE
            else: 
                return constants.PAWN_CANNOT_PROMOTE  
       
        if can_promote:
            promoted_piece = self.make_promotion_piece(promote_to, position, piece.get_color())
            self.set_piece(position, promoted_piece)
            self.fen = self.make_fen()   
            if self.is_game_over():
                return constants.SUCCESS_PAWN_PROMOTED_CHECKMATE if self.is_checkmate else constants.SUCCESS_PAWN_PROMOTED_STALEMATE
            
            if self.is_king_in_check(self.current_player):
                return constants.SUCCESS_PAWN_PROMOTED_CHECK
        return constants.SUCCESS_PAWN_PROMOTED
        
    def make_promotion_piece(self, piece_type: str, position: Position, color: str):
        if piece_type == "queen":
            return pieces.Queen(position, color)
        
        if piece_type == "rook":
            return pieces.Rook(position, color)

        if piece_type == "knight":
            return pieces.Knight(position, color)
        
        if piece_type == "bishop":
            return pieces.Bishop(position, color)
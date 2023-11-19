#!/usr/bin/python3
# Set the path to your python3 above

"""
Go0 random Go player
Cmput 455 sample code
Written by Cmput 455 TA and Martin Mueller
"""
from gtp_connection import GtpConnection, format_point, point_to_coord
from board_base import DEFAULT_SIZE, GO_POINT, GO_COLOR
from board import GoBoard
from board_util import GoBoardUtil
from engine import GoEngine
import time
import random
from board_base import (
    BLACK,
    WHITE,
    EMPTY,
    BORDER,
    GO_COLOR, GO_POINT,
    PASS,
    MAXSIZE,
    coord_to_point,
    opponent
)


class ABPlayer(GoEngine):
    def __init__(self) -> None:
        """
        Ninuki player which uses basic iterative deepening alpha-beta search.
        Many improvements are possible.
        """
        GoEngine.__init__(self, "Go0", 1.0)
        self.time_limit = 1

    def get_move(self, board: GoBoard, color: GO_COLOR) -> GO_POINT:
        if board.get_empty_points().size == 0:
            return "pass"
        if color == 'w':
            board.current_player = WHITE
        else:
            board.current_player = BLACK
        winner, move = self.solve_board(board)
        return format_point(point_to_coord(self.best_move, self.board.size)).lower()

    def alpha_beta(self, alpha, beta, depth):
        if time.time() - self.solve_start_time > (self.time_limit - 0.01):
            return 0, False, True

        is_terminal, winner = self.board.is_terminal()
        if is_terminal:
            if winner == self.board.current_player:
                return 1, True, False
            elif winner == opponent(self.board.current_player):
                return -1, True, False
            else:
                return 0, True, False

        if depth >= self.max_depth:
            return 0, False, False

        any_unsolved = False
        moves = GoBoardUtil.generate_legal_moves(self.board, self.board.current_player)
        if depth == 0:
            random.shuffle(moves)

        for move in moves:
            self.board.play_move(move, self.board.current_player)
            
            value, solved, timeout = self.alpha_beta(-beta, -alpha, depth+1)
            self.board.undo()
            value = -value

            if timeout:
                return 0, False, True
            
            if not solved:
                any_unsolved = True

            if value > alpha:
                alpha = value
                if depth == 0:
                    self.best_move = move

            if solved and value == 1:
                return 1, True, False

            if value >= beta:
                return beta, True, False
        
        return alpha, not any_unsolved, False

    def solve_board(self, board):
        self.solve_start_time = time.time()
        self.board = board.copy()
        self.tt = {}
        if self.board.get_empty_points().size == 0:
            self.best_move = PASS
        else:
            self.best_move = self.board.get_empty_points()[0]

        solved = False
        timeout = False
        self.max_depth = 1
        while not solved and not timeout:
            result, solved, timeout = self.alpha_beta(-1, 1, 0)
            self.max_depth += 1
        
        if timeout:
            return "unknown", None
        elif result == 1:
            if self.board.current_player == BLACK:
                return "b", format_point(point_to_coord(self.best_move, self.board.size)).lower()
            else:
                return "w", format_point(point_to_coord(self.best_move, self.board.size)).lower()
        elif result == -1:
            if self.board.current_player == BLACK:
                return "w", None
            else:
                return "b", None
        else:
            return "draw", format_point(point_to_coord(self.best_move, self.board.size)).lower()

    def set_time_limit(self, time_limit):
        self.time_limit = time_limit

def run() -> None:
    """
    start the gtp connection and wait for commands.
    """
    board: GoBoard = GoBoard(DEFAULT_SIZE)
    con: GtpConnection = GtpConnection(ABPlayer(), board)
    con.start_connection()


if __name__ == "__main__":
    run()

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
        moves = GoBoardUtil.generate_legal_moves(board, color)
        if len(moves) == 0:
            return "pass"
        move = moves[random.randint(0, len(moves) - 1)]
        return format_point(point_to_coord(move, board.size)).lower()

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

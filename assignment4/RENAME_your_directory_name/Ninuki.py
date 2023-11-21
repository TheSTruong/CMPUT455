#!/usr/bin/python3
# Set the path to your python3 above

"""
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

# timelimit
from signal_handler import timeout_handler
import signal

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

class A4SubmissionPlayer(GoEngine):
    def __init__(self) -> None:
        """
        Starter code for assignment 4
        
        RULES
        All games will be played on a 7x7 board.
        The time limit will be 60 seconds per move. If a program does not play within the time limit, it will be killed by the script and instantly loses the game. 
         We recommend leaving a little bit of extra time and not fully use the 60 seconds, just to be safe.
        The memory limit will be 1 Gigabyte per program.
        If a program generates an illegal move, it instantly loses the game.
        If a program crashes or exceeds the memory limit, it instantly loses the game.
        If a game is interrupted for other reasons, it may be replayed at the decision of the instructor.
        Your player is allowed but not required to resign. It will not be called to generate a move after the game is over.

        CONSTRAINTS
        You can use any code provided by us, or created by you as part of this course, but no other outside sources of code. 
         Using standard python libraries is OK, before using other more exotic libraries ask on the eClass forum.
        Your program is not allowed to use more than one thread for computation/search.
        Your program is not allowed to use programming languages other than Python3.
        Your program is allowed to read/write files within your assignment4 directory only.
        The total file size of the assignment submission, including all files, is limited to 1 Megabyte uncompressed.
         It must remain under that limit while your program is running, i.e. your program cannot generate files of larger total size.
        Further reasonable constraints to prevent abuse may be imposed as we become aware of them.
        """
        GoEngine.__init__(self, "Go0", 1.0)
        self.time_limit = 60    # TODO: Need to give it a few more second to be safe

    def set_time_limit(self, time_limit):
        self.time_limit = time_limit

    def get_move(self, board: GoBoard, color: GO_COLOR) -> GO_POINT:
        """
        Implement for assignment 4
        Returns the best move
        """
        try:
            signal.alarm(self.time_limit)    # set time_limit alarm
            # use solver to get move
        except TimeoutError:
            pass
            # what to do after time expires
        else:
            signal.alarm(0)    # disable timelimit alarm


def run() -> None:
    """
    start the gtp connection and wait for commands.
    """
    board: GoBoard = GoBoard(DEFAULT_SIZE)
    con: GtpConnection = GtpConnection(A4SubmissionPlayer(), board)
    con.start_connection()


if __name__ == "__main__":
    run()

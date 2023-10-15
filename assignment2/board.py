"""
board.py
Cmput 455 sample code
Written by Cmput 455 TA and Martin Mueller

Implements a basic Go board with functions to:
- initialize to a given board size
- check if a move is legal
- play a move

The board uses a 1-dimensional representation with padding
"""

import numpy as np
from typing import List, Tuple

from board_base import (
    board_array_size,
    coord_to_point,
    is_black_white,
    is_black_white_empty,
    opponent,
    where1d,
    BLACK,
    WHITE,
    EMPTY,
    BORDER,
    MAXSIZE,
    NO_POINT,
    PASS,
    GO_COLOR,
    GO_POINT,
)


"""
The GoBoard class implements a board and basic functions to play
moves, check the end of the game, and count the acore at the end.
The class also contains basic utility functions for writing a Go player.
For many more utility functions, see the GoBoardUtil class in board_util.py.

The board is stored as a one-dimensional array of GO_POINT in self.board.
See coord_to_point for explanations of the array encoding.
"""
class GoBoard(object):
    def __init__(self, size: int) -> None:
        """
        Creates a Go board of given size
        """
        assert 2 <= size <= MAXSIZE
        self.reset(size)
        self.calculate_rows_cols_diags()
        self.prev_black_captures = 0
        self.prev_white_captures = 0
        self.black_captures = 0
        self.white_captures = 0
        self.boardStack = []

    def add_two_captures(self, color: GO_COLOR) -> None:
        if color == BLACK:
            self.black_captures += 2
        elif color == WHITE:
            self.white_captures += 2
    def get_captures(self, color: GO_COLOR) -> None:
        if color == BLACK:
            return self.black_captures
        elif color == WHITE:
            return self.white_captures
    
    def calculate_rows_cols_diags(self) -> None:
        if self.size < 5:
            return
        # precalculate all rows, cols, and diags for 5-in-a-row detection
        self.rows = []
        self.cols = []
        for i in range(1, self.size + 1):
            current_row = []
            start = self.row_start(i)
            for pt in range(start, start + self.size):
                current_row.append(pt)
            self.rows.append(current_row)
            
            start = self.row_start(1) + i - 1
            current_col = []
            for pt in range(start, self.row_start(self.size) + i, self.NS):
                current_col.append(pt)
            self.cols.append(current_col)
        
        self.diags = []
        # diag towards SE, starting from first row (1,1) moving right to (1,n)
        start = self.row_start(1)
        for i in range(start, start + self.size):
            diag_SE = []
            pt = i
            while self.get_color(pt) == EMPTY:
                diag_SE.append(pt)
                pt += self.NS + 1
            if len(diag_SE) >= 5:
                self.diags.append(diag_SE)
        # diag towards SE and NE, starting from (2,1) downwards to (n,1)
        for i in range(start + self.NS, self.row_start(self.size) + 1, self.NS):
            diag_SE = []
            diag_NE = []
            pt = i
            while self.get_color(pt) == EMPTY:
                diag_SE.append(pt)
                pt += self.NS + 1
            pt = i
            while self.get_color(pt) == EMPTY:
                diag_NE.append(pt)
                pt += -1 * self.NS + 1
            if len(diag_SE) >= 5:
                self.diags.append(diag_SE)
            if len(diag_NE) >= 5:
                self.diags.append(diag_NE)
        # diag towards NE, starting from (n,2) moving right to (n,n)
        start = self.row_start(self.size) + 1
        for i in range(start, start + self.size):
            diag_NE = []
            pt = i
            while self.get_color(pt) == EMPTY:
                diag_NE.append(pt)
                pt += -1 * self.NS + 1
            if len(diag_NE) >=5:
                self.diags.append(diag_NE)
        assert len(self.rows) == self.size
        assert len(self.cols) == self.size
        assert len(self.diags) == (2 * (self.size - 5) + 1) * 2

    def reset(self, size: int) -> None:
        """
        Creates a start state, an empty board with given size.
        """
        self.size: int = size
        self.NS: int = size + 1
        self.WE: int = 1
        self.ko_recapture: GO_POINT = NO_POINT
        self.last_move: GO_POINT = NO_POINT
        self.last2_move: GO_POINT = NO_POINT
        self.current_player: GO_COLOR = BLACK
        self.maxpoint: int = board_array_size(size)
        self.board: np.ndarray[GO_POINT] = np.full(self.maxpoint, BORDER, dtype=GO_POINT)
        self._initialize_empty_points(self.board)
        self.calculate_rows_cols_diags()
        self.black_captures = 0
        self.white_captures = 0
        self.boardStack = []

    def copy(self) -> 'GoBoard':
        b = GoBoard(self.size)
        assert b.NS == self.NS
        assert b.WE == self.WE
        b.ko_recapture = self.ko_recapture
        b.last_move = self.last_move
        b.last2_move = self.last2_move
        b.current_player = self.current_player
        assert b.maxpoint == self.maxpoint
        b.board = np.copy(self.board)
        return b

    def get_color(self, point: GO_POINT) -> GO_COLOR:
        return self.board[point]

    def pt(self, row: int, col: int) -> GO_POINT:
        return coord_to_point(row, col, self.size)

    def _is_legal_check_simple_cases(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        Check the simple cases of illegal moves.
        Some "really bad" arguments will just trigger an assertion.
        If this function returns False: move is definitely illegal
        If this function returns True: still need to check more
        complicated cases such as suicide.
        """
        assert is_black_white(color)
        if point == PASS:
            return True
        # Could just return False for out-of-bounds, 
        # but it is better to know if this is called with an illegal point
        assert self.pt(1, 1) <= point <= self.pt(self.size, self.size)
        assert is_black_white_empty(self.board[point])
        if self.board[point] != EMPTY:
            return False
        if point == self.ko_recapture:
            return False
        return True

    def is_legal(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        Check whether it is legal for color to play on point
        This method tries to play the move on a temporary copy of the board.
        This prevents the board from being modified by the move
        """
        if point == PASS:
            return True
        board_copy: GoBoard = self.copy()
        can_play_move = board_copy.play_move(point, color)
        return can_play_move

    def end_of_game(self) -> bool:
        return self.last_move == PASS \
           and self.last2_move == PASS
           
    def get_empty_points(self) -> np.ndarray:
        """
        Return:
            The empty points on the board
        """
        return where1d(self.board == EMPTY)

    def row_start(self, row: int) -> int:
        assert row >= 1
        assert row <= self.size
        return row * self.NS + 1

    def _initialize_empty_points(self, board_array: np.ndarray) -> None:
        """
        Fills points on the board with EMPTY
        Argument
        ---------
        board: numpy array, filled with BORDER
        """
        for row in range(1, self.size + 1):
            start: int = self.row_start(row)
            board_array[start : start + self.size] = EMPTY

    def is_eye(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        Check if point is a simple eye for color
        """
        if not self._is_surrounded(point, color):
            return False
        # Eye-like shape. Check diagonals to detect false eye
        opp_color = opponent(color)
        false_count = 0
        at_edge = 0
        for d in self._diag_neighbors(point):
            if self.board[d] == BORDER:
                at_edge = 1
            elif self.board[d] == opp_color:
                false_count += 1
        return false_count <= 1 - at_edge  # 0 at edge, 1 in center

    def _is_surrounded(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        check whether empty point is surrounded by stones of color
        (or BORDER) neighbors
        """
        for nb in self._neighbors(point):
            nb_color = self.board[nb]
            if nb_color != BORDER and nb_color != color:
                return False
        return True

    def _has_liberty(self, block: np.ndarray) -> bool:
        """
        Check if the given block has any liberty.
        block is a numpy boolean array
        """
        for stone in where1d(block):
            empty_nbs = self.neighbors_of_color(stone, EMPTY)
            if empty_nbs:
                return True
        return False

    def _block_of(self, stone: GO_POINT) -> np.ndarray:
        """
        Find the block of given stone
        Returns a board of boolean markers which are set for
        all the points in the block 
        """
        color: GO_COLOR = self.get_color(stone)
        assert is_black_white(color)
        return self.connected_component(stone)

    def connected_component(self, point: GO_POINT) -> np.ndarray:
        """
        Find the connected component of the given point.
        """
        marker = np.full(self.maxpoint, False, dtype=np.bool_)
        pointstack = [point]
        color: GO_COLOR = self.get_color(point)
        assert is_black_white_empty(color)
        marker[point] = True
        while pointstack:
            p = pointstack.pop()
            neighbors = self.neighbors_of_color(p, color)
            for nb in neighbors:
                if not marker[nb]:
                    marker[nb] = True
                    pointstack.append(nb)
        return marker

    def _detect_and_process_capture(self, nb_point: GO_POINT) -> GO_POINT:
        """
        Check whether opponent block on nb_point is captured.
        If yes, remove the stones.
        Returns the stone if only a single stone was captured,
        and returns NO_POINT otherwise.
        This result is used in play_move to check for possible ko
        """
        single_capture: GO_POINT = NO_POINT
        opp_block = self._block_of(nb_point)
        if not self._has_liberty(opp_block):
            captures = list(where1d(opp_block))
            self.board[captures] = EMPTY
            if len(captures) == 1:
                single_capture = nb_point
        return single_capture
    
    def play_move(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        Tries to play a move of color on the point.
        Returns whether or not the point was empty.
        """
        if self.board[point] != EMPTY:
            return False
        self.boardStack.append((point,self.board[point]))
        self.board[point] = color
        self.current_player = opponent(color)
        self.last2_move = self.last_move
        self.last_move = point
        O = opponent(color)

        self.prev_black_captures = self.black_captures
        self.prev_white_captures = self.white_captures
        offsets = [1, -1, self.NS, -self.NS, self.NS+1, -(self.NS+1), self.NS-1, -self.NS+1]
        for offset in offsets:
            if self.board[point+offset] == O and self.board[point+(offset*2)] == O and self.board[point+(offset*3)] == color:
                self.boardStack.append((point+offset,self.board[point+offset]))
                self.boardStack.append((point+(offset*2),self.board[point+(offset*2)]))
                self.board[point+offset] = EMPTY
                self.board[point+(offset*2)] = EMPTY
                if color == BLACK:
                    self.black_captures += 2
                else:
                    self.white_captures += 2
        #Need to tweak later for previous scores.
        self.boardStack.append("Marker")
        return True
    
    def neighbors_of_color(self, point: GO_POINT, color: GO_COLOR) -> List:
        """ List of neighbors of point of given color """
        nbc: List[GO_POINT] = []
        for nb in self._neighbors(point):
            if self.get_color(nb) == color:
                nbc.append(nb)
        return nbc

    def _neighbors(self, point: GO_POINT) -> List:
        """ List of all four neighbors of the point """
        return [point - 1, point + 1, point - self.NS, point + self.NS]

    def _diag_neighbors(self, point: GO_POINT) -> List:
        """ List of all four diagonal neighbors of point """
        return [point - self.NS - 1,
                point - self.NS + 1,
                point + self.NS - 1,
                point + self.NS + 1]

    def last_board_moves(self) -> List:
        """
        Get the list of last_move and second last move.
        Only include moves on the board (not NO_POINT, not PASS).
        """
        board_moves: List[GO_POINT] = []
        if self.last_move != NO_POINT and self.last_move != PASS:
            board_moves.append(self.last_move)
        if self.last2_move != NO_POINT and self.last2_move != PASS:
            board_moves.append(self.last2_move)
        return board_moves

    def detect_five_in_a_row(self) -> GO_COLOR:
        """
        Returns BLACK or WHITE if any five in a row is detected for the color
        EMPTY otherwise.
        """
        for r in self.rows:
            result = self.has_five_in_list(r)
            if result != EMPTY:
                return result
        for c in self.cols:
            result = self.has_five_in_list(c)
            if result != EMPTY:
                return result
        for d in self.diags:
            result = self.has_five_in_list(d)
            if result != EMPTY:
                return result
        return EMPTY

    def has_five_in_list(self, list) -> GO_COLOR:
        """
        Returns BLACK or WHITE if any five in a rows exist in the list.
        EMPTY otherwise.
        """
        prev = BORDER
        counter = 1
        for stone in list:
            if self.get_color(stone) == prev:
                counter += 1
            else:
                counter = 1
                prev = self.get_color(stone)
            if counter == 5 and prev != EMPTY:
                return prev
        return EMPTY

    def hasFour(self, list, color):
        if self.board.size < 6:
            return 0
        straights = 0
        blocks = 0
        for i in range(len(list) - 6):
            if self.get_color(list[i+1]) == color and self.get_color(list[i+2]) == color \
            and self.get_color(list[i+3]) == color and self.get_color(list[i+4]) == color:
                if self.get_color(list[i]) == EMPTY and self.get_color(list[i+5]) == EMPTY:
                    straights += 1
                elif self.get_color(list[i]) == EMPTY or self.get_color(list[i+5]) == EMPTY:
                    blockes += 1
        return straights, blocks
    
    def hasThree(self, list, color):
        straights = 0
        blocks = 0
        for i in range(len(list) - 5):
            if self.get_color(list[i+1]) == color and self.get_color(list[i+2]) == color and self.get_color(list[i+3]) == color:
                if self.get_color(list[i]) == EMPTY and self.get_color(list[i+4]) == EMPTY:
                    straights += 1
                elif self.get_color(list[i]) == EMPTY or self.get_color(list[i+4]) == EMPTY:
                    blocks += 1
        return straights, blocks
    
    def hasTwo(self, list, color):
        straights = 0
        blocks = 0
        for i in range(len(list) - 4):
            if self.get_color(list[i+1]) == color and self.get_color(list[i+2]) == color:
                if self.get_color(list[i]) == EMPTY and self.get_color(list[i+3]) == EMPTY:
                    straights += 1
                elif self.get_color(list[i]) == EMPTY or self.get_color(list[i+3]) == EMPTY:
                    blocks += 1
        return straights, blocks
    
    def hasOne(self, list, color):
        straights = 0
        blocks = 0
        for i in range(len(list) - 3):
            if self.get_color(list[i+1]) == color:
                if self.get_color(list[i]) == EMPTY and self.get_color(list[i+2]) == EMPTY:
                    straights += 1
                elif self.get_color(list[i]) == EMPTY or self.get_color(list[i+2]) == EMPTY:
                    blocks += 1
        return straights, blocks
    
    def detectFours(self):
        everything = self.rows + self.cols + self.diags
        players = [dict(), dict()] # black, white
        
        for line in everything:
            whiteCount = 0
            blackCount = 0
            lastEmpty = -2
            firstWhite = -2
            firstBlack = -2
            for i in range(len(line)):
                pt = self.get_color(line[i])
                if pt == EMPTY:
                    if whiteCount:
                        if (firstWhite - lastEmpty == 1):
                            players[1]["straight " + str(whiteCount)] = players[1].get(whiteCount, 0) + 1
                        else:
                            players[1]["blocked " + str(whiteCount)] = players[1].get(whiteCount, 0) + 1
                        whiteCount = 0
                    elif blackCount:
                        if (firstBlack - lastEmpty == 1):
                            players[0]["straight " + str(blackCount)] = players[0].get(blackCount, 0) + 1
                        else:
                            players[0]["straight " + str(blackCount)] = players[0].get(blackCount, 0) + 1
                        blackCount = 0
                    lastEmpty = i
                elif pt == BLACK:
                    if whiteCount and (firstWhite - lastEmpty == 1):
                        players[1]["blocked " + str(whiteCount)] = players[1].get(whiteCount, 0) + 1
                        whiteCount = 0
                    if blackCount == 0:
                        firstBlack = i
                    blackCount += 1
                elif pt == WHITE:
                    if blackCount and (firstBlack - lastEmpty == 1):
                        players[0]["blocked " + str(blackCount)] = players[0].get(blackCount, 0) + 1
                        blackCount = 0
                    if whiteCount == 0:
                        firstWhite = i
                    whiteCount += 1
            if whiteCount and (firstWhite - lastEmpty == 1):
                players[1]["blocked " + str(whiteCount)] = players[1].get(whiteCount, 0) + 1
            if blackCount and (firstBlack - lastEmpty == 1):
                players[0]["blocked " + str(blackCount)] = players[0].get(blackCount, 0) + 1
        # print(players)
        return players

    
    # def detectNumInList(self) -> dict:
    #     """
    #     Returns the number of in-a-rows
    #     TODO: special case 4 . 4 then place in middle will have num[9]
    #     """
    #     playersInARows = [dict(), dict()] # white, black
    #     everything = self.rows + self.cols + self.diags

    #     for line in everything:
    #         i = 0
    #         whiteCount = 0
    #         blackCount = 0
    #         for j in range(i, i+5):
    #             # if playersInARows[0].get(5, 0) >= 1 or playersInARows[1].get(5, 0) >= 1:
    #             #     break
    #             pt = self.get_color(line[j])
    #             if pt == BLACK:
    #                 if whiteCount >= 5 or (whiteCount != 0 and line[i-1] == EMPTY):
    #                     playersInARows[0][whiteCount] = playersInARows[0].get(whiteCount, 0) + 1
    #                     break
    #                 whiteCount = 0
    #                 blackCount += 1
    #             elif pt == WHITE:
    #                 if blackCount >= 5 or (blackCount != 0 and line[i-1] == EMPTY):
    #                     playersInARows[1][blackCount] = playersInARows[1].get(blackCount, 0) + 1
    #                     break
    #                 blackCount = 0
    #                 whiteCount += 1
    #             elif pt == EMPTY:
    #                 if blackCount != 0:
    #                     playersInARows[0][whiteCount] = playersInARows[0].get(whiteCount, 0) + 1
    #                     whiteCount = 0
    #                     break
    #                 elif whiteCount != 0:
    #                     playersInARows[1][blackCount] = playersInARows[1].get(blackCount, 0) + 1
    #                     blackCount = 0
    #                     break
    #         playersInARows[0][whiteCount] = playersInARows[0].get(whiteCount, 0) + 1
    #         playersInARows[1][blackCount] = playersInARows[0].get(blackCount, 0) + 1
    #         if playersInARows[0].get(5, 0) >= 1 or playersInARows[1].get(5, 0) >= 1:
    #             break
    #     # print(playersInARows)
    #     return playersInARows
    
    def undoMove(self):
        if self.boardStack != [] and self.boardStack[-1] == "Marker":
            self.boardStack.pop()
        scoreCount = -1
        while(self.boardStack != [] and self.boardStack[-1] != "Marker"):
            scoreCount += 1
            point, pColor = self.boardStack.pop()

            self.board[point] = pColor
            self.current_player = opponent(self.current_player)
        if scoreCount >= 2:
            if self.current_player == BLACK:
                self.prev_black_captures -= scoreCount
                self.black_captures -= scoreCount
            elif self.current_player == WHITE:
                self.prev_black_captures -= scoreCount
                self.white_captures -= scoreCount
    
    def endOfGame(self):
        if self.get_empty_points().size == 0 or self.detect_five_in_a_row() != EMPTY:
            return True
        if self.black_captures >= 10 or self.white_captures >= 10 or self.end_of_game():
            return True
        return False
    
    def moveOrdering(self, move):
        score = 0
        self.play_move(move, self.current_player)
        score = -self.staticallyEvaluateForToPlay()
        self.undoMove()
        return score
    
    def staticallyEvaluateForToPlay(self):
        win_color = self.detect_five_in_a_row()
        if win_color != EMPTY:
            return -100000
        if self.current_player == "w":
                if self.black_captures >= 10:
                    return -100000
        elif self.current_player == "b":
                if self.white_captures >= 10:
                    return -100000
        # assert win_color != self.current_player
        return self.HeuristicScore()
    
    def HeuristicScore(self):
        opp = opponent(self.current_player)
        playersInARow = self.detectFours()
        white = playersInARow[1]
        black = playersInARow[0]
        
        score = 1000 * black.get("straight 4", 0) + 700 * black.get("straight 3", 0) + 450 * black.get("blocked 4", 0) + 300 * black.get("blocked 3", 0) + 250 * black.get("straight 2", 0) + 200 * black.get("blocked 2", 0) + 100 * black.get("straight 1", 0) + 25 * black.get("blocked 1", 0) \
                - 1000 * white.get("straight 4", 0) - 700 * white.get("straight 3", 0) - 450 * white.get("blocked 4", 0) - 300 * white.get("blocked 3", 0) - 250 * white.get("straight 2", 0) - 200 * white.get("blocked 2", 0) - 100 * white.get("straight 1", 0) - 25 * white.get("blocked 1", 0)
        return score

    # def HeuristicScore(self):
    #     opp = opponent(self.current_player)
    #     straight4s = 0
    #     straight3s = 0
    #     straight2s = 0
    #     striaght1s = 0
    #     blocked4s = 0
    #     blocked3s = 0
    #     blocked2s = 0
    #     blocked1s = 0

    #     for r in self.rows:
    #         straight4, blocked4 = self.hasFour(r, self.current_player)
    #         straight3, blocked3 = self.hasThree(r, self.current_player)
    #         straight2, blocked2 = self.hasTwo(r, self.current_player)
    #         straight1, blocked1 = self.hasOne(r, self.current_player)
    #         straight4s += straight4
    #         straight3s += straight3
    #         straight2s += straight2
    #         striaght1s += straight1
    #         blocked4s += blocked4
    #         blocked3s += blocked3
    #         blocked2s += blocked2
    #         blocked1s += blocked1
    #     for c in self.cols:
    #         straight4, blocked4 = self.hasFour(c, self.current_player)
    #         straight3, blocked3 = self.hasThree(c, self.current_player)
    #         straight2, blocked2 = self.hasTwo(c, self.current_player)
    #         straight1, blocked1 = self.hasOne(c, self.current_player)
    #         straight4s += straight4
    #         straight3s += straight3
    #         straight2s += straight2
    #         striaght1s += straight1
    #         blocked4s += blocked4
    #         blocked3s += blocked3
    #         blocked2s += blocked2
    #         blocked1s += blocked1
    #     for d in self.diags:
    #         straight4, blocked4 = self.hasFour(d, self.current_player)
    #         straight3, blocked3 = self.hasThree(d, self.current_player)
    #         straight2, blocked2 = self.hasTwo(d, self.current_player)
    #         straight1, blocked1 = self.hasOne(d, self.current_player)
    #         straight4s += straight4
    #         straight3s += straight3
    #         straight2s += straight2
    #         striaght1s += straight1
    #         blocked4s += blocked4
    #         blocked3s += blocked3
    #         blocked2s += blocked2
    #         blocked1s += blocked1

    #     for r in self.rows:
    #         straight4, blocked4 = self.hasFour(r, opp)
    #         straight3, blocked3 = self.hasThree(r, opp)
    #         straight2, blocked2 = self.hasTwo(r, opp)
    #         straight1, blocked1 = self.hasOne(r, opp)
    #         straight4s -= straight4
    #         straight3s -= straight3
    #         straight2s -= straight2
    #         striaght1s -= straight1
    #         blocked4s -= blocked4
    #         blocked3s -= blocked3
    #         blocked2s -= blocked2
    #         blocked1s -= blocked1
    #     for c in self.cols:
    #         straight4, blocked4 = self.hasFour(c, opp)
    #         straight3, blocked3 = self.hasThree(c, opp)
    #         straight2, blocked2 = self.hasTwo(c, opp)
    #         straight1, blocked1 = self.hasOne(c, opp)
    #         straight4s -= straight4
    #         straight3s -= straight3
    #         straight2s -= straight2
    #         striaght1s -= straight1
    #         blocked4s -= blocked4
    #         blocked3s -= blocked3
    #         blocked2s -= blocked2
    #         blocked1s -= blocked1
    #     for d in self.diags:
    #         straight4, blocked4 = self.hasFour(d, opp)
    #         straight3, blocked3 = self.hasThree(d, opp)
    #         straight2, blocked2 = self.hasTwo(d, opp)
    #         straight1, blocked1 = self.hasOne(d, opp)
    #         straight4s -= straight4
    #         straight3s -= straight3
    #         straight2s -= straight2
    #         striaght1s -= straight1
    #         blocked4s -= blocked4
    #         blocked3s -= blocked3
    #         blocked2s -= blocked2
    #         blocked1s -= blocked1

    #     return 1000 * straight4s + 750 * straight3s + 600 * blocked4s + 450 * blocked3s + 300 * straight2s + 225 * blocked2s + 100 * striaght1s + 20 * blocked1s
        # opp = opponent(self.current_player)
        # score = 0
        # lines = self.rows + self.cols + self.diags
        # for line in lines:
        #     print(len(line) - 5)
        #     for i in range(len(line) - 5):
        #         currentPlayerCount = 0
        #         opponentCount = 0
        #         # count the number of stones on each five-line
        #         for p in line[i:i + 5]:
        #             if self.board[p] == self.current_player:
        #                 currentPlayerCount += 1
        #             elif self.board[p] == opp:
        #                 opponentCount += 1
        #         # Is blocked
        #         if currentPlayerCount < 1 or opponentCount < 1:
        #             score += 10 ** currentPlayerCount - 10 ** opponentCount
        # return score
    
    def detectImmediateWin(self, point, color):
        #xxxx.
        #Horizontal capture
        score = 0
        leftIndex = point - 1
        rightIndex = point + 1
        opp_color = opponent(color)

        length = 1
        scoreLeft = 0
        while (self.board[leftIndex] == color or self.board[leftIndex] == EMPTY) and length < 5:
            length += 1 
            if self.board[leftIndex] == color:
                scoreLeft += 1
            if self.board[leftIndex] == EMPTY:
                scoreLeft += 0.5
            leftIndex -= 1
        if (self.board[leftIndex] == opp_color):
            scoreLeft = 0
        score += scoreLeft

        length = 1
        scoreRight = 0
        while (self.board[rightIndex] == color or self.board[rightIndex] == EMPTY) and length < 5:
            length += 1
            if self.board[rightIndex] == color:
                scoreRight += 1
            if self.board[rightIndex] == EMPTY:
                scoreRight += 0.5
            rightIndex += 1
        if (self.board[rightIndex] == opp_color):
            scoreRight = 0
        score += scoreRight

        #Vertical capture
        downIndex = point - self.NS
        upIndex = point + self.NS

        length = 1
        scoreDown = 0
        while (self.board[downIndex] == color or self.board[downIndex] == EMPTY) and length < 5:
            length += 1
            if self.board[downIndex] == color:
                scoreDown += 1
            if self.board[downIndex] == EMPTY:
                scoreDown += 0.5
            downIndex -= self.NS
        if (self.board[downIndex] == opp_color):
            scoreDown = 0
        score += scoreDown

        length = 1
        scoreUp = 0
        while (self.board[upIndex] == color or self.board[upIndex] == EMPTY) and length < 5:
            length += 1
            if self.board[upIndex] == color:
                scoreUp += 1
            if self.board[upIndex] == EMPTY:
                scoreUp += 0.5
            upIndex += self.NS
        if (self.board[upIndex] == opp_color):
            scoreUp = 0
        score += scoreUp

        #Diagonal Captures
        upLeftIndex = point + self.NS - 1
        downRightIndex = point - (self.NS - 1)
        scoreupLeftIndex = 0
        scoreRightIndex = 0

        length = 1
        while (self.board[upLeftIndex] == color or self.board[upLeftIndex] == EMPTY) and length < 5:
            length += 1
            if self.board[upLeftIndex] == color:
                scoreupLeftIndex += 1
            if self.board[upLeftIndex] == EMPTY:
                scoreupLeftIndex += 0.5
            upLeftIndex += self.NS - 1
        if (self.board[upLeftIndex] == opp_color):
            scoreupLeftIndex = 0
        score += scoreupLeftIndex

        length = 1
        while (self.board[downRightIndex] == color or self.board[downRightIndex] == EMPTY) and length < 5:
            length += 1
            if self.board[downRightIndex] == color:
                scoreRightIndex += 1
            if self.board[downRightIndex] == EMPTY:
                scoreRightIndex += 0.5
            downRightIndex -= (self.NS - 1)
        if (self.board[downRightIndex] == opp_color):
            scoreRightIndex = 0
        score += scoreRightIndex

        downLeftIndex = point - (self.NS + 1)
        upRightIndex = point + self.NS + 1
        scoreDownLeftIndex = 0
        scoreUpRightIndex = 0

        length = 1
        while (self.board[downLeftIndex] == color or self.board[downLeftIndex] == EMPTY) and length < 5:
            length += 1
            if self.board[downLeftIndex] == color:
                scoreDownLeftIndex += 1
            if self.board[downLeftIndex] == EMPTY:
                scoreDownLeftIndex += 0.5
            downLeftIndex -= (self.NS + 1)
        if (self.board[downLeftIndex] == opp_color):
            scoreDownLeftIndex = 0
        score += scoreDownLeftIndex

        length = 1
        while (self.board[upRightIndex] == color or self.board[upRightIndex] == EMPTY) and length < 5:
            length += 1
            if self.board[upRightIndex] == color:
                scoreUpRightIndex += 1
            if self.board[upRightIndex] == EMPTY:
                scoreUpRightIndex += 0.5
            upRightIndex += self.NS + 1
        if (self.board[upRightIndex] == opp_color):
            scoreUpRightIndex = 0
        score += scoreUpRightIndex

        return score
    
    def checkInRange(self, point):
        range = 2
        # Top left to bottom right
        it = 1
        in_a_row = 0
        while self.get_color(point - self.NS * it + it) == EMPTY and it <= range:
            in_a_row += 1
            it += 1
        

        it = 1
        while self.get_color(point + self.NS * it - it) == EMPTY and it <= range:
            in_a_row += 1
            it += 1
        
        
        # Left to right
        it = 1
        while self.get_color(point - it) == EMPTY and it <= range:
            in_a_row += 1
            it += 1
        
        
        it = 1 
        while self.get_color(point + it) == EMPTY and it <= range:
            in_a_row += 1
            it += 1
        

        # Top to bottom
        it = 1
        while self.get_color(point - self.NS * it) == EMPTY and it <= range:
            in_a_row += 1
            it += 1

        
        it = 1
        while self.get_color(point + self.NS * it) == EMPTY and it <= range:
            in_a_row += 1
            it += 1


        # Bottom left to top right
        it = 1
        while self.get_color(point - self.NS * it - it) == EMPTY and it <= range:
            in_a_row += 1
            it += 1
        
        it = 1
        while self.get_color(point + self.NS * it + it) == EMPTY and it <= range:
            in_a_row += 1
            it += 1
        
        if in_a_row >= range * 8:
            return False
        return True

    def removeUseless(self, list):
        newList = []
        for move in list:
            if self.checkInRange(move):
                newList.append(move)
        return newList
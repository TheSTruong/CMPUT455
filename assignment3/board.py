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
from random import shuffle

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
        self.black_captures = 0
        self.white_captures = 0

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
        self.board[point] = color
        self.current_player = opponent(color)
        self.last2_move = self.last_move
        self.last_move = point
        O = opponent(color)
        offsets = [1, -1, self.NS, -self.NS, self.NS+1, -(self.NS+1), self.NS-1, -self.NS+1]
        for offset in offsets:
            if self.board[point+offset] == O and self.board[point+(offset*2)] == O and self.board[point+(offset*3)] == color:
                self.board[point+offset] = EMPTY
                self.board[point+(offset*2)] = EMPTY
                if color == BLACK:
                    self.black_captures += 2
                else:
                    self.white_captures += 2
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
    
    """
    Simulation-based Player
    """

    def winner(self, color) -> bool:
        if color == BLACK:
            return self.detect_five_in_a_row() == BLACK or self.black_captures >= 10
        elif color == WHITE:
            return self.detect_five_in_a_row() == WHITE or self.white_captures >= 10
        else:
            return False

    def endOfGame(self) -> bool:
        return self.get_empty_points().size == 0\
            or self.detect_five_in_a_row() != EMPTY\
            or self.black_captures >= 10\
            or self.white_captures >= 10\
            or self.end_of_game()
    
    def simulate(self, color) -> bool:
        to_play = color
        if not self.endOfGame():
            while not self.endOfGame():
                all_moves = list(self.get_empty_points())
                shuffle(all_moves)
                to_play = opponent(to_play)
                self.play_move(all_moves[0], to_play)

        return self.winner(color)

    """
    Rule-based Player
    """
    ### UTIL FUNCTIONS ###
    
    def getLinePositions(self):
        """
        Get the positions of each row, col, and diagonal.
        """
        lines = []
        for line in self.rows:
            lines.append(line)
        for line in self.cols:
            lines.append(line)
        for line in self.diags:
            lines.append(line)
        return lines
    
    def getBoardsize(self):
        return self.size
    
    def swapPlayerPattern(self, patterns):
        for p in patterns:
            for pt in range(len(p)):
                if p[pt] == BLACK:
                    p[pt] = WHITE

    def getPattern(self, line, start, length):
        pattern = []
        if len(line) - start < length:
            return pattern
        for i in range(length):
            pattern.append(self.get_color(line[i + start]))
        return pattern
    
    ### RULE FUNCTIONS ###
    
    def checkWin(self, player) -> List[int]:
        """
        Check if the current player can win directly, return all winning moves if exist, [] otherwise.
        """
        
        # Check for 5 in a row
        opp = opponent(player)
        winning_moves = []
        for line in self.getLinePositions():
            for i in range(len(line) - 4):
                emptyPos = -1
                for pos in line[i: i + 5]:  # get five consecutive positions in a line
                    # Check for capture win
                    if player == BLACK:
                        if self.capturePiecesCount(pos, player) + self.black_captures >= 10:
                            if pos not in winning_moves:
                                winning_moves.append(pos)
                    elif player == WHITE:
                        if self.capturePiecesCount(pos, player) + self.white_captures >= 10:
                            if pos not in winning_moves:
                                winning_moves.append(pos)
                    color = self.get_color(pos)
                    if color == EMPTY:
                        if emptyPos == -1:
                            emptyPos = pos
                        else:   # more than 1 empty pos in this line
                            emptyPos = -1
                            break
                    elif color == opp:
                        emptyPos = -1
                        break
                if emptyPos != -1 and emptyPos not in winning_moves:
                    winning_moves.append(emptyPos)

        return winning_moves
    
    def checkBlockWin(self, player) -> List[int]:
        """
        Check if the opponent can win directly, return all blocking moves if exist, [] otherwise.
        e.g.
        oo.oo, .oooo.
        """
        # current = self.board.current_player
        self.current_player = opponent(player)
        # if the opponent can win directly, then only play a move that blocks the win
        # Checks for 5 in a row or capture > 10 blocks
        blocking_moves = self.checkWin(self.current_player)
        self.current_player = player     # reset the current player

        stallList = []
        moves = self.get_empty_points()
        for move in moves:
            cBoard = self.copy()
            if cBoard.capturePiecesCount(move, player) >= 2:
                cBoard.play_move(move, player)
                reducedCheckList = cBoard.checkWin(opponent(player))
                if len(reducedCheckList) < len(blocking_moves):
                    stallList.append(move)

        for move in stallList:
            if move not in blocking_moves:
                blocking_moves.append(move)
        return blocking_moves

    def checkOpenFour(self, player) -> List[int]:
        """
        if the color to play has a move that creates an open four position of type .XXXX., then play it.
        """
        patterns = [
            [EMPTY, EMPTY, BLACK, BLACK, BLACK, EMPTY],    # ..XXX. mv = 1
            [EMPTY, BLACK, EMPTY, BLACK, BLACK, EMPTY],    # .X.XX. mv = 2
            [EMPTY, BLACK, BLACK, EMPTY, BLACK, EMPTY],    # .XX.X. mv = 3
            [EMPTY, BLACK, BLACK, BLACK, EMPTY, EMPTY]     # .XXX.. mv = 4
        ]

        if player == WHITE:
            self.swapPlayerPattern(patterns)

        line_size = self.getBoardsize()
        pattern_length = 6
        comparisons = line_size - pattern_length + 1

        lines = self.getLinePositions()
        openfour_moves = []
        
        for line in lines:
            for offset in range(comparisons):
                pattern = self.getPattern(line, offset, pattern_length)
                if pattern in patterns:
                    i = patterns.index(pattern)
                    move = line[(i + 1) + offset]
                    if move not in openfour_moves:
                        assert self.get_color(move) == EMPTY
                        openfour_moves.append(move)
        return openfour_moves
    
    def checkCapture(self, player) -> List[int]:
        moveList = []
        moves = self.get_empty_points()
        for move in moves:
            if self.capturePiecesCount(move, player) >= 2:
                moveList.append(move)
        return moveList
    
    def capturePiecesCount(self, point, color):
            capturesThisTurn = 0
            
            #Horizontal capture
            leftIndex = point - 1
            rightIndex = point + 1
            countLeft = 0
            countRight = 0
            captureList = []
            opp_color = opponent(color) 
            while (self.board[leftIndex] == opp_color):
                    captureList.append(leftIndex)
                    countLeft += 1
                    leftIndex -= 1
            if (self.board[leftIndex] == color and countLeft == 2):
                capturesThisTurn += countLeft

            captureList.clear()
            while (self.board[rightIndex] == opp_color):
                    captureList.append(rightIndex)
                    rightIndex += 1
                    countRight += 1   
            if (self.board[rightIndex] == color and countRight == 2):
                capturesThisTurn += countRight  
                    

            #Vertical capture
            downIndex = point - self.NS
            upIndex = point + self.NS
            countUp = 0
            countDown = 0
            captureList = []
            opp_color = opponent(color) 
            while (self.board[downIndex] == opp_color):
                    captureList.append(downIndex)
                    countDown += 1
                    downIndex -= self.NS
            if (self.board[downIndex] == color and countDown == 2):
                capturesThisTurn += countDown
            captureList.clear()
            while (self.board[upIndex] == opp_color):
                    captureList.append(upIndex)
                    upIndex += self.NS
                    countUp += 1   
            if (self.board[upIndex] == color and countUp == 2):
                capturesThisTurn += countUp
              
            #Diagonal Captures
            captureList = []
            upLeftIndex = point + self.NS - 1
            countUpLeft = 0
            downRightIndex = point - (self.NS - 1)
            countDownRight = 0
            while (self.board[upLeftIndex] == opp_color):
                    captureList.append(upLeftIndex)
                    countUpLeft += 1
                    upLeftIndex += self.NS - 1
            if (self.board[upLeftIndex] == color and countUpLeft == 2):
                capturesThisTurn += countUpLeft
                
            while (self.board[downRightIndex] == opp_color):
                    captureList.append(downRightIndex)
                    countDownRight += 1
                    downRightIndex -= (self.NS - 1)
            if (self.board[downRightIndex] == color and countDownRight == 2):
                capturesThisTurn += countDownRight

            captureList = []
            downLeftIndex = point - (self.NS + 1)
            countDownLeft = 0
            upRightIndex = point + self.NS + 1
            countUpRight = 0
            while (self.board[downLeftIndex] == opp_color):
                    captureList.append(downLeftIndex)
                    countDownLeft += 1
                    downLeftIndex -= (self.NS + 1)
            if (self.board[downLeftIndex] == color and countDownLeft == 2):
                capturesThisTurn += countDownLeft
                    
            while (self.board[upRightIndex] == opp_color):
                    captureList.append(upRightIndex)
                    countUpRight += 1
                    upRightIndex += self.NS + 1
            if (self.board[upRightIndex] == color and countUpRight == 2):
                capturesThisTurn += countUpRight
            return capturesThisTurn
    
    def simulateRules(self, color):
        """
        return: (MoveType, MoveList)
        MoveType: {"Win", "BlockWin", "OpenFour", "BlockOpenFour", "Random"}
        MoveList: an unsorted List[int], each element is a move
        """
        result = self.checkWin(color)
        if (len(result) > 0):
            return ("Win", result)
        
        result = self.checkBlockWin(color)
        if (len(result) > 0):
            return ("BlockWin", result)
        
        result = self.checkOpenFour(color)
        if result:
            return ("OpenFour", result)
        
        result = self.checkCapture(color)
        if (len(result) > 0):
            return ("Capture", result)

        # result = [self.generateRandomMove(board)]
        result = self.get_empty_points()
        return ("Random", result)
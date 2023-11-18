#!/usr/bin/python3
# Set the path to your python3 above

"""
Go0 random Go player
Cmput 455 sample code
Written by Cmput 455 TA and Martin Mueller
"""
from gtp_connection import GtpConnection
from board_base import DEFAULT_SIZE, GO_POINT, GO_COLOR
from board import GoBoard
from board_util import GoBoardUtil
from engine import GoEngine

class Go0(GoEngine):
    def __init__(self) -> None:
        """
        Go player that selects moves randomly from the set of legal moves.
        Does not use the fill-eye filter.
        Passes only if there is no other legal move.
        """
        GoEngine.__init__(self, "Go0", 1.0)

    def get_move(self, board: GoBoard, color: GO_COLOR) -> GO_POINT:
        return GoBoardUtil.generate_random_move(board, color, 
                                                use_eye_filter=False)
    
    def solve(self, board: GoBoard):
        """
        A2: Implement your search algorithm to solve a board
        Change if deemed necessary
        """
        pass


def run() -> None:
    """
    start the gtp connection and wait for commands.
    """
    board: GoBoard = GoBoard(DEFAULT_SIZE)
    con: GtpConnection = GtpConnection(Go0(), board)
    con.start_connection()

class SimulationFlatMC:
    """
    A simulation-based "Flat Monte Carlo" player. 
    A simulation consists of a series of moves generated uniformly at random, and ends when the game is over (win or draw).
    The player runs N=10 simulations for each legal move, and picks one move with highest win percentage. 
    You are free to break ties between equally good moves in any way you wish.
    Your player should pass only when the game is over.
    """
    def __init__(self):
        self.num_simulations = 10

    def genmove(self, board, color):
        assert not board.endOfGame()
        moves = board.get_empty_points()
        numMoves = len(moves)
        moveWins = [0] * numMoves
        for i in range(numMoves):
            move = moves[i]
            moveWins[i] = self.simulate_move(board, move, color)
        bestIndex = moveWins.index(max(moveWins))    # break ties by first occurrence in moves
        best = moves[bestIndex]
        assert best in moves
        return best
    
    def simulate_move(self, board, move, color):
        wins = 0
        cboard = board.copy()
        cboard.play_move(move, color)
        for _ in range(self.num_simulations):
            winner = cboard.copy().simulate(color)
            if winner:
                wins += 1
        eval = wins / self.num_simulations
        return eval
    
if __name__ == "__main__":
    run()

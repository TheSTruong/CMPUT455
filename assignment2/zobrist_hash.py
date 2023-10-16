import random
from board_base import (
    BORDER
)

class ZobristHash:
    def __init__(self, boardSize):
        self.boardSize = boardSize * boardSize
        self.zArray = []
        for _ in range(self.boardSize):
            self.zArray.append([random.getrandbits(64) for _ in range(3)])

    # Computes the hash value of a given board
    def computeHash(self, gameState):
        count = 0 
        hash = 0
        for point in gameState.board:
            if point != BORDER:
                if count == 0:
                    hash = self.zArray[count][point]
                else:
                    hash = hash ^ self.zArray[count][point]
                count += 1
        return hash
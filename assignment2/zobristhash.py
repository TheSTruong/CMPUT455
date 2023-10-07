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

class ZobristHash:
    def __init__(self, boardSize):
        self.index = boardSize * boardSize
        self.zArray = []
        for _ in range(self.index):
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

            

    
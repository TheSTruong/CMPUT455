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

class zobristHash2:
    def __init__(self, size):
        self.zobristArray = []
        self.maxSize = size * size
        for _ in range(self.maxSize):
            self.zobristArray.append([random.getrandbits(64) for _ in range(3)])
        print(len(self.zobristArray))
        
    def hash(self, board):
        code = 0 
        count = 0 
        for point in board:
            if point != BORDER:
                if count == 0:
                    code = self.zobristArray[count][point]
                else:
                    code = code ^ self.zobristArray[count][point]
                count += 1
        return code
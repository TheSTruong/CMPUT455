import random


class ZobristHash:
    def __init__(self, boardSize):
        self.index = boardSize * boardSize
        self.array = [[random.getrandbits(64) for j in range(3)]
                      for i in range(self.index)]

    def hash(self, board):
        code = self.array[0][board[0]]
        for i in range(1, self.index):
            code = code ^ self.array[i][board[i]]
        return code
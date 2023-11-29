import numpy as np
import math
from board_base import opponent
from board import GoBoard
import random
import collections

class PreRootNode:
    def __init__(self):
        self.parent = None
        self.childVisits = collections.defaultdict(float)
        self.childEvals = collections.defaultdict(float)


class Node:
    def __init__(self, board, color, move, parent=None):
        self.board = board
        self.parent = parent
        self.expanded = False
        self.color = color
        self.move = move
        self.moves = self.board.get_empty_points()
        self.lenMoves = len(self.moves)
        self.children = {}
        self.childEvals = dict.fromkeys(self.moves, 0)
        self.childVisits = dict.fromkeys(self.moves, 0)
    
    def pprint(self):
        print(self.childEvals)

    def addChild(self, move):
        cboard = self.board.copy()
        cboard.play_move(move, self.color)
        self.children[move] = Node(cboard, opponent(self.color), move, self)
    
    def bestMove(self, maxNode):
        return max(self.childEvals, key=self.childEvals.get) if maxNode else min(self.childEvals, key=self.childEvals.get)
            
    def bestChild(self, exploitationConstant, maxNode):
        values = {}
        for key, value in self.childEvals.items():
            Q = value / (self.childVisits[key] + 1)
            currentNodeVisits = self.parent.childVisits[self.move] + 1
            exploitTerm = exploitationConstant * math.sqrt(math.log(currentNodeVisits) / (self.childVisits[key] + 1))
            if maxNode:
                values[key] = (Q + exploitTerm)
            else:
                values[key] = (Q - exploitTerm)
        if maxNode:
            return max(values, key=values.get)
        else:
            return min(values, key=values.get)
    
    def incNumVisits(self):
        self.parent.childVisits[self.move] += 1

    def setEval(self, eval):
        self.parent.childEvals[self.move] += eval
    
    def childQ(self):
        return self.parent.childEvals[self.move] / self.parent.childVisits

if __name__ == "__main__":
    board = GoBoard(3)
    node1 = Node(board, 1, random.choice(board.get_empty_points()))
    node2 = Node(board, 0, random.choice(board.get_empty_points()), node1)
    node2.incNumVisits()
    print(node1.childVisits)
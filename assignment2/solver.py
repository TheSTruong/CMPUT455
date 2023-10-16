from board import GoBoard
from board_util import GoBoardUtil
from TranspositionTable import TransTable
from zobristhash import ZobristHash
INFINITY = 1000000

def storeResult(tt, code, result):
    tt.store(code, result)
    return result


def alphabetaDL(state: GoBoard, alpha, beta, tt: TransTable, hasher: ZobristHash, depth):
    code = hasher.computeHash(state)
    result = tt.lookup(code)
    if result != None:
        return result

    if state.endOfGame() or depth == 0:
        result = (state.staticallyEvaluateForToPlay(), None)
        storeResult(tt, code, result)
        return result

    legalMoves = state.get_empty_points()
    sortedLegal = sorted(legalMoves, key=state.moveOrdering, reverse=True)
    bestMove = sortedLegal[0]

    for move in sortedLegal:
        state.play_move(move, state.current_player)
        value, mv = alphabetaDL(state, -beta, -alpha, tt, hasher, depth - 1)
        value = -value
        if value > alpha:
            alpha = value
            bestMove = move
        state.undoMove()
        if value >= beta:
            result = (beta, bestMove)
            storeResult(tt, code, result)
            return result

    result = (alpha, bestMove)
    storeResult(tt, code, result)
    return result


def call_alphabetaDL(rootState, tt, hasher, depth):
    return alphabetaDL(rootState, -INFINITY, INFINITY, tt, hasher, depth)
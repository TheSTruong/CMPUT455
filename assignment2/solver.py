from board import GoBoard
from board_util import GoBoardUtil
from TranspositionTable import TransTable
from zobristhash import ZobristHash
INFINITY = 1000000

def storeResult(tt, code, result):
    tt.store(code, result)
    return result


def alphabeta(state: GoBoard, alpha, beta, tt: TransTable, hasher: ZobristHash):
    code = hasher.computeHash(state)
    result = tt.lookup(code)
    if result != None:
        return result

    if state.endOfGame():
        result = (state.staticallyEvaluateForToPlay(), None)
        storeResult(tt, code, result)
        return result

    legalMoves = state.get_empty_points()
    sortedLegal = sorted(legalMoves, key=state.moveOrdering, reverse=True)
    sortedLegal = state.removeUseless(sortedLegal)
    bestMove = sortedLegal[0]

    for move in sortedLegal:
        state.play_move(move, state.current_player)
        value, mv = alphabeta(state, -beta, -alpha, tt, hasher)
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


def call_alphabeta(rootState, tt, hasher):
    return alphabeta(rootState, -INFINITY, INFINITY, tt, hasher)
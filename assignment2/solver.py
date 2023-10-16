from board import GoBoard
from transposition_table import TranspositionTable
from zobrist_hash import ZobristHash
INFINITY = 1000000

def storeResult(tt, code, result):
    tt.store(code, result)
    return result

def alphabetaDL(state, alpha, beta, depth, tt, hasher):
    code = hasher.computeHash(state)
    result = tt.lookup(code)
    if result != None:
        return result

    if state.endOfGame() or depth == 0:
        result = (state.staticallyEvaluateForToPlay(), None)
        return storeResult(tt, code, result)

    legalMoves = state.get_empty_points()
    sortedLegal = sorted(legalMoves, key=state.moveOrdering, reverse=True)
    bestMove = sortedLegal[0]

    for move in sortedLegal:
        state.play_move(move, state.current_player)
        value, mv = alphabetaDL(state, -beta, -alpha, depth - 1, tt, hasher)
        value = -value
        if value > alpha:
            alpha = value
            bestMove = move
        state.undoMove()
        if value >= beta:
            result = (beta, bestMove)
            return storeResult(tt, code, result)

    result = (alpha, bestMove)
    return storeResult(tt, code, result)

def call_alphabetaDL(rootState, depth, tt, hasher):
    return alphabetaDL(rootState, -INFINITY, INFINITY, depth, tt, hasher)
INFINITY = 1000000

def alphabeta(state, alpha, beta):
    if state.endOfGame():
        return state.staticallyEvaluateForToPlay() 
    for m in state.legalMoves():
        state.play(m)
        value = -alphabeta(state, -beta, -alpha)
        if value > alpha:
            alpha = value
        state.undoMove()
        if value >= beta: 
            return beta   # or value in failsoft (later)
    return alpha

# initial call with full window
def callAlphabeta(rootState):
    return alphabeta(rootState, -INFINITY, INFINITY)
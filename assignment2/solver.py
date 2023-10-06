INFINITY = 1000000
from TranspositionTable import TransTable
from zobristhash import ZobristHash
from zobristHash2 import zobristHash2
from board_util import GoBoardUtil



def storeResult(tt, state, result):
    tt.store(state.code(), result)
    return result

def negamaxBoolean(state, tt):
    hasher = ZobristHash(state.size)
    #hasher2 = zobristHash2(state.size)
    code = hasher.hash(GoBoardUtil.get_oneD_board(state))
    
    # result = tt.lookup(state.code())
    # if result != None:
    #     return result
    # if state.endOfGame():
    #     result = state.staticallyEvaluateForToPlay()
    #     return storeResult(tt, state, result)
    # for m in state.get_empty_points():
    #     state.play_move(m)
    #     success = not negamaxBoolean(state, tt)
    #     state.undoMove()
    #     if success:
    #         return storeResult(tt, state, True)
    # return storeResult(tt, state, False)
from __future__ import annotations
from collections import deque
from typing import Generator,Any

class Action:
  PASS='p'
  BET='b'

def playerOnePocketIsHigher(pocket1,pocket2):
  if pocket1=='K':
    return True
  if pocket1=='J':
    return False 
  if pocket2=='K':
    return False 
  if pocket2=='J':
    return True 
  raise ValueError('this should not occur bc one player must have a K or J')

def calcUtilityAtTerminalNode(pockets,actionStr: str):
#   actionStr = ''.join(actions)
  if actionStr=='pp':
    # both checked
    if playerOnePocketIsHigher(*pockets):
      return 1,-1
    else:
      return -1,1
  elif actionStr=='pbp':
    # player 1 folded, player 2 wins the ante
    return -1,1
  elif actionStr=='bp':
    # player 2 folded
    return 1,-1
  elif actionStr=='bb' or actionStr=='pbb':
    if playerOnePocketIsHigher(*pockets):
      return 2,-2
    else:
      return -2,2
  else:
    raise ValueError(f'unexpected actionStr={actionStr}')
#   return utility*ante

def findFirstOccurrences(arr,val,startIdx=0,numOccurrences=1):
  idx,ct=startIdx,0
  while idx<len(arr):
    if arr[idx]==val:
      ct+=1
    if ct>=numOccurrences:
      return True
    idx+=1

RANKS = ['K','Q','J']

class Node:
    def __init__(self,infoSetStr):
        self.infoSetStr=infoSetStr
        self._children=None
        self.data: Any = None

    def isTerminal(self):
        if self._children is None:
            self.children()
        return len(self._children)==0
        
    def children(self) -> list[Node]:
        if self._children is not None:
            return self._children
        if len(self.infoSetStr)>2 and self.infoSetStr[-1]==Action.PASS:
            # they either both checked or one bet and the other folded
            self._children = []
            return self._children
        if len(self.infoSetStr)>=3:
            hasTwoBets=findFirstOccurrences(self.infoSetStr,Action.BET,startIdx=1,numOccurrences=2)
            if hasTwoBets:
                self._children = []
                return self._children
        self._children = [Node(self.infoSetStr+actionStr) for actionStr in [Action.BET,Action.PASS]]
        return self._children
    
    def __str__(self):
        return f'{self.infoSetStr}, isTerminal={self.isTerminal()}, data={self.data}'

def bfsIter(root:Node) -> Generator[Node]:
    q=deque(root.children()) #do not include root node in the returned nodes
    while q:
        node = q.popleft()
        q.extend(node.children())
        yield node

# class InfoSetNode(Node):


class InfoSetData:
    def __init__(self):
        self.actions: dict[str,InfoSetActionData]={}
        self.expectedUtil: float=None

    def __str__(self):
        return f'{self.actions}'

class InfoSetActionData:
    def __init__(self):
        self.strategy=None
        self.belief=None 
        self.util=None

    def __str__(self):
        return f'S={self.strategy}, B={self.belief}, U={self.util}'

    def __repr__(self):
        return self.__str__()
          
class GameRootNode(Node):
    def __init__(self):
        self.infoSetStr=''
        self._children = [Node(rank) for rank in RANKS]

# def init():
#     root = GameRootNode()
#     gameTreeIter = iter(bfsIter(root))
#     while True:
#         node = next(gameTreeIter,None)
#         if not node:
#             break
#         print(node)
# init()

def initCfr():
    # init strategies
    root = GameRootNode()
    gameTreeIter = iter(bfsIter(root))
    while True:
        node = next(gameTreeIter,None)
        if not node:
            break
        # print(node)
        if not node.isTerminal():
            # node.children()
            data = InfoSetData()
            node.data=data
            children = node.children()
            for child in children:
                lastAction = child.infoSetStr[-1]
                actionData = InfoSetActionData()
                actionData.strategy = 1/len(children)
                data.actions[lastAction]=actionData
        print(node)
            
def runCfrIteration():
    # init strategies
    # init terminal utilities
    
    pass 



initCfr()




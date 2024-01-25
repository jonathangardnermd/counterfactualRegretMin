RANKS = ["K", "Q", "J"]
ACTIONS = ["b", "p"]
TERMINAL_ACTION_STR_MAP = {
    "pp",
    "bb",
    "bp",
    "pbb",
    "pbp",
}  # terminal action paths where all decisions have already been made (terminal nodes are NOT considered infoSets here, bc no decision needs to be made)
INFO_SET_ACTION_STRS = {
    "",
    "p",
    "b",
    "pb",
}  # action paths where a decision still needs to be made by one of the players (i.e. actions paths that end on an infoSet)



def getDecidingPlayerForInfoSetStr(infoSetStr: str):
    return (len(infoSetStr)-1)%2

class InfoSetData:
    def __init__(self):
        self.actions: dict[str, InfoSetActionData] = {
            "b": InfoSetActionData(initStratVal=1 / len(ACTIONS)),
            "p": InfoSetActionData(initStratVal=1 / len(ACTIONS)),
        }
        self.beliefs: dict[str, float] = {}
        self.expectedUtil: float = None
        self.likelihood: float = None

    def __str__(self):
        return f"{self.actions}, {self.beliefs}"

    def __repr__(self):
        return self.__str__()


class InfoSetActionData:
    def __init__(self, initStratVal):
        self.strategy = initStratVal
        # self.belief=None
        self.util = None

    def __str__(self):
        return f"S={self.strategy}, U={self.util}"

    def __repr__(self):
        return self.__str__()


# init infoSets
infoSets: dict[str, InfoSetData] = {}
sortedInfoSets = []
for actionsStrs in sorted(INFO_SET_ACTION_STRS, key=lambda x: len(x)):
    for rank in RANKS:
        infoSetStr = rank + actionsStrs
        infoSets[infoSetStr] = InfoSetData()
        sortedInfoSets.append(infoSetStr)

def getPossibleOpponentPockets(pocket):
    return [rank for rank in RANKS if rank != pocket]


def getAncestralInfoSetStrs(infoSetStr) -> list[InfoSetData]:
    if len(infoSetStr) == 1:
        raise ValueError(f'no ancestors of infoSet={infoSetStr}')
    possibleOpponentPockets = getPossibleOpponentPockets(infoSetStr[0])
    return [oppPocket + infoSetStr[1:-1] for oppPocket in possibleOpponentPockets]

def getDescendantInfoSetStrs(infoSetStr, action):
  oppPockets = getPossibleOpponentPockets(infoSetStr[0])
  actionStr = infoSetStr[1:]+action
  return [oppPocket+actionStr for oppPocket in oppPockets]

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

def calcUtilityAtTerminalNode(pocket1,pocket2,actionStr: str):
  if actionStr=='pp':
    # both checked
    if playerOnePocketIsHigher(pocket1,pocket2):
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
    if playerOnePocketIsHigher(pocket1,pocket2):
      return 2,-2
    else:
      return -2,2
  else:
    raise ValueError(f'unexpected actionStr={actionStr}')
  

def updateBeliefs():
    for infoSetStr in sortedInfoSets:
        infoSet = infoSets[infoSetStr]
        if len(infoSetStr) == 1:
            possibleOpponentPockets = getPossibleOpponentPockets(infoSetStr[0])
            for oppPocket in possibleOpponentPockets:
                infoSet.beliefs[oppPocket] = 1 / len(possibleOpponentPockets)
        else:
            ancestralInfoSetStrs = getAncestralInfoSetStrs(infoSetStr)
            lastAction = infoSetStr[-1]
            tot = 0
            for oppInfoSetStr in ancestralInfoSetStrs:
                oppInfoSet=infoSets[oppInfoSetStr]
                tot += oppInfoSet.actions[lastAction].strategy #Strategy.data.getVal(infoSet, lastAction)
            for oppInfoSetStr in ancestralInfoSetStrs:
                oppInfoSet=infoSets[oppInfoSetStr]
                oppPocket = oppInfoSetStr[0]
                infoSet.beliefs[oppPocket]=infoSet.actions[lastAction].strategy / tot
    return

def updateUtilitiesForInfoSetStr(infoSetStr):
    playerIdx = getDecidingPlayerForInfoSetStr(infoSetStr)
    infoSet = infoSets[infoSetStr]
    beliefs = infoSet.beliefs
    for action in ACTIONS:
        actionStr=infoSetStr[1:]+action 
        descendentInfoSetStrs = getDescendantInfoSetStrs(infoSetStr,action)
        utilFromInfoSets,utilFromTerminalNodes=0,0
        for descendentInfoSetStr in descendentInfoSetStrs:
            probOfThisInfoSet = beliefs[descendentInfoSetStr[0]]
            pockets=[0,0]
            pockets[playerIdx]=infoSetStr[0]
            pockets[1-playerIdx]=descendentInfoSetStr[0]
            if actionStr in TERMINAL_ACTION_STR_MAP:
                # choosing this action moves us to a terminal node
                utils=calcUtilityAtTerminalNode(*pockets,actionStr)
                utilFromTerminalNodes+=probOfThisInfoSet*utils[playerIdx]
            else:
                # choosing this action moves us to an opponent infoSet where they will choose an action (depending on their strategy, which is also OUR strategy bc this is self-play)
                descendentInfoSet = infoSets[descendentInfoSetStr]
                for oppAction in ACTIONS:
                    probOfOppAction = descendentInfoSet.actions[oppAction].strategy
                    destinationInfoSetStr = infoSetStr+action+oppAction
                    destinationActionStr = destinationInfoSetStr[1:]
                    if destinationActionStr in TERMINAL_ACTION_STR_MAP:
                        # our opponent choosing that action moves us to a terminal node 
                        utils=calcUtilityAtTerminalNode(*pockets,destinationActionStr)
                        utilFromTerminalNodes+=probOfThisInfoSet*probOfOppAction*utils[playerIdx]
                    else:
                        # it's another infoSet, and we've already calculated the expectedUtility of this infoSet
                        destinationInfoSet = infoSets[destinationInfoSetStr]
                        utilFromInfoSets+=probOfThisInfoSet*probOfOppAction*destinationInfoSet.expectedUtil

        infoSet.actions[action].util=utilFromInfoSets+utilFromTerminalNodes
    infoSet.expectedUtil = 0
    for action in ACTIONS:
        actionData = infoSet.actions[action]
        infoSet.expectedUtil+=actionData.strategy*actionData.util 



updateBeliefs()

for infoSetStr in reversed(sortedInfoSets):
    updateUtilitiesForInfoSetStr(infoSetStr)
print(infoSets)

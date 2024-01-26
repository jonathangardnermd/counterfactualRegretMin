from __future__ import annotations
from tabulate import tabulate
import sys

infoSets: dict[str, InfoSetData] = {}
sortedInfoSets = []

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
        self.likelihood: float = 0

    @staticmethod
    def printInfoSetDataTable(infoSets: dict[str,InfoSetData]):
        rows=[]
        for infoSetStr in sortedInfoSets:
            infoSet = infoSets[infoSetStr]
            row=[infoSetStr,*infoSet.getStrategyTableData(),infoSetStr,*infoSet.getBeliefTableData(),infoSetStr,*infoSet.getUtilityTableData(),f'{infoSet.expectedUtil:.2f}',f'{infoSet.likelihood:.2f}',infoSetStr,*infoSet.getGainTableData()]
            rows.append(row)
        
        headers = ["InfoSet","Strat:Bet", "Strat:Pass", "---","Belief:H", "Belief:L", "---","Util:Bet","Util:Pass","ExpectedUtil","Likelihood","---","TotGain:Bet","TotGain:Pass"]

        if 'tabulate' in sys.modules:
            print(tabulate(rows, headers=headers,tablefmt="pretty",stralign="left"))
        else:
            # Calculate maximum width for each column
            max_widths = [max(len(str(cell)) for cell in column) for column in zip(headers, *rows)]

            # Print headers
            header_line = "   ".join(header.ljust(width) for header, width in zip(headers, max_widths))
            print(header_line)

            # Print separator
            separator_line = "-" * (sum(max_widths)+3*len(headers))
            print(separator_line)

            # Print rows
            for row in rows:
                row_line = "   ".join(str(cell).ljust(width) for cell, width in zip(row, max_widths))
                print(row_line)

    def getStrategyTableData(self):
        return [f'{self.actions[action].strategy:.2f}' for action in ACTIONS]
    
    def getUtilityTableData(self):
        return [f'{self.actions[action].util:.2f}' for action in ACTIONS]
    
    def getGainTableData(self):
        return [f'{self.actions[action].cumulativeGain:.2f}' for action in ACTIONS]
    
    def getBeliefTableData(self):
        return [f'{self.beliefs[oppPocket]:.2f}' for oppPocket in self.beliefs.keys()]

class InfoSetActionData:
    def __init__(self, initStratVal):
        self.strategy = initStratVal
        self.util = None
        self.cumulativeGain = initStratVal #initialize it to be consistent with the initial strategies... not sure if this is necessary though

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
  

def initInfoSets():
    for actionsStrs in sorted(INFO_SET_ACTION_STRS, key=lambda x:len(x)):
        for rank in RANKS:
            infoSetStr = rank + actionsStrs
            infoSets[infoSetStr] = InfoSetData()
            sortedInfoSets.append(infoSetStr)

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
                tot += oppInfoSet.actions[lastAction].strategy
            for oppInfoSetStr in ancestralInfoSetStrs:
                oppInfoSet=infoSets[oppInfoSetStr]
                oppPocket = oppInfoSetStr[0]
                infoSet.beliefs[oppPocket]=oppInfoSet.actions[lastAction].strategy / tot
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

def calcInfoSetLikelihoods():
  for infoSetStr in sortedInfoSets:
    infoSet=infoSets[infoSetStr]
    possibleOppPockets=getPossibleOpponentPockets(infoSetStr[0])
    if len(infoSetStr)==1:
      infoSet.likelihood=1/len(RANKS)
    elif len(infoSetStr)==2:
      for oppPocket in possibleOppPockets:
        oppInfoSet = infoSets[oppPocket + infoSetStr[1:-1]]
        infoSet.likelihood+=1/len(RANKS)*oppInfoSet.actions[infoSetStr[-1]].strategy
    else:
      for oppPocket in possibleOppPockets:
        oppInfoSet = infoSets[oppPocket + infoSetStr[1:-1]]
        infoSetTwoLevelsAgo = infoSets[infoSetStr[:-2]] 
        infoSet.likelihood+=infoSetTwoLevelsAgo.likelihood*oppInfoSet.actions[infoSetStr[-1]].strategy/len(possibleOppPockets)

def calcGains():
  totAddedGain=0.0
  for infoSetStr in sortedInfoSets:
    infoSet = infoSets[infoSetStr]
    for action in ACTIONS:
      utilForActionPureStrat = infoSet.actions[action].util 
      gain = max(0,utilForActionPureStrat-infoSet.expectedUtil)
      totAddedGain+=gain
      infoSet.actions[action].cumulativeGain+=gain * infoSet.likelihood
  return totAddedGain

def updateStrategy():
  for infoSetStr in sortedInfoSets:
    infoSet = infoSets[infoSetStr]
    gains = [infoSet.actions[action].cumulativeGain for action in ACTIONS] 
    totGains = sum(gains)
    for action in ACTIONS:
      gain = infoSet.actions[action].cumulativeGain
      infoSet.actions[action].strategy = gain/totGains

def setInitialStrategiesToSpecificValues():
    # player 1
    infoSets['K'].actions['b'].strategy=2/3
    infoSets['K'].actions['p'].strategy=1/3

    infoSets['Q'].actions['b'].strategy=1/2
    infoSets['Q'].actions['p'].strategy=1/2

    infoSets['J'].actions['b'].strategy=1/3
    infoSets['J'].actions['p'].strategy=2/3

    infoSets['Kpb'].actions['b'].strategy=1
    infoSets['Kpb'].actions['p'].strategy=0

    infoSets['Qpb'].actions['b'].strategy=1/2
    infoSets['Qpb'].actions['p'].strategy=1/2

    infoSets['Jpb'].actions['b'].strategy=0
    infoSets['Jpb'].actions['p'].strategy=1

    # player2
    infoSets['Kb'].actions['b'].strategy=1
    infoSets['Kb'].actions['p'].strategy=0
    infoSets['Kp'].actions['b'].strategy=1
    infoSets['Kp'].actions['p'].strategy=0

    infoSets['Qb'].actions['b'].strategy=1/2
    infoSets['Qb'].actions['p'].strategy=1/2
    infoSets['Qp'].actions['b'].strategy=2/3
    infoSets['Qp'].actions['p'].strategy=1/3

    infoSets['Jb'].actions['b'].strategy=0
    infoSets['Jb'].actions['p'].strategy=1
    infoSets['Jp'].actions['b'].strategy=1/3
    infoSets['Jp'].actions['p'].strategy=2/3

# DO STUFF
initInfoSets()
# setInitialStrategiesToSpecificValues()

# numIterations=30000
numIterations=1
for i in range(numIterations):
    updateBeliefs()

    for infoSetStr in reversed(sortedInfoSets):
        updateUtilitiesForInfoSetStr(infoSetStr)

    calcInfoSetLikelihoods()
    totGains = calcGains()
    updateStrategy()

    print('TOT_GAINS',totGains)

InfoSetData.printInfoSetDataTable(infoSets)

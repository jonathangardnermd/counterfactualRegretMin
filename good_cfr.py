from __future__ import annotations

# COMMENT THE NEXT TWO LINES OUT IF YOU WANT TO RUN WITH VANILLA PYTHON WITHOUT NEEDING TO INSTALL tabulate and matplotlib in a venv
from tabulate import tabulate
import matplotlib.pyplot as plt
import sys

infoSets: dict[str, InfoSetData] = {}
sortedInfoSets = []

RANKS = ["K", "Q", "J"]
ACTIONS = ["b", "p"]

# The TERMINAL_ACTION_STR_MAP and INFO_SET_ACTION_STRS vars would generally need to be computed for larger games, but Kuhn poker is so simple that computing them is overkill. Therefore, we hardcode.
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
    # returns the playerIdx of the player whose turn it is at this infoSet. 
    return (len(infoSetStr)-1)%2

# the values we're updating are all indexed by the infoSet, so this class will store all the data for a particular infoSet in a single object
class InfoSetData:
    def __init__(self):
        # initialize the strategy for the infoSet to be uniform (e.g. 50% bet, 50% pass)
        self.actions: dict[str, InfoSetActionData] = {
            "b": InfoSetActionData(initStratVal=1 / len(ACTIONS)),
            "p": InfoSetActionData(initStratVal=1 / len(ACTIONS)),
        }
        self.beliefs: dict[str, float] = {}
        self.expectedUtil: float = None
        self.likelihood: float = None

    @staticmethod
    def printInfoSetDataTable(infoSets: dict[str,InfoSetData]):
        # print the various values for the infoSets in a nicely formatted table
        rows=[]
        for infoSetStr in sortedInfoSets:
            infoSet = infoSets[infoSetStr]
            row=[infoSetStr,*infoSet.getStrategyTableData(),infoSetStr,*infoSet.getBeliefTableData(),infoSetStr,*infoSet.getUtilityTableData(),f'{infoSet.expectedUtil:.2f}',f'{infoSet.likelihood:.2f}',infoSetStr,*infoSet.getGainTableData()]
            rows.append(row)
        
        headers = ["InfoSet","Strat:Bet", "Strat:Pass", "---","Belief:H", "Belief:L", "---","Util:Bet","Util:Pass","ExpectedUtil","Likelihood","---","TotGain:Bet","TotGain:Pass"]

        # in case you don't want to create a venv to install the tabulate package, this code will work without it. 
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

# Each infoSet has two actions that a player can choose to perform at it, and the infoSet-action pairs have various values we're updating, etc. This class will store all these action-specific values for the infoSet
class InfoSetActionData:
    def __init__(self, initStratVal):
        self.strategy = initStratVal
        self.util = None
        self.cumulativeGain = initStratVal #initialize it to be consistent with the initial strategies... not sure if this is necessary though

def getPossibleOpponentPockets(pocket):
    # if one player has a K (i.e. pocket=='K'), then the other player can have any card other than a K (i.e. ['Q','J'])
    return [rank for rank in RANKS if rank != pocket]

def getAncestralInfoSetStrs(infoSetStr) -> list[InfoSetData]:
    # given an infoSet, return the 2 opponent infoSets that can lead to it (e.g. given 'Kpb', return ['Qp','Jp'])
    if len(infoSetStr) == 1:
        raise ValueError(f'no ancestors of infoSet={infoSetStr}')
    possibleOpponentPockets = getPossibleOpponentPockets(infoSetStr[0])
    return [oppPocket + infoSetStr[1:-1] for oppPocket in possibleOpponentPockets]

def getDescendantInfoSetStrs(infoSetStr, action):
  # given an infoSet and an action to perform at that infoSet, return the 2 opponent infoSets that can result from it 
  # e.g. given infoSetStr='Kpb' and action='p', return ['Qpbp','Jpbp']
  oppPockets = getPossibleOpponentPockets(infoSetStr[0])
  actionStr = infoSetStr[1:]+action
  return [oppPocket+actionStr for oppPocket in oppPockets]

def playerOnePocketIsHigher(pocket1,pocket2):
  # return True if pocket1 beats pocket2, False otherwise (and pocket1 cannot equal pocket2 bc ranks are not re-used)
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
  # given a terminal actionStr and the players' pocket cards, return the payoff tuple for player 1 and player 2 
  # e.g. given 'K','Q','bb' return 2,-2 because player 1 has the higher card and both players put an ante and a bet in the pot, so player 1 gains $2 (and player 2 loses $2 bc it's a zero-sum game)
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
    # initialize the infoSet objects. They are 
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
  # calculate the likelihood (aka "reach probability") of reaching each infoSet assuming the infoSet "owner" (the player who acts at that infoSet) is trying to get there 
  # (and assuming the other player simply plays according to the current strategy)
  for infoSetStr in sortedInfoSets:
    infoSet=infoSets[infoSetStr]
    infoSet.likelihood=0 #reset it to zero on each iteration so the likelihoods don't continually grow (bc we're using += below)
    possibleOppPockets=getPossibleOpponentPockets(infoSetStr[0])
    if len(infoSetStr)==1:
      # the likelihood of the top-level infoSets (K, Q, J) is determined solely by nature/randomSampling. (i.e. the 'K' infoSet likelihood is 1/3, as is 'Q' and 'J')
      infoSet.likelihood=1/len(RANKS)
    elif len(infoSetStr)==2:
      # the second-tier infoSet likelihoods. Note, the second-tier infoSet 'Qp' may have resulted from the top-tier infoSets 'K' or 'J' 
      # depending on which card player 1 was dealt. The likelihood of 'Qp' is therefore the addition of the likelihood along each of these possible paths
      for oppPocket in possibleOppPockets:
        oppInfoSet = infoSets[oppPocket + infoSetStr[1:-1]]
        infoSet.likelihood+=1/len(RANKS)*oppInfoSet.actions[infoSetStr[-1]].strategy
    else:
      # For infoSets on the third-tier and beyond, we can use the likelihoods of the infoSets two levels before to calculate their likelihoods.
      # Note, we can't simply use the infoSet one tier before because that's the opponent's infoSet, and the calculation of likelihoods 
      # assumes that the infoSet's "owner" is trying to reach the infoSet. Therefore, when calculating a liklihood for player 1's infoSet, 
      # we can only use the likelihood of an ancestral infoSet if the ancestral infoSet is also "owned" by player 1, and the closest such infoSet is 2 levels above.
      # Note also, that although their are 2 ancestral infoSets one tier before, there is only one ancestral infoSet two tiers before. 
      # For example, 'Kpb' has one-tier ancestors 'Qp' and 'Jp', but only a single two-tier ancestor: 'K'
      for oppPocket in possibleOppPockets:
        oppInfoSet = infoSets[oppPocket + infoSetStr[1:-1]]
        infoSetTwoLevelsAgo = infoSets[infoSetStr[:-2]] # grab the closest ancestral infoSet with the same owner as the infoSet for which we seek to calculate likelihood
        ancestorLikelihood = infoSetTwoLevelsAgo.likelihood/len(possibleOppPockets) # note, each oppInfoSet is essentially slicing up the infoSetTwoLevelsAgo because they're each assuming a specific oppPocket. Therefore, we must divide by len(possibleOppPockets) 
        infoSet.likelihood+=ancestorLikelihood*oppInfoSet.actions[infoSetStr[-1]].strategy 

def calcGains():
  # for each action at each infoSet, calc the gains for this round weighted by the likelihood (aka "reach probability")
  # and add these weighted gains for this round to the cumulative gains over all previous iterations for that infoSet-action pair
  totAddedGain=0.0
  for infoSetStr in sortedInfoSets:
    infoSet = infoSets[infoSetStr]
    for action in ACTIONS:
      utilForActionPureStrat = infoSet.actions[action].util 
      gain = max(0,utilForActionPureStrat-infoSet.expectedUtil)
      totAddedGain+=gain
      infoSet.actions[action].cumulativeGain+=gain * infoSet.likelihood
  return totAddedGain # return the totAddedGain as a rough measure of convergence (it should grow smaller as we iterate more)

def updateStrategy():
  # update the strategy for each infoSet-action pair to be proportional to the cumulative gain for that action over all previous iterations
  for infoSetStr in sortedInfoSets:
    infoSet = infoSets[infoSetStr]
    gains = [infoSet.actions[action].cumulativeGain for action in ACTIONS] 
    totGains = sum(gains)
    for action in ACTIONS:
      gain = infoSet.actions[action].cumulativeGain
      infoSet.actions[action].strategy = gain/totGains

def setInitialStrategiesToSpecificValues():
    # to align with the values found in this youtube video (https://www.youtube.com/watch?v=ygDt_AumPr0&t=668s: Counterfactual Regret Minimization (AGT 26) by Professor Bryce),
    # you can optionally initialize the strategies to the same values he uses 
    # (and you'd only run a single iteration, obviously, because he works out all the values of strategy/belief/util by hand for a single iteration). 

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

##################################################################################################################
# We're done defining functions, etc. Now it's time to invoke them and DO STUFF!
##################################################################################################################
initInfoSets()
# setInitialStrategiesToSpecificValues() # uncomment in order to get the values in professor bryce's youtube video: https://www.youtube.com/watch?v=ygDt_AumPr0&t=668s: Counterfactual Regret Minimization (AGT 26)

numIterations=300000 # best numIterations for closest convergence
# numIterations=3000 # best numIterations for plotting the convergence
# numIterations=1 # best to checking that the output values match professor bryce's youtube video: https://www.youtube.com/watch?v=ygDt_AumPr0&t=668s: Counterfactual Regret Minimization (AGT 26)
totGains = []

# only plot the gain from every xth iteration (in order to lessen the amount of data that needs to be plotted)
numGainsToPlot=100 
gainGrpSize = numIterations//numGainsToPlot 

for i in range(numIterations):
    updateBeliefs()

    for infoSetStr in reversed(sortedInfoSets):
        updateUtilitiesForInfoSetStr(infoSetStr)

    calcInfoSetLikelihoods()
    totGain = calcGains()
    if i%gainGrpSize==0: # every 10 or 100 or x rounds, save off the gain so we can plot it afterwards and visually see convergence
       totGains.append(totGain)
       print(f'TOT_GAIN {totGain: .3f}')
    updateStrategy()

InfoSetData.printInfoSetDataTable(infoSets)

# The if statement is just meant to make the script easier to run if you don't want to install matplotlib
if 'matplotlib' in sys.modules:
    print(f'Plotting {len(totGains)} totGains')
    # Generate random x, y coordinates
    x = [x*gainGrpSize for x in range(len(totGains))]
    y = totGains

    # Create scatter plot
    plt.scatter(x, y)

    # Set title and labels
    plt.title('Total Gain per iteration')
    plt.xlabel(f'Iteration # ')
    plt.ylabel('Total Gain In Round')

    # Display the plot
    plt.show()


ante=1

RANK_NAMES = ['K','Q','J']

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

def calcUtilityAtTerminalNode(pockets,actions: list):
  actionStr = ''.join(actions)
  utility=None
  if actionStr=='pp':
    # both checked
    if playerOnePocketIsHigher(*pockets):
      utility= 1,-1
    else:
      utility= -1,1
  elif actionStr=='pbp':
    # player 1 folded, player 2 wins the ante
    utility= -1,1
  elif actionStr=='bp':
    # player 2 folded
    utility= 1,-1
  elif actionStr=='bb' or actionStr=='pbb':
    if playerOnePocketIsHigher(*pockets):
      utility= 2,-2
    else:
      utility= -2,2
  else:
    raise ValueError(f'unexpected actionStr={actionStr}')
  return utility*ante

def getAllPockets():
    pockets=[]
    for rank1 in RANK_NAMES:
        for rank2 in RANK_NAMES:
            if rank1!=rank2:
                pockets.append(rank1+rank2)
    return pockets

ALL_PAIRS = getAllPockets()
# print(getAllPockets())

def getPossibleOpponentPockets(pocket):
    return [rank for rank in RANK_NAMES if rank!=pocket]

def getOppInfoSets(infoSet, action):
  oppPockets = getPossibleOpponentPockets(infoSet[0])
  actionStr = infoSet[1:]+action
  return [oppPocket+actionStr for oppPocket in oppPockets]

# print(getPossibleOpponentPockets('Q'))

def getAncestralInfoSets(infoSet):
    if len(infoSet)==1:
        # there are no ancestralInfoSets
        return None
    possibleOpponentPockets = getPossibleOpponentPockets(infoSet[0])
    return [oppPocket+infoSet[1:-1] for oppPocket in possibleOpponentPockets]

# print(getAncestralInfoSets('Qpb'))
    

class NestedMap:
  def __init__(self):
     self.outerMap={}

  def getVal(self,outerKey,innerKey):
    return self.outerMap[outerKey][innerKey]
  
  def setVal(self,outerKey,innerKey,val):
    if outerKey not in self.outerMap:
      self.outerMap[outerKey]={}
    innerMap=self.outerMap[outerKey]
    innerMap[innerKey]=val 

  def addToVal(self,outerKey,innerKey,val):
    innerMap=self.outerMap[outerKey]
    innerMap[innerKey]+=val 

  def getInnerMap(self,outerKey):
    return self.outerMap[outerKey]
  
  def __str__(self):
    s=''
    for outerKey in sorted(self.outerMap.keys(),key=lambda x: len(x), reverse=True):
      innerMap = self.outerMap[outerKey]
      s+=outerKey+'\n'
      for innerKey in innerMap.keys():
        s+=f'\t{innerKey}={innerMap[innerKey]}\n'
    return s

class Strategy:
   data = NestedMap()
class Beliefs:
   data = NestedMap()
class Utilities:
   data=NestedMap()
class Gains:
  data=NestedMap()


class Action:
  PASS='p'
  BET='b'

def findFirstOccurrences(arr,val,numOccurrences=1):
  idx,ct=0,0
  while idx<len(arr):
    if arr[idx]==val:
      ct+=1
    if ct>=numOccurrences:
      return True
    idx+=1

class Hx:
  def __init__(self):
    self.pockets=None
    self.actions=[]

  def getInfoSetStr(self):
    playerIdx = len(self.actions)%2
    return self.pockets[playerIdx]+''.join(self.actions)

  def nextActions(self):
    if len(self.actions)>=2:

      hasTwoBets=findFirstOccurrences(self.actions,Action.BET,numOccurrences=2)
      if hasTwoBets:
        return []
    if len(self.actions)>1 and self.actions[-1]==Action.PASS:
      # they either both checked or one bet and the other folded
      return []
    return [Action.PASS, Action.BET]

  def popAction(self):
    action = self.actions.pop()

  def appendAction(self,action):
    self.actions.append(action)

  def __str__(self):
    return f'{self.pockets}, {self.actions}'
  

class GameTreeIterator:
  def __init__(self):
    self.hx=Hx()

  def initFullTree(self):
    for pr in ALL_PAIRS:
      self.hx.pockets=pr
      self.initTraverse()

  def initTraverse(self):
    # print(self.hx)
    infoSetStr=self.hx.getInfoSetStr()
    possibleActions = self.hx.nextActions()
    if not possibleActions:
      # print(f'Terminal: {self.hx}')
      return
    for action in possibleActions:
      initStrategies(infoSetStr,action,1/len(possibleActions))
      initUtilitiesForInfoSets(infoSetStr,action)

      self.hx.appendAction(action)
      self.initTraverse() #recursive call
      self.hx.popAction()  
      
  def traverseFullTree(self):
    for pr in ALL_PAIRS:
      self.hx.pockets=pr
      self.traverse()

  def traverse(self):
    # print(self.hx)
    possibleActions = self.hx.nextActions()
    if not possibleActions:
      # print(f'Terminal: {self.hx}')
      return
    
    updateBeliefs(self.hx)
    for action in possibleActions:
      self.hx.appendAction(action)
      self.traverse() #recursive call
      self.hx.popAction()   

class InfoSetIterator:
  def __init__(self):
    pass


def initStrategies(infoSetStr,action,numPossibleActions):
  Strategy.data.setVal(infoSetStr,action,1/numPossibleActions)

def initUtilitiesForInfoSets(infoSetStr,action):
  Utilities.data.setVal(infoSetStr,action,0)

def updateBeliefs(hx:Hx,ignore=None, ignore2=None):  
  infoSetStr = hx.getInfoSetStr()
  if len(infoSetStr)==1:
    possibleOpponentPockets=getPossibleOpponentPockets(infoSetStr[0])
    for oppPocket in possibleOpponentPockets:  
      Beliefs.data.setVal(infoSetStr,oppPocket,1/len(possibleOpponentPockets))
    return 
  ancestralInfoSets=getAncestralInfoSets(infoSetStr)
  lastAction = infoSetStr[-1]
  tot = 0
  for infoSet in ancestralInfoSets:
    tot+=Strategy.data.getVal(infoSet,lastAction)
  for infoSet in ancestralInfoSets:
    Beliefs.data.setVal(infoSetStr,infoSet[0],Strategy.data.getVal(infoSet,lastAction)/tot)

def calcUtilitiesForInfoSet(infoSet,expectedUtilsByInfoSet):
  playerIdx = (len(infoSet)-1)%2
  ALL_INFO_SETS = Strategy.data.outerMap.keys()
  beliefs = Beliefs.data.getInnerMap(infoSet)
  possibleActions = Strategy.data.getInnerMap(infoSet).keys()
  for action in possibleActions:
    # expectedUtilForAction=0
    utilFromInfoSets,utilFromTerminalNodes=0,0
    oppInfoSets=getOppInfoSets(infoSet,action)
    for oppInfoSet in oppInfoSets:
      probOfThisInfoSet = beliefs[oppInfoSet[0]]
      pockets=[0,0]
      pockets[playerIdx]=infoSet[0]
      pockets[1-playerIdx]=oppInfoSet[0]
      pocketsStr = ''.join(pockets)
      if oppInfoSet not in ALL_INFO_SETS:
        utils = calcUtilityAtTerminalNode(pocketsStr,oppInfoSet[1:])
        # util = util[playerIdx]
        utilFromTerminalNodes+=probOfThisInfoSet*utils[playerIdx]
        # print(f'oppInfoSet={oppInfoSet}, infoSet={infoSet}, playerIdx={playerIdx}, utils={utils}, beliefs={beliefs}')

        continue

      oppStrat = Strategy.data.getInnerMap(oppInfoSet)
      for oppAction in oppStrat.keys():
        probOfOppAction = oppStrat[oppAction]

        destinationInfoSet = infoSet+action+oppAction
        if destinationInfoSet in ALL_INFO_SETS:
          # it's another infoSet, and we've already calculated the expectedUtility of this infoSet
          utilFromInfoSets+=probOfThisInfoSet*probOfOppAction*expectedUtilsByInfoSet[destinationInfoSet]
        else:
          # it's a terminal node
          utils=calcUtilityAtTerminalNode(pocketsStr,destinationInfoSet[1:])
          utilFromTerminalNodes+=probOfThisInfoSet*probOfOppAction*utils[playerIdx]
          # print(f'infoSet={infoSet}, destinationInfoSet={pocketsStr,destinationInfoSet[1:]}, probOfThisInfoSet={probOfThisInfoSet}, probOfOppAction={probOfOppAction}, util={utils}')

    Utilities.data.setVal(infoSet,action,utilFromInfoSets+utilFromTerminalNodes)
  expectedUtilsByInfoSet[infoSet] = 0
  for action in possibleActions:
    strat = Strategy.data.getVal(infoSet,action)
    util = Utilities.data.getVal(infoSet,action)
    expectedUtilsByInfoSet[infoSet]+=strat*util 

def initGains():
  for infoSet in Strategy.data.outerMap.keys():
    innerMap = Strategy.data.outerMap[infoSet]
    for action in innerMap.keys():
      stratVal = innerMap[action]
      Gains.data.setVal(infoSet,action,stratVal)



def calcInfoSetLikelihoods():
  for infoSet in sorted(Strategy.data.outerMap.keys(), key=lambda x: len(x)):
    possibleOppPockets=getPossibleOpponentPockets(infoSet[0])
    if len(infoSet)==1:
      infoSetLikelihoods[infoSet]=1/len(RANK_NAMES)
    elif len(infoSet)==2:
      for oppPocket in possibleOppPockets:
        oppInfoSet = oppPocket + infoSet[1:-1]
        infoSetLikelihoods[infoSet]+=1/len(RANK_NAMES)*Strategy.data.getVal(oppInfoSet,infoSet[-1])
    else:
      for oppPocket in possibleOppPockets:
        oppInfoSet = oppPocket + infoSet[1:-1]
        infoSetLikelihoods[infoSet]+=infoSetLikelihoods[infoSet[:-2]]/len(possibleOppPockets)*Strategy.data.getVal(oppInfoSet,infoSet[-1])
        # print(f'likelihood: infoSet={infoSet}, oppInfoSet={oppInfoSet}, infoSetLikelihoods[infoSet[:-2]]={infoSetLikelihoods[infoSet[:-2]]}, stratVal={Strategy.data.getVal(oppInfoSet,infoSet[-1])}')


def calcGains(expectedUtilsByInfoSet,showGains=False):
  calcInfoSetLikelihoods()
  totAddedGain=0.0
  for infoSet in sortedInfoSet:
    possibleActions = Strategy.data.getInnerMap(infoSet).keys()
    for action in possibleActions:
      utilForActionPureStrat = Utilities.data.getVal(infoSet,action)
      gain = max(0,utilForActionPureStrat-expectedUtilsByInfoSet[infoSet])
      if showGains and gain>.01:
        print(f'infoSet={infoSet}, action={action}, gain={gain}, utilForActionPureStrat={utilForActionPureStrat}, expectedUtilsByInfoSet[infoSet]={expectedUtilsByInfoSet[infoSet]}')
      totAddedGain+=gain
      Gains.data.addToVal(infoSet,action,gain*infoSetLikelihoods[infoSet])
  return totAddedGain

def updateStrategy():
  for infoSet in sortedInfoSet:
    gains = Gains.data.getInnerMap(infoSet)
    totGains = sum(gains.values())
    possibleActions = Strategy.data.getInnerMap(infoSet).keys()
    for action in possibleActions:
      Strategy.data.setVal(infoSet,action,gains[action]/totGains)


# DO STUFF

g=GameTreeIterator()
g.initFullTree()
# print(Strategy.data)
# print(Utilities.data)

# #player 1
# Strategy.data.setVal('K','b',2/3)
# Strategy.data.setVal('K','p',1/3)

# Strategy.data.setVal('Q','b',1/2)
# Strategy.data.setVal('Q','p',1/2)

# Strategy.data.setVal('J','b',1/3)
# Strategy.data.setVal('J','p',2/3)

# Strategy.data.setVal('Kpb','b',1)
# Strategy.data.setVal('Kpb','p',0)

# Strategy.data.setVal('Qpb','b',1/2)
# Strategy.data.setVal('Qpb','p',1/2)

# Strategy.data.setVal('Jpb','b',0)
# Strategy.data.setVal('Jpb','p',1)

# #player2
# Strategy.data.setVal('Kb','b',1)
# Strategy.data.setVal('Kb','p',0)

# Strategy.data.setVal('Kp','b',1)
# Strategy.data.setVal('Kp','p',0)

# Strategy.data.setVal('Qb','b',1/2)
# Strategy.data.setVal('Qb','p',1/2)

# Strategy.data.setVal('Qp','b',2/3)
# Strategy.data.setVal('Qp','p',1/3)

# Strategy.data.setVal('Jb','b',0)
# Strategy.data.setVal('Jb','p',1)

# Strategy.data.setVal('Jp','b',1/3)
# Strategy.data.setVal('Jp','p',2/3)

sortedInfoSet = sorted(Strategy.data.outerMap.keys(), key=lambda x: len(x), reverse=True)

for i in range(10000):

  infoSetLikelihoods = {infoSet:0 for infoSet in Strategy.data.outerMap.keys()}

  g=GameTreeIterator()
  g.traverseFullTree()
  # print(Beliefs.data)


  # util=calcUtilityAtTerminalNode('JQ','pbb')
  # print(f'util={util}')

  expectedUtilsByInfoSet = {}
  
  # print(sortedInfoSet)

  for infoSet in sortedInfoSet:
    calcUtilitiesForInfoSet(infoSet,expectedUtilsByInfoSet)

  initGains()
  showGains=False
  # if i==999:
  #   showGains=True 
  totAddedGain=calcGains(expectedUtilsByInfoSet,showGains)
  print(totAddedGain)
  # print(infoSetLikelihoods)
  # print(Strategy.data)


  updateStrategy()
print(Strategy.data)
  



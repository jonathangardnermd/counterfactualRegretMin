
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
  # print(f'calcUtilityAtTerminalNode={actionStr}, pockets={pockets}')
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
    utility= 1,1
  elif actionStr=='bb' or actionStr=='pbb':
    if playerOnePocketIsHigher(*pockets):
      utility= 2,-2
    else:
      utility= -2,2
  else:
    # utility=0,0
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
print(getAllPockets())

def getPossibleOpponentPockets(pocket):
    return [rank for rank in RANK_NAMES if rank!=pocket]

print(getPossibleOpponentPockets('Q'))

def getAncestralInfoSets(infoSet):
    if len(infoSet)==1:
        # there are no ancestralInfoSets
        return None
    possibleOpponentPockets = getPossibleOpponentPockets(infoSet[0])
    return [oppPocket+infoSet[1:-1] for oppPocket in possibleOpponentPockets]

print(getAncestralInfoSets('Qpb'))
    

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
    print(self.hx)
    infoSetStr=self.hx.getInfoSetStr()
    possibleActions = self.hx.nextActions()
    if not possibleActions:
      print(f'Terminal: {self.hx}')
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
    print(self.hx)
    possibleActions = self.hx.nextActions()
    if not possibleActions:
      print(f'Terminal: {self.hx}')
      return
    
    updateBeliefs(self.hx)
    for action in possibleActions:
      self.hx.appendAction(action)
      self.traverse() #recursive call
      self.hx.popAction()  

  # def traverseFullInfoSets(self):
  #   for rank in RANK_NAMES:
  #     self.hx.pockets=[rank,None]
  #     self.traverseInfoSets()

  # def traverseInfoSets(self):
  #   print('INFOSET',self.hx)
  #   possibleActions = self.hx.nextActions()
  #   if not possibleActions:
  #     print(f'INFOSET Terminal: {self.hx}')
  #     return
    

    # updateBeliefs(self.hx)
    # for action in possibleActions:
    #   self.hx.appendAction(action)
    #   self.traverseInfoSets() #recursive call
    #   self.hx.popAction()  

class InfoSetIterator:
  def __init__(self):
    pass


def initStrategies(infoSetStr,action,numPossibleActions):
  Strategy.data.setVal(infoSetStr,action,1/numPossibleActions)

def initUtilitiesForInfoSets(infoSetStr,action):
  Utilities.data.setVal(infoSetStr,action,0)

def updateBeliefs(hx:Hx,ignore=None, ignore2=None):  
  infoSetStr = hx.getInfoSetStr()
  # print(f'updateBeliefs for {infoSetStr}')
  if len(infoSetStr)==1:
    possibleOpponentPockets=getPossibleOpponentPockets(infoSetStr[0])
    for oppPocket in possibleOpponentPockets:  
      Beliefs.data.setVal(infoSetStr,oppPocket,1/len(possibleOpponentPockets))
    return 
  ancestralInfoSets=getAncestralInfoSets(infoSetStr)
  # print(f'ancestors that will be used for the belief update: {ancestralInfoSets}')
  # print('Anc',ancestralInfoSets)
  lastAction = infoSetStr[-1]
  tot = 0
  for infoSet in ancestralInfoSets:
    tot+=Strategy.data.getVal(infoSet,lastAction)
  for infoSet in ancestralInfoSets:
    Beliefs.data.setVal(infoSetStr,infoSet[0],Strategy.data.getVal(infoSet,lastAction)/tot)
    # print(f'belief updated: ({infoSetStr},{infoSet[0]})={Beliefs.data.getVal(infoSetStr,infoSet[0])}')

g=GameTreeIterator()
g.initFullTree()
print(Strategy.data)
print(Utilities.data)

#player 1
Strategy.data.setVal('K','b',2/3)
Strategy.data.setVal('K','p',1/3)

Strategy.data.setVal('Q','b',1/2)
Strategy.data.setVal('Q','p',1/2)

Strategy.data.setVal('J','b',1/3)
Strategy.data.setVal('J','p',2/3)

Strategy.data.setVal('Kpb','b',1)
Strategy.data.setVal('Kpb','p',0)

Strategy.data.setVal('Qpb','b',1/2)
Strategy.data.setVal('Qpb','p',1/2)

Strategy.data.setVal('Jpb','b',0)
Strategy.data.setVal('Jpb','p',1)

#player2
Strategy.data.setVal('Kb','b',1)
Strategy.data.setVal('Kb','p',0)

Strategy.data.setVal('Kp','b',1)
Strategy.data.setVal('Kp','p',0)

Strategy.data.setVal('Qb','b',1/2)
Strategy.data.setVal('Qb','p',1/2)

Strategy.data.setVal('Qp','b',2/3)
Strategy.data.setVal('Qp','p',1/3)

Strategy.data.setVal('Jb','b',0)
Strategy.data.setVal('Jb','p',1)

Strategy.data.setVal('Jp','b',1/3)
Strategy.data.setVal('Jp','p',2/3)


g=GameTreeIterator()
g.traverseFullTree()
print(Beliefs.data)


util=calcUtilityAtTerminalNode('JQ','pbb')
print(f'util={util}')

expectedUtilsByInfoSet = {}
sortedInfoSet = sorted(Beliefs.data.outerMap.keys(), key=lambda x: len(x), reverse=True)
print(sortedInfoSet)

for infoSet in sortedInfoSet:
  beliefs = Beliefs.data.getInnerMap(infoSet)
  print(f'infoSet={infoSet}, beliefs={beliefs}')

  possibleOpponentPockets = list(beliefs.keys())

  possibleActions = Strategy.data.getInnerMap(infoSet)

  playerIdx = (len(infoSet)-1)%2
  for action in possibleActions:
    actionStr = infoSet[1:]+action
    expectedUtil=0
    for possibleOpponentPocket in possibleOpponentPockets:
      opponentsInfoSet = possibleOpponentPocket+actionStr

      util=None
      isInfoSet=None
      if opponentsInfoSet in Strategy.data.outerMap.keys():
        isInfoSet=True
        util=((-1)**(playerIdx))*expectedUtilsByInfoSet[opponentsInfoSet]
        print(f'opponentsInfoSet={opponentsInfoSet}, isInfoSet={isInfoSet}, infoSet={infoSet}, action={action}, opponentsInfoSet={opponentsInfoSet}, expectedUtilsByInfoSet[opponentsInfoSet]={expectedUtilsByInfoSet[opponentsInfoSet]}, playerIdx={playerIdx}, util={util}, belief={belief}')
      else:
        isInfoSet=False
        utils=calcUtilityAtTerminalNode(infoSet[0]+possibleOpponentPocket,actionStr)
        util=-1*utils[playerIdx]
        print(f'\topponentsInfoSet={opponentsInfoSet}, isInfoSet={isInfoSet}, infoSet={infoSet}, action={action}, playerIdx={playerIdx}, util={util}, belief={beliefs[possibleOpponentPocket]}')

      belief = beliefs[possibleOpponentPocket]
      expectedUtil+=util*belief

      # print(f'expectedUtil={expectedUtil}')
    Utilities.data.setVal(infoSet,action,expectedUtil)
    print(f'infoSet={infoSet}, action={action}, expectedUtil={expectedUtil}')

  expectedUtilsByInfoSet[infoSet] = 0
  for action in Utilities.data.getInnerMap(infoSet).keys():
    strat = Strategy.data.getVal(infoSet,action)
    util = Utilities.data.getVal(infoSet,action)
    expectedUtilsByInfoSet[infoSet]+=strat*util 
    

print(Utilities.data)
print('ExpectedUtils',expectedUtilsByInfoSet)



util=calcUtilityAtTerminalNode('JQ','pbb')
print(f'util={util}')
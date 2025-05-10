


import random
import math
from collections import defaultdict
from pypokerengine.players import BasePokerPlayer
from pypokerengine.utils.card_utils import gen_cards, estimate_hole_card_win_rate

class MCTSNode:
    def __init__(self, state, parent=None, action=None):
        self.state=state
        self.parent=parent
        self.action=action
        self.children=[]
        self.untried=[]
        self.visits=0
        self.value=0.0
        self.rewardSquares=0.0

    def upperConfidenceBound1(self, c=1.41):
        if self.visits==0:
            return float('inf')
        avrg=self.value/self.visits
        variance=(self.rewardSquares/self.visits)-(avrg*avrg)
        stdDeviation=math.sqrt(variance) if variance > 0 else 0.0
        return avrg+(c*stdDeviation*math.sqrt(math.log(self.parent.visits)/self.visits))







class MCTSPlayerPlus(BasePokerPlayer):




    def __init__(self, noOfSimulations=1000, minSampleForMax=200):
        super().__init__()
        self.noOfSimulations=noOfSimulations
        self.minSampleForMax=minSampleForMax
        self.gameInfo=None
        self.hole_card=None
        self.handStrengthCache={}
        self.opponentActionStats=defaultdict(lambda: defaultdict(int))

    def declare_action(self, valid_actions, hole_card, round_state):
        self.hole_card =hole_card
        self.gameInfo= round_state
        root= MCTSNode(round_state)
        root.untried=valid_actions.copy()

        for _ in range(self.noOfSimulations):
            node=self.select(root)
            reward=self.simulate(node)
            self.backpropagate(node, reward)

        bestChild=max(root.children, key=lambda c: c.upperConfidenceBound1())
        return bestChild.action["action"]

    def select(self, node):
        while not node.untried and node.children:
            node=max(node.children, key=lambda c: c.upperConfidenceBound1())
        if node.untried:
            return self.expand(node)
        return node





    def expand(self, node):
        actionPriority= self.getActionPriority(node)
        prioritizedActions= [a for a in node.untried if a["action"] in actionPriority]
        
        if prioritizedActions:
            action=random.choice(prioritizedActions)
        else:
            action=random.choice(node.untried)

        node.untried.remove(action)
        newState={k: v.copy() if isinstance(v, (dict, list)) else v
            for k, v in node.state.items()}
        
        current=newState["next_player"]
        
        
        if action["action"]=="fold":
            newState["seats"][current]["status"]="folded"
        elif action["action"]=="call":
            potAmount=newState["pot"]["main"]["amount"]
            newState["seats"][current]["stack"]=newState["seats"][current]["stack"] - potAmount
        elif action["action"]=="raise":
            amount=action.get("amount", 0)
            newState["seats"][current]["stack"]=newState["seats"][current]["stack"] - amount
            newState["pot"]["main"]["amount"]=newState["pot"]["main"]["amount"]+amount

        newState["currentPlayer"]=(current+1) % len(newState["seats"])
        newState["next_player"]=newState["currentPlayer"]
        child=MCTSNode(newState, parent=node, action=action)
        node.children.append(child)
        
        
        return child




    def simulate(self, node):
        if not self.hole_card:
            return 0.5
        communityCards=node.state['community_card']
        handStrength=self.evaluateHandStrength(self.hole_card, communityCards, node)
        
        return handStrength




    def evaluateHandStrength(self, hole_card, communityCards, node):
        key=tuple(hole_card+communityCards)

        if key in self.handStrengthCache:
            return self.handStrengthCache[key]
        
        win_rate=estimate_hole_card_win_rate(nb_simulation=100, nb_player=len(node.state['seats']),
        hole_card=gen_cards(hole_card),
                            community_card=gen_cards(communityCards))
        position=self.getPosition(node.state)
        positionBonus=0.05 if position=='late' else 0.0
        stackSize=node.state['seats'][node.state['next_player']]['stack']
        avrgStack=sum(s['stack'] for s in node.state['seats'])/len(node.state['seats'])
        stackBonus=0.05*(stackSize/avrgStack)
        handStrength=win_rate*0.6+positionBonus+stackBonus
        self.handStrengthCache[key]=handStrength
        return handStrength

    def getPosition(self, state):
        players=state['seats']
        currentPlayer=state['next_player']
        total=len(players)

        if currentPlayer>=total - 2: return 'late'
        elif currentPlayer>=total - 4:      return 'middle'
        else: return 'early'



    def backpropagate(self, node, reward):
        while node:
            node.visits+=1
            node.value+=reward
            node.rewardSquares+=reward*reward
            if node.visits>=self.minSampleForMax and node.children:
                best_est=max((child.value/child.visits) for child in node.children if child.visits > 0)
                node.value=best_est*node.visits 

            node=node.parent



    def getActionPriority(self, node):
        handStrength=self.evaluateHandStrength(self.hole_card, node.state['community_card'], node)
        oppId=node.state['seats'][node.state['next_player']]['uuid']
        predicted=self.predict_opponent_action(oppId)
        
        if handStrength > 0.7: return ["raise", "call"] if predicted != "raise" else ["call", "fold"]
        
        elif handStrength > 0.4: return ["call", "fold"]
        
        else: return ["fold", "call"]

    def receive_game_start_message(self, gameInfo):
        self.gameInfo=gameInfo

    def receive_round_start_message(self, round_count, hole_card, seats):
        self.hole_card=hole_card

    def receive_street_start_message(self, street, round_state): pass



    def receive_game_update_message(self, action, round_state):
        player_id=action["player_uuid"]
        act=action["action"]
        self.opponentActionStats[player_id][act]+=1

    def receive_round_result_message(self, winners, hand_info, round_state): pass



    def predict_opponent_action(self, player_id):
        if not self.opponentActionStats[player_id]:
            return "call"
        return max(self.opponentActionStats[player_id].items(), key=lambda x: x[1])[0]


def setup_ai():
    return MCTSPlayerPlus()

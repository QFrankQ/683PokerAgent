from pypokerengine.players import BasePokerPlayer
import random as rand
import pprint
import json
from pypokerengine.engine.card import Card
from pypokerengine.utils.card_utils import gen_deck, gen_cards, estimate_hole_card_win_rate
import time
import pprint
RANK_MAP = {
      2  :  '2',
      3  :  '3',
      4  :  '4',
      5  :  '5',
      6  :  '6',
      7  :  '7',
      8  :  '8',
      9  :  '9',
      10 : 'T',
      11 : 'J',
      12 : 'Q',
      13 : 'K',
      14 : 'A'
  }

RANK_TO_STRENGTH_MAP = {
      '2' : 2,
      '3' : 3,
      '4' : 4,
      '5' : 5,
      '6' : 6,
      '7' : 7,
      '8' : 8,
      '9' : 9,
      'T' : 10,
      'J' : 11,
      'Q' : 12,
      'K' : 13,
      'A' : 14
  }

class PotOddsPlayer(BasePokerPlayer):
    def __init__(self):
        self.name = "MyPlayer"
        open_file = open('hand_win_percentages.json', 'r')
        self.starting_hand_winning_percentage = json.load(open_file)
        open_file.close()
        self.action_stats = {
            'check': 0,
            'call': 0,
            'raise': 0,
            'fold': 0
        }
        # self.starting_hand_winning_percentage = self.hand_win_percentages.get("starting_hand", 0)

    def declare_action(self, valid_actions, hole_card, round_state):
        start_time = time.time()
        # valid_actions format => [raise_action_pp = pprint.PrettyPrinter(indent=2)
        # pp = pprint.PrettyPrinter(indent=2)
        # print("------------ROUND_STATE(RANDOM)--------")
        # pp.pprint(round_state)
        # print("------------HOLE_CARD----------")
        # pp.pprint(hole_card)
        # print("------------VALID_ACTIONS----------")
        # pp.pprint(valid_actions)
        # print("-------------------------------")
        cur_street = round_state['street']
        
        community_card = round_state['community_card']
        pot_size = round_state['pot']['main']['amount']
        call_size = self.get_call_size(round_state)
        #can optimize slightly by using the call size
        raise_size = self.get_raise_size(round_state)
        action = None
        if cur_street == 'preflop':
            #check the hand winning percentage
            
            if RANK_TO_STRENGTH_MAP[hole_card[0][1]] >= RANK_TO_STRENGTH_MAP[hole_card[1][1]]:
                hand = hole_card[0][1] + hole_card[1][1]
            else:
                hand = hole_card[1][1] + hole_card[0][1]
            
            #check whether the hand is suited or not
            if hole_card[0][1] == hole_card[1][1]:
                pass
            elif hole_card[0][0] == hole_card[1][0]:
                hand += 's'
            else:
                hand += 'o'
            
            winning_percentage = self.starting_hand_winning_percentage[hand][0]['Win %']
            # print (f"Winning percentage for {hand}: {winning_percentage}")
            
            #calculate the pot odds for calling
            if call_size == 0:
                pot_odds = 0
            else:
                pot_odds = call_size / (pot_size + call_size)       
            if winning_percentage < pot_odds:
                action = valid_actions[0]['action']
                print("fold preflop")
            else:
                action = valid_actions[1]['action']
            
            
        
        else:
            pot_size = round_state['pot']['main']['amount']
            
            hole_card = gen_cards(hole_card)
            community_card = gen_cards(community_card)
            win_rate = estimate_hole_card_win_rate(300, 2, hole_card, community_card)
            # print(f"Win rate: {win_rate:.2f}")
            
            to_call = False
            to_raise = False
            #calculate the pot odds for calling
            if call_size == 0:
                to_call = True
            else:
                call_pot_odds = call_size / (pot_size + call_size)
                if win_rate > call_pot_odds:
                    to_call = True
            
            #calculate the pot odds for raising
            # raise_pot_odds = raise_size / (pot_size + raise_size)
            if win_rate > 0.7:
                to_raise = True
            #decide whether to call or raise
            if to_raise and len(valid_actions) == 3:
                action = valid_actions[2]['action']
            elif to_call:
                action = valid_actions[1]['action']
            else:
                action = valid_actions[0]['action']
                
        # print(f"Action taken: {action}")
        if action == 'call' and call_size == 0:
            self.action_stats['check'] += 1
        else:
            self.action_stats[action] += 1
        # time_taken = time.time() - start_time
        # print(f"Time taken to decide action: {time_taken:.6f} seconds")
        return action


    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass
    
    def get_call_size(self, round_state):
        street = round_state['street']
        street_actions = round_state['action_histories'][street]
        if len(street_actions) == 0:
            return 0
        else:
            last_action = street_actions[-1]
            call_size = last_action.get('add_amount',0)
        return call_size
    def get_pot_size(self, round_state):
        pot_size = round_state['pot']['main']['amount']
        return pot_size
    
    def get_raise_size(self,round_state):
        call_size = self.get_call_size(round_state)
        street = round_state['street']
        if street == 'preflop' or street == 'flop':
            raise_size = 20 + call_size
        elif street == 'turn' or street == 'river':
            raise_size = 40 + call_size
        return raise_size
        
    def print_action_stats(self):
        print("PotOddsPlayer action stats:")
        for action, count in self.action_stats.items():
            print(f"Action: {action}, Count: {count}")
        

def setup_ai():
  return PotOddsPlayer()

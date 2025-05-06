from pypokerengine.players import BasePokerPlayer
import random as rand
import pprint
import json
from pypokerengine.engine.card import Card
from pypokerengine.utils.card_utils import gen_deck, gen_cards, estimate_hole_card_win_rate
import time

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

class WinRatePlayer(BasePokerPlayer):
    def __init__(self):
        self.name = "MyPlayer"
        open_file = open('hand_win_percentages.json', 'r')
        self.starting_hand_winning_percentage = json.load(open_file)
        open_file.close()
        # self.starting_hand_winning_percentage = self.hand_win_percentages.get("starting_hand", 0)

    def declare_action(self, valid_actions, hole_card, round_state):
        start_time = time.time()
        # valid_actions format => [raise_action_pp = pprint.PrettyPrinter(indent=2)
        pp = pprint.PrettyPrinter(indent=2)
        print("------------ROUND_STATE(RANDOM)--------")
        pp.pprint(round_state)
        # print("------------HOLE_CARD----------")
        # pp.pprint(hole_card)
        # print("------------VALID_ACTIONS----------")
        # pp.pprint(valid_actions)
        # print("-------------------------------")
        
        cur_street = round_state['street']
        
        community_card = round_state['community_card']
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
            if winning_percentage < 0.5:
                action = valid_actions[0]['action']
            else:
                action = valid_actions[1]['action']
            
        
        else:
            hole_card = gen_cards(hole_card)
            community_card = gen_cards(community_card)
            win_rate = estimate_hole_card_win_rate(300, 2, hole_card, community_card)
            # print(f"Win rate: {win_rate:.2f}")
            if win_rate < 0.3:
                action = valid_actions[0]['action']
            else:
                if win_rate > 0.7 and len(valid_actions) == 3:
                    action = valid_actions[2]['action']
                else:
                    action = valid_actions[1]['action']
        time_taken = time.time() - start_time
        print(f"Time taken to decide action: {time_taken:.6f} seconds")
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
    
    

def setup_ai():
  return WinRatePlayer()

from pypokerengine.players import BasePokerPlayer
import random as rand
import pprint
import json
from pypokerengine.engine.card import Card
from pypokerengine.utils.card_utils import gen_deck, gen_cards, estimate_hole_card_win_rate
import time
import random
import numpy as np
import math
from utils.poker_utils import PokerUtils

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

STREET_RANK_MAP ={
    'preflop': 0,
    'flop': 1,
    'turn': 2,
    'river': 3  
}

class PotOddsPlayerMixedStrat(BasePokerPlayer):
    def __init__(self):
        self.name = "MyPlayer"
        open_file = open('hand_win_percentages.json', 'r')
        self.starting_hand_winning_percentage = json.load(open_file)
        open_file.close()
        self.raise_threshold = 0.7
        self.preflop_raise_threshold = 0.6
        self.action_stats = {
            'bet':0,
            'check':0,
            'call': 0,
            'raise': 0,
            'fold': 0
        }
        self.opponent_opening_stats = {
            'fold':0,
            'limp':0, # conservative: When the oppenent calls the big blind
            'check':0, # conservative: When the opponent checks the big blind
            'raise':0, # aggressive: When the opponent raises the big blind
        }
        self.poker_utils = PokerUtils()
        self.last_round_state = None
        self.last_action = None
        self.last_street = None
        self.opponent_uuid = None
        self.uuid = None
        self.is_small_blind = None
        self.opponent_tightness = 0 

    def declare_action(self, valid_actions, hole_card, round_state):
        # start_time = time.time()
        # valid_actions format => [raise_action_pp = pprint.PrettyPrinter(indent=2)
        # pp = pprint.PrettyPrinter(indent=2)
        # print("------------ROUND_STATE(RANDOM)--------")
        # pp.pprint(round_state)
        # print("------------HOLE_CARD----------")
        # pp.pprint(hole_card)
        # print("------------VALID_ACTIONS----------")
        # pp.pprint(valid_actions)
        # print("-------------------------------")
        action = None
        if self.uuid is None:
            self.get_player_uuids(round_state)
            
        
        if self.is_new_round(round_state):
            round = round_state['round_count']
            if round % 30 == 0:
                print(f"Round {round} starting")
            self.setup_new_round(round_state)
            
        cur_street = round_state['street']
        
        community_card = round_state['community_card']
        pot_size = round_state['pot']['main']['amount']
        call_size = self.poker_utils.get_call_size(round_state)
        #can optimize slightly by using the call size
        raise_size = self.poker_utils.get_raise_size(round_state)
        
        self.update_opponent_opening_stats(round_state)
        if cur_street == 'preflop':
            #check the hand winning percentage
            
            winning_percentage = self.poker_utils.get_opening_hand_winning_percentage(hole_card)
            # print (f"Winning percentage for {hand}: {winning_percentage}")
            
            #calculate the pot odds for calling
            pot_odds = self.poker_utils.calculate_pot_odds(call_size, pot_size)
            if winning_percentage < pot_odds:
                action = valid_actions[0]['action']
            # elif winning_percentage > self.preflop_raise_threshold and len(valid_actions) == 3:
            #     action = valid_actions[2]['action']
            else:
                action = valid_actions[1]['action']
                
            #TODO update the opponent opening stats
            
        
        else:
            pot_size = round_state['pot']['main']['amount']
            
            hole_card = gen_cards(hole_card)
            community_card = gen_cards(community_card)
            win_rate = estimate_hole_card_win_rate(300, 2, hole_card, community_card)
            # print(f"Win rate: {win_rate:.2f}")
            
            to_call = None
            to_raise = False
            #calculate the pot odds for calling
            call_pot_odds = self.poker_utils.calculate_pot_odds(call_size, pot_size)
            if win_rate > call_pot_odds:
                to_call = True
            else:
                to_call = False
            
            #calculate the pot odds for raising
            # raise_pot_odds = raise_size / (pot_size + raise_size)
            
            if win_rate > self.raise_threshold:
                to_raise = True
                
            #randomize the decision to raise or call
                
            #decide whether to call or raise
            if to_raise and len(valid_actions) == 3:
                # Randomly decide to raise or call
                # to_raise = np.random.rand() < 0.8
                # if to_raise:
                #     action = valid_actions[2]['action']
                # else:
                #     action = valid_actions[1]['action']
                action = valid_actions[2]['action']
            elif to_call:
                #randomly decide to call or raise
                # raise_prob = (win_rate - call_pot_odds)/(self.raise_threshold - call_pot_odds)
                # to_raise = np.random.rand() < (raise_prob/2)
                # to_raise = np.random.rand() < 0.8
                # if to_raise and len(valid_actions) == 3:
                #     action = valid_actions[2]['action']
                # else:
                #     action = valid_actions[1]['action']
                action = valid_actions[1]['action']
                
            else:
                action = valid_actions[0]['action']
        # Update action statistics
        self.update_last_action_and_stats(action, call_size)
        self.update_round_state(round_state)
        # time_taken = time.time() - start_time
        # print(f"Time taken to decide action: {time_taken:.6f} seconds")
        #TODO: update last action
        return action
    
    def get_player_uuids(self, round_state):
        next_player = round_state['next_player']
        self.uuid = round_state['seats'][next_player]['uuid']
        self.opponent_uuid = round_state['seats'][1]['uuid'] if next_player==0 else round_state['seats'][0]['uuid']
    
    # def update_opponent_action_stats(self, action, call_size):
    #     if action == 'call' and call_size == 0:
    #         self.action_stats['check'] += 1
    #     elif action == 'raise' and call_size == 0:
    #         self.action_stats['bet'] += 1  
    #     else:
    #         self.action_stats[action] += 1
    
    def update_last_action_and_stats(self, self_action, call_size):
        
        if self_action == 'call' and call_size == 0:
            self.last_action = 'check'
            self.action_stats['check'] += 1
        elif self_action == 'raise' and call_size == 0:
            self.last_action = 'bet'
            self.action_stats['bet'] += 1  
        else:
            #convert the action to lower case
            self.last_action = self_action.lower()
            self.action_stats[self_action] += 1


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
    
    
    def is_new_round(self, round_state):
        cur_street = round_state['street']
        preflop_actions_length = len(round_state['action_histories']['preflop'])
        if cur_street == 'preflop' and preflop_actions_length <= 3:
            return True
        return False
    
    def update_round_state(self, round_state):
        self.last_round_state = round_state
        self.last_street = round_state['street']
        # self.last_action = None
        # self.is_small_blind = None
    
    def is_new_street(self, round_state):
        cur_street = round_state['street']
        if self.round_state is None:
            return True
        if cur_street != self.round_state['street']:
            return True
        return False
    
    def setup_new_round(self, round_state):
        self.update_opponent_folded_stats(round_state)
        preflop_actions_length = len(round_state['action_histories']['preflop'])
        # print(f"Preflop actions length: {preflop_actions_length}")
        #TODO: check who folded
        #check if the player is small blind or big blind
        if preflop_actions_length == 2:
            self.last_action = 'smallblind'
            self.is_small_blind = True
        elif preflop_actions_length == 3:
            self.last_action = 'bigblind'
        else:
            pass
    
    def update_opponent_folded_stats(self, round_state):
        cur_street = round_state['street']
        
        if self.last_action != 'fold' and self.last_street != 'river':
            if self.last_street == 'flop':
                self.opponent_opening_stats['fold'] += 1
        #TODO: check if the opponent has folded
        
        
    def update_opponent_opening_stats(self, round_state):
        cur_street = round_state['street']
        preflop_action_history = round_state['action_histories']['preflop']     
                
        if cur_street == 'turn' or cur_street == 'river':
            return
        elif cur_street == 'flop':
            # preflop last action made by my player, no opponent action missed
            flop_action_history = round_state['action_histories']['flop']
            if self.uuid == preflop_action_history[-1]['uuid']:
                return
            
            # not immediately after preflop, no opponent action missed
            if (self.is_small_blind and len(flop_action_history) > 1) or (not self.is_small_blind and len(flop_action_history) >0):
                return
            
            #immediately after preflop and last action not made by my player opponent action missed
            opponent_action = preflop_action_history[-1]['action'].lower()
            if opponent_action == 'call' and self.last_action == 'call':
                self.opponent_opening_stats['check'] += 1
            
            # if opponent_action == 'call' and self.last_action == 'bet':
            #     #bet refers to raising the big blind
            #     self.opponent_opening_stats['fold'] += 1
            
        else:
            opponent_action = preflop_action_history[-1]['action'].lower()
            if opponent_action == 'raise':
                self.opponent_opening_stats['raise'] += 1    
            if opponent_action == 'call' and self.last_action == 'bigblind':
                self.opponent_opening_stats['limp'] += 1
            
        
    def print_opponent_openning_stats(self):
        print("PotOddsPlayerMixedStrat opponent opening statistics:")
        for action, count in self.opponent_opening_stats.items():
            print(f"Action: {action}, Count: {count}")
    

    def print_action_stats(self):
        print("PotOddsPlayerMixedStrat action statistics:")
        for action, count in self.action_stats.items():
            print(f"Action: {action}, Count: {count}")

def setup_ai():
  return PotOddsPlayerMixedStrat()

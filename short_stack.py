from pypokerengine.players import BasePokerPlayer
import random as rand
import pprint
import json
from pypokerengine.engine.card import Card
from pypokerengine.utils.card_utils import gen_deck, gen_cards, estimate_hole_card_win_rate
import time
import random
# import numpy as np
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


class ShortStacked(BasePokerPlayer):
    def __init__(self):
        self.name = "MyPlayer"
        open_file = open('hand_win_percentages.json', 'r')
        self.starting_hand_winning_percentage = json.load(open_file)
        open_file.close()
        probs = sorted([v[0]['Win %'] for v in self.starting_hand_winning_percentage.values()])
        self.STARTING_PERCENTILES = {}
        for i in range(20, 91, 5):
            self.STARTING_PERCENTILES[i] = probs[int(len(probs) * (i / 100))]
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
            're-raise': 0, # aggressive: When the opponent re-raises
            'folded_to_raise': 0, # aggressive: When folds under pressure
            'call': 0, # aggressive: When the opponent calls the raise
        }
        self.opponent_num_raises = 0
        self.POLICY_ADJUSTMENT = {
            'call_threshold_adjustment': 0,
            'raise_threshold_adjustment': 0,
        }
        self.OPPONENT_TRAITS ={
            'opponent_tightness': 0,
            'opponent_aggressiveness': 0,
        }
        self.POLICY_REFERENCE = {
            'raise_rate': 0.4,
            'call_rate': 0.4,
            'fold_rate': 0.20,
        }
        self.opponent_num_raises = 0
        self.poker_utils = PokerUtils()
        self.last_round_state = None
        self.last_action = None
        self.opponent_last_action = None
        self.last_sreet = None
        self.opponent_uuid = None
        self.uuid = None
        self.is_small_blind = None
        self.opponent_tightness = 0 
        self.flop_win_rate = []
        self.river_win_rate = []
        self.opp_total_raise_win = 1e-4
        self.opp_total_raise_loss = 1e-4
        self.prev_stack = None
        

    def declare_action(self, valid_actions, hole_card, round_state):
        # start_time = time.time()
        # valid_actions format => [raise_action_pp = pprint.PrettyPrinter(indent=2)
        pp = pprint.PrettyPrinter(indent=2)
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
            self.prev_stack = round_state['seats'][0]['stack'] if self.uuid == round_state['seats'][0]['uuid'] else round_state['seats'][1]['stack']
            
            
        
        if self.is_new_round(round_state):
            self.opponent_num_raises = 0
            # -------------------------------
            # New code here

            
            if (round_state['round_count']) > 1 and self.last_action != 'fold' and self.last_round_state['street'] == 'river':

                # Check whether the opponent won the previous round (This is the start of next round).
                is_opp_win = 0
                for p in round_state['seats']:
                    if (p['uuid'] == self.uuid) and (p['stack'] <= self.prev_stack):
                        is_opp_win = 1
                    self.prev_stack = p['stack']
                    
                # Check whether the opponent won the previous round (This is the start of next round).
                # Count the number of raise action by the opponent.
                opp_raise = 0
                # pp.pprint(self.last_round_state['action_histories'])
                for street in self.last_round_state['action_histories']:
                    # print("street", street)
                    
                    for act in self.last_round_state['action_histories'][street]:
                        if (act['uuid'] != self.uuid) and (act['action'].lower() == 'raise'):
                            if is_opp_win:
                                self.opp_total_raise_win += 1
                            else:
                                self.opp_total_raise_loss += 1
        

                
            # ---------------------------------------
            
            round = round_state['round_count']
            if round % 30 == 0:
                print(f"Round {round} starting")
            self.setup_new_round(round_state)
            # self.adjust_policy(round_state)
            
        cur_street = round_state['street']
        opponent_last_action = round_state['action_histories'][cur_street][-1]['action'] if len(round_state['action_histories'][cur_street]) > 0 else None
        if opponent_last_action == 'raise':
            self.opponent_num_raises += 1
        community_card = round_state['community_card']
        pot_size = round_state['pot']['main']['amount']
        call_size = self.poker_utils.get_call_size(round_state)
        #can optimize slightly by using the call size
        raise_size = self.poker_utils.get_raise_size(round_state)
        
       

        if cur_street == 'preflop':
            action = self.preflop_strategy(hole_card, round_state)
            
        elif cur_street == 'flop':
            action = self.flop_policy(hole_card, round_state, valid_actions)
        elif cur_street == 'turn':
            action = self.turn_policy(hole_card, round_state, valid_actions)
        else:
            # print("RIVER reached")
            action = self.river_policy(hole_card, round_state, valid_actions)
       
        # Update action statistics
        
        self.update_last_action_and_stats(action, call_size)
        self.update_round_state_and_street(round_state)
        # time_taken = time.time() - start_time
        # print(f"Time taken to decide action: {time_taken:.6f} seconds")
        #TODO: update last action
        return action
    
    def get_player_uuids(self, round_state):
        next_player = round_state['next_player']
        self.uuid = round_state['seats'][next_player]['uuid']
        self.opponent_uuid = round_state['seats'][1]['uuid'] if next_player==0 else round_state['seats'][0]['uuid']
    
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
    
    def update_round_state_and_street(self, round_state):
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
        preflop_actions_length = len(round_state['action_histories']['preflop'])
        #check if the player is small blind or big blind
        if preflop_actions_length == 2:
            self.last_action = 'smallblind'
            self.is_small_blind = True
        elif preflop_actions_length == 3:
            self.last_action = 'bigblind'
            self.is_small_blind = False
        else:
            return
    
    def update_folded_stats(self, cur_round_state):
        if self.last_action == 'fold':
            if cur_round_state['round_count'] - self.last_round_state['round_count'] > 1:
                self.opponent_opening_stats['fold'] += cur_round_state['round_count'] - self.last_round_state['round_count'] -1
            return
        else:
            match self.last_street:
                case 'preflop':
                    if cur_round_state['round_count'] - self.last_round_state['round_count'] > 1:
                        self.opponent_opening_stats['fold'] += cur_round_state['round_count'] - self.last_round_state['round_count']
                    if self.last_action == 'bet' or self.last_action == 'raise':
                        self.opponent_opening_stats['folded_to_raise'] += 1
                    elif self.is_small_blind and self.last_action == 'call':
                        self.opponent_opening_stats['fold'] += 1
                case 'flop':
                    pass
                case 'turn':
                    pass
                case 'river':
                    pass
                case _:
                    pass
            
    def preflop_strategy(self, hole_card, round_state):
        #check the hand winning percentage
        winning_percentage = self.poker_utils.get_opening_hand_winning_percentage(hole_card)
        action =None
        #TODO: adjust range based on opponent's action
        
        
        if self.is_small_blind:
            if self.last_action == 'smallblind':
                call_threshold = self.STARTING_PERCENTILES[25] 
                if winning_percentage < call_threshold:
                    action = 'fold'
                elif winning_percentage < 3/5:
                    action = 'call'
                else:
                    action = 'raise'
            elif self.last_action == 'raise' or self.last_action == 'call' or self.last_action == 'bet':
                action = 'call'
                if winning_percentage > self.STARTING_PERCENTILES[85]:
                    action = 'raise'
        else:
            if self.last_action == 'bigblind':
                call_threshold = self.STARTING_PERCENTILES[20] 
    
                if winning_percentage < self.STARTING_PERCENTILES[85]:
                    action = 'call'
                else:
                    action = 'raise'
            elif self.last_action == 'raise' or self.last_action == 'bet':
                action = 'raise'
        if action is None:        
            print(f"self.last_action: {self.last_action}")
            print(f"self.is_small_blind: {self.is_small_blind}")
        return action
    
    def flop_policy(self, hole_card, round_state, valid_actions):
        #check the hand winning percentage
        hole_card = gen_cards(hole_card)
        community_card = gen_cards(round_state['community_card'])
        win_rate = estimate_hole_card_win_rate(500, 2, hole_card, community_card)
        # print(f"Win rate: {win_rate:.2f}")
        self.flop_win_rate.append(win_rate)
        call_size = self.poker_utils.get_call_size(round_state)
        pot_size = round_state['pot']['main']['amount']
        call_pot_odds = self.poker_utils.calculate_pot_odds(call_size, pot_size) 
        
        
        if win_rate > (self.raise_threshold) and len(valid_actions) == 3:
            action = 'raise'
        #TODO: small big blind switch
        elif call_pot_odds == 0 or (win_rate > call_pot_odds and win_rate > 0.35):
            action = 'call'
        else:
            action = 'fold'
        # print(f"win_rate: {win_rate}  call_pot_odds: {call_pot_odds}  action: {action}")
        return action
    
    def turn_policy(self, hole_card, round_state, valid_actions):
        #check the hand winning percentage
        hole_card = gen_cards(hole_card)
        community_card = gen_cards(round_state['community_card'])
        win_rate = estimate_hole_card_win_rate(500, 2, hole_card, community_card)
        # print(f"Win rate: {win_rate:.2f}")
        
        call_size = self.poker_utils.get_call_size(round_state)
        pot_size = round_state['pot']['main']['amount']
        call_pot_odds = self.poker_utils.calculate_pot_odds(call_size, pot_size)
        
        # print(f"win_rate: {win_rate}  call_pot_odds: {call_pot_odds}")
        
        if win_rate > (self.raise_threshold ) and len(valid_actions) == 3:
            action = 'raise'
        elif win_rate > call_pot_odds:
            action = 'call'
        else:
            action = 'fold'
        
        return action
    
    def river_policy(self, hole_card, round_state, valid_actions):
        #check the hand winning percentage
        hole_card = gen_cards(hole_card)
        community_card = gen_cards(round_state['community_card'])
        win_rate = estimate_hole_card_win_rate(500, 2, hole_card, community_card)
        # print(f"Win rate: {win_rate:.2f}")
        
        call_size = self.poker_utils.get_call_size(round_state)
        pot_size = round_state['pot']['main']['amount']
        call_pot_odds = self.poker_utils.calculate_pot_odds(call_size, pot_size) 
        
        # print(f"win_rate: {win_rate}  call_pot_odds: {call_pot_odds}")
        self.river_win_rate.append(win_rate)

        opp_threshold = self.opp_total_raise_win/(self.opp_total_raise_win + self.opp_total_raise_loss)
        # print("opp_threshold:", opp_threshold)
        if opp_threshold > 0.3:       
            if win_rate > (self.raise_threshold) and len(valid_actions) == 3:
                action = 'raise'
                # print("RAISING RIVER")
            elif (self.opponent_num_raises>=2 and win_rate > 0.53) or (win_rate > call_pot_odds and win_rate > 0.42) or call_pot_odds == 0:
                action = 'call'
                # print("CALLING RIVER")
            else:
                action = 'fold'
                # print("FOLDING RIVER")
        else: # flagged Raise Agent
            call_threshold = 0.53
            
            if win_rate > (self.raise_threshold) and len(valid_actions) == 3:
                action = 'raise'
                # print("RAISING RIVER")
            elif (self.opponent_num_raises>=2 and win_rate > call_threshold-0.04) or (win_rate > call_pot_odds and win_rate > 0.42) or call_pot_odds == 0:
                action = 'call'
                # print("CALLING RIVER")
            else:
                action = 'fold'
                # print("FOLDING RIVER")
        
        return action
    
    def adjust_policy(self, round_state):
        total_hands = round_state['round_count']
        
        
        if total_hands < 100:
            return
        if total_hands % 50 == 0:
            # print(f"self POLICY_ADJUSTMENT: {self.POLICY_ADJUSTMENT}")
            opponent_opening_fold_count = self.opponent_opening_stats['fold'] + self.opponent_opening_stats['folded_to_raise']
            opponent_conservative_count = self.opponent_opening_stats['check'] + self.opponent_opening_stats['limp']
            opponent_aggressive_count = self.opponent_opening_stats['raise'] + self.opponent_opening_stats['re-raise']
            # tightness = opponent_opening_fold_count / total_hands
            aggressiveness = opponent_aggressive_count / total_hands
            self.OPPONENT_TRAITS['opponent_aggresiveness'] = aggressiveness
            call_threshold_adjustment = aggressiveness - self.POLICY_REFERENCE['raise_rate']/2
            self.POLICY_ADJUSTMENT['call_threshold_adjustment'] = min(max(call_threshold_adjustment,-0.05),0.05)
            
            tightness = opponent_opening_fold_count / total_hands
            self.OPPONENT_TRAITS['opponent_tightness'] = tightness
            raise_threshold_adjustment = -(tightness - self.POLICY_REFERENCE['fold_rate'])/2
            self.POLICY_ADJUSTMENT['raise_threshold_adjustment'] = min(max(raise_threshold_adjustment,-0.05),0.05)
            
            
    def print_opponent_openning_stats(self):
        print("PotOddsPlayerMixedStrat opponent opening statistics:")
        for action, count in self.opponent_opening_stats.items():
            print(f"Action: {action}, Count: {count}")
    

    def print_action_stats(self):
        print("PotOddsPlayerMixedStrat action statistics:")
        for action, count in self.action_stats.items():
            print(f"Action: {action}, Count: {count}")

    #call only if is new round
    def update_opponent_preflop_stats(self, last_round_state):
        preflop_action_history = last_round_state['action_histories']['preflop']
        preflop_actions_length = len(preflop_action_history)
        # TODO Handle is small blind carefully
        i_am_small_blind = preflop_action_history[0]['uuid'] == self.uuid
        
        opponent_action_index = 3 if (i_am_small_blind) else 2
        if i_am_small_blind:
            for i in range(opponent_action_index, preflop_actions_length, 2):
                opponent_action = preflop_action_history[i]['action'].lower()
                my_action = preflop_action_history[i-1]['action'].lower()
                if opponent_action == 'call':
                    if (my_action == 'call'):
                        self.opponent_opening_stats['check'] += 1
                    elif my_action == 'raise':
                        self.opponent_opening_stats['call'] += 1
                    else:
                        pass
                #opponent action is raise
                else:
                    if (my_action == 'call'):
                        self.opponent_last_action = 'raise'
                        self.opponent_opening_stats['raise'] += 1  
                    # my_action == raise
                    else:
                        self.opponent_last_action = 're-raise'
                        self.opponent_opening_stats['re-raise'] += 1
        else:
            for i in range(opponent_action_index, preflop_actions_length, 2):
                opponent_action = preflop_action_history[i]['action'].lower()
                my_action = preflop_action_history[i-1]['action'].lower()
                if opponent_action == 'call':
                    if (my_action == 'bigblind'):
                        self.opponent_opening_stats['limp'] += 1
                    elif my_action == 'raise':
                        self.opponent_opening_stats['call'] += 1
                    else:
                        pass
                #opponent action is raise
                else:
                    if (my_action == 'bigblind'):
                        self.opponent_last_action = 'raise'
                        self.opponent_opening_stats['raise'] += 1  
                    # my_action == raise
                    else:
                        self.opponent_last_action = 're-raise'
                        self.opponent_opening_stats['re-raise'] += 1
    
    def get_flop_win_rate(self):
        return self.flop_win_rate
    
    def get_river_win_rate(self):
        return self.river_win_rate
    
        
def setup_ai():
    return ShortStacked ()

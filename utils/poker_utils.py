import json
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

class PokerUtils:
    def __init__(self):
        self.action_stats = {
            'check': 0,
            'call': 0,
            'raise': 0,
            'fold': 0
        }
        self.starting_hand_winning_percentage = {}
        self.load_starting_hand_winning_percentage()

    def load_starting_hand_winning_percentage(self):
        with open('hand_win_percentages.json', 'r') as open_file:
            self.starting_hand_winning_percentage = json.load(open_file)
        open_file.close()
        
    def get_opening_hand_winning_percentage(self, hole_card):
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
        
        return self.starting_hand_winning_percentage[hand][0]['Win %']
    
    def get_call_size(self, round_state):
        street = round_state['street']
        street_actions = round_state['action_histories'][street]
        if len(street_actions) == 0:
            return 0
        else:
            last_action = street_actions[-1]
            call_size = last_action.get('add_amount',0)
        return call_size
    
    def get_raise_size(self, round_state):
        call_size = self.get_call_size(round_state)
        street = round_state['street']
        if street == 'preflop' or street == 'flop':
            raise_size = 20 + call_size
        elif street == 'turn' or street == 'river':
            raise_size = 40 + call_size
        return raise_size
    
    def calculate_pot_odds(self, call_size, pot_size):
        if call_size == 0:
            return 0
        else:
            return call_size / (pot_size + call_size)
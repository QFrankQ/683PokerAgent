import eval7
import random
import itertools
import csv
from collections import defaultdict
from tqdm import tqdm
import json

def generate_starting_hands():
    ranks = '23456789TJQKA'
    hands = []

    # Pocket pairs
    for r in ranks:
        hands.append(r + r)

    # Suited and offsuit combinations
    for i in range(len(ranks)):
        for j in range(i + 1, len(ranks)):
            hands.append(ranks[j] + ranks[i] + 's')  # suited
            hands.append(ranks[j] + ranks[i] + 'o')  # offsuit
    return hands

def get_hand_combinations(starting_hand):
    """Return all 4 or 12 actual card combinations for a hand like 'AKo' or 'AKs'"""
    ranks = '23456789TJQKA'
    suits = 'cdhs'

    if len(starting_hand) == 2:  # pocket pair like 'AA'
        r = starting_hand[0]
        cards = [r + s for s in suits]
        return list(itertools.combinations(cards, 2))
    else:
        r1, r2, suited = starting_hand[0], starting_hand[1], starting_hand[2]
        combos = []
        for s1 in suits:
            for s2 in suits:
                if s1 == s2 and suited == 'o':
                    continue
                if s1 != s2 and suited == 's':
                    continue
                card1 = r1 + s1
                card2 = r2 + s2
                if card1 != card2:
                    combos.append((card1, card2))
        return combos

def simulate_hand(starting_hand, num_simulations=10000):
    wins, ties, total = 0, 0, 0
    combos = get_hand_combinations(starting_hand)
    deck = eval7.Deck()

    for _ in range(num_simulations):
        # Choose one random combo for the hero
        hero_cards = [eval7.Card(c) for c in random.choice(combos)]

        # Build and shuffle deck excluding hero's cards
        deck = eval7.Deck()
        for card in hero_cards:
            deck.cards.remove(card)
        deck.shuffle()

        # Deal opponent hole cards
        opp_cards = deck.peek(2)
        for card in opp_cards:
            deck.cards.remove(card)

        # Deal community cards
        community = deck.peek(5)

        hero_hand = hero_cards + community
        opp_hand = opp_cards + community

        hero_value = eval7.evaluate(hero_hand)
        opp_value = eval7.evaluate(opp_hand)

        if hero_value > opp_value:
            wins += 1
        elif hero_value == opp_value:
            ties += 1
        total += 1

    return wins / total, ties / total

def main():
    hands = generate_starting_hands()
    results = []

    for hand in tqdm(hands, desc="Simulating hands"):
        win_pct, tie_pct = simulate_hand(hand, num_simulations=1000)
        results.append((hand, round(win_pct * 100, 2), round(tie_pct * 100, 2)))

    # Save as dictionary to a json file
    # with open('hand_win_percentages.json', 'w') as f:
    #     json.dump(results, f, indent=4)
    # Save as dictionary to a text file
    hand_dict = defaultdict(list)
    for hand, win_pct, tie_pct in results:
        hand_dict[hand].append({'Win %': win_pct, 'Tie %': tie_pct})
        
    with open('hand_win_percentages.json', 'w') as f:
        json.dump(hand_dict, f, indent=4)
    # with open('hand_win_percentages.txt', 'w') as f:
    #     for hand, stats in hand_dict.items():
    #         f.write(f"{hand}: {stats}\n")
    # Save to CSV
    # with open('hand_win_percentages.csv', 'w', newline='') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(['Hand', 'Win %', 'Tie %'])
    #     writer.writerows(results)

    print("Simulation complete! Results saved to 'hand_win_percentages.csv'.")

if __name__ == "__main__":
    main()

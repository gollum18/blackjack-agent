import argparse

from bqa.player import (
    Account, Agent, Dealer
)


def compare_hands(hand1, hand2):
    '''Compares HAND1 with HAND2.

    Args:
        hand1 (list): A Python list containing bqa.cards.Card
        instances.
        hand2 (list): A Python list containing bqa.cards.Card
        instances.

    Returns:
        (int): -1 if HAND1 is a bust or HAND2 is greater than
        HAND1 without HAND2 having a bust. 0 if HAND1 is
        equal to HAND2. 1 if HAND1 is a blackjack and HAND2
        is not equal to it or if HAND1 does not have a bust
        and has a greater value than HAND2.
    '''
    hand1_value = hand_value(hand1)
    hand2_value = hand_value(hand2)
    # check for bust
    if hand1_value > 21: -1
    elif hand2_value > 21: 1
    # check for equal
    if hand1_value == hand2_value: return 0
    # check for blackjack
    if hand1_value == 21: return 1
    elif hand2_value == 21: return -1
    # otherwise compare the hand values directly
    if hand1_value > hand2_value: return 1
    elif hand1_value < hand2_value: return -1
    return 0


def hand_value(hand):
    '''Determines the value of HAND.

    Returns:
        (int): The value of HAND.
    '''
    # split the hand into two lists, aces and non-aces
    aces = [c for c in hand if c.face == 1]
    non_aces = [c for c in hand if c.face != 1]
    # generate the non-aces sum
    hand_total = sum([c.face_value() for c in non_aces])
    if not aces: return hand_total
    # an ace counts as 11 unless it results in a bust
    #  in that case it is a 1
    for _ in aces:
        if hand_total + 11 > 21:
            hand_total += 1
        else:
            hand_total += 11
    return hand_total


def play(*args, **kwargs):
    dealer = Dealer(**kwargs['dealer_args'])
    agent = Agent(**kwargs['agent_args'])
    game_kwargs = kwargs['game_args']
    total_rounds = game_kwargs['rounds']
    game_stage = Agent.PRE_ROUND
    wager, rounds_played = 0, 0
    # play until the dealer or agent run out of chips or 
    #  the number of epochs is reached
    while (not dealer.account.bankrupt() and 
            not agent.account.bankrupt() and 
            rounds_played < total_rounds):
        game_state = {'game_stage': game_stage}
        if game_stage == Agent.PRE_ROUND:
            # shuffle the deck
            discard = []
            discard.extend(dealer.hand)
            dealer.hand.clear()
            discard.extend(agent.hand)
            agent.hand.clear()
            dealer.deck.reshuffle(discard)
            discard.clear()
            discard = None
            wager = agent.determine_wager(game_state)
            agent.account.withdraw(wager)
            game_state['wager'] = wager
            agent.update_parameters(game_state)
            for i in range(4):
                if i % 2 == 0:
                    dealer.hand.append(dealer.deck.draw())
                else:
                    agent.hand.append(dealer.deck.draw())
            game_stage = Agent.IN_ROUND
        elif game_stage == Agent.IN_ROUND:
            if hand_value(agent.hand) > 21:
                game_stage = Agent.POST_ROUND
                continue
            game_state['dealer_show'] = dealer.hand[0]
            game_state['agent_hand'] = tuple(agent.hand)
            agent.update_parameters(game_state)
            action = agent.determine_action(game_state)
            if action == Agent.HIT:
                agent.hand.append(dealer.deck.draw())
            elif action == Agent.STAND:
                while hand_value(dealer.hand) < 16:
                    dealer.hand.append(dealer.deck.draw())
                game_stage == Agent.POST_ROUND
        elif game_stage == Agent.POST_ROUND:
            winner = compare_hands(dealer.hand, agent.hand)
            if winner < 0: # agent won
                dealer.account.withdraw(wager)
                agent.account.deposit(wager * 2)
                chip_delta = wager * 2
                outcome = Agent.WIN
            elif winner > 0: # dealer won
                dealer.account.deposit(wager)
                chip_delta = -wager
                outcome = Agent.LOSS
            else: # draw
                dealer.account.deposit(wager / 2)
                agent.account.deposit(wager / 2)
                chip_delta = wager / 2
                outcome = Agent.DRAW
            game_state['outcome'] = outcome
            game_state['chip_delta'] = chip_delta
            agent.update_parameters(game_state)
            game_stage = Agent.PRE_ROUND
        rounds_played += 1


    agent.save_table()
    print('Total games played: {}'.format(agent.total_games_played()))
    print('Agent Win Rate: {}%'.format(agent.get_win_rate()*100))
    print('Agent Draw Rate: {}%'.format(agent.get_draw_rate()*100))
    print('Agent Loss Rate: {}%'.format(agent.get_loss_rate()*100))

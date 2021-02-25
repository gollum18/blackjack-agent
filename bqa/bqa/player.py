from collections import Counter
from math import exp
from random import random

from bqa.cards import Deck
from bqa.qtable import QTable


def action_as_index(action):
    # (BET)
    # (HIT, STAND)
    # (WIN, DRAW, LOSS)
    if action == Agent.BET or action == Agent.STAND or action == Agent.WIN: return 0
    elif action == Agent.HIT or action == Agent.DRAW: return 1
    else: return 0


def get_pair_sum(x, y):
    '''Returns the sum(s) from the pair sums matrix for 
    the corresponding face cards.

    Args:
        x (int): The face for the first card.
        y (int): The face for the second card.
    '''
    # the left and right cards can be 11 or 21
    # for simplicity, treat 2 aces as a 2 (though it is also a 12)
    pair_sums = [
        #A, 2, 3, 4, 5, 6, 7, 8,  9, 10/J/Q/K
        [2, 13, 14, 15, 16, 17, 18, 19, 20, 21], #A
        [13, 4, 5, 6, 7, 8, 9, 10, 11, 12], #2
        [14, 5, 6, 7, 8, 9, 10, 11, 12, 13], #3
        [15, 6, 7, 8, 9, 10, 11, 12, 13, 14], #4
        [16, 7, 8, 9, 10, 11, 12, 13, 14, 15], #5
        [17, 8, 9, 10, 11, 12, 13, 14, 15, 16], #6
        [18, 9, 10, 11, 12, 13, 14, 15, 16, 17], #7
        [19, 10, 11, 12, 13, 14, 15, 16, 17, 18], #8
        [20, 11, 12, 13, 14, 15, 16, 17, 18, 19], #9
        [21, 12, 13, 14, 15, 16, 17, 18, 19, 20] #10/J/Q/K
    ]

    def limit(z):
        if x == 1:
            return 0
        elif x >= 10:
            return 9
        else:
            return z - 1

    x2 = limit(x)
    y2 = limit(y)
    return pair_sums[x2][y2]


def get_unknown_cards(known_cards):
    unknown_cards = []
    known_counts = Counter(known_cards)
    for i in range(1, 14):
        if i in known_counts:
            count = known_counts[i]
            for _ in range(4 - count):
                unknown_cards.append(i)
        else:
            for _ in range(4):
                unknown_cards.append(i)
    return unknown_cards


class Account:

    def __init__(self, chips=200):
        self._chips = chips


    def __add__(self, other):
        if not isinstance(self, other): raise TypeError
        self._chips += other


    def __sub__(self, other):
        if not isinstance(other, int): raise TypeError
        self._chips -= other


    def bankrupt(self): return self._chips == 0


    def balance(self): return self._chips


    def deposit(self, amount): self._chips += amount


    def withdraw(self, amount): self._chips -= amount


class Player:

    def __init__(self, account=Account()):
        self.account = account
        self.hand = []


class Agent(Player):

    BET = 'BET'
    STAND = 'STAND'
    HIT = 'HIT'
    WIN = 'WIN'
    DRAW = 'DRAW'
    LOSS = 'LOSS'
    PRE_ROUND = 0
    IN_ROUND = 1
    POST_ROUND = 2
    PRE_ROUND_ACTIONS = (BET)
    IN_ROUND_ACTIONS = (STAND, HIT)
    POST_ROUND_ACTIONS = (WIN, DRAW, LOSS)
    WAGERS = [10, 20, 50, 100]
    PAYOUT = 200

    def __init__(self, db='table.db', alpha=0.05, beta=0.05, learning_rate=0.05, discount_factor=0.05, temperature=0.05, account=Account(chips=500)):
        '''Returns an instance of an Agent that implements a 
        mixed Q-Learning/Neural Network architecture for policy
        decisions.

        Args:
            db (str): The name of the backing database file.
            learning_rate (float): The learning rate (alpha) used
            in q-learning policy updates.
            discount_factor (float): The discount factor (gamma)
            used in q-learning policy updates.
        '''
        super().__init__(account)
        self._table = QTable(db=db)
        # Q-learning/Neural Network parameters
        self._alpha = alpha
        self._beta = beta
        self._lr = learning_rate
        self._df = discount_factor
        self._prior_state = None
        self._prior_actions = None
        self._losses = 0
        self._draws = 0
        self._wins = 0
        self._chip_delta = 0
        self._min_chip_delta = 0
        self._max_chip_delta = 0
        self._temp = temperature


    def _action_distribution(self, state):
        '''Returns a sorted action distribution for STATE.

        Args:
            state (dict): A dictionary containing mappings
            for the current game state.

        Returns:
            (list): A list of tuples where each tuple consists 
            of an action and a probability.
        '''
        game_stage = state['game_stage']
        probabilities = self._softmax(self._table.get(state)[2])
        if game_stage == Agent.PRE_ROUND:
            dist = list(zip(Agent.PRE_ROUND_ACTIONS, probabilities))
        elif game_stage == Agent.IN_ROUND:
            dist = list(zip(Agent.IN_ROUND_ACTIONS, probabilities))
        dist.sort(key=lambda x : x[1])
        return dist


    def _expected_payout(self, state, action):
        '''Determines the expected payout of transitioning 
        from STATE to SUCCESSOR using ACTION. The expected
        payout represents the 'bias' in the agent's model.

        Args:
            state (dict): The prior state.
            action (str): The action taken to transition from
            the prior state to the current state.

        Returns:
            (float): The expected payout of assuming the risk
            in transitioning from STATE to SUCCESSOR using 
            ACTION.
        '''
        game_stage = state['game_stage']
        if game_stage == Agent.PRE_ROUND:
            wager = state['wager']
            risk = self._risk(state, action)
            return wager * risk
        elif game_stage == Agent.IN_ROUND:
            agent_hand = state['agent_hand']
            dealer_show = state['dealer_show']
            agent_total = sum([c.face for c in agent_hand])
            known_cards = [dealer_show.face].extend([c.face for c in agent_hand])
            unknown_cards = get_unknown_cards(known_cards)
            non_busting_cards = list(filter(lambda x: x + agent_total <= 21, unknown_cards))
            face_to_blackjack = 21 - agent_total
            cards_for_blackjack = list(filter(lambda x : x == face_to_blackjack, unknown_cards))
            non_busting_counts = dict(Counter(non_busting_cards))
            blackjack_counts = sum(cards_for_blackjack)
            total_unknowns = len(unknown_cards)
            expected_payout = (blackjack_counts / total_unknowns) * (Agent.PAYOUT * (1 / (21 - face_to_blackjack)))
            total_unknowns = len(unknown_cards)
            for card, count in non_busting_counts.items():
                p = count / total_unknowns
                payout = Agent.PAYOUT * (1 / (21 - card))
                expected_payout += p * payout
            if action == Agent.HIT:
                return expected_payout
            else:
                return 0
        elif game_stage == Agent.POST_ROUND:
            return state['chip_delta']



    def _get_actions(self, state):
        '''Determines the available actions for STATE.

        Args:
            state (dict): A dictionary containing mappings
            for the current game state.

        Returns:
            (list): A list containing action strings.
        '''
        game_stage = state['game_stage']
        if game_stage == Agent.PRE_ROUND: return Agent.PRE_ROUND_ACTIONS
        elif game_stage == Agent.IN_ROUND: return Agent.IN_ROUND_ACTIONS


    def _reward(self, state, action, successor):
        '''Determines the reward for transitioning from
        STATE to SUCCESSOR using ACTION.

        Args:
            state (dict): The prior state.
            action (int): The action used to transition to 
            the successor state.
            successor (dict): The current state.
        '''
        prior_game_stage = state['game_stage']
        succ_game_stage = successor['game_stage']
        prior_risk = self._risk(state, action)
        succ_risk = self._risk(successor, action)
        if succ_game_stage == Agent.POST_ROUND:
            base = 250
            outcome = successor['outcome']
            chip_delta = successor['chip_delta']
            if outcome == Agent.WIN:
                if action == Agent.HIT: return base * prior_risk
                elif action == Agent.STAND: return base
                else: return base
                return base
            elif outcome == Agent.LOSS:
                if action == Agent.HIT: return -base
                elif action == Agent.STAND: return 0
                else: return 0
            elif outcome == Agent.DRAW:
                return 0
        elif succ_game_stage == Agent.IN_ROUND:
            base = 500
            if prior_game_stage == Agent.PRE_ROUND: return base
            x = self._softmax([prior_risk, succ_risk])
            return (1 - (x[1] / sum(x))) * base
        elif succ_game_stage == Agent.PRE_ROUND:
            base = 100
            wr = self.get_win_rate()
            dr = self.get_draw_rate()
            lr = self.get_loss_rate()
            if wr == 0 or lr == 0:
                return base
            return base * wr + base * dr - base * lr
        return 0


    def _risk(self, state, action):
        '''Determines the statistical risk of transitioning
        from the prior STATE to the next state using ACTION.

        Args:
            state (dict): The prior state.
            action (str): The action used to transition to
            the successor state.

        Returns:
            (float): A floating-point number in the range
            [0, 1].
        '''
        # The risk function for PRE_ROUND needs to factor in:
        #   win rate/loss rate/draw rate
        #   chip delta - larger negative values are riskier
        #     larger positive values are safer
        # The risk function for IN_ROUND needs to factor in:
        #   Probability of staying at or below 21
        #   Probability of getting 21
        #   Probability of dealer hidden card summing to 21
        #   Probability of having greater sum than dealer
        game_stage = state['game_stage'] 
        if game_stage == Agent.PRE_ROUND:
            cd_num = self._chip_delta - self._min_chip_delta
            cd_den = self._max_chip_delta - self._min_chip_delta
            return 0 if cd_den == 0 else 1 - (cd_num / cd_den)
        elif game_stage == Agent.IN_ROUND:
            dealer_show = state['dealer_show']
            agent_hand = state['agent_hand']
            agent_total = sum([c.face for c in agent_hand])
            known_cards = [dealer_show.face]
            known_cards.extend([c.face for c in agent_hand])
            unknown_cards = get_unknown_cards(known_cards)
            non_busting_cards = len(list(filter(lambda x: x + agent_total <= 21, unknown_cards)))
            busting_cards = len(unknown_cards) - non_busting_cards
            face_to_blackjack = 21 - agent_total
            cards_for_blackjack = len(list(filter(lambda x : x == face_to_blackjack, unknown_cards)))
            p_not_busting = non_busting_cards / len(unknown_cards)
            p_getting_blackjack = cards_for_blackjack / len(unknown_cards)
            p_dealer_blackjack = len(list(filter(lambda x : x + dealer_show.face == 21, unknown_cards))) / len(unknown_cards)
            p_no_dealer_blackjack = 1 - p_dealer_blackjack
            dealer_hidden_cards = len(list(filter(lambda x: x + dealer_show.face < agent_total, unknown_cards)))
            # TODO: Need to verify the P(AT - DT > 0) calculation
            p_at_gt_dt = dealer_hidden_cards / len(unknown_cards)
            if p_not_busting == 0: return 0
            risk = ((p_getting_blackjack + p_at_gt_dt) * p_not_busting * p_dealer_blackjack) / (p_not_busting * p_no_dealer_blackjack)
            if action == Agent.HIT:
                return 1 - risk
            return risk
        elif game_stage == Agent.POST_ROUND:
            outcome = state['outcome']
            total_games_played = self.total_games_played() + 1
            wins = self._wins + 1 if outcome == Agent.WIN else self._wins
            losses = self._losses + 1 if outcome == Agent.LOSS else self._losses
            draws = self._draws + 1 if outcome == Agent.DRAW else self._draws
            if total_games_played == 0: return 0
            return (wins + draws - losses) / total_games_played


    def _softmax(self, v):
        '''Performs the softmax function on the input 
        vector V to transform it's elements to decimals
        that sum to 1.

        Args:
            v (list): A list containing numeric values.

        Returns:
            (list): A list containing decimals that
            sum to 1.
        '''
        vsum = sum(map(exp, [x / self._temp for x in v]))
        return list(map(lambda x : exp(x/self._temp) / vsum, v))


    def _update_qtable(self, state):
        '''Updates the Q-Table for the prior state maintained
        by the agent for the new STATE.

        Args:
            (state): The new state as observed by the agent.
        '''
        successor = state
        state = self._prior_state
        get_result = self._table.get(state)
        prior_weights, prior_biases, prior_qvalues = get_result[0], get_result[1], get_result[2]
        get_result = self._table.get(successor)
        succ_weights, succ_biases, succ_qvalues = get_result[0], get_result[1], get_result[2]
        for action in self._prior_actions:
            action_index = action_as_index(action)
            # determine the updated weight
            old_weight = prior_weights[action_index]
            new_weight = self._risk(state, action)
            prior_weights[action_index] = (1 - self._alpha) * old_weight + self._alpha * new_weight
            # determine the updated bias
            old_bias = prior_biases[action_index]
            new_bias = self._expected_payout(state, action)
            prior_biases[action_index] = (1 - self._beta) * old_bias + self._beta * new_bias
            # determine the updated q-values
            prior_qvalue = prior_qvalues[action_index]
            succ_qvalue = succ_qvalues[action_index]
            reward = self._reward(state, action, successor)
            new_qvalue = (
                # bellman-ford minus the argmax portion    
                prior_qvalue +
                self._lr * (
                    reward + 
                    self._df * (
                        succ_qvalue - prior_qvalue
                    )
                )
            )
            action_weight = prior_weights[action_index]
            action_bias = prior_biases[action_index]
            prior_qvalues[action_index] = action_weight * new_qvalue + action_bias
        self._table.put(state, prior_weights, prior_biases, prior_qvalues)


    def determine_action(self, state):
        '''Stochastically chooses an action from STATE 
        using a weighted probability distribution for 
        the various actions.

        Args:
            state (dict): A dictionary containing mappings 
            for the current game state.
        '''
        action = None
        dist = self._action_distribution(state)
        p = random()
        for a, P in dist:
            if p < P:
                action = a
                break
        if not action: action = dist[-1][0]
        return action


    def determine_wager(self, state):
        '''Determines how much chips the agent should wager.

        Returns:
            (int): The number of chips that the agent should
            wager.
        '''
        cd_num = self._chip_delta - self._min_chip_delta
        cd_den = self._max_chip_delta - self._max_chip_delta
        risk = cd_num / cd_den if cd_den != 0 else .5
        if risk <= 0.25:
            wager = 0
        elif risk <= 0.5:
            wager = 1
        elif risk <= 0.75:
            wager = 2
        else:
            wager = 3
        if Agent.WAGERS[0] > self.account.balance():
            wager = self.account.balance()
        while Agent.WAGERS[wager] > self.account.balance():
            wager -= 1
        return Agent.WAGERS[wager]


    def get_draw_rate(self):
        '''Gets the agents draw rate. How often the agent draws.

        Return:
            (float): A floating point number in the range [0, 1].
        '''
        games_played = self.total_games_played()
        if games_played == 0: return 0
        return self._draws / self.total_games_played()


    def get_loss_rate(self):
        '''Gets the agents loss rate. How often the agent loses.

        Returns:
            (float): A floating point number in the range [0, 1]. 
        '''
        games_played = self.total_games_played()
        if games_played == 0: return 0
        return self._losses / self.total_games_played()

    def get_win_rate(self):
        '''Gets the agents win rate. How often the agent wins.

        Returns:
            (float): A floating point number in the range [0, 1].
        '''
        games_played = self.total_games_played()
        if games_played == 0: return 0
        return self._wins / games_played


    def save_table(self):
        '''Saves the agents q-table.'''
        self._table.save_table()


    def total_games_played(self):
        return self._wins + self._draws + self._losses


    def update_parameters(self, state):
        game_stage = state['game_stage']
        # always update the q-table regardless of game stage
        if self._prior_state:
            self._update_qtable(state)
        # update agent variables needed by other calculations
        if game_stage == Agent.PRE_ROUND:
            self._prior_actions = Agent.PRE_ROUND_ACTIONS
        elif game_stage == Agent.IN_ROUND:
            self._prior_actions = Agent.IN_ROUND_ACTIONS
        elif game_stage == Agent.POST_ROUND:
            self._prior_actions = Agent.POST_ROUND_ACTIONS
            outcome = state['outcome']
            chip_delta = state['chip_delta']
            if outcome == Agent.WIN: self._wins += 1
            elif outcome == Agent.LOSS: self._losses += 1
            elif outcome == Agent.DRAW: self._draws += 1
            self._chip_delta += chip_delta
            self._min_chip_delta = min(self._min_chip_delta, self._chip_delta)
            self._max_chip_delta = max(self._max_chip_delta, self._chip_delta)
        self._prior_state = state


class Dealer(Player):

    def __init__(self, deck=Deck(), account=Account(chips=2000)):
        super().__init__(account)
        self.deck = Deck()

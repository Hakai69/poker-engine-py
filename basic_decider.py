from game_objects import Action, ActionType, HoleCards, Board, GameStatus, GamePhase
from player import Player
from stats import calculate_equity

class BasicDecisionMaker(Player):
    '''Basic decision maker based on a pre-made decision tree.'''
    def __init__(self, name: str, *, verbose: bool = False):
        super().__init__(name)
        self.verbose = verbose
    
    def get_action(
        self,
        player_hand: HoleCards,
        board: Board,
        status: GameStatus,
        *,
        op_holecards: HoleCards | None = None
    ) -> Action:
        
        winrate, lose_rate = calculate_equity(player_hand, board)
        draw_rate = 1 - winrate - lose_rate
        if self.verbose:
            print(f'Bot\'s hand: {player_hand}')
            print('\033[4mEquity\033[0m')
            print(f'Win: {winrate:.1%}, Draw: {draw_rate:.1%}, Lose: {lose_rate:.1%}')

        # Retrieve game status information
        pot_size = sum(status.bets)
        bet_to_call = status.bets[1 - status.current_player] - status.bets[status.current_player]
        min_bet = max(status.blind, bet_to_call)
        money = status.players_money[status.current_player]

        # Aggressive showdown strategy
        if status.game_phase == GamePhase.SHOWDOWN:
            if op_holecards is None:
                return Action(ActionType.SHOW)
            is_win, idx = board.evaluate(player_hand, op_holecards)
            if is_win and idx == 1:
                return Action(ActionType.MUCK)
            return Action(ActionType.SHOW)
        
        valid_actions = status.get_valid_actions()
        
        spare_money = money - bet_to_call
        if winrate > 0.9: # Very high equity
            if ActionType.RAISE in valid_actions:
                return Action(ActionType.RAISE, spare_money) # All-in
            return Action(ActionType.CALL)
                        
        # Rules based on the equity
        if winrate > 0.7:  # High equity
            if ActionType.RAISE in valid_actions:
                raise_amount = max(min_bet * 2, pot_size * 0.5)
                raise_amount = min(raise_amount, spare_money)
                return Action(ActionType.RAISE, int(raise_amount))
            
            if ActionType.CALL in valid_actions:
                return Action(ActionType.CALL)
            
            return Action(ActionType.CHECK)

        if winrate > 0.5:
            if ActionType.RAISE in valid_actions:
                raise_amount = max(min_bet, pot_size * 0.1)
                raise_amount = min(raise_amount, spare_money)
                return Action(ActionType.RAISE, int(raise_amount))
            
            if ActionType.CALL in valid_actions:
                return Action(ActionType.CALL)
            
            return Action(ActionType.CHECK)
            
        if winrate > 0.4:  # Moderate equity
            if ActionType.CALL in valid_actions:
                return Action(ActionType.CALL)
            return Action(ActionType.CHECK)

        
        if winrate + draw_rate > 0.3:  # Low equity
            if ActionType.CALL in valid_actions:
                return Action(ActionType.CALL)
            return Action(ActionType.CHECK)
        
        # Very low equity
        if ActionType.CHECK in valid_actions:
            return Action(ActionType.CHECK)
        
        return Action(ActionType.FOLD)

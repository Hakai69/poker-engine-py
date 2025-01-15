from enum import Enum, auto

from .action import ActionType

class GamePhase(Enum):
    PRE_FLOP = auto()
    FLOP = auto()
    TURN = auto()
    RIVER = auto()
    SHOWDOWN = auto()
    FINISHED = auto()
    
    def next_phase(self):
        if self == GamePhase.PRE_FLOP:
            return GamePhase.FLOP
        if self == GamePhase.FLOP:
            return GamePhase.TURN
        if self == GamePhase.TURN:
            return GamePhase.RIVER
        if self == GamePhase.RIVER:
            return GamePhase.SHOWDOWN
        if self == GamePhase.SHOWDOWN:
            return GamePhase.FINISHED
        raise ValueError('Game is already finished.')
    
    def __str__(self) -> str:
        return self.name.replace('_', ' ').title()

class GameStatus:
    '''
    Information about the current game state the players should be able
    to know.
    '''
    def __init__(self, player1_money: int, player2_money: int, blind: int):
        self.players_money = [player1_money, player2_money]
        self.game_phase = GamePhase.PRE_FLOP
        self.bets = [0, 0]
        self.initial_player = 0
        self.current_player = 1
        self.last_aggresive_player = 0
        self.blind = blind
        
    def get_valid_actions(self):
        player = self.current_player
        other = 1 - player
        if self.game_phase == GamePhase.SHOWDOWN:
            return [ActionType.MUCK, ActionType.SHOW]
        
        valid_actions = [ActionType.FOLD]
        if self.bets[player] >= self.bets[other]:
            valid_actions.append(ActionType.CHECK)
        else:
            valid_actions.append(ActionType.CALL)
        
        if self.players_money[player] > self.bets[other]:
            valid_actions.append(ActionType.RAISE)
            
        return valid_actions
    
    def __str__(self):
        return (
            f'GamePhase: {self.game_phase}, '
            f'Current player: {self.current_player}, '
            f'Bets: {self.bets}, '
            f'Players money: {self.players_money}'
        )
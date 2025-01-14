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

class GameStatus:
    def __init__(self, players_money):
        self.players_money = players_money
        self.game_phase = GamePhase.PRE_FLOP
        self.bets = [0, 0]
        self.current_player = 0
        self.last_aggresive_player = 0
        
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
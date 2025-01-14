from abc import ABC, abstractmethod
from typing import Collection, Literal

from .game_objects import Hand, Board, GameStatus, Action, ActionType

class Player(ABC):
    '''A player in the game.'''
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def get_action(
        self,
        hand: Hand,
        board: Board,
        status: GameStatus,
        *,
        op_hand: Hand | None = None
    ) -> Action:
        '''Return the player's move given the current board.'''
        
class ConsolePlayer(Player):
    '''A player that plays through the terminal.'''
    _string_to_action_type = {
        'fold' : ActionType.FOLD,
        'check': ActionType.CHECK,
        'call' : ActionType.CALL,
        'raise': ActionType.RAISE,
        'muck' : ActionType.MUCK,
        'show' : ActionType.SHOW
    }
    @staticmethod
    def action_type_from_string(
        raw_action: Literal['fold', 'check', 'call', 'raise', 'muck', 'show']
    ) -> ActionType | None:
        
        return ConsolePlayer._string_to_action_type.get(raw_action, None)
    
    @staticmethod
    def ask_action_type(valid_actions: Collection[ActionType]) -> ActionType:
        query = f'Enter your move ({'/'.join(map(str, valid_actions))}): '
        raw_action = input(query)
        action_type = ConsolePlayer.action_type_from_string(raw_action)
        while not action_type or action_type not in valid_actions:
            print('Invalid action. Please try again.')
            raw_action = input(query)
            action_type = ConsolePlayer.action_type_from_string(raw_action)
            
        return action_type
    
    @staticmethod
    def ask_action_value(action_type: ActionType) -> int | None:
        value = None
        if action_type == ActionType.RAISE:
            value = input('Enter the amount you want to raise: ')
            while not value.isdigit():
                print('Invalid value. Please try again.')
                value = input('Enter the amount you want to raise: ')
            value = int(value)
                
        return value
        
    def get_action(
        self,
        hand: Hand,
        board: Board,
        status: GameStatus,
        *,
        op_hand: Hand | None = None
    ) -> Action:
        
        print(f'{self.name}\'s turn')
        print(f'Your hand: {hand}')
        print(f'The board: {board}')
        print(f'The status: {status}')
        
        valid_actions = status.get_valid_actions()
        action_type = self.ask_action_type(valid_actions)
        value = self.ask_action_value(action_type)
        
        return Action(action_type, value)

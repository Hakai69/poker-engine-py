from game_objects import HoleCards, Action, ActionType, GameStatus, Board
from stats.equity import EquityCalculator
from player import Player

class DecisionMaker(Player):
    def __init__(self, name: str):
        super().__init__(name)
        self.equity_calculator = EquityCalculator()

    def decide_action(self, hole_cards: HoleCards, board: Board, status: GameStatus) -> Action:
        # Calculate equity (sin rango del oponente)
        equity = self.equity_calculator.calculate_equity(
            hole_cards=HoleCards(hole_cards),
            board=board
        )

        valid_actions = status.get_valid_actions()
        
        if equity > 0.7:  # Muy buena mano
            if ActionType.RAISE in valid_actions:
                # Apuesta agresiva: 3/4 del pot
                return Action(ActionType.RAISE, int(sum(status.bets) * 0.75))
            elif ActionType.CALL in valid_actions:
                return Action(ActionType.CALL, None)
            
        elif equity > 0.5:  # Mano decente
            if ActionType.RAISE in valid_actions and status.bets[1 - status.current_player] == 0:
                # Apuesta moderada: 1/2 del pot
                return Action(ActionType.RAISE, int(sum(status.bets) * 0.5))
            elif ActionType.CALL in valid_actions:
                return Action(ActionType.CALL, None)
            elif ActionType.CHECK in valid_actions:
                return Action(ActionType.CHECK, None)
                
        elif equity > 0.3:  # Mano mala
            if ActionType.CHECK in valid_actions:
                return Action(ActionType.CHECK, None)
            elif ActionType.CALL in valid_actions and status.bets[1 - status.current_player] <= status.players_money[status.current_player] * 0.1:
                # Solo call si la apuesta es pequeña
                return Action(ActionType.CALL, None)
                
        # por default check o fold
        if ActionType.CHECK in valid_actions:
            return Action(ActionType.CHECK, None)
        
        return Action(ActionType.FOLD, None)

    def _calculate_pot_size(self, status: GameStatus) -> int:
        return sum(status.bets) + sum(
            min(bet, money) 
            for bet, money in zip(status.bets, status.players_money)
        )
        
    
    def __repr__(self):
        return str(self.decide_action.__name__)
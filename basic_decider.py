from game_objects import Action, ActionType, HoleCards, Board, GameStatus

class DecisionMaker:
    def decide_action(self, player_hand: HoleCards, board: Board, status: GameStatus) -> Action:
        equity = board.evaluate(player_hand)

        # Obtener información del estado del juego
        pot_size = sum(status.bets)  # Tamaño del bote
        bet_to_call = status.bets[1 - status.current_player] - status.bets[status.current_player]
        min_bet = max(status.blind, bet_to_call)

        # Reglas basadas en la equity
        if equity > 0.7:  # Equity alta
            if ActionType.RAISE in status.get_valid_actions():
                raise_amount = max(min_bet * 2, pot_size * 0.5)
                return Action(ActionType.RAISE, raise_amount)
            
            elif ActionType.CALL in status.get_valid_actions():
                return Action(ActionType.CALL, None)
            
            # Por si algo fallase (no debería llegar aquí)
            return Action(ActionType.FOLD, None)
            
        elif equity > 0.4:  # Equity moderada
            if ActionType.CALL in status.get_valid_actions():
                return Action(ActionType.CALL, None)
            elif ActionType.CHECK in status.get_valid_actions():
                return Action(ActionType.CHECK, None)
            return Action(ActionType.FOLD, None)
        
        else:  # Equity baja
            if ActionType.CHECK in status.get_valid_actions():
                return Action(ActionType.CHECK)
            
            return Action(ActionType.FOLD)

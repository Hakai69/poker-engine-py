raise NotImplementedError("Implementar la clase EquityCalculator")

from game_objects.board import Board
from game_objects.deck import Deck

class EquityCalculator:
    @classmethod
    def calculate_equity(cls, hole_cards, board, opponent_range=None, num_simulations=1000):
        player_cards = list(hole_cards)
        if opponent_range is None:
            opponent_range = []  

        equity_results = []
        for _ in range(num_simulations):
            simulation_deck = Deck(existing_cards=player_cards + board)

            opponent_hand = cls._draw_opponent_hand(simulation_deck)
            board_simulation = cls._draw_board(simulation_deck)

            # Evaluar manos usando el método evaluate de Board
            board_instance = Board()
            board_instance[:3] = board_simulation[:3]
            board_instance[3] = board_simulation[3]
            board_instance[4] = board_simulation[4]

            is_win, id_winner = board_instance.evaluate(player_cards, opponent_hand)
            if is_win:
                equity_results.append(id_winner == 0)
                continue
            
        equity = sum(equity_results) / len(equity_results)
        return equity


    def _draw_opponent_hand(deck):
        return [deck.deal() for _ in range(2)]  # Oponente recibe 2 cartas

    def _draw_board(deck):
        return [deck.deal() for _ in range(5)]  # El board tiene 5 cartas

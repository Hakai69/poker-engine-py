from math import perm, comb

from game_objects.board import Board
from game_objects.deck import Deck
from game_objects import Deck, Board, HoleCards, GamePhase

# Fast algorithms for copying boards in any state
def _preflop(board: Board, deck: Deck):
    new_board = Board()
    new_board[:] = deck.deal(), deck.deal(), deck.deal(), deck.deal(), deck.deal()
    return new_board

def _flop(board: Board, deck: Deck):
    new_board = Board()
    new_board[:3] = board[:3]
    new_board[-2:] = deck.deal(), deck.deal()
    return new_board

def _turn(board: Board, deck: Deck):
    new_board = Board()
    new_board[:4] = board[:4]
    new_board[-1] = deck.deal()
    return new_board

def _river(board: Board, deck: Deck):
    new_board = Board()
    new_board[:] = board[:]
    return new_board

generate_board_func = {
    GamePhase.PRE_FLOP: _preflop,
    GamePhase.FLOP: _flop,
    GamePhase.TURN: _turn,
    GamePhase.RIVER: _river
}
    


def calculate_equity(
    hole_cards: HoleCards,
    board: Board,
    num_simulations=1000
) -> tuple[float, float]:
    '''
    Calculate the equity of the player hand against a random opponent hand.
    Args:
        hole_cards (HoleCards): The player hand.
        board (Board): The board, regardless how many cards it has.
        num_simulations (int): The number of simulations to run.
        
    Returns:
        tuple[float, float]: The winrate and lose rate of the player hand.
    '''

    player_cards = list(hole_cards)
    if opponent_range is None:
        opponent_range = []
        
    game_phase = board.status
    board_f = generate_board_func[game_phase]

    equity_results = []
    for _ in range(num_simulations):
        simulation_deck = Deck(existing_cards=player_cards + board)
        # Generate oponent hand
        opponent_hand = HoleCards([simulation_deck.deal() for _ in range(2)])
        # Generate board
        simmulation_board = board_f(board, simulation_deck)
        
        # Evaluate position
        is_win, winner_idx = simmulation_board.evaluate(player_cards, opponent_hand)
        if is_win:
            equity_results.append(winner_idx == 0)
            continue
        
    # Calculate both winrate and lose rate since the are not complementary
    # (draw rate)
    winrate = sum(equity_results) / num_simulations
    lose_rate = equity_results.count(False) / num_simulations
    return winrate, lose_rate

def better_equity_calculator(
    hole_cards: HoleCards,
    board: Board
) -> tuple[float, float]:
    '''
    Calculate the equity of the player hand against a random opponent hand.
    Uses combinatorial analysis to calculate the equity instead of simmulations.
    Args:
        hole_cards (HoleCards): The player hand.
        board (Board): The board, regardless how many cards it has.
    
    '''
    raise NotImplementedError()
    n_board_cards = len(board)
    known_cards = n_board_cards + 2
    unknown_cards = 5 - n_board_cards + 2
    total_cards = 52 - known_cards
    total_cases = perm(total_cards, unknown_cards)
    # Check for flushes
    # Count and save all flushes that still are possible
    common_colors = [data for data in board.color_count().items() if data[1] - len(board) >= 0]
    own_colors = {color:hole_cards.color_count() for color,_ in common_colors}
    total_flush_cases = 0
    for color, count in common_colors:
        missing = 5 - count
        for excess in range(unknown_cards - missing):
            new_colored_cards = 5 - count + excess
            flush_cases = perm(13 - count - own_colors[color], new_colored_cards)
            # From the remaining cards, we can only get non-colors and cards 
            # that have not been seen not to repeat cases
            seen_cards_non_color = known_cards - own_colors[color] - count
            remaining_cards = unknown_cards - 5 + count - excess
            remaining_cases = perm(
                total_cards - 13 - seen_cards_non_color,
                remaining_cards
            )
            arrangements = comb(unknown_cards, new_colored_cards)
            total_flush_cases += flush_cases * remaining_cases * arrangements
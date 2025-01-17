from game_objects import (
    Deck,
    HoleCards,
    Board,
    ActionType,
    Action,
    GamePhase,
    GameStatus
)

from player import Player

class Game:
    def __init__(
        self,
        player1: Player,
        player2: Player,
        player1_money: int = 1000,
        player2_money: int = 1000,
        blind: int = 10
    ):
        assert player1.name != player2.name
        if blind % 2:
            raise ValueError('Blind must be an even number.')
        self.players = [player1, player2]
        self.hole_cards = [None, None]
        self.board = Board()
        self.deck = Deck()
        
        self.blind = blind
        player1_money = max(player1_money, 0)
        player2_money = max(player2_money, 0)
        self.status = GameStatus(player1_money, player2_money, blind)
        
    def process_action(self, action: Action, verbose: bool = False) -> None:
        status = self.status
        player = status.current_player
        other = 1 - player
        if action.type == ActionType.FOLD:
            status.players_money[other] += status.bets[player] + status.bets[other]
            status.game_phase = GamePhase.FINISHED
            if verbose:
                print(f'{self.players[player]} folded.')
            return
        
        if action.type == ActionType.CHECK:
            if status.bets[player] != status.bets[other]:
                raise ValueError('Cannot check when the bet is different from the other player\'s bet.')
            if verbose:
                print(f'{self.players[player]} checked.')
            return
        
        if action.type == ActionType.CALL:
            amount = status.bets[other] - status.bets[player]
            if amount == 0:
                return self.process_action(Action(ActionType.CHECK), verbose=verbose)
            
            status.players_money[player] -= amount
            status.bets[player] += amount
            assert status.bets[player] == status.bets[other]
            if verbose:
                print(f'{self.players[player]} called.')
            return
        
        if action.type == ActionType.RAISE:
            call_bet = status.bets[other] - status.bets[player]
            total_bet = action.value + call_bet
            total_bet = min(total_bet, status.players_money[player])
            # Cannot raise over all-in in two player game
            total_bet = min(total_bet, status.players_money[other])
            if total_bet - call_bet == 0:
                return self.process_action(Action(ActionType.CALL), verbose=verbose)
            status.players_money[player] -= total_bet
            status.bets[player] += total_bet
            status.last_aggresive_player = player
            if verbose:
                raise_bet = total_bet - call_bet
                print(f'{self.players[player]} raised by {raise_bet}.')
            return
        
        if action.type == ActionType.MUCK:
            if status.game_phase != GamePhase.SHOWDOWN:
                raise ValueError('Cannot muck before the showdown.')
            status.players_money[other] += status.bets[player] + status.bets[other]
            status.game_phase = GamePhase.FINISHED
            if verbose:
                print(f'{self.players[player]} mucked.')
            return
        
        if action.type == ActionType.SHOW:
            if status.game_phase != GamePhase.SHOWDOWN:
                raise ValueError('Cannot show before the showdown.')
            if verbose:
                print(f'{self.players[player]} showed their hole cards.')
            return
        
        raise ValueError('Invalid action type.')
    
    def summary(self, initial_money: tuple[int, int]) -> None:
        print('Summary:')
        if initial_money[0] > self.status.players_money[0]:
            print(f'{self.players[1]} won {initial_money[0] - self.status.players_money[0]}!')
            return
        print(f'{self.players[0]} won {initial_money[1] - self.status.players_money[1]}!')
        
    def play_phase(self, verbose: bool = False) -> None:
        status = self.status
        phase = status.game_phase
        next_phase = phase.next_phase()
        
        action1 = self.players[status.current_player] \
            .get_action(self.hole_cards[status.current_player], self.board.copy(), status.copy())
        self.process_action(action1, verbose=verbose)
        status.current_player = 1 - status.current_player
        while status.game_phase == phase:
            action = self.players[status.current_player] \
                .get_action(self.hole_cards[status.current_player], self.board.copy(), status.copy())
            self.process_action(action, verbose=verbose)
            status.current_player = 1 - status.current_player
            if status.bets[0] == status.bets[1]:
                status.game_phase = next_phase
        
        status.current_player = status.initial_player

    def play_round(self, verbose: bool = False):
        status = self.status
        status.initial_player = 1 - status.initial_player
        status.current_player = status.initial_player
        status.game_phase = GamePhase.PRE_FLOP
        status.last_aggresive_player = 1 - status.initial_player
        if status.players_money[0] < self.blind:
            raise ValueError(f'{self.players[0]} is out of money!')
        if status.players_money[1] < self.blind:
            raise ValueError(f'{self.players[1]} is out of money!')
        
        if status.players_money[0] < 0 or status.players_money[1] < 0:
            raise ValueError('Something went wrong, players have negative money.')
        
        initial_money = (status.players_money[0], status.players_money[1])
        status.players_money[status.initial_player] -= self.blind // 2
        status.players_money[1 - status.initial_player] -= self.blind
        status.bets[status.initial_player] = self.blind // 2
        status.bets[1 - status.initial_player] = self.blind
        all_in = status.players_money[status.initial_player] == 0
        
        if verbose: print('Playing a new round!')
        self.board.clear()
        for i in range(2):
            self.hole_cards[i] = HoleCards([self.deck.deal(), self.deck.deal()])
        if verbose:
            print(f'Player 1 hole cards: {self.hole_cards[0]}')
            print(f'Player 2 hole cards: {self.hole_cards[1]}')
        
        # PREFLOP
        if verbose: print('Pre-flop betting round!')
        if not all_in:
            self.play_phase(verbose=verbose)
        
        if status.game_phase == GamePhase.FINISHED:
            self.summary(initial_money)
            if verbose:
                print('Round finished!')
            return
        
        if status.players_money[0] == 0 or status.players_money[1] == 0:
            all_in = True
        
        # FLOP
        if verbose: print('Flop betting round!')
        self.board.flop(self.deck.deal(), self.deck.deal(), self.deck.deal())
        if verbose: print(f'Board: {self.board}')
        if not all_in:
            self.play_phase(verbose=verbose)
            
        if status.game_phase == GamePhase.FINISHED:
            self.summary(initial_money)
            if verbose:
                print('Round finished!')
            return
        
        if status.players_money[0] == 0 or status.players_money[1] == 0:
            all_in = True
            
        # TURN
        if verbose: print('Turn betting round!')
        self.board.turn(self.deck.deal())
        if verbose: print(f'Board: {self.board}')
        if not all_in:
            self.play_phase(verbose=verbose)
        
        if status.game_phase == GamePhase.FINISHED:
            self.summary(initial_money)
            if verbose:
                print('Round finished!')
            return
        
        if status.players_money[0] == 0 or status.players_money[1] == 0:
            all_in = True
            
        # RIVER
        if verbose: print('River betting round!')
        self.board.river(self.deck.deal())
        if verbose: print(f'Board: {self.board}')
        if not all_in:
            self.play_phase(verbose=verbose)
        
        if status.game_phase == GamePhase.FINISHED:
            self.summary(initial_money)
            if verbose:
                print('Round finished!')
            return
        
        # SHOWDOWN
        if verbose: print('Showdown!')
        ag_player = status.last_aggresive_player
        action = self.players[ag_player] \
            .get_action(self.hole_cards[ag_player], self.board.copy(), status.copy())
        self.process_action(action, verbose=verbose)
        
        if status.game_phase == GamePhase.FINISHED:
            self.summary(initial_money)
            if verbose:
                print('Round finished!')
            return
        
        other = 1 - ag_player
        action = self.players[other].get_action(
            self.hole_cards[other],
            self.board.copy(),
            status.copy(),
            op_holecards=self.hole_cards[ag_player]
        )
        self.process_action(action, verbose=verbose)
        
        if status.game_phase == GamePhase.FINISHED:
            self.summary(initial_money)
            if verbose:
                print('Round finished!')
            return
        
        is_win, index = self.board.evaluate(*self.hole_cards)
        if not is_win:
            status.players_money[0] += status.bets[0]
            status.players_money[1] += status.bets[1]
            return
        
        status.players_money[index] += sum(status.bets)
        
        # Change initial playe
        self.summary(initial_money)
        if verbose:
            print(f'{self.players[index]} won the round!')
            
            
if __name__ == '__main__':
    from player import ConsolePlayer
    player1 = ConsolePlayer('Player 1')
    player2 = ConsolePlayer('Player 2')
    game = Game(player1, player2)
    game.play_round(verbose=True)
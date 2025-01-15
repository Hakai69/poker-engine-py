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
        player2_money: int = 1000
    ):
        assert player1.name != player2.name
        self.players = [player1, player2]
        self.hole_cards = [None, None]
        self.board = Board()
        self.deck = Deck()
        self.status = GameStatus([max(player1_money, 0), max(player2_money, 0)])
        
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
            initial_bet = status.bets[other]
            amount = action.value + status.bets[other] - status.bets[player]
            amount = min(amount, status.players_money[player])
            # Cannot raise over all-in in two player game
            amount = min(amount, status.players_money[other])
            if amount - initial_bet == 0:
                return self.process_action(Action(ActionType.CALL), verbose=verbose)
            status.players_money[player] -= amount
            status.bets[player] += amount
            status.last_aggresive_player = player
            if verbose:
                print(f'{self.players[player]} raised by {amount - initial_bet}.')
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
        phase = self.status.game_phase
        next_phase = phase.next_phase()
        action1 = self.players[0].get_action(self.hole_cards[0], self.board, self.status)
        self.process_action(action1, verbose=verbose)
        i = 1
        while self.status.game_phase == phase:
            action = self.players[i].get_action(self.hole_cards[i], self.board, self.status)
            self.process_action(action, verbose=verbose)
            i = 1 - i
            if self.status.bets[0] == self.status.bets[1]:
                self.status.game_phase = next_phase        

    def play_round(self, verbose: bool = False):
        if self.status.players_money[0] == 0:
            raise ValueError(f'{self.players[0]} is out of money!')
        if self.status.players_money[1] == 0:
            raise ValueError(f'{self.players[1]} is out of money!')
        
        if self.status.players_money[0] < 0 or self.status.players_money[1] < 0:
            raise ValueError('Something went wrong, players have negative money.')
        
        initial_money = (self.status.players_money[0], self.status.players_money[1])
        all_in = False
        
        if verbose: print('Playing a new round!')
        self.board.clear()
        for i in range(2):
            self.hole_cards[i] = HoleCards([self.deck.deal(), self.deck.deal()])
        if verbose:
            print(f'Player 1 hole cards: {self.hole_cards[0]}')
            print(f'Player 2 hole cards: {self.hole_cards[1]}')
        
        # PREFLOP
        if verbose: print('Pre-flop betting round!')
        self.play_phase(verbose=verbose)
        
        if self.status.game_phase == GamePhase.FINISHED:
            if verbose:
                print('Round finished!')
                self.summary(initial_money)
            return
        
        if self.status.players_money[0] == 0 or self.status.players_money[1] == 0:
            all_in = True
        
        # FLOP
        if verbose: print('Flop betting round!')
        self.board.add(self.deck.deal())
        self.board.add(self.deck.deal())
        self.board.add(self.deck.deal())
        if verbose: print(f'Board: {self.board}')
        if not all_in:
            self.play_phase(verbose=verbose)
            
        if self.status.game_phase == GamePhase.FINISHED:
            if verbose:
                print('Round finished!')
                self.summary(initial_money)
            return
        
        if self.status.players_money[0] == 0 or self.status.players_money[1] == 0:
            all_in = True
            
        # TURN
        if verbose: print('Turn betting round!')
        self.board.add(self.deck.deal())
        if verbose: print(f'Board: {self.board}')
        if not all_in:
            self.play_phase(verbose=verbose)
        
        if self.status.game_phase == GamePhase.FINISHED:
            if verbose:
                print('Round finished!')
                self.summary(initial_money)
            return
        
        if self.status.players_money[0] == 0 or self.status.players_money[1] == 0:
            all_in = True
            
        # RIVER
        if verbose: print('River betting round!')
        self.board.add(self.deck.deal())
        if verbose: print(f'Board: {self.board}')
        if not all_in:
            self.play_phase(verbose=verbose)
        
        if self.status.game_phase == GamePhase.FINISHED:
            if verbose:
                print('Round finished!')
                self.summary(initial_money)
            return
        
        # SHOWDOWN
        if verbose: print('Showdown!')
        ag_player = self.status.last_aggresive_player
        self.players[ag_player].get_action(self.hole_cards[ag_player], self.board, self.status)
        
        if self.status.game_phase == GamePhase.FINISHED:
            if verbose:
                print('Round finished!')
                self.summary(initial_money)
            return
        
        other = 1 - ag_player
        self.players[other].get_action(self.hole_cards[other], self.board, self.status)
        
        if self.status.game_phase == GamePhase.FINISHED:
            if verbose:
                print('Round finished!')
                self.summary(initial_money)
            return
        
        winner, index = self.board.evaluate(*self.hole_cards)
        if not winner:
            self.status.players_money[0] += self.status.bets[0]
            self.status.players_money[1] += self.status.bets[1]
            return
        
        self.status.players_money[winner] += sum(self.status.bets)
        if verbose:
            print(f'{self.players[winner]} won the round!')
            self.summary(initial_money)
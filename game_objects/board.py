from collections import Counter
from typing import Iterable
import numpy as np

from .hole_cards import HoleCards
from .card import Card
from .color import Color

class Board(list):
    '''The board in Poker, also known as the community cards.'''
    def __init__(self):
        super().__init__([None] * 5)
        
    def flop(self, c1: Card, c2: Card, c3: Card) -> None:
        '''Replace the current board with the flop.'''
        if any(self[:3]):
            raise ValueError('The flop has already been dealt.')
        self[:3] = [c1, c2, c3]
        
    def turn(self, c4: Card) -> None:
        '''Add the turn card to the board.'''
        if not self[2]:
            raise ValueError('The flop must be dealt before the turn.')
        if self[3]:
            raise ValueError('The turn has already been dealt.')
        self[3] = c4
        
    def river(self, c5: Card) -> None:
        '''Add the river card to the board.'''
        if not self[3]:
            raise ValueError('The turn must be dealt before the river.')
        if self[4]:
            raise ValueError('The river has already been dealt.')
        self[4] = c5
        
    def clear(self) -> None:
        '''Remove all cards from the board.'''
        self[:] = [None] * 5
        
    def __str__(self) -> str:
        return f'[{', '.join(map(str, self))}]'
    
    def color_count(self) -> Counter:
        '''Return the number of cards in the hand with the given color.'''
        return Counter(card.color for card in self)
    
    def number_count(
        self,
        hole_cards: HoleCards = None,
        *,
        color: Color = None
    ) -> Counter:
        
        if not hole_cards: hole_cards = []
        # Count and adjust the ace to be the highest card
        # If color is provided, only count the cards of that color
        c = Counter((card.number - 1) % 13 for card in self if not color or card.color == color)
        c.update((card.number - 1) % 13 for card in hole_cards if not color or card.color == color)
        return c
    
    def check_straight(
        self,
        hole_cards: HoleCards = None,
        *,
        color: Color = None
    ) -> int:
        '''
        Check if there is a straight in the board and hole cards. If color is
        provided, only consider cards of that color.
        Args:
            hole_cards: The hole cards of the player.
            color: The color to consider.
        
        Returns:
            int: The rank from 0 to 9 of the straight if there is one, \
                otherwise -1.
        '''
        if not color:
            cards = set(
                (
                    *(card.number for card in self),
                    *(card.number for card in hole_cards)
                )
            )
        else:
            cards = set(
                (
                    *(card.number for card in self if card.color == color),
                    *(card.number for card in hole_cards if card.color == color)
                    )
                )
        if 1 in cards:
            cards.add(14)
            
        cards = sorted(cards, reverse=True)

        accum = 1
        for i in range(len(cards) - 1):
            if cards[i] - 1 != cards[i+1]:
                accum = 1
            else:
                accum += 1
                if accum == 5:
                    return cards[i] - 1 # Ranks: 0-9

        return -1
    
    def evaluate(
        self,
        h0: HoleCards,
        h1: HoleCards,
        *,
        verbose: bool = False
    ) -> tuple[bool, int]:
        '''
        Evaluate the hands of two players given the board and return a tuple.
        Args:
            h0: The hole cards of the first player.
            h1: The hole cards of the second player.
            verbose: Whether to print the evaluation.
            
        Returns:
            tuple[bool, int]: A tuple with two elements.
                The first element is a boolean indicating whether someone won.
                The second element is an integer indicating who won only if the
                first element is true.
        '''
        
        assert all(self[:])

        # Check for flushes
        fls0, fls1 = None, None
        colors = self.color_count()
        for color, count in colors.most_common(2):
            if count > 2:
                if h0.color_count(color) + count >= 5:
                    fls0 = color
                if h1.color_count(color) + count >= 5:
                    fls1 = color
        
        # STRAIGHT FLUSHES AND ROYAL FLUSHES
        if fls0 or fls1:
            # Check for straight flushes
            if not (fls0 and fls1):
                # Only one can have a straight flush
                if fls0 and self.check_straight(h0, color=fls0) != -1:
                    if verbose: print('Straight Flush')
                    return True, 0
                if fls1 and self.check_straight(h1, color=fls1) != -1:
                    if verbose: print('Straight Flush')
                    return True, 1
            else:
                str0 = self.check_straight(h0, color=fls0)
                str1 = self.check_straight(h1, color=fls1)
                str0_bool = str0 != -1
                str1_bool = str1 != -1
                if str0_bool or str1_bool:
                    if verbose: print('Straight Flush')
                    if not (str0_bool and str1_bool):
                        # Only one has straight flush
                        return True, int(str1_bool)
                    
                    # Both have straight flushes so compare them
                    return str0 != str1, int(str0 < str1)
        
        # POKER AND FULL HOUSE
        nums0 = self.number_count(h0)
        nums1 = self.number_count(h1)
        combos0 = nums0.most_common(2)
        combos1 = nums1.most_common(2)
        poker0 = combos0[0][1] == 4
        full0 = sum(count for _, count in combos0) == 5
        poker1 = combos1[0][1] == 4
        full1 = sum(count for _, count in combos1) == 5
        
        if poker0 or full0 or poker1 or full1:
            if poker0 or poker1:
                if verbose: print('Poker')
                if not (poker0 and poker1):
                    # Only one has poker
                    return True, int(poker1)
                
                # Both have pokers so compare them
                poker_number0 = combos0[0][0]
                poker_number1 = combos1[1][0]
                if poker_number0 != poker_number1:
                    return True, int(poker_number0 < poker_number1)
                
                # Look for high card
                # Could do an n-largest algorithm but it's constant time either way
                highest0 = sorted(nums0.keys(), reverse=True)[:2]
                highest1 = sorted(nums1.keys(), reverse=True)[:2]
                
                highest0 = highest0[0] if highest0[0] != poker_number0 else highest0[1]
                highest1 = highest1[0] if highest1[0] != poker_number1 else highest1[1]
                
                
                return highest0 != highest1, int(highest0 < highest1)
                    
            if verbose: print('Full House')
            if not (full0 and full1):
                # Only one has full house
                return True, int(full1)    
            
            # Both have full houses so compare them
            full_numbers0 = [n for n, _ in combos0]
            full_numbers1 = [n for n, _ in combos1]
            # First compare the three of a kinds
            if full_numbers0[0] != full_numbers1[0]:
                return True, int(full_numbers0[0] < full_numbers1[0])
            
            # Then compare the pairs
            return full_numbers0[1] != full_numbers1[1], int(full_numbers0[1] < full_numbers1[1])            
        
        # FLUSHES
        if fls0 or fls1:
            if verbose: print('Flush')
            if not (fls0 and fls1):
                # Only one has flush
                return True, int(bool(fls1))

            # Both have flushes, so highest card wins
            nums0 = self.number_count(h0, color=fls0)
            nums1 = self.number_count(h1, color=fls1)
            highests0 = sorted(nums0.keys(), reverse=True)
            highests1 = sorted(nums1.keys(), reverse=True)
            return highests0 != highests1, int(highests0 < highests1)

        
        # STRAIGHTS
        str0 = self.check_straight(h0)
        str1 = self.check_straight(h1)
        str0_bool = str0 != -1
        str1_bool = str1 != -1
        if str0_bool or str1_bool:
            if verbose: print('Straight')
            if not (str0_bool and str1_bool):
                # Only one has straight flush
                return True, int(str1_bool)
            
            # Both have straight flushes so compare them
            return str0 != str1, int(str0 < str1)
        
        # THREE OF A KINDS
        trip0 = combos0[0][1] == 3
        trip1 = combos1[0][1] == 3
        if trip0 or trip1:
            if verbose: print('Three of a Kind')
            if not (trip0 and trip1):
                # Only one has three of a kind
                return True, int(trip1)
            
            # Both have three of a kinds so compare them
            trip_number0 = combos0[0][0]
            trip_number1 = combos1[0][0]
            if trip_number0 != trip_number1:
                return True, int(trip_number0 < trip_number1)
            
            # Look for high cards
            highests0 = sorted(nums0.keys(), reverse=True)[:3]
            highests1 = sorted(nums1.keys(), reverse=True)[:3]
            
            # Remove the three of a kind from the high cards
            # Otherwise remove the worst card
            highest0.remove(trip_number0)
            if len(highest0) == 3:
                highest0.pop()
                
            highest1.remove(trip_number1)
            if len(highest1) == 3:
                highest1.pop()
            
            # Compare both lists
            return highests0 != highests1, int(highests0 < highests1)
        
        # TWO PAIRS
        twopair0 = combos0[0][1] == 2 and combos0[1][1] == 2
        twopair1 = combos1[0][1] == 2 and combos1[1][1] == 2
        if twopair0 or twopair1:
            if verbose: print('Two Pair')
            if not (twopair0 and twopair1):
                # Only one has two pairs
                return True, int(twopair1)
            
            # Both have two pairs so compare them
            pair_numbers0 = sorted([n for n, _ in combos0], reverse=True)
            pair_numbers1 = sorted([n for n, _ in combos1], reverse=True)
            
            if pair_numbers0 != pair_numbers1:
                return True, int(pair_numbers0 < pair_numbers1)
            
            # Look for high card
            highests0 = sorted(nums0.keys(), reverse=True)[:3]
            highests1 = sorted(nums1.keys(), reverse=True)[:3]
            highest0 = highests0[-1] # Default
            highest1 = highests1[-1] # Default
            for i in range(2):
                if highests0[i] not in pair_numbers0:
                    highest0 = highests0[i]
                    break
            for i in range(2):
                if highests1[i] not in pair_numbers1:
                    highest1 = highests1[i]
                    break
                
            return highest0 != highest1, int(highest0 < highest1)
        
        # PAIRS
        pair0 = combos0[0][1] == 2
        pair1 = combos1[0][1] == 2
        if pair0 or pair1:
            if verbose: print('Pair')
            if not (pair0 and pair1):
                # Only one has pair
                return True, int(pair1)
            
            # Both have pairs so compare them
            pair_number0 = combos0[0][0]
            pair_number1 = combos1[0][0]
            if pair_number0 != pair_number1:
                return True, int(pair_number0 < pair_number1)
            
            # Look for high cards
            highests0 = sorted(nums0.keys(), reverse=True)[:4]
            highests1 = sorted(nums1.keys(), reverse=True)[:4]
            
            highests0.remove(pair_number0)
            if len(highests0) == 4:
                highests0.pop()
                
            highests1.remove(pair_number1)
            if len(highests1) == 4:
                highests1.pop()
                
            
            return highests0 != highests1, int(highests0 < highests1)
        
        # HIGH CARD
        if verbose: print('High Card')
        highests0 = sorted(nums0.keys(), reverse=True)[:5]
        highests1 = sorted(nums1.keys(), reverse=True)[:5]
        
        return highests0 != highests1, int(highests0 < highests1)
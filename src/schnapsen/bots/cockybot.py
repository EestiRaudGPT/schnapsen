from schnapsen.game import Bot, Move, PlayerPerspective, Marriage, RegularMove
from schnapsen.deck import Card, Suit, Rank
from schnapsen.bots import RandBot
from schnapsen.game import SchnapsenGamePlayEngine
import random

class AssignmentBot(Bot):
    """Your suit order is [SPADES, HEARTS, CLUBS, DIAMONDS], from lower suit to higher suit."""

    def get_move(self, perspective: PlayerPerspective, leader_move: Move | None) -> Move:
        """Get the move for the Bot."""
        pass

    def _get_suit_value(self, suit: Suit) -> int:
        """returns value based on order: [SPADES, HEARTS, CLUBS, DIAMONDS] (low to high)"""
        order = [Suit.SPADES, Suit.HEARTS, Suit.CLUBS, Suit.DIAMONDS]
        return order.index(suit)

    def _get_card_points(self, card: Card) -> int:
        """returns points for a card: A=11, 10=10, K=4, Q=3, J=2"""
        map_points = {
            Rank.ACE: 11,
            Rank.TEN: 10,
            Rank.KING: 4,
            Rank.QUEEN: 3,
            Rank.JACK: 2
        }
        return map_points.get(card.rank, 0)

    def condition2(self, perspective: PlayerPerspective, leader_move: Move | None) -> bool:
        pass

    def condition3(self, perspective: PlayerPerspective, leader_move: Move | None) -> bool:
        pass

    def action1(self, perspective: PlayerPerspective, leader_move: Move | None) -> Move:
        pass

    def action2(self, perspective: PlayerPerspective, leader_move: Move | None) -> Move:
        pass

    def action3(self, perspective: PlayerPerspective, leader_move: Move | None) -> Move:
        pass

    def action4(self, perspective: PlayerPerspective, leader_move: Move | None) -> Move:
        pass

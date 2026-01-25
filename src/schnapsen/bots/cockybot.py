from schnapsen.game import Bot, Move, PlayerPerspective, Marriage, RegularMove, CloseTalon, GamePhase
from schnapsen.deck import Card, Suit, Rank
from schnapsen.bots import RandBot
from schnapsen.game import SchnapsenGamePlayEngine
import random

class CockyBot(Bot):
    """
    CockyBot plays conservatively until it reaches the trigger conditions.
    Once these conditions are met, it switches to cocky mode.
    """

    def __init__(self, points_requirement: int, trumps_requirement: int, name: str | None = None) -> None:
        """
        Initialize the bot.
        """
        super().__init__(name)
        self.points_requirement = points_requirement
        self.trumps_requirement = trumps_requirement

    def get_move(self, perspective: PlayerPerspective, leader_move: Move | None) -> Move:
        """
        Get the move for the Bot.

        1. Check if we should become cocky (trigger conditions).
        2. If conditions are met and talon is open, Close Talon.
        3. If we are cocky (or talon is closed), play aggressively.
        4. Otherwise, play conservatively.
        """
        if not perspective.am_i_leader():
            return self._play_follow(perspective, leader_move)

        if perspective.get_phase() == GamePhase.ONE:
            if self._should_become_cocky(perspective):
                return CloseTalon()
            else:
                return self._play_conservative_lead(perspective)
        
        #This is only executed in the second phase of the game when we are leading.
        return self._play_aggressive_lead(perspective)
            

    def _should_become_cocky(self, perspective: PlayerPerspective) -> bool:
        """
        Check if the trigger conditions are met.
        """
        my_score = perspective.get_my_score()
        total_score = my_score.direct_points #changed so that only closes talon when real points reach 40, not incl pending.
        trump_suit = perspective.get_trump_suit()
        trumps_in_hand = [c for c in perspective.get_hand().get_cards() if c.suit == trump_suit]
        
        return total_score >= self.points_requirement and len(trumps_in_hand) >= self.trumps_requirement

    def _try_special_moves(self, perspective: PlayerPerspective) -> Move | None:
        """
        Attempt to play a trump exchange or marriage if available.
        There are two for loops to ensure that the trump exchange has priority.
        """
        valid_moves = perspective.valid_moves()
        for move in valid_moves:
            if move.is_trump_exchange():
                return move
        
        for move in valid_moves:
            if move.is_marriage():
                return move
        return None

    def _play_aggressive_lead(self, perspective: PlayerPerspective) -> Move:
        """
        Strategy:
        1. Declare marriage if possible.
        2. Lead with highest scoring trump cards.
        3. Lead with highest scoring non-trump cards.

        This is for the second phase of the game when we are leading.
        """
        # Marriage
        special_move = self._try_special_moves(perspective)
        if special_move and special_move.is_marriage():
            return special_move
            
        valid_moves = perspective.valid_moves()
        regular_moves = [m.as_regular_move() for m in valid_moves if m.is_regular_move()]
        
        if not regular_moves:
            # Fallback to any valid move
            return valid_moves[0] if valid_moves else Move.CloseTalon()

        trump_suit = perspective.get_trump_suit()
        
        # Sort by points (descending)
        # Highest trumps
        trumps = [m for m in regular_moves if m.card.suit == trump_suit]
        trumps.sort(key=lambda m: self._get_card_points(m.card), reverse=True)
        
        if trumps:
            return trumps[0] #The first move in the list will always be the one with the highest points.
            
        # Highest non-trumps
        non_trumps = [m for m in regular_moves if m.card.suit != trump_suit]
        non_trumps.sort(key=lambda m: self._get_card_points(m.card), reverse=True)
        
        if non_trumps:
            return non_trumps[0]
            
        # Fallback
        return regular_moves[0]

    def _play_conservative_lead(self, perspective: PlayerPerspective) -> Move:
        """
        Conservative Leading Strategy:
        1. Avoid playing Trump cards unless necessary.
        2. Play face cards (K, Q, J) or low cards first.
        3. Save high-scoring cards (Ace, Ten).
        """
        # Try special move first.
        special_move = self._try_special_moves(perspective)
        if special_move:
            return special_move

        valid_moves = perspective.valid_moves()
        regular_moves = [m.as_regular_move() for m in valid_moves if m.is_regular_move()]
        
        trump_suit = perspective.get_trump_suit()
        non_trumps = [m for m in regular_moves if m.card.suit != trump_suit]
        
        # 2. Play face cards or low cards (Points < 10 basically, or sorted low to high)
        # Prioritize non-trumps
        move_candidates = non_trumps if non_trumps else regular_moves
        
        # Sort by points ascending (low points first)
        move_candidates.sort(key=lambda m: self._get_card_points(m.card))
        
        return move_candidates[0]

    def _play_follow(self, perspective: PlayerPerspective, leader_move: Move) -> Move:
        """
        Following Strategy:
        Phase 1:
        1. Lowest scoring card that still wins the trick (Non-Trump)
        2. Lowest scoring trump that still wins the trick
        3. Lowest card

        Phase 2:
        1. Lowest card
        """
        valid_moves = perspective.valid_moves()
        regular_moves = [m.as_regular_move() for m in valid_moves if m.is_regular_move()]
        
        # Helper to getting points
        def get_points(move):
            return self._get_card_points(move.card)

        # Sort moves by points ascending.
        regular_moves.sort(key=get_points)
        
        phase = perspective.get_phase()
        
        if phase == GamePhase.TWO:
            # We always want to play the lowest card in phase 2.
            return regular_moves[0]
            
        # Phase 1 logic
        if leader_move.is_regular_move():
            leader_card = leader_move.as_regular_move().card
        else: # When leader's move is a marriage.
            leader_card = leader_move.as_marriage().underlying_regular_move().card

        trump_suit = perspective.get_trump_suit()
        
        winning_non_trumps = []
        winning_trumps = []
        
        for move in regular_moves:
            card = move.card
            is_winner = False
            
            # Check if the card wins the trick.
            if card.suit == leader_card.suit:
                # Same suit, so check if the card has higher points.
                if self._get_card_points(card) > self._get_card_points(leader_card):
                    is_winner = True
            elif card.suit == trump_suit:
                # A trump card always wins against a non-trump card.
                if leader_card.suit != trump_suit:
                    is_winner = True
            
            if is_winner:
                if card.suit == trump_suit:
                    winning_trumps.append(move)
                else:
                    winning_non_trumps.append(move)
        
        # The lowest scoring non-trump card that wins is tried first.
        if winning_non_trumps:
            # Already sorted by points ascending because regular_moves was sorted like that.
            return winning_non_trumps[0]
            
        # The lowest scoring trump card that wins is tried second.
        if winning_trumps:
            return winning_trumps[0]
            
        # The lowest card (loss) is tried third.
        return regular_moves[0]


    def _get_card_points(self, card: Card) -> int:
        """
        Returns points for a card.
        """
        map_points = {
            Rank.ACE: 11,
            Rank.TEN: 10,
            Rank.KING: 4,
            Rank.QUEEN: 3,
            Rank.JACK: 2
        }
        return map_points.get(card.rank, 0)

class StrictCockyBot(CockyBot):
    '''
    StrictCockyBot plays like CockyBot, except that when it closes the talon, the trumps in its hand must be either an Ace or a Ten.
    '''

    def _should_become_cocky(self, perspective: PlayerPerspective) -> bool:
        """
        Check if the trigger conditions are met.
        Only counts Aces and Tens as valid trumps for the requirement.
        """
        my_score = perspective.get_my_score()
        total_score = my_score.direct_points 
        trump_suit = perspective.get_trump_suit()
        
        # strict_trumps are only ACE or TEN of the trump suit
        strict_trumps = [
            c for c in perspective.get_hand().get_cards() 
            if c.suit == trump_suit and c.rank in [Rank.ACE, Rank.TEN]
        ]
        
        return total_score >= self.points_requirement and len(strict_trumps) >= self.trumps_requirement
        
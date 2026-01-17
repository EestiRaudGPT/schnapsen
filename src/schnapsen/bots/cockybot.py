from schnapsen.game import Bot, Move, PlayerPerspective, Marriage, RegularMove, CloseTalon, GamePhase
from schnapsen.deck import Card, Suit, Rank
from schnapsen.bots import RandBot
from schnapsen.game import SchnapsenGamePlayEngine
import random

class CockyBot(Bot):
    """
    CockyBot plays conservatively until it reaches 40 points and holds 2 trump cards.
    Once these conditions are met, it switches to a 'Cocky' (aggressive) strategy.
    """

    def __init__(self, name: str | None = None) -> None:
        """
        Initialize the bot.
        """
        super().__init__(name)

    def get_move(self, perspective: PlayerPerspective, leader_move: Move | None) -> Move:
        """
        Get the move for the Bot.

        1. Check if we should become 'Cocky' (40 pts, 2 trumps).
        2. If conditions are met and talon is open, Close Talon.
        3. If we are 'Cocky' (or talon is closed), play aggressively.
        4. Otherwise, play conservatively.
        """
        if self._should_become_cocky(perspective):
            if perspective.get_phase() == GamePhase.ONE:
                return CloseTalon()
            else:
                return self._play_aggressive_lead(perspective)
        else:
            return self._play_conservative_lead(perspective)
            

    def _should_become_cocky(self, perspective: PlayerPerspective) -> bool:
        """
        Check if the 'Cocky' conditions are met:
        - We have at least 40 points (direct + pending).
        - We have at least 2 trump cards in hand.
        - The Talon is open (GamePhase.ONE).
        """
        my_score = perspective.get_my_score()
        total_score = my_score.direct_points + my_score.pending_points
        trump_suit = perspective.get_trump_suit()
        trumps_in_hand = [c for c in perspective.get_hand().get_cards() if c.suit == trump_suit]
        
        return total_score >= 40 and len(trumps_in_hand) >= 2

    def _try_special_moves(self, perspective: PlayerPerspective) -> Move | None:
        """
        Attempt to play a Trump Exchange or Marriage if available.
        """
        valid_moves = perspective.valid_moves()
        # Priority: Exchange first (cheap/advantageous), then Marriage
        for move in valid_moves:
            if move.is_trump_exchange():
                return move
        
        for move in valid_moves:
            if move.is_marriage():
                # Prefer royal marriage? Abstract says "immediately declare marriage".
                # Any marriage is good for points.
                return move
        return None

    def _play_aggressive_lead(self, perspective: PlayerPerspective) -> Move:
        """
        Aggressive Leading Strategy (Cocky Mode):
        1. Declare Marriage if possible.
        2. Lead with highest scoring Trump cards.
        3. Lead with highest scoring Non-Trump cards.
        """
        # 1. Marriage
        special_move = self._try_special_moves(perspective)
        if special_move and special_move.is_marriage():
            return special_move
            
        valid_moves = perspective.valid_moves()
        # Filter regular moves
        regular_moves = [m.as_regular_move() for m in valid_moves if m.is_regular_move()]
        
        if not regular_moves:
            # Should practically not happen if we check valid_moves, unless only special moves exist?
            # valid_moves always has regular moves if hand not empty.
            # If only trump exchange/close talon provided? Logic above handles special.
            # Fallback to any valid
            return valid_moves[0] if valid_moves else Move.CloseTalon() # Should not be empty

        trump_suit = perspective.get_trump_suit()
        
        # Sort by points (high to low)
        # 2. Highest Trumps
        trumps = [m for m in regular_moves if m.card.suit == trump_suit]
        trumps.sort(key=lambda m: self._get_card_points(m.card), reverse=True)
        
        if trumps:
            return trumps[0]
            
        # 3. Highest Non-Trumps
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
        # Try special first? Abstract says "Make marriages and trump exchanges when possible."
        special_move = self._try_special_moves(perspective)
        if special_move:
            return special_move

        valid_moves = perspective.valid_moves()
        regular_moves = [m.as_regular_move() for m in valid_moves if m.is_regular_move()]
        
        trump_suit = perspective.get_trump_suit()
        non_trumps = [m for m in regular_moves if m.card.suit != trump_suit]
        
        # 2. Play face cards or low cards (Points < 10 basically, or sorted low to high)
        # Prioritize non-trumps
        candidates = non_trumps if non_trumps else regular_moves
        
        # Sort by points ascending (Low points first)
        candidates.sort(key=lambda m: self._get_card_points(m.card))
        
        return candidates[0]

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

        # Sort by points ascending (Lowest card)
        regular_moves.sort(key=get_points)
        
        phase = perspective.get_phase()
        
        if phase == GamePhase.TWO:
            # Phase 2: Lowest card
            return regular_moves[0]
            
        # Phase 1 Logic
        # Determine leader's card
        if leader_move.is_regular_move():
            leader_card = leader_move.as_regular_move().card
        else: # Marriage
            leader_card = leader_move.as_marriage().underlying_regular_move().card

        trump_suit = perspective.get_trump_suit()
        
        winning_non_trumps = []
        winning_trumps = []
        
        for move in regular_moves:
            card = move.card
            is_winner = False
            
            # Check if wins
            if card.suit == leader_card.suit:
                # Same suit, must be higher rank/points to win
                if self._get_card_points(card) > self._get_card_points(leader_card):
                    is_winner = True
            elif card.suit == trump_suit:
                # Trump always wins against non-trump
                if leader_card.suit != trump_suit:
                    is_winner = True
            
            if is_winner:
                if card.suit == trump_suit:
                    winning_trumps.append(move)
                else:
                    winning_non_trumps.append(move)
        
        # Priority 1: Lowest scoring card that wins (Non-Trump)
        if winning_non_trumps:
            # Already sorted by points because regular_moves was sorted
            return winning_non_trumps[0]
            
        # Priority 2: Lowest scoring trump that wins
        if winning_trumps:
            # Already sorted
            return winning_trumps[0]
            
        # Priority 3: Lowest card (loss)
        return regular_moves[0]


    def _get_card_points(self, card: Card) -> int:
        """
        Returns points for a card: A=11, 10=10, K=4, Q=3, J=2.
        """
        map_points = {
            Rank.ACE: 11,
            Rank.TEN: 10,
            Rank.KING: 4,
            Rank.QUEEN: 3,
            Rank.JACK: 2
        }
        return map_points.get(card.rank, 0)

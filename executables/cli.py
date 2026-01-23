import random
import pathlib

from typing import Optional

import click
from schnapsen.alternative_engines.ace_one_engine import AceOneGamePlayEngine

from schnapsen.bots import MLDataBot, train_ML_model, MLPlayingBot, RandBot
from schnapsen.bots.cockybot import CockyBot
from schnapsen.bots.bully_bot import BullyBot

from schnapsen.bots.example_bot import ExampleBot

from schnapsen.game import (Bot, GamePlayEngine, Move, PlayerPerspective,
                            SchnapsenGamePlayEngine, TrumpExchange)
from schnapsen.alternative_engines.twenty_four_card_schnapsen import TwentyFourSchnapsenGamePlayEngine

from schnapsen.bots.rdeep import RdeepBot


@click.group()
def main() -> None:
    """Various Schnapsen Game Examples"""


def play_games_and_return_stats(engine: GamePlayEngine, bot1: Bot, bot2: Bot, pairs_of_games: int) -> int:
    """
    Play 2 * pairs_of_games games between bot1 and bot2, using the SchnapsenGamePlayEngine, and return how often bot1 won.
    Prints progress. Each pair of games is the same original dealing of cards, but the roles of the bots are swapped.
    """
    bot1_wins: int = 0
    lead, follower = bot1, bot2
    for game_pair in range(pairs_of_games):
        for lead, follower in [(bot1, bot2), (bot2, bot1)]:
            winner, _, _ = engine.play_game(lead, follower, random.Random(game_pair))
            if winner == bot1:
                bot1_wins += 1
        if game_pair > 0 and (game_pair + 1) % 500 == 0:
            print(f"Progress: {game_pair + 1}/{pairs_of_games} game pairs played")
    return bot1_wins


@main.command()
def random_game() -> None:
    engine = SchnapsenGamePlayEngine()
    bot1 = RandBot(random.Random(12112121))
    bot2 = RandBot(random.Random(464566))
    for i in range(1000):
        winner_id, game_points, score = engine.play_game(bot1, bot2, random.Random(i))
        print(f"Game ended. Winner is {winner_id} with {game_points} points, score {score}")


class NotificationExampleBot(Bot):

    def get_move(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        moves = perspective.valid_moves()
        return moves[0]

    def notify_game_end(self, won: bool, perspective: PlayerPerspective) -> None:
        print(f'result {"win" if won else "lost"}')
        print(f'I still have {len(perspective.get_hand())} cards left')

    def notify_trump_exchange(self, move: TrumpExchange) -> None:
        print(f"That trump exchanged! {move.jack}")


@main.command()
def notification_game() -> None:
    engine = TwentyFourSchnapsenGamePlayEngine()
    bot1 = NotificationExampleBot()
    bot2 = RandBot(random.Random(464566))
    engine.play_game(bot1, bot2, random.Random(94))


class HistoryBot(Bot):
    def get_move(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        history = perspective.get_game_history()
        print(f'the initial state of this game was {history[0][0]}')
        moves = perspective.valid_moves()
        return moves[0]


@main.command()
def try_example_bot_game() -> None:
    engine = SchnapsenGamePlayEngine()
    bot1 = ExampleBot()
    bot2 = RandBot(random.Random(464566))
    winner, points, score = engine.play_game(bot1, bot2, random.Random(1))
    print(f"Winner is: {winner}, with {points} points, score {score}!")


@main.command()
def rdeep_game() -> None:
    bot1: Bot
    bot2: Bot
    engine = SchnapsenGamePlayEngine()
    rdeep = bot1 = RdeepBot(num_samples=16, depth=4, rand=random.Random(4564654644))
    bot2 = RandBot(random.Random(464566))
    wins = 0
    amount = 100
    for game_number in range(1, amount + 1):
        if game_number % 2 == 0:
            bot1, bot2 = bot2, bot1
        winner_id, _, _ = engine.play_game(bot1, bot2, random.Random(game_number))
        if winner_id == rdeep:
            wins += 1
        if game_number % 10 == 0:
            print(f"won {wins} out of {game_number}")


@main.group()
def ml() -> None:
    """Commands for the ML bot"""


@ml.command()
def create_replay_memory_dataset() -> None:
    # define replay memory database creation parameters
    num_of_games: int = 10000
    replay_memory_dir: str = 'ML_replay_memories'
    replay_memory_filename: str = 'random_random_10k_games.txt'
    replay_memory_location = pathlib.Path(replay_memory_dir) / replay_memory_filename

    bot_1_behaviour: Bot = RandBot(random.Random(5234243))
    # bot_1_behaviour: Bot = RdeepBot(num_samples=4, depth=4, rand=random.Random(4564654644))
    bot_2_behaviour: Bot = RandBot(random.Random(54354))
    # bot_2_behaviour: Bot = RdeepBot(num_samples=4, depth=4, rand=random.Random(68438))
    delete_existing_older_dataset = False

    # check if needed to delete any older versions of the dataset
    if delete_existing_older_dataset and replay_memory_location.exists():
        print(f"An existing dataset was found at location '{replay_memory_location}', which will be deleted as selected.")
        replay_memory_location.unlink()

    # in any case make sure the directory exists
    replay_memory_location.parent.mkdir(parents=True, exist_ok=True)

    # create new replay memory dataset, according to the behaviour of the provided bots and the provided random seed
    engine = SchnapsenGamePlayEngine()
    replay_memory_recording_bot_1 = MLDataBot(bot_1_behaviour, replay_memory_location=replay_memory_location)
    replay_memory_recording_bot_2 = MLDataBot(bot_2_behaviour, replay_memory_location=replay_memory_location)
    for i in range(1, num_of_games + 1):
        if i % 500 == 0:
            print(f"Progress: {i}/{num_of_games}")
        engine.play_game(replay_memory_recording_bot_1, replay_memory_recording_bot_2, random.Random(i))
    print(f"Replay memory dataset recorder for {num_of_games} games.\nDataset is stored at: {replay_memory_location}")


@ml.command()
def train_model() -> None:
    # directory where the replay memory is saved
    replay_memory_filename: str = 'random_random_10k_games.txt'
    # filename of replay memory within that directory
    replay_memories_directory: str = 'ML_replay_memories'
    # Whether to train a complicated Neural Network model or a simple one.
    # Tips: a neural network usually requires bigger datasets to be trained on, and to play with the parameters of the model.
    # Feel free to play with the hyperparameters of the model in file 'ml_bot.py', function 'train_ML_model',
    # under the code of body of the if statement 'if use_neural_network:'
    replay_memory_location = pathlib.Path(replay_memories_directory) / replay_memory_filename
    model_name: str = 'simple_model'
    model_dir: str = "ML_models"
    model_location = pathlib.Path(model_dir) / model_name
    overwrite: bool = False

    if overwrite and model_location.exists():
        print(f"Model at {model_location} exists already and will be overwritten as selected.")
        model_location.unlink()

    train_ML_model(replay_memory_location=replay_memory_location, model_location=model_location,
                   model_class='LR')


@ml.command()
def try_bot_game() -> None:
    engine = SchnapsenGamePlayEngine()
    model_dir: str = 'ML_models'
    model_name: str = 'simple_model'
    model_location = pathlib.Path(model_dir) / model_name
    bot1: Bot = MLPlayingBot(model_location=model_location)
    bot2: Bot = RandBot(random.Random(464566))
    number_of_games: int = 10000
    pairs_of_games = number_of_games // 2

    # play games with altering leader position on first rounds
    ml_bot_wins_against_random = play_games_and_return_stats(engine=engine, bot1=bot1, bot2=bot2, pairs_of_games=pairs_of_games)
    print(f"The ML bot with name {model_name}, won {ml_bot_wins_against_random} times out of {number_of_games} games played.")


@main.command()
def game_24() -> None:
    engine = TwentyFourSchnapsenGamePlayEngine()
    bot1 = RandBot(random.Random(12112121))
    bot2 = RandBot(random.Random(464566))
    for i in range(1000):
        winner_id, game_points, score = engine.play_game(bot1, bot2, random.Random(i))
        print(f"Game ended. Winner is {winner_id} with {game_points} points, score {score}")


@main.command()
def game_ace_one() -> None:
    engine = AceOneGamePlayEngine()
    bot1 = RandBot(random.Random(12112121))
    bot2 = RdeepBot(num_samples=16, depth=4, rand=random.Random(464566))
    for i in range(1000):
        winner_id, game_points, score = engine.play_game(bot1, bot2, random.Random(i))
        print(f"Game ended. Winner is {winner_id} with {game_points} points, score {score}")


class ExperimentCockyBot(CockyBot):
    '''
    This bot adds to Cockybot by tracking its performance during the game.
    '''
    def __init__(self, name: str = "CockyBot") -> None:
        super().__init__(name)
        self.marriages_declared = 0
        self.trump_exchanges_declared = 0
        self.closed_talon = False
        self.closure_points = 0
        self.trumps_when_closing: list[str] = []
        self.non_trumps_when_closing: list[str] = []
        self.tricks_at_closure = 0
        self.opponent_points_at_closure = 0
        self.final_score = 0
        self.final_won_cards_count = 0

    def get_move(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        move = super().get_move(perspective, leader_move)
        
        if move.is_marriage():
            self.marriages_declared += 1
            
        if move.is_trump_exchange():
            self.trump_exchanges_declared += 1
            
        if move.is_close_talon():
            self.closed_talon = True
            score = perspective.get_my_score()
            self.closure_points = score.direct_points #only direct points are added
            
            trump_suit = perspective.get_trump_suit()
            self.trumps_when_closing = [str(c) for c in perspective.get_hand().get_cards() if c.suit == trump_suit]
            self.non_trumps_when_closing = [str(c) for c in perspective.get_hand().get_cards() if c.suit != trump_suit]
            
            # The tricks won so far is just the number of won cards divided by 2.
            self.tricks_at_closure = len(perspective.get_won_cards()) // 2
            
            # Track opponent's score at closure for correct game point calculation
            opp_score = perspective.get_opponent_score()
            self.opponent_points_at_closure = opp_score.direct_points #only direct points are added
            
        return move

    def notify_game_end(self, won: bool, perspective: PlayerPerspective) -> None:
        '''
        Overrides the method from the game engine, so that we can get the bot's final score and won cards count when the game ends
        (this method is called by the game engine when the game ends)
        '''
        score = perspective.get_my_score()
        self.final_score = score.direct_points 
        self.final_won_cards_count = len(perspective.get_won_cards())


class ExperimentRandBot(RandBot):
    ''' 
    This bot adds to RandBot by tracking its performance during the game.
    '''
    def __init__(self, rng: random.Random, name: str = "RandBot") -> None:
        super().__init__(rng, name)
        self.closed_talon = False
        self.closure_points = 0
        self.opponent_points_at_closure = 0
        self.final_score = 0

    def get_move(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        move = super().get_move(perspective, leader_move)
        if move.is_close_talon():
            self.closed_talon = True
            score = perspective.get_my_score()
            self.closure_points = score.direct_points 
            opp_score = perspective.get_opponent_score()
            self.opponent_points_at_closure = opp_score.direct_points
        return move

    def notify_game_end(self, won: bool, perspective: PlayerPerspective) -> None:
        score = perspective.get_my_score()
        self.final_score = score.direct_points 


class ExperimentBullyBot(BullyBot):
    '''
    This bot adds to BullyBot by tracking its performance during the game.
    '''
    def __init__(self, rand: random.Random, name: Optional[str] = None) -> None:
        super().__init__(rand, name)
        self.marriages_declared = 0
        self.trump_exchanges_declared = 0
        self.closed_talon = False
        self.closure_points = 0
        self.trumps_when_closing: list[str] = []
        self.non_trumps_when_closing: list[str] = []
        self.tricks_at_closure = 0
        self.opponent_points_at_closure = 0
        self.final_score = 0
        self.final_won_cards_count = 0

    def get_move(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        move = super().get_move(perspective, leader_move)
        
        if move.is_marriage():
            self.marriages_declared += 1
            
        if move.is_trump_exchange():
            self.trump_exchanges_declared += 1
            
        if move.is_close_talon():
            self.closed_talon = True
            score = perspective.get_my_score()
            self.closure_points = score.direct_points 
            
            trump_suit = perspective.get_trump_suit()
            self.trumps_when_closing = [str(c) for c in perspective.get_hand().get_cards() if c.suit == trump_suit]
            self.non_trumps_when_closing = [str(c) for c in perspective.get_hand().get_cards() if c.suit != trump_suit]
            
            self.tricks_at_closure = len(perspective.get_won_cards()) // 2
            
            # Track opponent's score at closure for correct game point calculation
            opp_score = perspective.get_opponent_score()
            self.opponent_points_at_closure = opp_score.direct_points 
            
        return move

    def notify_game_end(self, won: bool, perspective: PlayerPerspective) -> None:
        '''
        Overrides the method from the game engine, so that we can get the bot's final score and won cards count when the game ends
        '''
        score = perspective.get_my_score()
        self.final_score = score.direct_points 
        self.final_won_cards_count = len(perspective.get_won_cards())


class ExperimentRDeepBot(RdeepBot):
    '''
    This bot adds to RdeepBot by tracking its performance during the game.
    '''
    def __init__(self, num_samples: int, depth: int, rand: random.Random, name: Optional[str] = None) -> None:
        super().__init__(num_samples, depth, rand, name)
        self.marriages_declared = 0
        self.trump_exchanges_declared = 0
        self.closed_talon = False
        self.closure_points = 0
        self.trumps_when_closing: list[str] = []
        self.non_trumps_when_closing: list[str] = []
        self.tricks_at_closure = 0
        self.opponent_points_at_closure = 0
        self.final_score = 0
        self.final_won_cards_count = 0

    def get_move(self, perspective: PlayerPerspective, leader_move: Optional[Move]) -> Move:
        move = super().get_move(perspective, leader_move)
        
        if move.is_marriage():
            self.marriages_declared += 1
            
        if move.is_trump_exchange():
            self.trump_exchanges_declared += 1
            
        if move.is_close_talon():
            self.closed_talon = True
            score = perspective.get_my_score()
            self.closure_points = score.direct_points 
            
            trump_suit = perspective.get_trump_suit()
            self.trumps_when_closing = [str(c) for c in perspective.get_hand().get_cards() if c.suit == trump_suit]
            self.non_trumps_when_closing = [str(c) for c in perspective.get_hand().get_cards() if c.suit != trump_suit]
            
            self.tricks_at_closure = len(perspective.get_won_cards()) // 2
            
            # Track opponent's score at closure for correct game point calculation
            opp_score = perspective.get_opponent_score()
            self.opponent_points_at_closure = opp_score.direct_points 
            
        return move

    def notify_game_end(self, won: bool, perspective: PlayerPerspective) -> None:
        '''
        Overrides the method from the game engine, so that we can get the bot's final score and won cards count when the game ends
        '''
        score = perspective.get_my_score()
        self.final_score = score.direct_points 
        self.final_won_cards_count = len(perspective.get_won_cards())


@main.command()
def cocky_experiment() -> None:
    """Run CockyBot vs RandBot experiment (1000 games)"""
    import csv
    
    engine = SchnapsenGamePlayEngine()
    total_games = 1000
    
    # Define CSV fields
    fieldnames = [
        "Seed", "Match outcome", "Winner", "Loser", 
        "Winner score", "Loser score", "Game points",
        "Deck closed", "Closer", 
        "Closure points", "CockyBot marriages",
        "CockyBot trump exchanges",
        "CockyBot won after closing", "Trumps when closing", 
        "Non-trumps when closing", "Tricks won after closing", "RandBot RNG Seed"
    ]
    
    output_file = 'cocky_experiment_results_new.csv'
    print(f"Output will be saved to {output_file}")
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i in range(total_games):
            seed = i
            rng_game = random.Random(seed)
            rand_bot_rng_seed = seed + 20000
            rng_randbot = random.Random(rand_bot_rng_seed)
            #this makes sure that the rng used by randbot is different from the one used by the game.
            #this is important because otherwise randbot's choices are linked to how the cards are dealt.
            
            bot_cocky = ExperimentCockyBot(name="CockyBot")
            bot_rand = ExperimentRandBot(rng=rng_randbot, name="RandBot")
            
            # Randomize starter
            if i % 2 == 0:
                leader, follower = bot_cocky, bot_rand
            else:
                leader, follower = bot_rand, bot_cocky
                
            winner, game_points, score = engine.play_game(leader, follower, rng_game)
            
            # Winner and loser
            winner_name = str(winner)
            loser_name = "RandBot" if winner == bot_cocky else "CockyBot"
            
            winner_score = bot_cocky.final_score if winner == bot_cocky else bot_rand.final_score
            loser_score = bot_rand.final_score if winner == bot_cocky else bot_cocky.final_score
            
            # Deck closed?
            deck_closed = bot_cocky.closed_talon or bot_rand.closed_talon
            closer_identity = "None"
            if bot_cocky.closed_talon:
                closer_identity = "CockyBot"
            elif bot_rand.closed_talon:
                closer_identity = "RandBot"
                
            # Cockybot won after closing?
            cockybot_won_after_closing = False
            if bot_cocky.closed_talon:
                if winner == bot_cocky:
                    cockybot_won_after_closing = True
            
            # Tricks won by Cockybot after closing
            tricks_won_after_closing = 0
            if bot_cocky.closed_talon:
                final_tricks = bot_cocky.final_won_cards_count // 2
                tricks_won_after_closing = final_tricks - bot_cocky.tricks_at_closure
            
            #Makes sure game points have been calculated correctly when talon has been closed
            if bot_cocky.closed_talon or bot_rand.closed_talon:
                closer = bot_cocky if bot_cocky.closed_talon else bot_rand
                if winner == closer:
                    if closer.opponent_points_at_closure == 0:
                        game_points = 3
                    elif closer.opponent_points_at_closure < 33:
                        game_points = 2
                    else:
                        game_points = 1
                else:
                    #The logic is the same, but in this case these game points are for the non-closer
                    if closer.opponent_points_at_closure == 0:
                        game_points = 3
                    else:
                        game_points = 2

            row = {
                "Seed": seed,
                "Match outcome": f"{winner_name} beat {loser_name}",
                "Winner": winner_name,
                "Loser": loser_name,
                "Winner score": winner_score,
                "Loser score": loser_score,
                "Game points": game_points,
                "Deck closed": deck_closed,
                "Closer": closer_identity,
                "Closure points": bot_cocky.closure_points if bot_cocky.closed_talon else (bot_rand.closure_points if bot_rand.closed_talon else "N/A"),
                "CockyBot marriages": bot_cocky.marriages_declared,
                "CockyBot trump exchanges": bot_cocky.trump_exchanges_declared,
                "CockyBot won after closing": str(cockybot_won_after_closing),
                "Trumps when closing": str(bot_cocky.trumps_when_closing) if bot_cocky.closed_talon else "N/A",
                "Non-trumps when closing": str(bot_cocky.non_trumps_when_closing) if bot_cocky.closed_talon else "N/A",
                "Tricks won after closing": str(tricks_won_after_closing) if bot_cocky.closed_talon else "N/A",
                "RandBot RNG Seed": rand_bot_rng_seed
            }
            
            writer.writerow(row)
            
    print("Cockybot experiment done")


@main.command()
def bully_experiment() -> None:
    """Run BullyBot vs RandBot experiment (1000 games)"""
    import csv
    
    engine = SchnapsenGamePlayEngine()
    total_games = 1000
    
    # Define CSV fields
    fieldnames = [
        "Seed", "Match outcome", "Winner", "Loser", 
        "Winner score", "Loser score", "Game points",
        "Deck closed", "Closer", 
        "Closure points", "BullyBot marriages",
        "BullyBot trump exchanges",
        "BullyBot won after closing", "Trumps when closing", 
        "Non-trumps when closing", "Tricks won after closing",
        "BullyBot RNG Seed", "RandBot RNG Seed"
    ]
    
    output_file = 'bully_experiment_results_new.csv'
    print(f"Output will be saved to {output_file}")
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i in range(total_games):
            seed = i
            rng_game = random.Random(seed)
            rand_bot_rng_seed = seed + 20000
            bully_bot_rng_seed = seed + 30000
            rng_randbot = random.Random(rand_bot_rng_seed)
            rng_bully = random.Random(bully_bot_rng_seed)
            
            bot_bully = ExperimentBullyBot(rand=rng_bully, name="BullyBot")
            bot_rand = ExperimentRandBot(rng=rng_randbot, name="RandBot")
            
            # Randomize starter
            if i % 2 == 0:
                leader, follower = bot_bully, bot_rand
            else:
                leader, follower = bot_rand, bot_bully
                
            winner, game_points, score = engine.play_game(leader, follower, rng_game)
            
            # Winner and loser
            winner_name = str(winner)
            loser_name = "RandBot" if winner == bot_bully else "BullyBot"
            
            winner_score = bot_bully.final_score if winner == bot_bully else bot_rand.final_score
            loser_score = bot_rand.final_score if winner == bot_bully else bot_bully.final_score
            
            # Deck closed?
            deck_closed = bot_bully.closed_talon or bot_rand.closed_talon
            closer_identity = "None"
            if bot_bully.closed_talon:
                closer_identity = "BullyBot"
            elif bot_rand.closed_talon:
                closer_identity = "RandBot"
                
            # BullyBot won after closing?
            bullybot_won_after_closing = False
            if bot_bully.closed_talon:
                if winner == bot_bully:
                    bullybot_won_after_closing = True
            
            # Tricks won by BullyBot after closing
            tricks_won_after_closing = 0
            if bot_bully.closed_talon:
                final_tricks = bot_bully.final_won_cards_count // 2
                tricks_won_after_closing = final_tricks - bot_bully.tricks_at_closure

            #Makes sure game points have been calculated correctly when talon has been closed
            if bot_bully.closed_talon or bot_rand.closed_talon:
                closer = bot_bully if bot_bully.closed_talon else bot_rand
                if winner == closer:
                    if closer.opponent_points_at_closure == 0:
                        game_points = 3
                    elif closer.opponent_points_at_closure < 33:
                        game_points = 2
                    else:
                        game_points = 1
                else:
                    #The logic is the same, but in this case these game points are for the non-closer
                    if closer.opponent_points_at_closure == 0:
                        game_points = 3
                    else:
                        game_points = 2

            row = {
                "Seed": seed,
                "Match outcome": f"{winner_name} beat {loser_name}",
                "Winner": winner_name,
                "Loser": loser_name,
                "Winner score": winner_score,
                "Loser score": loser_score,
                "Game points": game_points,
                "Deck closed": deck_closed,
                "Closer": closer_identity,
                "Closure points": bot_bully.closure_points if bot_bully.closed_talon else (bot_rand.closure_points if bot_rand.closed_talon else "N/A"),
                "BullyBot marriages": bot_bully.marriages_declared,
                "BullyBot trump exchanges": bot_bully.trump_exchanges_declared,
                "BullyBot won after closing": str(bullybot_won_after_closing),
                "Trumps when closing": str(bot_bully.trumps_when_closing) if bot_bully.closed_talon else "N/A",
                "Non-trumps when closing": str(bot_bully.non_trumps_when_closing) if bot_bully.closed_talon else "N/A",
                "Tricks won after closing": str(tricks_won_after_closing) if bot_bully.closed_talon else "N/A",
                "BullyBot RNG Seed": bully_bot_rng_seed,
                "RandBot RNG Seed": rand_bot_rng_seed
            }
            
            writer.writerow(row)
            
    print("BullyBot experiment done")


@main.command()
def rdeep_experiment() -> None:
    """Run RDeepBot vs RandBot experiment (1000 games)"""
    import csv
    
    engine = SchnapsenGamePlayEngine()
    total_games = 1000
    rdeep_num_samples = 12
    rdeep_depth = 5
    
    # Define CSV fields
    fieldnames = [
        "Seed", "Match outcome", "Winner", "Loser", 
        "Winner score", "Loser score", "Game points",
        "Deck closed", "Closer", 
        "Closure points", "RDeepBot marriages",
        "RDeepBot trump exchanges",
        "RDeepBot won after closing", "Trumps when closing", 
        "Non-trumps when closing", "Tricks won after closing",
        "RDeepBot Num Samples", "RDeepBot Depth",
        "RDeepBot RNG Seed", "RandBot RNG Seed"
    ]
    
    output_file = 'rdeep_experiment_results_new.csv'
    print(f"Output will be saved to {output_file}")
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i in range(total_games):
            seed = i
            rng_game = random.Random(seed)
            rand_bot_rng_seed = seed + 20000
            rdeep_bot_rng_seed = seed + 40000
            rng_randbot = random.Random(rand_bot_rng_seed)
            rng_rdeepbot = random.Random(rdeep_bot_rng_seed)
            
            bot_rdeep = ExperimentRDeepBot(num_samples=rdeep_num_samples, depth=rdeep_depth, rand=rng_rdeepbot, name="RDeepBot")
            bot_rand = ExperimentRandBot(rng=rng_randbot, name="RandBot")
            
            # Randomize starter
            if i % 2 == 0:
                leader, follower = bot_rdeep, bot_rand
            else:
                leader, follower = bot_rand, bot_rdeep
                
            winner, game_points, score = engine.play_game(leader, follower, rng_game)
            
            # Winner and loser
            winner_name = str(winner)
            loser_name = "RandBot" if winner == bot_rdeep else "RDeepBot"
            
            winner_score = bot_rdeep.final_score if winner == bot_rdeep else bot_rand.final_score
            loser_score = bot_rand.final_score if winner == bot_rdeep else bot_rdeep.final_score
            
            # Deck closed?
            deck_closed = bot_rdeep.closed_talon or bot_rand.closed_talon
            closer_identity = "None"
            if bot_rdeep.closed_talon:
                closer_identity = "RDeepBot"
            elif bot_rand.closed_talon:
                closer_identity = "RandBot"
                
            # RDeepBot won after closing?
            rdeepbot_won_after_closing = False
            if bot_rdeep.closed_talon:
                if winner == bot_rdeep:
                    rdeepbot_won_after_closing = True
            
            # Tricks won by RDeepBot after closing
            tricks_won_after_closing = 0
            if bot_rdeep.closed_talon:
                final_tricks = bot_rdeep.final_won_cards_count // 2
                tricks_won_after_closing = final_tricks - bot_rdeep.tricks_at_closure

            #Makes sure game points have been calculated correctly when talon has been closed
            if bot_rdeep.closed_talon or bot_rand.closed_talon:
                closer = bot_rdeep if bot_rdeep.closed_talon else bot_rand
                if winner == closer:
                    if closer.opponent_points_at_closure == 0:
                        game_points = 3
                    elif closer.opponent_points_at_closure < 33:
                        game_points = 2
                    else:
                        game_points = 1
                else:
                    #The logic is the same, but in this case these game points are for the non-closer
                    if closer.opponent_points_at_closure == 0:
                        game_points = 3
                    else:
                        game_points = 2

            row = {
                "Seed": seed,
                "Match outcome": f"{winner_name} beat {loser_name}",
                "Winner": winner_name,
                "Loser": loser_name,
                "Winner score": winner_score,
                "Loser score": loser_score,
                "Game points": game_points,
                "Deck closed": deck_closed,
                "Closer": closer_identity,
                "Closure points": bot_rdeep.closure_points if bot_rdeep.closed_talon else (bot_rand.closure_points if bot_rand.closed_talon else "N/A"),
                "RDeepBot marriages": bot_rdeep.marriages_declared,
                "RDeepBot trump exchanges": bot_rdeep.trump_exchanges_declared,
                "RDeepBot won after closing": str(rdeepbot_won_after_closing),
                "Trumps when closing": str(bot_rdeep.trumps_when_closing) if bot_rdeep.closed_talon else "N/A",
                "Non-trumps when closing": str(bot_rdeep.non_trumps_when_closing) if bot_rdeep.closed_talon else "N/A",
                "Tricks won after closing": str(tricks_won_after_closing) if bot_rdeep.closed_talon else "N/A",
                "RDeepBot Num Samples": rdeep_num_samples,
                "RDeepBot Depth": rdeep_depth,
                "RDeepBot RNG Seed": rdeep_bot_rng_seed,
                "RandBot RNG Seed": rand_bot_rng_seed
            }
            
            writer.writerow(row)
            
    print("RDeepBot experiment done")
        
if __name__ == "__main__":
    main()

import csv

def analyze_results(filename: str, bot_name: str):
    print(f"Analyzing {filename} for {bot_name} Performance")
    
    wins = 0
    losses = 0
    points_counts = dict()
    
    closed_count = 0
    closed_and_won_count = 0
    won_after_closing_column_count = 0 
    
    wins_with_marriage = 0
    wins_with_trump_exchange = 0
    
    total_marriages = 0
    total_trump_exchanges = 0
    
    # Closing details
    tricks_after_closing_list = []
    
    try:
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                winner = row['Winner']
                closer = row['Closer']
                game_points = int(row['Game points'])
                
                marriages = int(row.get(f'{bot_name} marriages', 0))
                trump_exchanges = int(row.get(f'{bot_name} trump exchanges', 0))
                
                total_marriages += marriages
                total_trump_exchanges += trump_exchanges
                
                # Win Analysis
                if winner == bot_name:
                    wins += 1
                    points_counts[game_points] = points_counts.get(game_points, 0) + 1
                    
                    if marriages > 0:
                        wins_with_marriage += 1
                    if trump_exchanges > 0:
                        wins_with_trump_exchange += 1
                else:
                    losses += 1
                
                # Closing Analysis
                if closer == bot_name:
                    closed_count += 1
                    if winner == bot_name:
                        closed_and_won_count += 1
                    
                    # Additional closing stats
                    if row['Tricks won after closing'] != 'N/A':
                        tricks_after_closing_list.append(int(row['Tricks won after closing']))

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found. Please run the experiment first.")
        return

    total_games = wins + losses
    if total_games == 0:
        print("No games found.")
        return

    print("\n" + "="*40)
    print(f"   {bot_name} Analysis Report")
    print("="*40)
    
    print(f"\nOverall Performance:")
    print(f"  Total games: {total_games}")
    print(f"  Wins:        {wins}")
    print(f"  Losses:      {losses}")
    print(f"  Win rate:    {wins / total_games * 100:.2f}%")
    
    print(f"\nGame points (in wins):")
    for points in [3, 2, 1]:
        points_count = points_counts[points]
        points_percentage = points_count / wins * 100 if wins > 0 else 0
        print(f"  {points} points: {points_count} ({points_percentage:.1f}%)")

    print(f"\nStrategic moves:")
    print(f"  Total marriages:       {total_marriages} ({total_marriages/total_games:.2f} per game)")
    if wins > 0:
        print(f"  Wins with marriage:    {wins_with_marriage} ({wins_with_marriage/wins*100:.2f}% of wins)")
    print(f"  Total trump exchanges: {total_trump_exchanges} ({total_trump_exchanges/total_games:.2f} per game)")
    if wins > 0:
        print(f"  Wins with trump exch:  {wins_with_trump_exchange} ({wins_with_trump_exchange/wins*100:.2f}% of wins)")

    print(f"\nDeck closing statistics:")
    print(f"  Times closed:          {closed_count}")
    print(f"  Times not closed:      {total_games - closed_count}")
    print(f"  Closing frequency:     {closed_count / total_games * 100:.2f}%")
    print(f"  Times won after closing: {closed_and_won_count}")
    if closed_count > 0:
        print(f"  Win rate when closing: {closed_and_won_count / closed_count * 100:.2f}%")
        avg_tricks = sum(tricks_after_closing_list) / len(tricks_after_closing_list) if tricks_after_closing_list else 0
        print(f"  Avg tricks after close:{avg_tricks:.2f}")
    else:
        print("  Win rate when closing: N/A")
        
    # Non-closing stats for comparison
    games_not_closed = total_games - closed_count
    wins_not_closed = wins - closed_and_won_count
    if games_not_closed > 0:
        win_rate_not_closed = wins_not_closed / games_not_closed * 100
        print(f"  Win rate not closing:  {win_rate_not_closed:.2f}%")

if __name__ == "__main__":
    analyze_results('bully_proper_experiment_results.csv', 'BullyBot')
    analyze_results('rdeep_proper_experiment_results.csv', 'RDeepBot')
    analyze_results('cocky_experiment_results_40points2trumps.csv', 'CockyBot')
    analyze_results('cocky_experiment_results_30points3trumps.csv', 'CockyBot')
    analyze_results('cocky_experiment_results_40points2stricttrumps.csv', 'CockyBot')
    analyze_results('cocky_experiment_results_100points2trumps.csv', 'CockyBot')
    analyze_results('cocky_experiment_results_10points1trumps.csv', 'CockyBot')
    analyze_results('cocky_experiment_results_10points2trumps.csv', 'CockyBot')
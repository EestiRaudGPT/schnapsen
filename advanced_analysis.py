import csv
import math
from typing import Dict, List, Tuple

def calculate_stats(filename: str, bot_name: str, baseline_win_rate: float = 0.5):
    """
    Analyzes game results and calculates advanced statistics including p-value.
    
    Args:
        filename: Path to the CSV results file
        bot_name: Name of the bot to analyze
        baseline_win_rate: The expected win rate under the null hypothesis (default 0.5 for random)
    """
    print(f"\n{'='*60}")
    print(f"   Advanced Statistical Analysis: {bot_name}")
    print(f"{'='*60}")
    
    wins = 0
    losses = 0
    game_points_list = []
    
    try:
        with open(filename, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                winner = row['Winner']
                points = int(row['Game points'])
                
                if winner == bot_name:
                    wins += 1
                    game_points_list.append(points)
                else:
                    losses += 1
                    game_points_list.append(-points) # Negative points for loss representation
                    
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return

    n = wins + losses
    if n == 0:
        print("No games recorded.")
        return

    win_rate = wins / n
    std_error = math.sqrt((win_rate * (1 - win_rate)) / n)
    
    # Z-test for proportions
    # Null hypothesis: win_rate = baseline_win_rate (0.5)
    p_hat = win_rate
    p_0 = baseline_win_rate
    z_score = (p_hat - p_0) / math.sqrt((p_0 * (1 - p_0)) / n)
    
    # Calculate p-value (two-tailed)
    # Using approximation for standard normal distribution
    # p_value = 2 * (1 - norm.cdf(abs(z_score)))
    # Since we don't want to depend on scipy/numpy for this script, we'll use an error function approximation
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z_score) / math.sqrt(2))))

    # Confidence Interval (95%)
    margin_of_error = 1.96 * std_error
    ci_lower = win_rate - margin_of_error
    ci_upper = win_rate + margin_of_error

    print(f"\nResult Summary:")
    print(f"  Total Games (n):    {n}")
    print(f"  Wins:              {wins}")
    print(f"  Losses:            {losses}")
    print(f"  Observed Win Rate: {win_rate:.4f} ({win_rate*100:.2f}%)")
    
    print(f"\nStatistical Significance (vs Random 50%):")
    print(f"  Null Hypothesis:   True win rate is 50%")
    print(f"  Z-Score:           {z_score:.4f}")
    print(f"  P-Value:           {p_value:.10f}")
    
    alpha = 0.05
    is_significant = p_value < alpha
    significance_str = "SIGNIFICANT" if is_significant else "NOT SIGNIFICANT"
    print(f"  Conclusion:        The result is statistically {significance_str} at alpha={alpha}")
    
    print(f"\n95% Confidence Interval:")
    print(f"  Range:             [{ci_lower:.4f}, {ci_upper:.4f}]")
    print(f"  Interpretation:    We are 95% confident the true win rate is between {ci_lower*100:.2f}% and {ci_upper*100:.2f}%")

    # Average Points Analysis
    # This treats losses as 'negative game points' just to see net point flow, 
    # or we can just look at avg points when winning. Usually 'Game Points' in Schnapsen 
    # are strictly positive for the winner (1, 2, or 3).
    avg_points_win = sum([p for p in game_points_list if p > 0]) / wins if wins > 0 else 0
    print(f"\nPoints Efficiency:")
    print(f"  Avg Game Points (Winning): {avg_points_win:.2f}")


if __name__ == "__main__":
    calculate_stats('cocky_experiment_results_new.csv', 'CockyBot')
    calculate_stats('bully_experiment_results_new.csv', 'BullyBot')
    calculate_stats('rdeep_experiment_results_new.csv', 'RDeepBot')

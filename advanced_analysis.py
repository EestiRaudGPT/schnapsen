import csv
import numpy as np
from scipy import stats

def calculate_stats(filename: str, bot_name: str, baseline_win_rate: float = 0.5):
    """
    Analyzes game results using numpy and scipy for statistical calculations.
    """
    print(f"\n{'='*60}")
    print(f"   Advanced Statistical Analysis (NumPy/SciPy): {bot_name}")
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
                    # We store 0 for losses when calculating 'winning points avg', 
                    # or we could skip them. Let's filter later.
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return

    n = wins + losses
    if n == 0:
        print("No games recorded.")
        return

    # --- Statistical Analysis using NumPy/SciPy ---
    
    # 1. Basic Counts
    win_rate = wins / n
    
    # 2. Confidence Interval (95%) using Normal Approximation
    # Standard Error = sqrt(p*(1-p)/n)
    std_error = stats.sem(np.array([1]*wins + [0]*losses)) # Standard error of the mean
    
    # Confidence interval using normal distribution (ppf)
    confidence_level = 0.95
    degrees_freedom = n - 1
    # For large n, t-dist converts to normal, but stats.t.interval is convenient
    ci_low, ci_high = stats.t.interval(confidence_level, degrees_freedom, loc=win_rate, scale=std_error)
    
    # 3. Hypothesis Testing (Binomial Test is exact and preferred over Z-test for proportions)
    # Null Hypothesis: p = 0.5
    binom_result = stats.binomtest(wins, n, p=baseline_win_rate, alternative='two-sided')
    p_value = binom_result.pvalue
    
    # We can also back-calculate the Z-score for display purposes if needed, 
    # but binomtest doesn't return it.
    # Let's verify significance
    alpha = 0.05
    is_significant = p_value < alpha
    significance_str = "SIGNIFICANT" if is_significant else "NOT SIGNIFICANT"

    # 4. Points Analysis with NumPy
    points_array = np.array(game_points_list)
    avg_points_win = np.mean(points_array) if len(points_array) > 0 else 0.0

    # --- Reporting ---
    print(f"\nResult Summary:")
    print(f"  Total Games (n):    {n}")
    print(f"  Wins:              {wins}")
    print(f"  Losses:            {losses}")
    print(f"  Observed Win Rate: {win_rate:.4f} ({win_rate*100:.2f}%)")
    
    print(f"\nStatistical Significance (Binomial Test):")
    print(f"  Null Hypothesis:   True win rate is 50%")
    print(f"  P-Value:           {p_value:.10f}")
    print(f"  Conclusion:        The result is statistically {significance_str} at alpha={alpha}")
    
    print(f"\n95% Confidence Interval (t-distribution):")
    print(f"  Range:             [{ci_low:.4f}, {ci_high:.4f}]")
    print(f"  Interpretation:    We are 95% confident the true win rate is between {ci_low*100:.2f}% and {ci_high*100:.2f}%")

    print(f"\nPoints Efficiency:")
    print(f"  Avg Game Points (Winning): {avg_points_win:.2f}")


if __name__ == "__main__":
    calculate_stats('cocky_experiment_results_new.csv', 'CockyBot')
    calculate_stats('bully_experiment_results_new.csv', 'BullyBot')
    calculate_stats('rdeep_experiment_results_new.csv', 'RDeepBot')

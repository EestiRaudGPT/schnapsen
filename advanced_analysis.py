import csv
import os
try:
    from statsmodels.stats.contingency_tables import mcnemar
except ImportError:
    print("Error: statsmodels is not installed. Please install it using 'pip install statsmodels'")
    exit(1)

def mcnemar_test(bot_a: str, bot_b: str, file_a: str, file_b: str):
    '''
    Performs a McNemar test on two datasets.
    We have to use McNemar's test because we are not comparing two random groups of games.
    We are comparing how two bots perform against the same baseline (RandBot) over the same 1000 games.
    So we have a paired sample.
    '''

    # Load data for Bot A
    print(f"Loading data for {bot_a} from {file_a}...")
    sample_a = []
    if not os.path.exists(file_a):
        print(f"Warning: File {file_a} not found.")
    else:
        with open(file_a, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                winner = row['Winner']
                if winner == 'RandBot':
                    sample_a.append(0) #Bot lost
                else:
                    sample_a.append(1) #Bot won
    
    # Load data for Bot B
    print(f"Loading data for {bot_b} from {file_b}...")
    sample_b = []
    if not os.path.exists(file_b):
        print(f"Warning: File {file_b} not found.")
    else:
        with open(file_b, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                winner = row['Winner']
                if winner == 'RandBot':
                    sample_b.append(0) #Bot lost
                else:
                    sample_b.append(1) #Bot won

    print(f"{bot_a}: Loaded {len(sample_a)} games.")
    print(f"{bot_b}: Loaded {len(sample_b)} games.")

    if len(sample_a) != len(sample_b) or len(sample_a) == 0:
        print(f"\nSkipping {bot_a} vs {bot_b}: Samples must be paired and non-empty.")
    else:
        n10 = 0 # A wins, B loses (favors A)
        n01 = 0 # A loses, B wins (favors B)
        n11 = 0 # A wins, B wins (draw)
        n00 = 0 # A loses, B loses (draw)
        
        for a, b in zip(sample_a, sample_b):
            #zip lets us iterate over two lists at the same time (it returns a tuple of two elements)
            if a == 1 and b == 0:
                n10 += 1
            elif a == 0 and b == 1:
                n01 += 1
            elif a == 1 and b == 1:
                n11 += 1
            else:
                n00 += 1
                
        print(f"\nComparing {bot_a} vs {bot_b}:")
        print(f"Paired Disagreements: {bot_a} wins/{bot_b} loses = {n10}")
        print(f"Paired Disagreements: {bot_a} loses/{bot_b} wins = {n01}")
        print(f"Agreements: {bot_a} wins/{bot_b} wins = {n11}, {bot_a} loses/{bot_b} loses = {n00}")
        
        # How the table works
        #         B=0    B=1
        # A=0     n00    n01
        # A=1     n10    n11
        table = [[n00, n01],
                [n10, n11]]
                
        result = mcnemar(table, exact=False, correction=True)
        '''
        Exact being false means we use chi-square distribution, which is an approximation, and we use it because we have a large sample size.
        Chi-square distribution tracks how much the results deviate from what we would expect if the null hypothesis (the two bots perform the same) were true.
        Correction being true means we apply the continuity correction.
        Continuity correction is a small adjustment to the chi-square statistic to account for the fact that the chi-square distribution is continuous (uses decimals) while the McNemar test is discrete (uses whole numbers).
        This is necessary because you can't have half a win or half a loss.
        '''
        
        print(f"P-value: {result.pvalue:.6f}")
        
        alpha = 0.05
        if result.pvalue < alpha:
            winner = bot_a if n10 > n01 else bot_b
            print(f"Result: The difference is STATISTICALLY SIGNIFICANT (p < {alpha}). {winner} performs better.")
        else:
            print(f"Result: The difference is NOT statistically significant (p >= {alpha}).")


mcnemar_test("CockyBot (40/2)", "CockyBot (30/3)", "cocky_experiment_results_40points2trumps.csv", "cocky_experiment_results_30points3trumps.csv")

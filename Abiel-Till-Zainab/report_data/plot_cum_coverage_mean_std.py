import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the CSV file
num_cases = [5, 10, 15]
coverage_pct = [30, 50, 70]
max_tests = 25
model = 'gpt-4o'

def difficulty_level(num_cases):
    if num_cases == 5:
        return 0
    elif num_cases == 10:
        return 1
    elif num_cases == 15:
        return 2

plt.figure(figsize=(10, 6))

# Create a dictionary to store coverage values for each test number
test_coverages = {i: [] for i in range(1, max_tests + 1)}

# Collect all coverage values
for i in range(len(num_cases)):
    for j in range(len(coverage_pct)):
        try:
            df = pd.read_csv(f'report_data/{model}/{num_cases[i]}_{coverage_pct[j]}.csv')
        except FileNotFoundError:
            continue
        
        test_columns = [col for col in df.columns if 'Test' in col]
        total_lines = len(df[df['Code'].notna()]) - 1

        for k, test in enumerate(test_columns[:max_tests]):
            covered_lines = (df[test_columns[:k+1]].sum(axis=1) > 0) & df['Code'].notna()
            coverage_pct_val = covered_lines[:-1].sum() / total_lines * 100
            test_coverages[k + 1].append(coverage_pct_val)

# Calculate mean and std for each test number
test_numbers = list(test_coverages.keys())
means = [np.mean(test_coverages[t]) for t in test_numbers]
stds = [np.std(test_coverages[t]) for t in test_numbers]

# Plot mean line with std deviation band
plt.plot(test_numbers, means, 'tab:blue', marker='o', label='Mean (±1 std dev.)', linewidth=2)
plt.fill_between(test_numbers, 
                 [m - s for m, s in zip(means, stds)],
                 [m + s for m, s in zip(means, stds)],
                 color='tab:blue', alpha=0.2)

plt.xlabel('Test Number')
plt.ylabel('Cumulative Line Coverage (%)')
#plt.title('Average Test Coverage Analysis')
plt.legend()
plt.grid(True)
plt.tight_layout()

# Save the plot
plt.savefig(f'report_data/cum_coverage_mean_std_{model}.png', bbox_inches='tight')
plt.close()

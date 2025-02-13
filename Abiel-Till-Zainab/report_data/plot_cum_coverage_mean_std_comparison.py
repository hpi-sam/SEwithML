import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the CSV file
num_cases = [5, 10, 15]
coverage_pct = [30, 50, 70]
max_tests = 25

# Update models list
models = ['gpt-4o', 'gpt-4o-mini']
colors = ['tab:blue', 'tab:orange']

plt.figure(figsize=(10, 6))

# Create separate dictionaries for each model
test_coverages = {model: {i: [] for i in range(1, max_tests + 1)} for model in models}

# Collect all coverage values
for model in models:
    for i in range(len(num_cases)):
        for j in range(len(coverage_pct)):
            try:
                df = pd.read_csv(f'report_data/{model}/{num_cases[i]}_{coverage_pct[j]}.csv')
            except FileNotFoundError:
                continue
            
            test_columns = [col for col in df.columns if 'Test' in col]
            total_lines = len(df[df['Code'].notna()]) - 1
            
            # Calculate coverage for available tests
            coverage_values = []
            for k, test in enumerate(test_columns):
                covered_lines = (df[test_columns[:k+1]].sum(axis=1) > 0) & df['Code'].notna()
                coverage_pct_val = covered_lines[:-1].sum() / total_lines * 100
                coverage_values.append(coverage_pct_val)
            
            # Add the available coverage values (but only up to max_tests)
            for k, val in enumerate(coverage_values[:max_tests], 1):
                test_coverages[model][k].append(val)
            
            # Extend coverage values up to max_tests using the last value
            last_coverage = coverage_values[min(len(coverage_values)-1, max_tests-1)] if coverage_values else 0
            for k in range(len(coverage_values[:max_tests]) + 1, max_tests + 1):
                test_coverages[model][k].append(last_coverage)

# Plot for each model
for model, color in zip(models, colors):
    test_numbers = list(test_coverages[model].keys())
    means = [np.mean(test_coverages[model][t]) for t in test_numbers]
    stds = [np.std(test_coverages[model][t]) for t in test_numbers]

    plt.plot(test_numbers, means, color=color, marker='o', label=f'{model} (±1 std dev.)', linewidth=2)
    plt.fill_between(test_numbers, 
                     [m - s for m, s in zip(means, stds)],
                     [m + s for m, s in zip(means, stds)],
                     color=color, alpha=0.2)

plt.xlabel('Test Number')
plt.ylabel('Cumulative Line Coverage (%)')
#plt.title('Average Test Coverage Analysis')
plt.legend()
plt.grid(True)
plt.tight_layout()

# Save the plot
plt.savefig(f'report_data/cum_coverage_mean_std_comparison.png', bbox_inches='tight')
plt.close()

import pandas as pd
import matplotlib.pyplot as plt

# Read the CSV file
num_cases = [5, 10, 15]
coverage_pct = [30, 50, 70]
max_tests = 25

def difficulty_level(num_cases):
    if num_cases == 5:
        return 0
    elif num_cases == 10:
        return 1
    elif num_cases == 15:
        return 2
    
def pct_difficulty(coverage_pct):
    if coverage_pct == 30:
        return 0
    elif coverage_pct == 50:
        return 1
    elif coverage_pct == 70:
        return 2

plt.figure(figsize=(10, 6))
# colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
difficulty_colors = ['tab:green', 'tab:orange', 'tab:red']
difficulty_markers = ['o', 'h', 's']
color_idx = 0

for i in range(len(num_cases)):
    for j in range(len(coverage_pct)):
        try:
            df = pd.read_csv(f'report_data/gpt-4o-mini/{num_cases[i]}_{coverage_pct[j]}.csv')
        except FileNotFoundError:
            continue
        
        # Calculate cumulative coverage for each test
        test_columns = [col for col in df.columns if 'Test' in col]
        total_lines = len(df[df['Code'].notna()]) - 1

        cum_coverage = []
        new_coverage = []

        for k, test in enumerate(test_columns[:max_tests]):  # Limit to first 25 tests
            covered_lines = (df[test_columns[:k+1]].sum(axis=1) > 0) & df['Code'].notna()
            coverage_pct_val = covered_lines[:-1].sum() / total_lines * 100
            cum_coverage.append(coverage_pct_val)
            
            if k == 0:
                new_coverage.append(coverage_pct_val)
            else:
                new_coverage.append(coverage_pct_val - cum_coverage[k-1])

        # Plot each combination with a different color
        label = f'{num_cases[i]} cases, {coverage_pct[j]}% returns'
        plt.plot(range(1, len(test_columns[:max_tests]) + 1), cum_coverage, 
                f'{difficulty_colors[difficulty_level(num_cases[i])]}', marker=difficulty_markers[pct_difficulty(coverage_pct[j])], label=label, linewidth=2)
        
        # Print final coverage for this combination
        print(f"Final coverage for {num_cases[i]} cases, {coverage_pct[j]}% returns: {cum_coverage[-1]:.2f}%")

        color_idx += 1

plt.xlabel('Test Number')
plt.ylabel('Cumulative Line Coverage (%)')
#plt.title('')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True)
plt.tight_layout()

# Save the plot
plt.savefig('report_data/cum_coverage_gpt_4o.png', bbox_inches='tight')
plt.close()

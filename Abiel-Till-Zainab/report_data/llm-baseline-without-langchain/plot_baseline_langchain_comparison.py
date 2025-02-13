import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Read the CSV data
df = pd.read_csv('report_data/llm-baseline-without-langchain/scores.csv')

# Set style - using a built-in matplotlib style instead of seaborn
plt.style.use('ggplot')  # Alternative options: 'fivethirtyeight', 'bmh', or remove this line completely
fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
# fig.suptitle('Coverage Comparison by Number of Cases and Return Percentage', fontsize=14)

# Colors for consistency
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

# Create subplots for each number of cases
unique_cases = sorted(df['N_cases'].unique())
for n_cases, ax in zip(unique_cases, [ax1, ax2, ax3]):
    data = df[df['N_cases'] == n_cases]
    
    x = range(len(data['return_percentage']))
    width = 0.25
    
    # Plot bars for each approach
    ax.bar([i - width for i in x], data['coverage_baseline'], width, label='GPT4o (Baseline without Langchain)', color=colors[0])
    ax.bar(x, data['coverage_gpt4o_mini_langchain'], width, label='GPT4o-mini (Langchain)', color=colors[2])
    ax.bar([i + width for i in x], data['coverage_gpt4o_langchain'], width, label='GPT4o (Langchain)', color=colors[1])
    
    ax.set_ylabel('Cumulative Coverage (%)')
    ax.set_xlabel('Return Percentage')
    ax.set_title(f'Number of Cases: {n_cases}')
    ax.set_xticks(x)
    ax.set_xticklabels(data['return_percentage'])
    ax.grid(True, alpha=0.3)
    
    # Add legend only to the first subplot
    if n_cases == unique_cases[0]:
        ax.legend(bbox_to_anchor=(4.4, 1)) # bbox_to_anchor=(0.5, -0.15), ncol=3

plt.tight_layout()
fig.savefig('report_data/llm-baseline-without-langchain/coverage_comparison.png', dpi=500, bbox_inches='tight')
# plt.show()
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os

def count_tests_to_full_coverage(df, deletion_type):
    # Find the deletion event for the specified type
    deletion_event = df[df['event'] == 'deleted_test'][df['ranking_info'] == deletion_type].iloc[0]
    deletion_idx = df.index.get_loc(deletion_event.name)
    
    # Get subsequent events until full coverage is reached
    subsequent_events = df.iloc[deletion_idx + 1:]
    tests_needed = 0
    
    for _, event in subsequent_events.iterrows():
        if event['is_full_coverage']:
            break
        if event['event'] == 'generated_test' or event['event'] == 'generated_test_auto':
            tests_needed += 1
    
    return tests_needed

# Get all CSV files in the directory
csv_files = glob.glob('report_data/regenetation_report/3-tests-deletion/f*.csv')

# Initialize lists to store results
min_tests = []
med_tests = []
max_tests = []
file_names = []

# Process each file
for file_path in csv_files:
    df = pd.read_csv(file_path)
    file_name = os.path.basename(file_path).split('_')[0]
    file_names.append(file_name)
    
    # Count tests needed for each deletion type
    min_tests.append(count_tests_to_full_coverage(df, 'min'))
    med_tests.append(count_tests_to_full_coverage(df, 'med'))
    max_tests.append(count_tests_to_full_coverage(df, 'max'))

# Create DataFrame with results
data = {
    'File': file_names,
    'Tests_After_Min': min_tests,
    'Tests_After_Med': med_tests,
    'Tests_After_Max': max_tests
}

df = pd.DataFrame(data)

# Convert to long format for seaborn
df_long = pd.melt(df, id_vars=['File'], 
                  value_vars=['Tests_After_Min', 'Tests_After_Med', 'Tests_After_Max'],
                  var_name='Deletion_Type', value_name='Tests_Needed')

df_long['Deletion_Type'] = df_long['Deletion_Type'].map({
    'Tests_After_Min': 'Min. Unique Coverage',
    'Tests_After_Med': 'Medium Unique Coverage',
    'Tests_After_Max': 'Max. Unique Coverage'
})

# Create the visualization
plt.figure(figsize=(10, 6))

# Create violin plot without box plots
sns.violinplot(data=df_long, x='Deletion_Type', y='Tests_Needed', 
               inner=None, palette=['lightblue', 'lightgreen', 'coral'],
               bw=0.3)  # Reduced bandwidth for better discrete data representation

# Add individual points with matching colors but darker
sns.stripplot(data=df_long, x='Deletion_Type', y='Tests_Needed', 
              palette=['darkblue', 'darkgreen', 'darkred'],  # Darker colors for better contrast
              alpha=0.6, size=8, jitter=0.05)

# Add mean and median lines for each violin
for i, col in enumerate(['Tests_After_Min', 'Tests_After_Med', 'Tests_After_Max']):
    mean_val = df[col].mean()
    median_val = df[col].median()
    
    # Plot mean line
    plt.hlines(y=mean_val, xmin=i-0.2, xmax=i+0.2, color='tab:red', linestyle='-', 
               linewidth=2, label='Mean' if i == 0 else "")
    
    # Plot median line
    plt.hlines(y=median_val, xmin=i-0.2, xmax=i+0.2, color='tab:blue', linestyle='-', 
               linewidth=2, label='Median' if i == 0 else "")
    
    # Add mean value text
    plt.text(i, plt.ylim()[1], f'Mean: {mean_val:.2f}', 
             ha='center', va='bottom')

# Customize the plot
# plt.title('Distribution of Regeneration Effort by Deleted Test Coverage Type')
plt.xlabel('')
plt.ylabel('Number of Tests Needed to Regain 100% Cumulative Coverage')

# Add legend
plt.legend(loc='upper right')

plt.tight_layout()
plt.savefig('report_data/regenetation_report/3-tests-deletion/deletion_results.png')
# plt.show()

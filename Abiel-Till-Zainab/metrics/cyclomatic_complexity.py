import os
import subprocess
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def analyze_modules_with_radon(modules_dir, output_csv):
    """
    Analyzes Python modules in a given directory using Radon called through 
    subprocess that runs Radon's command-line interface (CLI) commands 
    and saves the metrics to a CSV file.
    """
    module_metrics = []
    for module_file in os.listdir(modules_dir):
        module_path = os.path.join(modules_dir, module_file)
        try:
            # cyclomatic complexity
            cc_output = subprocess.check_output(['radon', 'cc', module_path, '-s', '-j'], universal_newlines=True)
            cc_data = json.loads(cc_output)
            # raw metrics
            raw_output = subprocess.check_output(['radon', 'raw', module_path, '-j'], universal_newlines=True)
            raw_data = json.loads(raw_output)
            
            # Extracting cyclomatic complexity data
            blocks = cc_data.get(module_path, [])
            complexities = []
            n_functions = 0
            n_classes = 0
            
            for block in blocks:
                complexity = block.get('complexity', 0)
                complexities.append(complexity)
                if block['type'] == 'function' or block['type'] == 'method':
                    n_functions += 1
                elif block['type'] == 'class':
                    n_classes += 1
                    # Include complexities of methods in classes
                    methods = block.get('methods', [])
                    for method in methods:
                        method_complexity = method.get('complexity', 0)
                        complexities.append(method_complexity)
                        n_functions += 1  # Methods = functions within classes
                
            total_complexity = sum(complexities)
            num_blocks = len(complexities)
            if num_blocks > 0:
                avg_complexity = total_complexity / num_blocks
            else:
                avg_complexity = 0
            
            # Extract raw metrics
            metrics = raw_data.get(module_path, {})
            loc = metrics.get('loc', 0)
            lloc = metrics.get('lloc', 0)
            sloc = metrics.get('sloc', 0)
            comments = metrics.get('comments', 0)
            multi = metrics.get('multi', 0)
            blank = metrics.get('blank', 0)
            
            module_metrics.append({
                'Module': module_file,
                'Average Complexity': round(avg_complexity, 2),
                'Total Complexity': total_complexity,
                'Lines_of_Code-LOC': loc,
                'Logical_LOC': lloc,
                'Source_LOC': sloc,
                'Comment_Lines': comments,
                'Multi_Line_Strings': multi,
                'Blank_Lines': blank,
                'Functions': n_functions,
                'Classes': n_classes,
            })
        except Exception as e:
            print(f"Error analyzing {module_file}: {e}")
    # metrics to CSV
    df = pd.DataFrame(module_metrics)
    df.to_csv(output_csv, index=False)
    print(f"Metrics saved to {output_csv}")
    return df


def generate_plots(df):
    sns.set(style="whitegrid")

    # Plot Average Complexity vs LOC
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='Lines_of_Code-LOC', y='Average Complexity', hue='Module')
    plt.title('Average Complexity vs LOC')
    plt.xlabel('Lines of Code (LOC)')
    plt.ylabel('Average Cyclomatic Complexity')
    plt.legend([],[], frameon=False)  # Remove legend
    plt.tight_layout()
    plt.savefig('complexity_vs_loc.png')
    plt.close()
    print("Generated plot: complexity_vs_loc.png")

    # Plot Distribution of Average Complexity
    plt.figure(figsize=(10, 6))
    sns.histplot(df['Average Complexity'], bins=20, kde=True)
    plt.title('Distribution of Average Cyclomatic Complexity')
    plt.xlabel('Average Cyclomatic Complexity')
    plt.ylabel('Number of Modules')
    plt.tight_layout()
    plt.savefig('complexity_distribution.png')
    plt.close()
    print("Generated plot: complexity_distribution.png")

    # Plot LOC vs Number of Functions
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='Lines_of_Code-LOC', y='Functions', hue='Module')
    plt.title('Number of Functions vs LOC')
    plt.xlabel('Lines of Code (LOC)')
    plt.ylabel('Number of Functions')
    plt.legend([],[], frameon=False)  # Remove legend
    plt.tight_layout()
    plt.savefig('functions_vs_loc.png')
    plt.close()
    print("Generated plot: functions_vs_loc.png")

def generate_html_report(df):
    html_content = df.to_html(index=False)
    with open('module_metrics.html', 'w') as f:
        f.write('<html><head><title>Module Metrics Report</title></head><body>')
        f.write('<h1>Module Metrics Report</h1>')
        f.write(html_content)
        f.write('</body></html>')
    print("Generated HTML report: module_metrics.html")

def main():
    modules_dir = 'modules_to_analyze'
    output_csv = 'module_metrics.csv'
    df = analyze_modules_with_radon(modules_dir, output_csv)
    generate_plots(df)
    generate_html_report(df)

if __name__ == "__main__":
    main()

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

data = [
    {
        "function": "Fun-1",
        "min-coverage": "none",
        "med-coverage": "✓",
        "max-coverage": "none",
        "regression-of-coverage": {"max": "100%", "med": "93.3%", "min": "100.0%"}
    },
    {
        "function": "Fun-2",
        "min-coverage": "✓",
        "med-coverage": "✓",
        "max-coverage": "✓",
        "regression-of-coverage": {"max": "84.6%", "med": "92.3%", "min": "92.3%"}
    },
    {
        "function": "Fun-3",
        "min-coverage": "✓",
        "med-coverage": "x",
        "max-coverage": "✓",
        "regression-of-coverage": {"max": "97.6%", "med": "97.6%", "min": "97.6%"}
    },
    {
        "function": "Fun-4",
        "min-coverage": "x",
        "med-coverage": "✓",
        "max-coverage": "✓",
        "regression-of-coverage": {"max": "95.8%", "med": "95.8%", "min": "95.8%"}
    },
    {
        "function": "Fun-5",
        "min-coverage": "none",
        "med-coverage": "✓",
        "max-coverage": "✓",
        "regression-of-coverage": {"max": "95.8%", "med": "95.8%", "min": "100%"}
    },
    {
        "function": "Fun-6",
        "min-coverage": "✓",
        "med-coverage": "✓",
        "max-coverage": "✓",
        "regression-of-coverage": {"max": "95.8%", "med": "95.8%", "min": "95.8%"}
    },
    {
        "function": "Fun-7",
        "min-coverage": "✓",
        "med-coverage": "✓",
        "max-coverage": "✓",
        "regression-of-coverage": {"max": "97.0%", "med": "97.0%", "min": "97.0%"}
    },
    {
        "function": "Fun-8",
        "min-coverage": "✓",
        "med-coverage": "✓",
        "max-coverage": "✓",
        "regression-of-coverage": {"max": "61.5%", "med": "96.1%", "min": "96.1%"}
    },
    {
        "function": "Fun-9",
        "min-coverage": "✓",
        "med-coverage": "none",
        "max-coverage": "none",
        "regression-of-coverage": {"max": "100%", "med": "100%", "min": "50.0%"}
    },
    {
        "function": "Fun-10",
        "min-coverage": "none",
        "med-coverage": "✓",
        "max-coverage": "✓",
        "regression-of-coverage": {"max": "93.7%", "med": "93.7%", "min": "100.0%"}
    },
    {
        "function": "Fun-11",
        "min-coverage": "none",
        "med-coverage": "✓",
        "max-coverage": "none",
        "regression-of-coverage": {"max": "100%", "med": "91.6%", "min": "100.0%"}
    },
    {
        "function": "Fun-12",
        "min-coverage": "✓",
        "med-coverage": "✓",
        "max-coverage": "✓",
        "regression-of-coverage": {"max": "92.3%", "med": "92.3%", "min": "92.3%"}
    }
]


def parse_percentage(val):
    """Convert a string like '92.3%' to a float 92.3. If 'none', interpret as 100.0 (no drop)."""
    if not isinstance(val, str):
        return 100.0
    if val.lower() == "none":
        return 100.0
    return float(val.strip('%'))


def parse_attempt_status(status):
    """
    Convert '✓' to 1 (success in single attempt),
    'x' to 2 (needed multiple attempts),
    'none' means coverage did not drop, so treat as 0 or 1 (depends on your interpretation).
    """
    # You can define your own numeric encoding or keep it as a string for plotting.
    if status == "✓":
        return 1
    elif status == "x":
        return 2
    else:  # "none"
        return 0


# We will reshape the data for easier plotting
rows = []
for entry in data:
    fn = entry["function"]
    # Coverage statuses for min, med, max
    min_stat = parse_attempt_status(entry["min-coverage"])
    med_stat = parse_attempt_status(entry["med-coverage"])
    max_stat = parse_attempt_status(entry["max-coverage"])

    # Coverage regressions
    reg_max = parse_percentage(entry["regression-of-coverage"].get("max", "100%"))
    reg_med = parse_percentage(entry["regression-of-coverage"].get("med", "100%"))
    reg_min = parse_percentage(entry["regression-of-coverage"].get("min", "100%"))

    rows.append({
        "function": fn,
        "deleted_test_rank": "min",
        "attempt_status": min_stat,
        "coverage_after_deletion": reg_min
    })
    rows.append({
        "function": fn,
        "deleted_test_rank": "med",
        "attempt_status": med_stat,
        "coverage_after_deletion": reg_med
    })
    rows.append({
        "function": fn,
        "deleted_test_rank": "max",
        "attempt_status": max_stat,
        "coverage_after_deletion": reg_max
    })

df = pd.DataFrame(rows)

# Create a numeric index for 'Fun-1' ... 'Fun-12' to help with line plots
df['function_index'] = df['function'].str.extract(r'(\d+)').astype(int)

# Sort by function index
df.sort_values(by='function_index', inplace=True)


###############################################################################
# 1) Line Plot: Coverage Regression by Deleted Test Rank (min/med/max)
#    X-axis: function_index, Y-axis: coverage_after_deletion
###############################################################################
plt.figure(figsize=(8, 5))
for rank in ['min', 'med', 'max']:
    subset = df[df['deleted_test_rank'] == rank]
    plt.plot(
        subset['function_index'], 
        subset['coverage_after_deletion'],
        marker='o', 
        label=f'{rank}-coverage test deleted'
    )

plt.title("")
plt.xlabel("Function")
plt.ylabel("Coverage After Deletion (%)")
plt.ylim([0, 105])  # coverage can't exceed 100, but a bit of margin
plt.xticks(df['function_index'].unique())
plt.legend()
plt.grid(True)
plt.savefig("Test Coverage Rank vs total coverage drop.png", bbox_inches='tight')
plt.show()


###############################################################################
# 2) Line Plot: Single Attempt vs. Multiple Attempts
#    We'll interpret 'attempt_status' as:
#      0 => no coverage drop
#      1 => single attempt
#      2 => multiple attempts
#    X-axis: function_index, Y-axis: attempt_status
###############################################################################
plt.figure(figsize=(8, 5))
for rank in ['min', 'med', 'max']:
    subset = df[df['deleted_test_rank'] == rank]
    plt.plot(
        subset['function_index'], 
        subset['attempt_status'],
        marker='o', 
        label=f'{rank}-coverage test deletion'
    )

plt.title("")
plt.xlabel("Function")
plt.ylabel("Attempts")
plt.xticks(df['function_index'].unique())
plt.yticks([0, 1, 2], ["No Effect", "Single", "Multi"])
plt.legend()
plt.grid(True)
plt.savefig("Attempts vs Test Coverage Rank.png", bbox_inches='tight')
plt.show()

###############################################################################
# 3) Success Rate by Coverage Rank
#    Plot: Bar chart or line chart of success rate for min/med/max
#    success rate = # with attempt_status=1 / (# with attempt_status=1 or 2)
###############################################################################
# We'll exclude attempt_status=0 since that's 'none'.

# Prepare data
rank_levels = ['min', 'med', 'max']
success_rates = []

for rank in rank_levels:
    sub = df[df['deleted_test_rank'] == rank]
    # Only consider rows with attempt_status in all {0,1,2}
    sub = sub[sub['attempt_status'] >= 0]
    if len(sub) == 0:
        # No data for this rank at all
        success_rates.append(0.0)
    else:
        single_attempts = (sub['attempt_status'] == 1).sum()
        no_effect = (sub['attempt_status'] == 0).sum()
        total = len(sub)
        rate = (single_attempts + no_effect) / total * 100.0
        success_rates.append(rate)

plt.figure(figsize=(6, 4))
plt.plot(rank_levels, success_rates, marker='o', linestyle='-')
plt.title("")
plt.xlabel("Coverage Rank of Deleted Test")
plt.ylabel("Single Attempt Success Rate (%)")
plt.ylim([0, 105])
plt.grid(True)
plt.savefig("Success Rate (Single-Attempt) by Coverage Rank.png", bbox_inches='tight')
plt.show()

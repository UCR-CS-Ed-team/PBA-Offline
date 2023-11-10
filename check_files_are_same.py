import pandas as pd

file_prefixes = ['quickanalysis', 'basic-stats-roster', 'anomalies']

for prefix in file_prefixes:
    pre = pd.read_csv(f'output_testing/{prefix}-pre.csv')
    post = pd.read_csv(f'output_testing/{prefix}-post.csv')

    if pre.equals(post):
        print(f'✓ The {prefix} files are the same.')
    else:
        print(f'✗ The {prefix} files are different:')
        print(pre.compare(post))

import pandas as pd

file_prefixes = ['quickanalysis', 'basic_stats_roster', 'anomalies']

for prefix in file_prefixes:
	df1 = pd.read_csv(f'output_testing/{prefix}-pre.csv')
	df2 = pd.read_csv(f'output_testing/{prefix}-post.csv')

	if df1.equals(df2):
		print(f'✓ The {prefix} files are the same.')
	else:
		print(f'✗ The {prefix} files are different.')

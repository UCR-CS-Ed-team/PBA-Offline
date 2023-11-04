import os
import re
from tkinter import filedialog

import pandas as pd

from tools.utilities import (
	create_data_structure,
	download_code,
	get_selected_labs,
	write_output_to_csv,
)

use_standalone = False

# Primary anomaly regular expressions
POINTERS_REGEX = (
	r'((?:\(+)?(?:int|char|string|void|bool|float|double)(?:\)+)?(?:\s+)?\*{1,2}(?:\s+)?\w+(?:\s+)?\=?.*\;$)'
)
INFINITE_LOOP_REGEX = r'((while(?:\s+)?\((?:true|1)\))|(for(?:\s+)?\(;;\)))'
ATYPICAL_INCLUDE_REGEX = r'(#(?:\s+)?include(?:\s+)?<(?:iomanip|algorithm|utility|limits|stdio)>)'
ATYPICAL_KEYWORD_REGEX = r"""
	((break(?:\s+)?;)
	|(switch(?:\s+)?\(\w+\)(?:\s+)?{)
	|(continue(?:\s+)?;)
	|(sizeof\(\w+\))
	|(case\s+\S+(?:\s+)?:)
	|(\.erase(?:\s+)?\(.*\)))
	"""
BRACE_STYLING_REGEX = r"""
	((?P<leftbrace>^(?:\s+)?{)
	|(?P<rightbrace>\S+;(?:\s+)?})
	|(?P<oneline>(?:if|for)(?:\s+)?\(.+\)(?:\s+)?\S+.*;)
	|(?P<else1>}(?:\s+)?else)
	|(?P<else2>else\s\S+.*;))
	"""
ARRAY_ACCESSES_REGEX = r'(\w+\[.*\])'
NAMESPACE_STD_REGEX = r'(std::)'
ESCAPED_NEWLINE_REGEX = r'(\\n)'
USER_DEFINED_FUNCTIONS_REGEX = (
	r'(^(?:\s+)?(?:(?:unsigned|signed|long|short)\s)?(?:int|char|string|void|bool|float|double)\s\w+\(.*\))'
)
TERNARY_OPERATOR_REGEX = r'(.+\s\?\s.+\s\:\s.+)'
COMMAND_LINE_ARGUMENTS_REGEX = r'(main\(\s?int argc,\s?(?:char\s?\*\s?argv\[\])|(?:char\s?\*\*\s?argv))\s?\)'
NULLS_REGEX = r'(NULL|nullptr|\\0)'
SCOPE_OPERATOR_REGEX = r'(\w+::\w+)'
LINE_SPACING_REGEX = r'(^\S+)'
MULTIPLE_DECLARATIONS_REGEX = r'((?:int|char|string|void|bool|float|double)\s+\w+[^\"\']+(?:\s+)?,(?:\s+)?\w+.*;)'
MULTIPLE_CIN_SAME_LINE_REGEX = r'(cin(?:\s+)?>>(?:\s+)?\w+(?:\s+)?>>)'
AND_OR_REGEX = r'(if(?:\s+)?\([^\"\']+\s+(?:and|or)\s+[^\"\']+\))'
LIST_INIT_REGEX = r'((?:int|char|string|void|bool|float|double)\s+\w+(?:\s+)?{.*};)'
VECTOR_NAME_SPACING_REGEX = r'(vector<.+>\w+)'
SPACELESS_OPERATOR_REGEX = (
	r'([\w\]\)]+(?:>|>=|<|<=|=|==|!=|<<|>>|\+|-|\+=|-=|\*|/|%|&&|\|\|)[\w\[\(]+(?![^<<]*(?:\"|\')))'
)
CONTROL_STATEMENT_SPACING_REGEX = r'((?:if|for|while)\(.*\))'
MAIN_VOID_REGEX = r'(int main\(void\))'
ACCESS_AND_INCREMENT_REGEX = r"""
	((?P<arrays>\w+\[(?:\w+\+\+|\w+--|\+\+\w+|--\w+)\])
	|(?P<vectors>\w+\.at\((?:\w+\+\+|\w+--|\+\+\w+|--\w+)\)))
	"""
AUTO_REGEX = r'(auto\s\w+)'
SET_PRECISION_REGEX = r'cout(?:\s+)?<<(?:\s+)?setprecision\(.+\)(?:\s+)?<<(?:\s+)?fixed'
RANGED_BASED_LOOP_REGEX = r'(for\s*\(\s*\w+\s+\w+\s+:\s+\w+\s*\))'
ITERATOR_FUNCTIONS_REGEX = r'(\w+\.(?:begin|end)\(\))'
MAX_MIN_MACRO_REGEX = r'(INT_MAX|INT_MIN)'
SWAP_FUNCTION_REGEX = r'(swap\(.*\))'
CIN_INSIDE_WHILE_REGEX = r'(while\s*\(.*cin\s*>>\s*\w+.*\))'

# Helper regular expressions
INT_MAIN_REGEX = r'int main(?:\s+)?\(.*\)'
LEFT_BRACE_REGEX = r'({)'
RIGHT_BRACE_REGEX = r'(})'
FORWARD_DEC_REGEX = r'(^(?:(?:unsigned|signed|long|short)\s)?(?:int|char|string|void|bool|float|double)\s\w+\(.*\);)'


def get_anomaly_score(code, auto=0):
	# Below is the format for the anomaly in question
	# [Count_instances, points/instance, anomaly on/off, regex, count of instances, instance cap (-1 for no cap)]
	# Add to the hashmap Styleanomaly in case you need new anomaly to be detected
	Styleanomaly = {
		'Pointers': {0: 1, 1: 0.9, 2: 1, 3: POINTERS_REGEX, 4: 0, 5: -1},
		'Infinite_loop': {0: 1, 1: 0.9, 2: 1, 3: INFINITE_LOOP_REGEX, 4: 0, 5: -1},
		'Atypical Includes': {0: 1, 1: 0.1, 2: 1, 3: ATYPICAL_INCLUDE_REGEX, 4: 0, 5: -1},
		'Atypical Keywords': {0: 1, 1: 0.3, 2: 1, 3: ATYPICAL_KEYWORD_REGEX, 4: 0, 5: -1},
		'Array Accesses': {0: 1, 1: 0.9, 2: 1, 3: ARRAY_ACCESSES_REGEX, 4: 0, 5: -1},
		'Namespace Std': {0: 1, 1: 0.1, 2: 1, 3: NAMESPACE_STD_REGEX, 4: 0, 5: -1},
		'Brace Styling': {0: 1, 1: 0.1, 2: 1, 3: BRACE_STYLING_REGEX, 4: 0, 5: -1},
		'Escaped Newline': {0: 1, 1: 0.1, 2: 1, 3: ESCAPED_NEWLINE_REGEX, 4: 0, 5: -1},
		'User-Defined Functions': {0: 1, 1: 0.8, 2: 0, 3: USER_DEFINED_FUNCTIONS_REGEX, 4: 0, 5: -1},
		'Ternary Operator': {0: 1, 1: 0.2, 2: 1, 3: TERNARY_OPERATOR_REGEX, 4: 0, 5: -1},
		'Command-Line Arguments': {0: 1, 1: 0.8, 2: 1, 3: COMMAND_LINE_ARGUMENTS_REGEX, 4: 0, 5: -1},
		'Nulls': {0: 1, 1: 0.4, 2: 1, 3: NULLS_REGEX, 4: 0, 5: -1},
		'Scope Operator': {0: 1, 1: 0.25, 2: 1, 3: SCOPE_OPERATOR_REGEX, 4: 0, 5: -1},
		'Line Spacing': {0: 1, 1: 0.1, 2: 1, 3: LINE_SPACING_REGEX, 4: 0, 5: -1},
		'Multiple Declarations Same Line': {0: 1, 1: 0.3, 2: 1, 3: MULTIPLE_DECLARATIONS_REGEX, 4: 0, 5: -1},
		'Multiple Cin Same Line': {0: 1, 1: 0.3, 2: 1, 3: MULTIPLE_CIN_SAME_LINE_REGEX, 4: 0, 5: -1},
		'and & or': {0: 1, 1: 0.1, 2: 1, 3: AND_OR_REGEX, 4: 0, 5: -1},
		'List Initialization': {0: 1, 1: 0.8, 2: 1, 3: LIST_INIT_REGEX, 4: 0, 5: -1},
		'Vector Name Spacing': {0: 1, 1: 0.1, 2: 1, 3: VECTOR_NAME_SPACING_REGEX, 4: 0, 5: -1},
		'Spaceless Operator': {0: 1, 1: 0.1, 2: 1, 3: SPACELESS_OPERATOR_REGEX, 4: 0, 5: -1},
		'Control Statement Spacing': {0: 1, 1: 0.1, 2: 1, 3: CONTROL_STATEMENT_SPACING_REGEX, 4: 0, 5: -1},
		'Main Void': {0: 1, 1: 0.5, 2: 1, 3: MAIN_VOID_REGEX, 4: 0, 5: -1},
		'Access And Increment': {0: 1, 1: 0.2, 2: 1, 3: ACCESS_AND_INCREMENT_REGEX, 4: 0, 5: -1},
		'Auto': {0: 1, 1: 0.3, 2: 1, 3: AUTO_REGEX, 4: 0, 5: -1},
		'zyBooks Set Precision': {0: 1, 1: 0.2, 2: 1, 3: SET_PRECISION_REGEX, 4: 0, 5: -1},
		'Ranged-Based for Loop': {0: 1, 1: 0.6, 2: 1, 3: RANGED_BASED_LOOP_REGEX, 4: 0, 5: -1},
		'Iterator Functions': {0: 1, 1: 0.3, 2: 1, 3: ITERATOR_FUNCTIONS_REGEX, 4: 0, 5: -1},
		'Max Min Macros': {0: 1, 1: 0.3, 2: 1, 3: MAX_MIN_MACRO_REGEX, 4: 0, 5: -1},
		'Swap Function': {0: 1, 1: 0.6, 2: 1, 3: SWAP_FUNCTION_REGEX, 4: 0, 5: -1},
		'Cin Inside While': {0: 1, 1: 0.6, 2: 1, 3: CIN_INSIDE_WHILE_REGEX, 4: 0, 5: -1},
	}

	anomaly_score = 0  # Initial anomaly Score
	anomalies_found = 0  # Counts the number of anamolies found
	checkLineSpacing = False  # Indicates whether to check for Line Spacing anomaly
	leftBraceCount = 0  # Count of left braces for Line Spacing anomaly
	rightBraceCount = 0  # Count of right braces for Line Spacing anomaly
	openingBrace = False  # Indicates if `line` is the opening brace for the function on its own line

	# For automatic anomaly detection, enable every anomaly
	if auto == 1:
		for anomaly in Styleanomaly:
			Styleanomaly[anomaly][2] = 1

	lines = code.splitlines()
	for i, line in enumerate(lines):  # Reading through lines in the code and checking for each anomaly
		if Styleanomaly['Pointers'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Pointers'][3], line):
				if Styleanomaly['Pointers'][0] == 1 or (
					Styleanomaly['Pointers'][0] == 0 and Styleanomaly['Pointers'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Pointers'][5] <= -1) or (
						Styleanomaly['Pointers'][5] > -1 and (Styleanomaly['Pointers'][4] < Styleanomaly['Pointers'][5])
					):
						anomaly_score += Styleanomaly['Pointers'][1]
					Styleanomaly['Pointers'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Infinite_loop'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Infinite_loop'][3], line):
				if Styleanomaly['Infinite_loop'][0] == 1 or (
					Styleanomaly['Infinite_loop'][0] == 0 and Styleanomaly['Infinite_loop'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Infinite_loop'][5] <= -1) or (
						Styleanomaly['Infinite_loop'][5] > -1
						and (Styleanomaly['Infinite_loop'][4] < Styleanomaly['Infinite_loop'][5])
					):
						anomaly_score += Styleanomaly['Infinite_loop'][1]
					Styleanomaly['Infinite_loop'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Atypical Includes'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Atypical Includes'][3], line):
				if Styleanomaly['Atypical Includes'][0] == 1 or (
					Styleanomaly['Atypical Includes'][0] == 0 and Styleanomaly['Atypical Includes'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Atypical Includes'][5] <= -1) or (
						Styleanomaly['Atypical Includes'][5] > -1
						and (Styleanomaly['Atypical Includes'][4] < Styleanomaly['Atypical Includes'][5])
					):
						anomaly_score += Styleanomaly['Atypical Includes'][1]
					Styleanomaly['Atypical Includes'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Atypical Keywords'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Atypical Keywords'][3], line, flags=re.X):
				if Styleanomaly['Atypical Keywords'][0] == 1 or (
					Styleanomaly['Atypical Keywords'][0] == 0 and Styleanomaly['Atypical Keywords'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Atypical Keywords'][5] <= -1) or (
						Styleanomaly['Atypical Keywords'][5] > -1
						and (Styleanomaly['Atypical Keywords'][4] < Styleanomaly['Atypical Keywords'][5])
					):
						anomaly_score += Styleanomaly['Atypical Keywords'][1]
					Styleanomaly['Atypical Keywords'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Array Accesses'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Array Accesses'][3], line):
				if Styleanomaly['Array Accesses'][0] == 1 or (
					Styleanomaly['Array Accesses'][0] == 0 and Styleanomaly['Array Accesses'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Array Accesses'][5] <= -1) or (
						Styleanomaly['Array Accesses'][5] > -1
						and (Styleanomaly['Array Accesses'][4] < Styleanomaly['Array Accesses'][5])
					):
						anomaly_score += Styleanomaly['Array Accesses'][1]
					Styleanomaly['Array Accesses'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Namespace Std'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Namespace Std'][3], line):
				if Styleanomaly['Namespace Std'][0] == 1 or (
					Styleanomaly['Namespace Std'][0] == 0 and Styleanomaly['Namespace Std'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Namespace Std'][5] <= -1) or (
						Styleanomaly['Namespace Std'][5] > -1
						and (Styleanomaly['Namespace Std'][4] < Styleanomaly['Namespace Std'][5])
					):
						anomaly_score += Styleanomaly['Namespace Std'][1]
					Styleanomaly['Namespace Std'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Brace Styling'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Brace Styling'][3], line, flags=re.X):
				if Styleanomaly['Brace Styling'][0] == 1 or (
					Styleanomaly['Brace Styling'][0] == 0 and Styleanomaly['Brace Styling'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Brace Styling'][5] <= -1) or (
						Styleanomaly['Brace Styling'][5] > -1
						and (Styleanomaly['Brace Styling'][4] < Styleanomaly['Brace Styling'][5])
					):
						anomaly_score += Styleanomaly['Brace Styling'][1]
					Styleanomaly['Brace Styling'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Escaped Newline'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Escaped Newline'][3], line):
				if Styleanomaly['Escaped Newline'][0] == 1 or (
					Styleanomaly['Escaped Newline'][0] == 0 and Styleanomaly['Escaped Newline'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Escaped Newline'][5] <= -1) or (
						Styleanomaly['Escaped Newline'][5] > -1
						and (Styleanomaly['Escaped Newline'][4] < Styleanomaly['Escaped Newline'][5])
					):
						anomaly_score += Styleanomaly['Escaped Newline'][1]
					Styleanomaly['Escaped Newline'][4] += 1
					anomalies_found += 1

		if Styleanomaly['User-Defined Functions'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['User-Defined Functions'][3], line) and not line.__contains__('main()'):
				if Styleanomaly['User-Defined Functions'][0] == 1 or (
					Styleanomaly['User-Defined Functions'][0] == 0 and Styleanomaly['User-Defined Functions'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['User-Defined Functions'][5] <= -1) or (
						Styleanomaly['User-Defined Functions'][5] > -1
						and (Styleanomaly['User-Defined Functions'][4] < Styleanomaly['User-Defined Functions'][5])
					):
						anomaly_score += Styleanomaly['User-Defined Functions'][1]
					Styleanomaly['User-Defined Functions'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Ternary Operator'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Ternary Operator'][3], line):
				if Styleanomaly['Ternary Operator'][0] == 1 or (
					Styleanomaly['Ternary Operator'][0] == 0 and Styleanomaly['Ternary Operator'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Ternary Operator'][5] <= -1) or (
						Styleanomaly['Ternary Operator'][5] > -1
						and (Styleanomaly['Ternary Operator'][4] < Styleanomaly['Ternary Operator'][5])
					):
						anomaly_score += Styleanomaly['Ternary Operator'][1]
					Styleanomaly['Ternary Operator'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Command-Line Arguments'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Command-Line Arguments'][3], line):
				if Styleanomaly['Command-Line Arguments'][0] == 1 or (
					Styleanomaly['Command-Line Arguments'][0] == 0 and Styleanomaly['Command-Line Arguments'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Command-Line Arguments'][5] <= -1) or (
						Styleanomaly['Command-Line Arguments'][5] > -1
						and (Styleanomaly['Command-Line Arguments'][4] < Styleanomaly['Command-Line Arguments'][5])
					):
						anomaly_score += Styleanomaly['Command-Line Arguments'][1]
					Styleanomaly['Command-Line Arguments'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Nulls'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Nulls'][3], line):
				if Styleanomaly['Nulls'][0] == 1 or (Styleanomaly['Nulls'][0] == 0 and Styleanomaly['Nulls'][4] == 0):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Nulls'][5] <= -1) or (
						Styleanomaly['Nulls'][5] > -1 and (Styleanomaly['Nulls'][4] < Styleanomaly['Nulls'][5])
					):
						anomaly_score += Styleanomaly['Nulls'][1]
					Styleanomaly['Nulls'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Scope Operator'][2] != 0:  # Check if the anomaly is turned on
			if (
				re.search(Styleanomaly['Scope Operator'][3], line)
				and not line.__contains__('string::npos')
				and not line.__contains__('std::')
			):
				if Styleanomaly['Scope Operator'][0] == 1 or (
					Styleanomaly['Scope Operator'][0] == 0 and Styleanomaly['Scope Operator'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Scope Operator'][5] <= -1) or (
						Styleanomaly['Scope Operator'][5] > -1
						and (Styleanomaly['Scope Operator'][4] < Styleanomaly['Scope Operator'][5])
					):
						anomaly_score += Styleanomaly['Scope Operator'][1]
					Styleanomaly['Scope Operator'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Max Min Macros'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Max Min Macros'][3], line):
				if Styleanomaly['Max Min Macros'][0] == 1 or (
					Styleanomaly['Max Min Macros'][0] == 0 and Styleanomaly['Max Min Macros'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Max Min Macros'][5] <= -1) or (
						Styleanomaly['Max Min Macros'][5] > -1
						and (Styleanomaly['Max Min Macros'][4] < Styleanomaly['Max Min Macros'][5])
					):
						anomaly_score += Styleanomaly['Max Min Macros'][1]
					Styleanomaly['Max Min Macros'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Swap Function'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Swap Function'][3], line):
				if Styleanomaly['Swap Function'][0] == 1 or (
					Styleanomaly['Swap Function'][0] == 0 and Styleanomaly['Swap Function'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Swap Function'][5] <= -1) or (
						Styleanomaly['Swap Function'][5] > -1
						and (Styleanomaly['Swap Function'][4] < Styleanomaly['Swap Function'][5])
					):
						anomaly_score += Styleanomaly['Swap Function'][1]
					Styleanomaly['Swap Function'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Cin Inside While'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Cin Inside While'][3], line):
				if Styleanomaly['Cin Inside While'][0] == 1 or (
					Styleanomaly['Cin Inside While'][0] == 0 and Styleanomaly['Cin Inside While'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Cin Inside While'][5] <= -1) or (
						Styleanomaly['Cin Inside While'][5] > -1
						and (Styleanomaly['Cin Inside While'][4] < Styleanomaly['Cin Inside While'][5])
					):
						anomaly_score += Styleanomaly['Cin Inside While'][1]
					Styleanomaly['Cin Inside While'][4] += 1
					anomalies_found += 1

		# "Line Spacing" should only check lines inside main() and user functions
		lineIsMain = re.search(INT_MAIN_REGEX, line)
		lineIsUserFunc = re.search(USER_DEFINED_FUNCTIONS_REGEX, line)
		lineIsForwardDec = re.search(FORWARD_DEC_REGEX, line)
		if (lineIsMain or lineIsUserFunc) and not lineIsForwardDec:
			checkLineSpacing = True

		# Keep track of how many left and right braces we've seen
		if re.search(LEFT_BRACE_REGEX, line) and checkLineSpacing:
			leftBraceCount += 1
		if re.search(RIGHT_BRACE_REGEX, line) and checkLineSpacing:
			rightBraceCount += 1

		# If brace counts match, we've seen the whole main() or user function
		if (leftBraceCount == rightBraceCount) and leftBraceCount > 0:
			checkLineSpacing = False
			leftBraceCount = 0
			rightBraceCount = 0

		# Check if we're looking at the opening brace for a function on its own line
		# If we are, skip it- it's a Brace Styling anomaly, not a Line Spacing anomaly
		if re.search(LEFT_BRACE_REGEX, line) and (
			re.search(INT_MAIN_REGEX, lines[i - 1]) or re.search(USER_DEFINED_FUNCTIONS_REGEX, lines[i - 1])
		):
			openingBrace = True
		else:
			openingBrace = False

		if (
			Styleanomaly['Line Spacing'][2] != 0
			and checkLineSpacing
			and not lineIsMain
			and not lineIsUserFunc
			and not openingBrace
			and (leftBraceCount >= 1)
		):  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Line Spacing'][3], line):
				if Styleanomaly['Line Spacing'][0] == 1 or (
					Styleanomaly['Line Spacing'][0] == 0 and Styleanomaly['Line Spacing'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Line Spacing'][5] <= -1) or (
						Styleanomaly['Line Spacing'][5] > -1
						and (Styleanomaly['Line Spacing'][4] < Styleanomaly['Line Spacing'][5])
					):
						anomaly_score += Styleanomaly['Line Spacing'][1]
					Styleanomaly['Line Spacing'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Multiple Declarations Same Line'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Multiple Declarations Same Line'][3], line):
				if Styleanomaly['Multiple Declarations Same Line'][0] == 1 or (
					Styleanomaly['Multiple Declarations Same Line'][0] == 0
					and Styleanomaly['Multiple Declarations Same Line'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Multiple Declarations Same Line'][5] <= -1) or (
						Styleanomaly['Multiple Declarations Same Line'][5] > -1
						and (
							Styleanomaly['Multiple Declarations Same Line'][4]
							< Styleanomaly['Multiple Declarations Same Line'][5]
						)
					):
						anomaly_score += Styleanomaly['Multiple Declarations Same Line'][1]
					Styleanomaly['Multiple Declarations Same Line'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Multiple Cin Same Line'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Multiple Cin Same Line'][3], line):
				if Styleanomaly['Multiple Cin Same Line'][0] == 1 or (
					Styleanomaly['Multiple Cin Same Line'][0] == 0 and Styleanomaly['Multiple Cin Same Line'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Multiple Cin Same Line'][5] <= -1) or (
						Styleanomaly['Multiple Cin Same Line'][5] > -1
						and (Styleanomaly['Multiple Cin Same Line'][4] < Styleanomaly['Multiple Cin Same Line'][5])
					):
						anomaly_score += Styleanomaly['Multiple Cin Same Line'][1]
					Styleanomaly['Multiple Cin Same Line'][4] += 1
					anomalies_found += 1

		if Styleanomaly['and & or'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['and & or'][3], line):
				if Styleanomaly['and & or'][0] == 1 or (
					Styleanomaly['and & or'][0] == 0 and Styleanomaly['and & or'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['and & or'][5] <= -1) or (
						Styleanomaly['and & or'][5] > -1 and (Styleanomaly['and & or'][4] < Styleanomaly['and & or'][5])
					):
						anomaly_score += Styleanomaly['and & or'][1]
					Styleanomaly['and & or'][4] += 1
					anomalies_found += 1

		if Styleanomaly['List Initialization'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['List Initialization'][3], line):
				if Styleanomaly['List Initialization'][0] == 1 or (
					Styleanomaly['List Initialization'][0] == 0 and Styleanomaly['List Initialization'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['List Initialization'][5] <= -1) or (
						Styleanomaly['List Initialization'][5] > -1
						and (Styleanomaly['List Initialization'][4] < Styleanomaly['List Initialization'][5])
					):
						anomaly_score += Styleanomaly['List Initialization'][1]
					Styleanomaly['List Initialization'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Vector Name Spacing'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Vector Name Spacing'][3], line):
				if Styleanomaly['Vector Name Spacing'][0] == 1 or (
					Styleanomaly['Vector Name Spacing'][0] == 0 and Styleanomaly['Vector Name Spacing'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Vector Name Spacing'][5] <= -1) or (
						Styleanomaly['Vector Name Spacing'][5] > -1
						and (Styleanomaly['Vector Name Spacing'][4] < Styleanomaly['Vector Name Spacing'][5])
					):
						anomaly_score += Styleanomaly['Vector Name Spacing'][1]
					Styleanomaly['Vector Name Spacing'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Spaceless Operator'][2] != 0:  # Check if the anomaly is turned on
			match = re.search(Styleanomaly['Spaceless Operator'][3], line)
			if match and '#include' not in line and 'vector<' not in match.group():
				if Styleanomaly['Spaceless Operator'][0] == 1 or (
					Styleanomaly['Spaceless Operator'][0] == 0 and Styleanomaly['Spaceless Operator'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Spaceless Operator'][5] <= -1) or (
						Styleanomaly['Spaceless Operator'][5] > -1
						and (Styleanomaly['Spaceless Operator'][4] < Styleanomaly['Spaceless Operator'][5])
					):
						anomaly_score += Styleanomaly['Spaceless Operator'][1]
					Styleanomaly['Spaceless Operator'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Control Statement Spacing'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Control Statement Spacing'][3], line):
				if Styleanomaly['Control Statement Spacing'][0] == 1 or (
					Styleanomaly['Control Statement Spacing'][0] == 0
					and Styleanomaly['Control Statement Spacing'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Control Statement Spacing'][5] <= -1) or (
						Styleanomaly['Control Statement Spacing'][5] > -1
						and (
							Styleanomaly['Control Statement Spacing'][4] < Styleanomaly['Control Statement Spacing'][5]
						)
					):
						anomaly_score += Styleanomaly['Control Statement Spacing'][1]
					Styleanomaly['Control Statement Spacing'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Main Void'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Main Void'][3], line):
				if Styleanomaly['Main Void'][0] == 1 or (
					Styleanomaly['Main Void'][0] == 0 and Styleanomaly['Main Void'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Main Void'][5] <= -1) or (
						Styleanomaly['Main Void'][5] > -1
						and (Styleanomaly['Main Void'][4] < Styleanomaly['Main Void'][5])
					):
						anomaly_score += Styleanomaly['Main Void'][1]
					Styleanomaly['Main Void'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Access And Increment'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Access And Increment'][3], line, flags=re.X):
				if Styleanomaly['Access And Increment'][0] == 1 or (
					Styleanomaly['Access And Increment'][0] == 0 and Styleanomaly['Access And Increment'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Access And Increment'][5] <= -1) or (
						Styleanomaly['Access And Increment'][5] > -1
						and (Styleanomaly['Access And Increment'][4] < Styleanomaly['Access And Increment'][5])
					):
						anomaly_score += Styleanomaly['Access And Increment'][1]
					Styleanomaly['Access And Increment'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Auto'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Auto'][3], line):
				if Styleanomaly['Auto'][0] == 1 or (Styleanomaly['Auto'][0] == 0 and Styleanomaly['Auto'][4] == 0):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Auto'][5] <= -1) or (
						Styleanomaly['Auto'][5] > -1 and (Styleanomaly['Auto'][4] < Styleanomaly['Auto'][5])
					):
						anomaly_score += Styleanomaly['Auto'][1]
					Styleanomaly['Auto'][4] += 1
					anomalies_found += 1

		if Styleanomaly['zyBooks Set Precision'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['zyBooks Set Precision'][3], line):
				if Styleanomaly['zyBooks Set Precision'][0] == 1 or (
					Styleanomaly['zyBooks Set Precision'][0] == 0 and Styleanomaly['zyBooks Set Precision'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['zyBooks Set Precision'][5] <= -1) or (
						Styleanomaly['zyBooks Set Precision'][5] > -1
						and (Styleanomaly['zyBooks Set Precision'][4] < Styleanomaly['zyBooks Set Precision'][5])
					):
						anomaly_score += Styleanomaly['zyBooks Set Precision'][1]
					Styleanomaly['zyBooks Set Precision'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Ranged-Based for Loop'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Ranged-Based for Loop'][3], line):
				if Styleanomaly['Ranged-Based for Loop'][0] == 1 or (
					Styleanomaly['Ranged-Based for Loop'][0] == 0 and Styleanomaly['Ranged-Based for Loop'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Ranged-Based for Loop'][5] <= -1) or (
						Styleanomaly['Ranged-Based for Loop'][5] > -1
						and (Styleanomaly['Ranged-Based for Loop'][4] < Styleanomaly['Ranged-Based for Loop'][5])
					):
						anomaly_score += Styleanomaly['Ranged-Based for Loop'][1]
					Styleanomaly['Ranged-Based for Loop'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Iterator Functions'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Iterator Functions'][3], line):
				if Styleanomaly['Iterator Functions'][0] == 1 or (
					Styleanomaly['Iterator Functions'][0] == 0 and Styleanomaly['Iterator Functions'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Iterator Functions'][5] <= -1) or (
						Styleanomaly['Iterator Functions'][5] > -1
						and (Styleanomaly['Iterator Functions'][4] < Styleanomaly['Iterator Functions'][5])
					):
						anomaly_score += Styleanomaly['Iterator Functions'][1]
					Styleanomaly['Iterator Functions'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Max Min Macros'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Max Min Macros'][3], line):
				if Styleanomaly['Max Min Macros'][0] == 1 or (
					Styleanomaly['Max Min Macros'][0] == 0 and Styleanomaly['Max Min Macros'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Max Min Macros'][5] <= -1) or (
						Styleanomaly['Max Min Macros'][5] > -1
						and (Styleanomaly['Max Min Macros'][4] < Styleanomaly['Max Min Macros'][5])
					):
						anomaly_score += Styleanomaly['Max Min Macros'][1]
					Styleanomaly['Max Min Macros'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Swap Function'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Swap Function'][3], line):
				if Styleanomaly['Swap Function'][0] == 1 or (
					Styleanomaly['Swap Function'][0] == 0 and Styleanomaly['Swap Function'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Swap Function'][5] <= -1) or (
						Styleanomaly['Swap Function'][5] > -1
						and (Styleanomaly['Swap Function'][4] < Styleanomaly['Swap Function'][5])
					):
						anomaly_score += Styleanomaly['Swap Function'][1]
					Styleanomaly['Swap Function'][4] += 1
					anomalies_found += 1

		if Styleanomaly['Cin Inside While'][2] != 0:  # Check if the anomaly is turned on
			if re.search(Styleanomaly['Cin Inside While'][3], line):
				if Styleanomaly['Cin Inside While'][0] == 1 or (
					Styleanomaly['Cin Inside While'][0] == 0 and Styleanomaly['Cin Inside While'][4] == 0
				):
					# Score for this anomaly is capped to Styleanomaly[x][5] instances
					if (Styleanomaly['Cin Inside While'][5] <= -1) or (
						Styleanomaly['Cin Inside While'][5] > -1
						and (Styleanomaly['Cin Inside While'][4] < Styleanomaly['Cin Inside While'][5])
					):
						anomaly_score += Styleanomaly['Cin Inside While'][1]
					Styleanomaly['Cin Inside While'][4] += 1
					anomalies_found += 1

	# For automatic anomaly detection, return *which* anomalies were found
	if auto == 1:
		anomalies_found = {}
		for anomaly in Styleanomaly:
			anomalies_found[anomaly] = Styleanomaly[anomaly][4]

	return anomalies_found, anomaly_score


def anomaly(data, selected_labs, auto=0):  # Function to calculate the anomaly score
	output = {}
	for lab in selected_labs:
		for user_id in data:
			if user_id not in output:
				output[user_id] = {}

			if lab in data[user_id]:
				max_score = 0
				code = data[user_id][lab][-1].code  # Choose a default submission
				for sub in data[user_id][lab]:
					if sub.max_score > max_score:
						max_score = sub.max_score
						code = sub.code

				anomalies_found, anomaly_score = get_anomaly_score(code, auto)
				output[user_id][lab] = [anomalies_found, anomaly_score, code]
	return output


##############################
#           Control          #
##############################
if use_standalone:
	# logfile_path = input("Enter the path to the logfile: ")
	# logfile_path = '/Users/abhinavreddy/Downloads/standalone_incdev_analysis/input/logfile.csv'
	file_path = filedialog.askopenfilename()
	folder_path = os.path.split(file_path)[0]
	file_name = os.path.basename(file_path).split('/')[-1]
	logfile = pd.read_csv(file_path)
	logfile = logfile[logfile.role == 'Student']

	# Update column names if necessary
	# Enables support for log files from learn.zybooks.com and Mode
	logfile.columns = logfile.columns.str.replace('\(US/Pacific\)', '', regex=True)
	logfile.columns = logfile.columns.str.replace('is_submission', 'submission')
	logfile.columns = logfile.columns.str.replace('content_resource_id', 'lab_id')

	selected_labs = get_selected_labs(logfile)
	print('Processing ' + file_name)
	logfile = download_code(logfile)
	data = create_data_structure(logfile)

	final_roster = {}
	anomaly_detection_output = anomaly(data, selected_labs)
	for user_id in anomaly_detection_output:
		for lab in anomaly_detection_output[user_id]:
			anomalies_found = anomaly_detection_output[user_id][lab][0]
			anomaly_score = anomaly_detection_output[user_id][lab][1]
			if user_id in final_roster:
				final_roster[user_id]['Lab ' + str(lab) + ' anomalies found'] = anomalies_found
				final_roster[user_id]['Lab ' + str(lab) + ' anomaly score'] = anomaly_score
				final_roster[user_id]['Lab ' + str(lab) + ' student code'] = anomaly_detection_output[user_id][lab][2]
			else:
				final_roster[user_id] = {
					'User ID': user_id,
					'Last Name': data[user_id][lab][0].last_name[0],
					'First Name': data[user_id][lab][0].first_name[0],
					'Email': data[user_id][lab][0].email[0],
					'Role': 'Student',
					'Lab ' + str(lab) + ' anomalies found': anomalies_found,
					'Lab ' + str(lab) + ' anomaly score': anomaly_score,
					'Lab ' + str(lab) + ' student code': anomaly_detection_output[user_id][lab][2],
				}
	write_output_to_csv(final_roster)

import os
import re
from tkinter import filedialog
from typing import Tuple

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


class StyleAnomaly:
    """Represents a style anomaly.

    Attributes:
        name (str): The name of the style anomaly.
        regex (str): The regular expression used to match the anomaly in code.
        is_active (bool): Whether to check for the anomaly in code.
        weight (int): The points per instance of anomaly.
        max_instances (int): The maximum number of instances of the anomaly. -1 means no limit.
        verbose (bool): Whether to compile the anomaly's regex with the verbose flag or not.
                        Multi-line regular expressions need this to be true.
    """

    def __init__(
        self, name: str, regex: str, is_active: bool, weight: float, max_instances: int, verbose: bool = False
    ) -> None:
        self.name = name
        self.regex = re.compile(regex, re.VERBOSE if verbose else 0)
        self.is_active = is_active
        self.weight = weight
        self.num_instances = 0
        self.max_instances = max_instances

    def should_inc_score(self) -> bool:
        """Determines whether an anomaly score should be incremented by an anomaly's weight.

        Returns:
            bool: True if the anomaly is configured to count all instances,
                  OR if we have not yet counted the maximum number of instances of this anomaly. Else, false.
        """
        return self.max_instances == -1 or (self.max_instances > -1 and self.num_instances < self.max_instances)


def get_line_spacing_score(code: str, a: StyleAnomaly) -> Tuple[int, float]:
    """Computes number of anomalies and anomaly score for the Line Spacing anomaly.

    Line Spacing requires additional logic to determine where main() and user functions are.
    Because of this, we use a separate function just for this anomaly.
    We only count non-indented lines inside of main() or user-defined functions.
    If the student wrote the function's opening brace on its own line, we exclude that line.

    The Line Spacing anomaly is defined inside this function.

    Args:
        code (str): The student's code.

    Returns:
        Tuple[int, int]: A tuple containing the number of anomalies found and anomaly score for Line Spacing.
    """

    anomaly_score = 0
    num_anomalies_found = 0
    left_brace_count = 0
    right_brace_count = 0
    check_line_spacing = False  # Don't check for anomaly until we're in a function
    opening_brace = False  # Indicates if `line` is the opening brace for the function on its own line
    lines = code.splitlines()

    for i, line in enumerate(lines):
        # "Line Spacing" should only check lines inside main() and user functions
        line_is_main = re.search(INT_MAIN_REGEX, line)
        line_is_user_func = re.search(USER_DEFINED_FUNCTIONS_REGEX, line)
        line_is_forward_dec = re.search(FORWARD_DEC_REGEX, line)
        if (line_is_main or line_is_user_func) and not line_is_forward_dec:
            check_line_spacing = True

        # Keep track of how many left and right braces we've seen
        if check_line_spacing:
            if re.search(LEFT_BRACE_REGEX, line):
                left_brace_count += 1
            if re.search(RIGHT_BRACE_REGEX, line):
                right_brace_count += 1

        # If brace counts match, we've seen the whole main() or user function
        if (left_brace_count == right_brace_count) and left_brace_count > 0:
            check_line_spacing = False
            left_brace_count = 0
            right_brace_count = 0

        # Check if we're looking at the opening brace for a function on its own line
        # If we are, skip it. It's a Brace Styling anomaly, not a Line Spacing anomaly
        if re.search(LEFT_BRACE_REGEX, line) and (
            re.search(INT_MAIN_REGEX, lines[i - 1]) or re.search(USER_DEFINED_FUNCTIONS_REGEX, lines[i - 1])
        ):
            opening_brace = True
        else:
            opening_brace = False

        if (
            a.is_active
            and check_line_spacing
            and not line_is_main
            and not line_is_user_func
            and not opening_brace
            and (left_brace_count >= 1)
            and a.regex.search(line)
        ):
            if a.should_inc_score():
                anomaly_score += a.weight
            a.num_instances += 1
            num_anomalies_found += 1

    return num_anomalies_found, round(anomaly_score, 1)


# TODO: For Escaped Newline, differentiate between line ending and a student's \n
style_anomalies = [
    StyleAnomaly('Pointers', POINTERS_REGEX, True, 0.9, -1),
    StyleAnomaly('Infinite Loop', INFINITE_LOOP_REGEX, True, 0.9, -1),
    StyleAnomaly('Atypical Includes', ATYPICAL_INCLUDE_REGEX, True, 0.1, -1),
    StyleAnomaly('Atypical Keywords', ATYPICAL_KEYWORD_REGEX, True, 0.3, -1, True),
    StyleAnomaly('Array Accesses', ARRAY_ACCESSES_REGEX, True, 0.9, -1),
    StyleAnomaly('Namespace Std', NAMESPACE_STD_REGEX, False, 0.1, -1),
    StyleAnomaly('Brace Styling', BRACE_STYLING_REGEX, True, 0.1, -1, True),
    StyleAnomaly('Escaped Newline', ESCAPED_NEWLINE_REGEX, True, 0.1, -1),
    StyleAnomaly('User-Defined Functions', USER_DEFINED_FUNCTIONS_REGEX, True, 0.8, -1),
    StyleAnomaly('Ternary Operator', TERNARY_OPERATOR_REGEX, True, 0.2, -1),
    StyleAnomaly('Command-Line Arguments', COMMAND_LINE_ARGUMENTS_REGEX, True, 0.8, -1),
    StyleAnomaly('Nulls', NULLS_REGEX, True, 0.4, -1),
    StyleAnomaly('Scope Operator', SCOPE_OPERATOR_REGEX, True, 0.25, -1),
    StyleAnomaly('Line Spacing', LINE_SPACING_REGEX, True, 0.1, -1),
    StyleAnomaly('Multiple Declarations Same Line', MULTIPLE_DECLARATIONS_REGEX, True, 0.3, -1),
    StyleAnomaly('Multiple Cin Same Line', MULTIPLE_CIN_SAME_LINE_REGEX, True, 0.3, -1),
    StyleAnomaly('and & or', AND_OR_REGEX, True, 0.1, -1),
    StyleAnomaly('List Initialization', LIST_INIT_REGEX, True, 0.8, -1),
    StyleAnomaly('Vector Name Spacing', VECTOR_NAME_SPACING_REGEX, True, 0.1, -1),
    StyleAnomaly('Spaceless Operator', SPACELESS_OPERATOR_REGEX, True, 0.1, -1),
    StyleAnomaly('Control Statement Spacing', CONTROL_STATEMENT_SPACING_REGEX, True, 0.1, -1),
    StyleAnomaly('Main Void', MAIN_VOID_REGEX, True, 0.5, -1),
    StyleAnomaly('Access And Increment', ACCESS_AND_INCREMENT_REGEX, True, 0.2, -1, True),
    StyleAnomaly('Auto', AUTO_REGEX, True, 0.3, -1),
    StyleAnomaly('zyBooks Set Precision', SET_PRECISION_REGEX, True, 0.2, -1),
    StyleAnomaly('Ranged-Based For Loop', RANGED_BASED_LOOP_REGEX, True, 0.6, -1),
    StyleAnomaly('Iterator Functions', ITERATOR_FUNCTIONS_REGEX, True, 0.3, -1),
    StyleAnomaly('Max Min Macros', MAX_MIN_MACRO_REGEX, True, 0.3, -1),
    StyleAnomaly('Swap Function', SWAP_FUNCTION_REGEX, True, 0.6, -1),
    StyleAnomaly('Cin Inside While', CIN_INSIDE_WHILE_REGEX, True, 0.6, -1),
]


def get_single_anomaly_score(code: str, a: StyleAnomaly) -> Tuple[int, float]:
    anomaly_score = 0
    num_anomalies_found = 0
    lines = code.splitlines()

    if a.name == 'Line Spacing':  # Line Spacing anomaly requires additional logic
        line_spacing_num_found, line_spacing_score = get_line_spacing_score(lines, a)
        num_anomalies_found += line_spacing_num_found
        anomaly_score += line_spacing_score
    else:
        for line in lines:
            if a.is_active and a.regex.search(line):  # If the anomaly is active and we find a match
                if a.should_inc_score():  # Should we increment anomaly score? Based on current and max # instances
                    anomaly_score += a.weight  # Anomaly score reflects anomaly's max # of instances
                a.num_instances += 1
                num_anomalies_found += 1

    return num_anomalies_found, round(anomaly_score, 1)


def get_total_anomaly_score(code: str) -> Tuple[int, float]:
    anomaly_score = 0
    num_anomalies_found = 0

    for a in style_anomalies:
        found, score = get_single_anomaly_score(code, a)
        num_anomalies_found += found
        anomaly_score += score

    return num_anomalies_found, anomaly_score


def get_anomaly_score(code, auto=0):
    # Below is the format for the anomaly in question
    # [Count_instances, points/instance, anomaly on/off, regex, count of instances, instance cap (-1 for no cap)]
    # Add to the hashmap Styleanomaly in case you need new anomaly to be detected
    style_anomalies = {
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
    anomalies_found = 0  # Counts the number of anomalies found
    check_line_spacing = False  # Indicates whether to check for Line Spacing anomaly
    left_brace_count = 0  # Count of left braces for Line Spacing anomaly
    right_brace_count = 0  # Count of right braces for Line Spacing anomaly
    opening_brace = False  # Indicates if `line` is the opening brace for the function on its own line

    # For automatic anomaly detection, enable every anomaly
    if auto == 1:
        for anomaly in style_anomalies:
            style_anomalies[anomaly][2] = 1

    lines = code.splitlines()
    for i, line in enumerate(lines):  # Reading through lines in the code and checking for each anomaly
        if style_anomalies['Pointers'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Pointers'][3], line):
                if style_anomalies['Pointers'][0] == 1 or (
                    style_anomalies['Pointers'][0] == 0 and style_anomalies['Pointers'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Pointers'][5] <= -1) or (
                        style_anomalies['Pointers'][5] > -1
                        and (style_anomalies['Pointers'][4] < style_anomalies['Pointers'][5])
                    ):
                        anomaly_score += style_anomalies['Pointers'][1]
                    style_anomalies['Pointers'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Infinite_loop'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Infinite_loop'][3], line):
                if style_anomalies['Infinite_loop'][0] == 1 or (
                    style_anomalies['Infinite_loop'][0] == 0 and style_anomalies['Infinite_loop'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Infinite_loop'][5] <= -1) or (
                        style_anomalies['Infinite_loop'][5] > -1
                        and (style_anomalies['Infinite_loop'][4] < style_anomalies['Infinite_loop'][5])
                    ):
                        anomaly_score += style_anomalies['Infinite_loop'][1]
                    style_anomalies['Infinite_loop'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Atypical Includes'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Atypical Includes'][3], line):
                if style_anomalies['Atypical Includes'][0] == 1 or (
                    style_anomalies['Atypical Includes'][0] == 0 and style_anomalies['Atypical Includes'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Atypical Includes'][5] <= -1) or (
                        style_anomalies['Atypical Includes'][5] > -1
                        and (style_anomalies['Atypical Includes'][4] < style_anomalies['Atypical Includes'][5])
                    ):
                        anomaly_score += style_anomalies['Atypical Includes'][1]
                    style_anomalies['Atypical Includes'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Atypical Keywords'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Atypical Keywords'][3], line, flags=re.X):
                if style_anomalies['Atypical Keywords'][0] == 1 or (
                    style_anomalies['Atypical Keywords'][0] == 0 and style_anomalies['Atypical Keywords'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Atypical Keywords'][5] <= -1) or (
                        style_anomalies['Atypical Keywords'][5] > -1
                        and (style_anomalies['Atypical Keywords'][4] < style_anomalies['Atypical Keywords'][5])
                    ):
                        anomaly_score += style_anomalies['Atypical Keywords'][1]
                    style_anomalies['Atypical Keywords'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Array Accesses'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Array Accesses'][3], line):
                if style_anomalies['Array Accesses'][0] == 1 or (
                    style_anomalies['Array Accesses'][0] == 0 and style_anomalies['Array Accesses'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Array Accesses'][5] <= -1) or (
                        style_anomalies['Array Accesses'][5] > -1
                        and (style_anomalies['Array Accesses'][4] < style_anomalies['Array Accesses'][5])
                    ):
                        anomaly_score += style_anomalies['Array Accesses'][1]
                    style_anomalies['Array Accesses'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Namespace Std'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Namespace Std'][3], line):
                if style_anomalies['Namespace Std'][0] == 1 or (
                    style_anomalies['Namespace Std'][0] == 0 and style_anomalies['Namespace Std'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Namespace Std'][5] <= -1) or (
                        style_anomalies['Namespace Std'][5] > -1
                        and (style_anomalies['Namespace Std'][4] < style_anomalies['Namespace Std'][5])
                    ):
                        anomaly_score += style_anomalies['Namespace Std'][1]
                    style_anomalies['Namespace Std'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Brace Styling'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Brace Styling'][3], line, flags=re.X):
                if style_anomalies['Brace Styling'][0] == 1 or (
                    style_anomalies['Brace Styling'][0] == 0 and style_anomalies['Brace Styling'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Brace Styling'][5] <= -1) or (
                        style_anomalies['Brace Styling'][5] > -1
                        and (style_anomalies['Brace Styling'][4] < style_anomalies['Brace Styling'][5])
                    ):
                        anomaly_score += style_anomalies['Brace Styling'][1]
                    style_anomalies['Brace Styling'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Escaped Newline'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Escaped Newline'][3], line):
                if style_anomalies['Escaped Newline'][0] == 1 or (
                    style_anomalies['Escaped Newline'][0] == 0 and style_anomalies['Escaped Newline'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Escaped Newline'][5] <= -1) or (
                        style_anomalies['Escaped Newline'][5] > -1
                        and (style_anomalies['Escaped Newline'][4] < style_anomalies['Escaped Newline'][5])
                    ):
                        anomaly_score += style_anomalies['Escaped Newline'][1]
                    style_anomalies['Escaped Newline'][4] += 1
                    anomalies_found += 1

        if style_anomalies['User-Defined Functions'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['User-Defined Functions'][3], line) and 'main()' not in line:
                if style_anomalies['User-Defined Functions'][0] == 1 or (
                    style_anomalies['User-Defined Functions'][0] == 0
                    and style_anomalies['User-Defined Functions'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['User-Defined Functions'][5] <= -1) or (
                        style_anomalies['User-Defined Functions'][5] > -1
                        and (
                            style_anomalies['User-Defined Functions'][4] < style_anomalies['User-Defined Functions'][5]
                        )
                    ):
                        anomaly_score += style_anomalies['User-Defined Functions'][1]
                    style_anomalies['User-Defined Functions'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Ternary Operator'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Ternary Operator'][3], line):
                if style_anomalies['Ternary Operator'][0] == 1 or (
                    style_anomalies['Ternary Operator'][0] == 0 and style_anomalies['Ternary Operator'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Ternary Operator'][5] <= -1) or (
                        style_anomalies['Ternary Operator'][5] > -1
                        and (style_anomalies['Ternary Operator'][4] < style_anomalies['Ternary Operator'][5])
                    ):
                        anomaly_score += style_anomalies['Ternary Operator'][1]
                    style_anomalies['Ternary Operator'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Command-Line Arguments'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Command-Line Arguments'][3], line):
                if style_anomalies['Command-Line Arguments'][0] == 1 or (
                    style_anomalies['Command-Line Arguments'][0] == 0
                    and style_anomalies['Command-Line Arguments'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Command-Line Arguments'][5] <= -1) or (
                        style_anomalies['Command-Line Arguments'][5] > -1
                        and (
                            style_anomalies['Command-Line Arguments'][4] < style_anomalies['Command-Line Arguments'][5]
                        )
                    ):
                        anomaly_score += style_anomalies['Command-Line Arguments'][1]
                    style_anomalies['Command-Line Arguments'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Nulls'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Nulls'][3], line):
                if style_anomalies['Nulls'][0] == 1 or (
                    style_anomalies['Nulls'][0] == 0 and style_anomalies['Nulls'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Nulls'][5] <= -1) or (
                        style_anomalies['Nulls'][5] > -1 and (style_anomalies['Nulls'][4] < style_anomalies['Nulls'][5])
                    ):
                        anomaly_score += style_anomalies['Nulls'][1]
                    style_anomalies['Nulls'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Scope Operator'][2] != 0:  # Check if the anomaly is turned on
            if (
                re.search(style_anomalies['Scope Operator'][3], line)
                and 'string::npos' not in line
                and 'std::' not in line
            ):
                if style_anomalies['Scope Operator'][0] == 1 or (
                    style_anomalies['Scope Operator'][0] == 0 and style_anomalies['Scope Operator'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Scope Operator'][5] <= -1) or (
                        style_anomalies['Scope Operator'][5] > -1
                        and (style_anomalies['Scope Operator'][4] < style_anomalies['Scope Operator'][5])
                    ):
                        anomaly_score += style_anomalies['Scope Operator'][1]
                    style_anomalies['Scope Operator'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Max Min Macros'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Max Min Macros'][3], line):
                if style_anomalies['Max Min Macros'][0] == 1 or (
                    style_anomalies['Max Min Macros'][0] == 0 and style_anomalies['Max Min Macros'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Max Min Macros'][5] <= -1) or (
                        style_anomalies['Max Min Macros'][5] > -1
                        and (style_anomalies['Max Min Macros'][4] < style_anomalies['Max Min Macros'][5])
                    ):
                        anomaly_score += style_anomalies['Max Min Macros'][1]
                    style_anomalies['Max Min Macros'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Swap Function'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Swap Function'][3], line):
                if style_anomalies['Swap Function'][0] == 1 or (
                    style_anomalies['Swap Function'][0] == 0 and style_anomalies['Swap Function'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Swap Function'][5] <= -1) or (
                        style_anomalies['Swap Function'][5] > -1
                        and (style_anomalies['Swap Function'][4] < style_anomalies['Swap Function'][5])
                    ):
                        anomaly_score += style_anomalies['Swap Function'][1]
                    style_anomalies['Swap Function'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Cin Inside While'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Cin Inside While'][3], line):
                if style_anomalies['Cin Inside While'][0] == 1 or (
                    style_anomalies['Cin Inside While'][0] == 0 and style_anomalies['Cin Inside While'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Cin Inside While'][5] <= -1) or (
                        style_anomalies['Cin Inside While'][5] > -1
                        and (style_anomalies['Cin Inside While'][4] < style_anomalies['Cin Inside While'][5])
                    ):
                        anomaly_score += style_anomalies['Cin Inside While'][1]
                    style_anomalies['Cin Inside While'][4] += 1
                    anomalies_found += 1

        # "Line Spacing" should only check lines inside main() and user functions
        line_is_main = re.search(INT_MAIN_REGEX, line)
        line_is_user_func = re.search(USER_DEFINED_FUNCTIONS_REGEX, line)
        line_is_forward_dec = re.search(FORWARD_DEC_REGEX, line)
        if (line_is_main or line_is_user_func) and not line_is_forward_dec:
            check_line_spacing = True

        # Keep track of how many left and right braces we've seen
        if re.search(LEFT_BRACE_REGEX, line) and check_line_spacing:
            left_brace_count += 1
        if re.search(RIGHT_BRACE_REGEX, line) and check_line_spacing:
            right_brace_count += 1

        # If brace counts match, we've seen the whole main() or user function
        if (left_brace_count == right_brace_count) and left_brace_count > 0:
            check_line_spacing = False
            left_brace_count = 0
            right_brace_count = 0

        # Check if we're looking at the opening brace for a function on its own line
        # If we are, skip it- it's a Brace Styling anomaly, not a Line Spacing anomaly
        if re.search(LEFT_BRACE_REGEX, line) and (
            re.search(INT_MAIN_REGEX, lines[i - 1]) or re.search(USER_DEFINED_FUNCTIONS_REGEX, lines[i - 1])
        ):
            opening_brace = True
        else:
            opening_brace = False

        if (
            style_anomalies['Line Spacing'][2] != 0
            and check_line_spacing
            and not line_is_main
            and not line_is_user_func
            and not opening_brace
            and (left_brace_count >= 1)
        ):  # Check if the anomaly is turned on
            if re.search(style_anomalies['Line Spacing'][3], line):
                if style_anomalies['Line Spacing'][0] == 1 or (
                    style_anomalies['Line Spacing'][0] == 0 and style_anomalies['Line Spacing'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Line Spacing'][5] <= -1) or (
                        style_anomalies['Line Spacing'][5] > -1
                        and (style_anomalies['Line Spacing'][4] < style_anomalies['Line Spacing'][5])
                    ):
                        anomaly_score += style_anomalies['Line Spacing'][1]
                    style_anomalies['Line Spacing'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Multiple Declarations Same Line'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Multiple Declarations Same Line'][3], line):
                if style_anomalies['Multiple Declarations Same Line'][0] == 1 or (
                    style_anomalies['Multiple Declarations Same Line'][0] == 0
                    and style_anomalies['Multiple Declarations Same Line'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Multiple Declarations Same Line'][5] <= -1) or (
                        style_anomalies['Multiple Declarations Same Line'][5] > -1
                        and (
                            style_anomalies['Multiple Declarations Same Line'][4]
                            < style_anomalies['Multiple Declarations Same Line'][5]
                        )
                    ):
                        anomaly_score += style_anomalies['Multiple Declarations Same Line'][1]
                    style_anomalies['Multiple Declarations Same Line'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Multiple Cin Same Line'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Multiple Cin Same Line'][3], line):
                if style_anomalies['Multiple Cin Same Line'][0] == 1 or (
                    style_anomalies['Multiple Cin Same Line'][0] == 0
                    and style_anomalies['Multiple Cin Same Line'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Multiple Cin Same Line'][5] <= -1) or (
                        style_anomalies['Multiple Cin Same Line'][5] > -1
                        and (
                            style_anomalies['Multiple Cin Same Line'][4] < style_anomalies['Multiple Cin Same Line'][5]
                        )
                    ):
                        anomaly_score += style_anomalies['Multiple Cin Same Line'][1]
                    style_anomalies['Multiple Cin Same Line'][4] += 1
                    anomalies_found += 1

        if style_anomalies['and & or'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['and & or'][3], line):
                if style_anomalies['and & or'][0] == 1 or (
                    style_anomalies['and & or'][0] == 0 and style_anomalies['and & or'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['and & or'][5] <= -1) or (
                        style_anomalies['and & or'][5] > -1
                        and (style_anomalies['and & or'][4] < style_anomalies['and & or'][5])
                    ):
                        anomaly_score += style_anomalies['and & or'][1]
                    style_anomalies['and & or'][4] += 1
                    anomalies_found += 1

        if style_anomalies['List Initialization'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['List Initialization'][3], line):
                if style_anomalies['List Initialization'][0] == 1 or (
                    style_anomalies['List Initialization'][0] == 0 and style_anomalies['List Initialization'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['List Initialization'][5] <= -1) or (
                        style_anomalies['List Initialization'][5] > -1
                        and (style_anomalies['List Initialization'][4] < style_anomalies['List Initialization'][5])
                    ):
                        anomaly_score += style_anomalies['List Initialization'][1]
                    style_anomalies['List Initialization'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Vector Name Spacing'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Vector Name Spacing'][3], line):
                if style_anomalies['Vector Name Spacing'][0] == 1 or (
                    style_anomalies['Vector Name Spacing'][0] == 0 and style_anomalies['Vector Name Spacing'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Vector Name Spacing'][5] <= -1) or (
                        style_anomalies['Vector Name Spacing'][5] > -1
                        and (style_anomalies['Vector Name Spacing'][4] < style_anomalies['Vector Name Spacing'][5])
                    ):
                        anomaly_score += style_anomalies['Vector Name Spacing'][1]
                    style_anomalies['Vector Name Spacing'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Spaceless Operator'][2] != 0:  # Check if the anomaly is turned on
            match = re.search(style_anomalies['Spaceless Operator'][3], line)
            if match and '#include' not in line and 'vector<' not in match.group():
                if style_anomalies['Spaceless Operator'][0] == 1 or (
                    style_anomalies['Spaceless Operator'][0] == 0 and style_anomalies['Spaceless Operator'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Spaceless Operator'][5] <= -1) or (
                        style_anomalies['Spaceless Operator'][5] > -1
                        and (style_anomalies['Spaceless Operator'][4] < style_anomalies['Spaceless Operator'][5])
                    ):
                        anomaly_score += style_anomalies['Spaceless Operator'][1]
                    style_anomalies['Spaceless Operator'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Control Statement Spacing'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Control Statement Spacing'][3], line):
                if style_anomalies['Control Statement Spacing'][0] == 1 or (
                    style_anomalies['Control Statement Spacing'][0] == 0
                    and style_anomalies['Control Statement Spacing'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Control Statement Spacing'][5] <= -1) or (
                        style_anomalies['Control Statement Spacing'][5] > -1
                        and (
                            style_anomalies['Control Statement Spacing'][4]
                            < style_anomalies['Control Statement Spacing'][5]
                        )
                    ):
                        anomaly_score += style_anomalies['Control Statement Spacing'][1]
                    style_anomalies['Control Statement Spacing'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Main Void'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Main Void'][3], line):
                if style_anomalies['Main Void'][0] == 1 or (
                    style_anomalies['Main Void'][0] == 0 and style_anomalies['Main Void'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Main Void'][5] <= -1) or (
                        style_anomalies['Main Void'][5] > -1
                        and (style_anomalies['Main Void'][4] < style_anomalies['Main Void'][5])
                    ):
                        anomaly_score += style_anomalies['Main Void'][1]
                    style_anomalies['Main Void'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Access And Increment'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Access And Increment'][3], line, flags=re.X):
                if style_anomalies['Access And Increment'][0] == 1 or (
                    style_anomalies['Access And Increment'][0] == 0 and style_anomalies['Access And Increment'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Access And Increment'][5] <= -1) or (
                        style_anomalies['Access And Increment'][5] > -1
                        and (style_anomalies['Access And Increment'][4] < style_anomalies['Access And Increment'][5])
                    ):
                        anomaly_score += style_anomalies['Access And Increment'][1]
                    style_anomalies['Access And Increment'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Auto'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Auto'][3], line):
                if style_anomalies['Auto'][0] == 1 or (
                    style_anomalies['Auto'][0] == 0 and style_anomalies['Auto'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Auto'][5] <= -1) or (
                        style_anomalies['Auto'][5] > -1 and (style_anomalies['Auto'][4] < style_anomalies['Auto'][5])
                    ):
                        anomaly_score += style_anomalies['Auto'][1]
                    style_anomalies['Auto'][4] += 1
                    anomalies_found += 1

        if style_anomalies['zyBooks Set Precision'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['zyBooks Set Precision'][3], line):
                if style_anomalies['zyBooks Set Precision'][0] == 1 or (
                    style_anomalies['zyBooks Set Precision'][0] == 0
                    and style_anomalies['zyBooks Set Precision'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['zyBooks Set Precision'][5] <= -1) or (
                        style_anomalies['zyBooks Set Precision'][5] > -1
                        and (style_anomalies['zyBooks Set Precision'][4] < style_anomalies['zyBooks Set Precision'][5])
                    ):
                        anomaly_score += style_anomalies['zyBooks Set Precision'][1]
                    style_anomalies['zyBooks Set Precision'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Ranged-Based for Loop'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Ranged-Based for Loop'][3], line):
                if style_anomalies['Ranged-Based for Loop'][0] == 1 or (
                    style_anomalies['Ranged-Based for Loop'][0] == 0
                    and style_anomalies['Ranged-Based for Loop'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Ranged-Based for Loop'][5] <= -1) or (
                        style_anomalies['Ranged-Based for Loop'][5] > -1
                        and (style_anomalies['Ranged-Based for Loop'][4] < style_anomalies['Ranged-Based for Loop'][5])
                    ):
                        anomaly_score += style_anomalies['Ranged-Based for Loop'][1]
                    style_anomalies['Ranged-Based for Loop'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Iterator Functions'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Iterator Functions'][3], line):
                if style_anomalies['Iterator Functions'][0] == 1 or (
                    style_anomalies['Iterator Functions'][0] == 0 and style_anomalies['Iterator Functions'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Iterator Functions'][5] <= -1) or (
                        style_anomalies['Iterator Functions'][5] > -1
                        and (style_anomalies['Iterator Functions'][4] < style_anomalies['Iterator Functions'][5])
                    ):
                        anomaly_score += style_anomalies['Iterator Functions'][1]
                    style_anomalies['Iterator Functions'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Max Min Macros'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Max Min Macros'][3], line):
                if style_anomalies['Max Min Macros'][0] == 1 or (
                    style_anomalies['Max Min Macros'][0] == 0 and style_anomalies['Max Min Macros'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Max Min Macros'][5] <= -1) or (
                        style_anomalies['Max Min Macros'][5] > -1
                        and (style_anomalies['Max Min Macros'][4] < style_anomalies['Max Min Macros'][5])
                    ):
                        anomaly_score += style_anomalies['Max Min Macros'][1]
                    style_anomalies['Max Min Macros'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Swap Function'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Swap Function'][3], line):
                if style_anomalies['Swap Function'][0] == 1 or (
                    style_anomalies['Swap Function'][0] == 0 and style_anomalies['Swap Function'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Swap Function'][5] <= -1) or (
                        style_anomalies['Swap Function'][5] > -1
                        and (style_anomalies['Swap Function'][4] < style_anomalies['Swap Function'][5])
                    ):
                        anomaly_score += style_anomalies['Swap Function'][1]
                    style_anomalies['Swap Function'][4] += 1
                    anomalies_found += 1

        if style_anomalies['Cin Inside While'][2] != 0:  # Check if the anomaly is turned on
            if re.search(style_anomalies['Cin Inside While'][3], line):
                if style_anomalies['Cin Inside While'][0] == 1 or (
                    style_anomalies['Cin Inside While'][0] == 0 and style_anomalies['Cin Inside While'][4] == 0
                ):
                    # Score for this anomaly is capped to Styleanomaly[x][5] instances
                    if (style_anomalies['Cin Inside While'][5] <= -1) or (
                        style_anomalies['Cin Inside While'][5] > -1
                        and (style_anomalies['Cin Inside While'][4] < style_anomalies['Cin Inside While'][5])
                    ):
                        anomaly_score += style_anomalies['Cin Inside While'][1]
                    style_anomalies['Cin Inside While'][4] += 1
                    anomalies_found += 1

    # For automatic anomaly detection, return *which* anomalies were found
    if auto == 1:
        anomalies_found = {}
        for anomaly in style_anomalies:
            anomalies_found[anomaly] = style_anomalies[anomaly][4]

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
    file_path = filedialog.askopenfilename()
    folder_path = os.path.split(file_path)[0]
    file_name = os.path.basename(file_path).split('/')[-1]
    logfile = pd.read_csv(file_path)
    logfile = logfile[logfile.role == 'Student']

    selected_labs = get_selected_labs(logfile)
    print('Processing ' + file_name)
    logfile = download_code(logfile)
    data = create_data_structure(logfile)

    final_roster = {}
    anomaly_detection_output = anomaly(data, selected_labs)
    for user_id in anomaly_detection_output:
        for lab in anomaly_detection_output[user_id]:
            anomalies_found = anomaly_detection_output[user_id][lab][0]
            get_total_anomaly_score = anomaly_detection_output[user_id][lab][1]
            if user_id in final_roster:
                final_roster[user_id]['Lab ' + str(lab) + ' anomalies found'] = anomalies_found
                final_roster[user_id]['Lab ' + str(lab) + ' anomaly score'] = get_total_anomaly_score
                final_roster[user_id]['Lab ' + str(lab) + ' student code'] = anomaly_detection_output[user_id][lab][2]
            else:
                final_roster[user_id] = {
                    'User ID': user_id,
                    'Last Name': data[user_id][lab][0].last_name[0],
                    'First Name': data[user_id][lab][0].first_name[0],
                    'Email': data[user_id][lab][0].email[0],
                    'Role': 'Student',
                    'Lab ' + str(lab) + ' anomalies found': anomalies_found,
                    'Lab ' + str(lab) + ' anomaly score': get_total_anomaly_score,
                    'Lab ' + str(lab) + ' student code': anomaly_detection_output[user_id][lab][2],
                }
    write_output_to_csv(final_roster)

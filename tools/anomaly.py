import os
import re
from tkinter import filedialog

import pandas as pd

from tools.utilities import (
    create_data_structure,
    download_code,
    get_code_with_max_score,
    get_selected_labs,
    write_output_to_csv,
)

use_standalone = False
SCORE_PRECISION = 2


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


# Primary anomaly regular expressions
POINTERS_REGEX = r'((?:\(+)?(?:int|char|string|void|bool|float|double)(?:\)+)?\s*\*{1,2}\s*\w+\s*\=?.*\;$)'
INFINITE_LOOP_REGEX = r'((while\s*\((?:true|1)\))|(for\s*\(;;\)))'
ATYPICAL_INCLUDE_REGEX = r'(#\s*include\s*<(?:iomanip|algorithm|utility|limits|stdio)>)'
ATYPICAL_KEYWORD_REGEX = r"""
	((break\s*;)
	|(switch\s*\(\w+\)\s*{)
	|(continue\s*;)
	|(sizeof\(\w+\))
	|(case\s+\S+\s*:)
	|(\.erase\s*\(.*\)))
	"""
BRACE_STYLING_REGEX = r"""
	((?P<leftbrace>^\s*{)
	|(?P<rightbrace>\S+;\s*})
	|(?P<oneline>(?:if|for)\s*\(.+\)\s*\S+.*;)
	|(?P<else1>}\s*else)
	|(?P<else2>else\s\S+.*;))
	"""
ARRAY_ACCESSES_REGEX = r'(\w+\[.*\])'
NAMESPACE_STD_REGEX = r'(std::)'
ESCAPED_NEWLINE_REGEX = r'(\\n)'
USER_DEFINED_FUNCTIONS_REGEX = (
    r'(^\s*(?:(?:unsigned|signed|long|short)\s)?(?:int|char|string|void|bool|float|double)\s(?!main)\w+\(.*\))'
)
TERNARY_OPERATOR_REGEX = r'(.+\s\?\s.+\s\:\s.+)'
COMMAND_LINE_ARGUMENTS_REGEX = r'(main\(\s?int argc,\s?(?:char\s?\*\s?argv\[\])|(?:char\s?\*\*\s?argv))\s?\)'
NULLS_REGEX = r'(NULL|nullptr|\\0)'
SCOPE_OPERATOR_REGEX = r'^(?!.*?(string::npos|std::)).*\b(\w+::\w+)\b'
LINE_SPACING_REGEX = r'(^\S+)'
MULTIPLE_DECLARATIONS_REGEX = r'((?:int|char|string|void|bool|float|double)\s+\w+[^\"\']+\s*,\s*\w+.*;)'
MULTIPLE_CIN_SAME_LINE_REGEX = r'(cin\s*>>\s*\w+\s*>>)'
AND_OR_REGEX = r'(if\s*\([^\"\']+\s+(?:and|or)\s+[^\"\']+\))'
LIST_INIT_REGEX = r'((?:int|char|string|void|bool|float|double)\s+\w+\s*{.*};)'
VECTOR_NAME_SPACING_REGEX = r'(vector<.+>\w+)'
SPACELESS_OPERATOR_REGEX = r"""
	^(?!.*(?:\#include|vector<)).* # Exclude lines with `#include` and `vector<`
	([\w\]\)]+
	(?:>|>=|<|<=|=|==|!=|<<|>>|\+|-|\+=|-=|\*|/|%|&&|\|\|)
	[\w\[\(]+
	(?![^<<]*(?:\"|\'))) # Exclude string literals
	"""
CONTROL_STATEMENT_SPACING_REGEX = r'((?:if|for|while)\(.*\))'
MAIN_VOID_REGEX = r'(int main\(void\))'
ACCESS_AND_INCREMENT_REGEX = r"""
	((?P<arrays>\w+\[(?:\w+\+\+|\w+--|\+\+\w+|--\w+)\])
	|(?P<vectors>\w+\.at\((?:\w+\+\+|\w+--|\+\+\w+|--\w+)\)))
	"""
AUTO_REGEX = r'(auto\s\w+)'
SET_PRECISION_REGEX = r'cout\s*<<\s*setprecision\(.+\)\s*<<\s*fixed'
RANGED_BASED_LOOP_REGEX = r'(for\s*\(\s*\w+\s+\w+\s+:\s+\w+\s*\))'
ITERATOR_FUNCTIONS_REGEX = r'(\w+\.(?:begin|end)\(\))'
MAX_MIN_MACRO_REGEX = r'(INT_MAX|INT_MIN)'
SWAP_FUNCTION_REGEX = r'(swap\(.*\))'
CIN_INSIDE_WHILE_REGEX = r'(while\s*\(.*cin\s*>>\s*\w+.*\))'

# Helper regular expressions
INT_MAIN_REGEX = r'int main\s*\(.*\)'
LEFT_BRACE_REGEX = r'({)'
RIGHT_BRACE_REGEX = r'(})'
FORWARD_DEC_REGEX = r'(^(?:(?:unsigned|signed|long|short)\s)?(?:int|char|string|void|bool|float|double)\s\w+\(.*\);)'


# TODO: For Escaped Newline, differentiate between line ending and a student's \n
style_anomalies = [
    StyleAnomaly('Pointers', POINTERS_REGEX, True, 0.9, -1),
    StyleAnomaly('Infinite Loop', INFINITE_LOOP_REGEX, True, 0.9, -1),
    StyleAnomaly('Atypical Includes', ATYPICAL_INCLUDE_REGEX, True, 0.1, -1),
    StyleAnomaly('Atypical Keywords', ATYPICAL_KEYWORD_REGEX, True, 0.3, -1, True),
    StyleAnomaly('Array Accesses', ARRAY_ACCESSES_REGEX, True, 0.9, -1),
    StyleAnomaly('Namespace Std', NAMESPACE_STD_REGEX, True, 0.1, -1),
    StyleAnomaly('Brace Styling', BRACE_STYLING_REGEX, True, 0.1, -1, True),
    StyleAnomaly('Escaped Newline', ESCAPED_NEWLINE_REGEX, False, 0.1, -1),
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
    StyleAnomaly('Spaceless Operator', SPACELESS_OPERATOR_REGEX, True, 0.1, -1, True),
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


def get_line_spacing_score(lines: list[str], a: StyleAnomaly) -> tuple[int, float]:
    """Computes number of anomalies and anomaly score for the Line Spacing anomaly.

    Line Spacing requires additional logic to determine where main() and user functions are.
    Because of this, we use a separate function just for this anomaly.
    We only count non-indented lines inside of main() or user-defined functions.
    If the student wrote the function's opening brace on its own line, we exclude that line.

    Args:
        lines (str): The student's code, split into lines with splitlines().

    Returns:
        Tuple[int, int]: A tuple containing the number of anomalies found and anomaly score for Line Spacing.
    """

    anomaly_score = 0
    num_anomalies_found = 0
    left_brace_count = 0
    right_brace_count = 0
    check_line_spacing = False  # Don't check for anomaly until we're in a function
    opening_brace = False  # Indicates if `line` is the opening brace for the function on its own line

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
        opening_brace = bool(
            re.search(LEFT_BRACE_REGEX, line)
            and (re.search(INT_MAIN_REGEX, lines[i - 1]) or re.search(USER_DEFINED_FUNCTIONS_REGEX, lines[i - 1]))
        )

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

    return num_anomalies_found, round(anomaly_score, SCORE_PRECISION)


def get_single_anomaly_score(code: str, a: StyleAnomaly) -> tuple[int, float]:
    """Finds number of anomalies and anomaly score for a given code snippet and style anomaly.

    Args:
        code (str): The student's code as a single string.
        a (StyleAnomaly): The style anomaly to check for in the code.

    Returns:
        tuple[int, float]: A tuple containing the number of anomalies found and the anomaly score.
    """

    anomaly_score = 0
    num_anomalies_found = 0
    a.num_instances = 0
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

    return num_anomalies_found, round(anomaly_score, SCORE_PRECISION)


def get_total_anomaly_score(code: str) -> tuple[int, float]:
    """Finds total # of style anomalies and anomaly score for all anomalies for a code snippet.

    Args:
        code (str): The student's code as a single string.

    Returns:
        tuple[int, float]: A tuple containing the number of anomalies found and the anomaly score.
    """

    anomaly_score = 0
    num_anomalies_found = 0

    for a in style_anomalies:
        found, score = get_single_anomaly_score(code, a)
        num_anomalies_found += found
        anomaly_score += score

    return num_anomalies_found, anomaly_score


def anomaly(data: dict, selected_labs: list[float]) -> dict:
    """Finds style anomalies in the selected labs for each student.

    Args:
        data (dict): A dictionary of all lab submissions for each student.
        selected_labs (list[float]): A list of lab IDs to look for style anomalies in.

    Returns:
        dict: A dictionary containing the anomalies found for each user and lab.
            The structure of the dictionary is as follows:
            {
                user_id_1: {
                    lab_id_1: [anomalies_found, anomaly_score, code],
                    lab_id_2: [anomalies_found, anomaly_score, code],
                    ...
                },
                user_id_2: {
                    lab_id_1: [anomalies_found, anomaly_score, code],
                    lab_id_2: [anomalies_found, anomaly_score, code],
                    ...
                },
                ...
            }
    """

    output = {}
    for lab in selected_labs:
        for user_id in data:
            if user_id not in output:
                output[user_id] = {}
            if lab in data[user_id]:
                code = get_code_with_max_score(user_id, lab, data)
                anomalies_found, anomaly_score = get_total_anomaly_score(code)
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

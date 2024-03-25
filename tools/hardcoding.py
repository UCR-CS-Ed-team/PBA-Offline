import re

import pandas as pd

from tools.utilities import create_data_structure, download_code, get_selected_labs, setup_logger, write_output_to_csv

logger = setup_logger(__name__)  # DEBUGGING

use_standalone = False

IF_STATEMENT_REGEX = r'if\s*\((.*)\)'
LITERAL_VALUE_IN_COMP_REGEX = r'\w+\s*==\s*((?:[\"\'][^\"\']*[\"\'])|\d+)'
VAR_NAME_IN_COMP_REGEX = r'(\w+)\s*==\s*(?:[\"\'][^\"\']*[\"\']|\d+)'


def get_code_with_max_score(user_id: int, lab: float, submissions: dict) -> str:
    """Returns the first highest-scoring code submission for a student for a lab.

    The "first" highest-scoring submission means the oldest submission with the highest score.

    Args:
        user_id (int): Find the highest-scoring submission for the student with this ID.
        lab (float): Find the highest-scoring submission for this lab, e.g. lab 3.12.
        submissions (dict): All of the student's submissions for this lab.

    Returns:
        code (str): The code for the first highest-scoring submission.
    """

    max_score = 0
    code = submissions[user_id][lab][-1].code  # Choose a default submission
    for sub in submissions[user_id][lab]:
        if sub.max_score > max_score:
            max_score = sub.max_score
            code = sub.code
    return code


def remove_quotes(s: str) -> str:
    """Removes the surrounding quotes from a string if present.

    Args:
        s (str): The input string.

    Returns:
        str: The string with the surrounding quotes removed, if present.
    """

    single_quotes = s.startswith("'") and s.endswith("'")
    double_quotes = s.startswith('"') and s.endswith('"')
    if single_quotes or double_quotes:
        return s[1:-1]
    return s


def get_vars_in_if_statement(line: str) -> list:
    """Returns the names of variables being compared to literals in an `if` statement's condition.

    Args:
        line (str): The line of code to check for `if` statement literal comparisons.

    Returns:
        list: A list of names of variables being compared to literals, e.g. `x == 2` returns 'x'.
              If the line doesn't have an `if` statement, returns an empty list.
    """
    vars_in_if = []
    if_statement_match = re.search(IF_STATEMENT_REGEX, line)
    if if_statement_match:
        # Find all comparisons to literals (e.g. x == 'y') and save the var name
        vars_in_if = re.findall(VAR_NAME_IN_COMP_REGEX, if_statement_match.group(1))
    return vars_in_if


def get_literals_in_if_statement(line: str) -> list:
    """Returns the literal values being compared to variables in an `if` statement's condition.

    Args:
        line (str): The line of code to check for `if` statement literals.

    Returns:
        list: A list of literal values found in the if statement.
              If the line doesn't have an `if` statement, returns an empty list.
    """

    literals_in_if = []
    if_statement_match = re.search(IF_STATEMENT_REGEX, line)
    if if_statement_match:
        # Find all comparisons to literals (e.g. x == 'y') and save the literals
        literals_in_if = re.findall(LITERAL_VALUE_IN_COMP_REGEX, if_statement_match.group(1))
    return literals_in_if


def get_lines_in_if_scope(code: list[str], start_index: int) -> list[str]:
    """Returns the lines of code within the scope of an if statement.

    If 'if' is not in any line, return an empty list.

    Args:
        code (list[str]): A code submission split by newlines into a list of strings.
        start_index (int): The line index of the target `if` statement in the code submission.
    """

    if start_index < 0 or 'if' not in code[start_index]:
        return []

    first_line = code[start_index]
    lines_in_scope = []
    if_depth = 0

    # Handles first line being `} else if (...) {`
    # Prevents only the first line being returned
    if first_line.lstrip().startswith('}'):
        code[start_index] = first_line.lstrip(' }')

    for line in code[start_index:]:
        # If the line is an `if` comparing to literals, increase depth
        literals_in_if = get_literals_in_if_statement(line)  # TODO: should this check for any `if` statement?
        if literals_in_if:
            if_depth += 1
        # Exclude lines in nested `if` statements that compare to literals
        if if_depth == 1:
            lines_in_scope.append(line)
        if '}' in line:
            if_depth -= 1
        if if_depth == 0:
            break
    return lines_in_scope


def get_cout_output_with_var(if_lines: list[str], var_assignments: list[tuple[str, str]], output: str) -> str:
    """Finds a cout statement within `if_lines` involving variables and returns the statement's output.

    The function substitutes the value of the variable from `var_assignments` to find the output.

    Args:
        if_lines (list[str]): A list of lines of C++ code that are within an 'if' statement.
        var_assignments (list[tuple[str, str]]): A list of variable names and values.
        output (str): The output of a testcase.

    Returns:
        str: The output of the 'cout' statement.
    """

    for if_line in if_lines:
        cout_index = if_line.find('cout')
        if cout_index > -1:  # If line is a 'cout' statement
            for var in var_assignments:
                var_name = var[0]
                var_value = var[1]
                if if_line.rfind(var_name) > cout_index:  # If line outputs a variable
                    # Substitute variable's value, remove extraneous parts of the line
                    if_line = if_line.replace(var_name, var_value)
                    if_line = if_line.replace('<<', ' ')
                    if_line = if_line.replace('"', ' ').replace("'", ' ')
                    if_line = if_line.replace('cout', '').replace('endl', '')
                    if_line = if_line.rstrip(' ;')
                    cout_output = []  # Only consider words in the testcase output
                    for word in if_line.split():
                        if word in output:
                            cout_output.append(word)
                    return ' '.join(cout_output)
    return ''


def has_if_with_literal_and_cout(code: str) -> int:
    """
    Returns 1 if code has an if statement comparing to literals, followed by cout.
    Used for case 3: no testcases or solution
    """

    lines = code.splitlines()
    lines = [line for line in lines if line.strip() != '']  # Remove empty lines

    # Search every line for an 'if' comparing to a literal
    for i, line in enumerate(lines):
        literals_in_if = get_literals_in_if_statement(line)
        if literals_in_if:
            # Look at all lines in the scope of the `if` statement
            lines_in_if_scope = get_lines_in_if_scope(lines, i)
            for if_line in lines_in_if_scope:
                if 'cout' in if_line:
                    return 1
    return 0


def is_testcase_hardcoded(code: str, testcase: tuple) -> int:
    """Checks whether a code submission hardcodes the output of a testcase.

    Returns 1 if the code has a line `cout << x` where x is the testcase output.
    Does not consider any testcase inputs.

    Args:
        code (str): The student code to be evaluated
        testcase (tuple): A testcase, represented by a tuple of expected input and output

    Returns:
        int: 1 indicates the testcase output was hardcoded, else 0
    """

    output = testcase[1]

    for line in code.splitlines():
        cout_index = line.find('cout')
        if (cout_index != -1) and (line.find(output) > cout_index):
            return 1
    return 0


def is_testcase_hardcoded_in_if(code: str, testcase: tuple) -> int:
    """Checks if a code submission hardcoded a testcase inside an `if` statement.

    Returns 1 if the code:
    - Has an if statement comparing to a literal, followed by cout
    - The literal contains the input testcase, or a part of the testcase
    - The cout statement outputs the testcase's output using a variable

    E.g. this function finds snippets like this:
        ```
        if (x == 2) {
            cout << x << " is even" << endl;
        }
        ```

    Args:
        code (str): The student code to be evaluated
        testcase (tuple): A testcase, represented by a tuple of expected input and output

    Returns:
        int: 1 indicates the testcase is hardcoded, 0 indicates no hardcoding
    """

    input = testcase[0]
    output = testcase[1]

    lines = code.splitlines()
    lines = [line for line in lines if line.strip() != '']  # Remove empty lines

    # Search every line for an 'if' comparing to a literal
    for i, line in enumerate(lines):
        var_names_in_if = get_vars_in_if_statement(line)
        literals_in_if = get_literals_in_if_statement(line)

        if literals_in_if:
            var_assignments = []  # Track variable assignments as (name, value)
            for j, literal in enumerate(literals_in_if):
                var_name = var_names_in_if[j]  # Variable won't have quotes
                var_value = remove_quotes(literal)
                # If input testcase (or any part of it) is in the literal
                if input == var_value or any(word == var_value for word in input.split()):
                    var_assignments.append((var_name, var_value))

            if len(var_assignments) > 0:
                # Look at all lines in the scope of the `if` statement
                lines_in_if_scope = get_lines_in_if_scope(lines, i)
                cout_output = get_cout_output_with_var(lines_in_if_scope, var_assignments, output)
                if cout_output == output:
                    return 1
    return 0


def get_hardcode_score_with_soln(code: str, testcases: set[tuple], solution_code: str) -> int:
    """Gets a hardcoding score for a submission to a lab with a solution and testcases.

    Returns 1 if the following are true for any testcase:
    - Code hardcodes a testcase with a cout statement
    - Solution code does not hardcode the same testcase's output

    Args:
        code (str): The student code to be evaluated
        testcases (set[tuple]): Set of testcases, each represented by a tuple of expected input and output
        solution_code (str): The assignment's solution code

    Returns:
        int: The hardcoding score, where 1 indicates the presence of hardcoding and 0 indicates no hardcoding
    """

    is_hardcoded = False
    testcases_in_soln = set()

    # Track which testcase outputs are used in the solution
    for testcase in testcases:
        testcase_in_soln = is_testcase_hardcoded(solution_code, testcase)
        if testcase_in_soln:
            testcases_in_soln.add(testcase)

    # Check for hardcoding
    for testcase in testcases:
        testcase_in_code = is_testcase_hardcoded_in_if(code, testcase) or is_testcase_hardcoded(code, testcase)
        testcase_in_soln = testcase in testcases_in_soln
        if testcase_in_code and not testcase_in_soln:
            logger.debug(f'is_hardcoded is True for testcase {testcase}.')
            is_hardcoded = True  # TODO: return 1 here, True is for debugging

    if is_hardcoded:
        return 1
    return 0


def hardcoding_analysis_1(data, selected_labs, testcases, solution_code):
    """Case 1: testcases and solution is available"""
    output = {}
    for lab in selected_labs:
        for user_id in data:
            if user_id not in output:
                output[user_id] = {}
            if lab in data[user_id]:
                code = get_code_with_max_score(user_id, lab, data)
                hardcode_score = get_hardcode_score_with_soln(code, testcases, solution_code)
                output[user_id][lab] = [hardcode_score, code]
    return output


def hardcoding_analysis_2(data, selected_labs, testcases):
    """Case 2: testcases are available, but no solution"""
    output = {}
    testcase_use_counts = {testcase: 0 for testcase in testcases}
    testcase_use_threshold = 0.6
    num_students = len(data)

    for lab in selected_labs:
        for user_id in data:
            if user_id not in output:
                output[user_id] = {}
            if lab in data[user_id]:
                code = get_code_with_max_score(user_id, lab, data)
                output[user_id][lab] = [0, code, set()]
                for testcase in testcases:  # Track num times students hardcode testcases
                    hardcode_score = is_testcase_hardcoded_in_if(code, testcase)
                    output[user_id][lab][0] = hardcode_score
                    if hardcode_score > 0:
                        output[user_id][lab][2].add(testcase)
                        testcase_use_counts[testcase] += 1
        for user_id in data:
            for testcase in testcases:
                hardcoded_testcases = output[user_id][lab][2]
                hardcoding_percentage = testcase_use_counts[testcase] / num_students
                logger.debug(f'{testcase_use_counts[testcase]}/{num_students} hardcoded testcase {testcase}...')
                if (testcase in hardcoded_testcases) and (hardcoding_percentage >= testcase_use_threshold):
                    output[user_id][lab][2].remove(testcase)
                    if len(output[user_id][lab][2]) <= 0:
                        output[user_id][lab][0] = 0
    return output


def hardcoding_analysis_3(data, selected_labs):
    """Case 3: no testcases or solution"""
    output = {}
    if_literal_use_count = 0
    if_literal_threshold = 0.6
    num_students = len(data)

    for lab in selected_labs:
        for user_id in data:
            if user_id not in output:
                output[user_id] = {}
            if lab in data[user_id]:
                code = get_code_with_max_score(user_id, lab, data)
                hardcode_score = has_if_with_literal_and_cout(code)
                output[user_id][lab] = [hardcode_score, code]
                if_literal_use_count += hardcode_score
        hardcoding_percentage = if_literal_use_count / num_students
        logger.debug(f'{if_literal_use_count}/{num_students} compared to literals in an if statement...')
        for user_id in data:
            if hardcoding_percentage > if_literal_threshold:
                output[user_id][lab][0] = 0
    return output


# TODO: check what this is used for, can we remove?
def newtool(data, selected_labs):
    """
    Parameters
    ----------
    data: `dict` [`str`, `dict`]
                    Nested dictionary containing all student submission objects
                    Particular submission can be accessed with data[user_id][lab_id][n]

    Returns
    -------
    newtool_output = {
            'student_id(1)' : {
                    'lab1' : [num_runs, num_develops, num_submits],
                    'lab2' : [num_runs, num_develops, num_submits],
                    .
                    .
                    'labn' : [num_runs, num_develops, num_submits]
            }
    }
    newtool_output = `dict` [`str`][`dict`]

    Nested dictionary of students containing student_id and labs and their results
    """
    newtool_output = {}
    for lab in selected_labs:
        for user_id in data:
            if user_id not in newtool_output:
                newtool_output[user_id] = {}
            num_runs = 0
            num_submits = 0
            num_develops = 0
            if lab in data[user_id]:
                for submission in data[user_id][lab]:
                    num_runs += 1
                    if int(submission.submission[0]) == 1:
                        num_submits += 1
                num_develops = num_runs - num_submits
            newtool_output[user_id][lab] = [num_runs, num_develops, num_submits]
    return newtool_output


##############################
#           Control          #
##############################
"""
Submission object structure (represents each column in the log file)
    Submission = (
        student_id, 
        crid, 
        lab_id, 
        submission_id, 
        type, 
        code, 
        sub_time,
        caption,
        first_name,
        last_name,
        email,
        zip_location,
        submission,
        max_score,
        anomaly_dict=None
    )

Data from create_data_structure function
    data = {
		student_id_1: {
			'lab 1': [
				Submission(), Submission(),
				Submission(), Submission(),
				...
			],
			....
			'lab n': [
				Submission(), Submission(),
				Submission(), Submission(),
				...
			],
		},
		...
		student_id_n: {
			...
		}
	}

newtool_output from user defined function structure 
    newtool_output = {
        student_id : {
            'Lab 1' : [num_runs, num_develops, num_submits],
                ...
            'Lab 2' : [num_runs, num_develops, num_submits],
                ...
            'Lab n' : [num_runs, num_develops, num_submits],
                ...
        }
    }

summary_output structure to be sent to write_output_to_csv function 
-> final_roster[user_id] contains all the column names to be written in the output csv 
    final_roster = {
        student_id : {
            'Lab 1 num of runs' : 7,
            'Lab 1 num of develops' : 6,
            'Lab 1 num of submits' : 1,
            ...
            'Lab 2 num of runs' : 8,
            'Lab 2 num of develops' : 6,
            'Lab 2 num of submits' : 2
        }
    }



"""
if use_standalone:
    logfile_path = input('Enter path to the file including file name: ')
    logfile = pd.read_csv(logfile_path)
    logfile = logfile[logfile.role == 'Student']
    selected_labs = get_selected_labs(logfile)
    logfile = download_code(logfile)
    data = create_data_structure(logfile)

    # This will be sent to the write function
    # (student roster contains keys are student_id, and keys will be columns in the csv)
    student_roster = {}
    newtool_output = newtool(data, selected_labs)
    for student_id in newtool_output:
        for lab in newtool_output[student_id]:
            num_runs = newtool_output[student_id][lab][0]
            num_develops = newtool_output[student_id][lab][1]
            num_submits = newtool_output[student_id][lab][2]
            if student_id in student_roster:
                student_roster[student_id]['Lab ' + str(lab) + ' Num of Runs'] = num_runs
                student_roster[student_id]['Lab ' + str(lab) + ' Num of Develops'] = num_develops
                student_roster[student_id]['Lab ' + str(lab) + ' Num of Submits'] = num_submits
            else:
                student_roster[student_id] = {
                    'User ID': student_id,
                    'Last Name': data[student_id][lab][0].last_name[0],
                    'First Name': data[student_id][lab][0].first_name[0],
                    'Email': data[student_id][lab][0].email[0],
                    'Role': 'Student',
                    'Lab ' + str(lab) + ' Num of Runs': num_runs,
                    'Lab ' + str(lab) + ' Num of Develops': num_develops,
                    'Lab ' + str(lab) + ' Num of Submits': num_submits,
                }
    write_output_to_csv(student_roster)

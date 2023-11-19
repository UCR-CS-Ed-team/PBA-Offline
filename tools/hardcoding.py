import re

import pandas as pd

from tools.utilities import create_data_structure, download_code, get_selected_labs, setup_logger, write_output_to_csv

logger = setup_logger(__name__)  # DEBUGGING

use_standalone = False

# Finds strings of the form 'if (... x == y ...)'
IF_WITH_LITERAL_REGEX = r'(if\s*\(.*\w+\s*==\s*((?:[\"\'][^\"\']*[\"\'])|\d+).*\))'


def get_lines_in_if_scope(code: list[str], start_index: int) -> list[str]:
    """
    Returns the lines of code within the scope of an if statement.
    If 'if' is not in any line, return an empty list.
    """
    if not any('if' in line for line in code):
        return []

    lines_in_scope = []
    brace_count = 0

    # Handles first line being `} else if (...) {`
    # Prevents only the first line being returned
    first_line = code[start_index]
    if first_line.strip().startswith('}'):
        brace_count += 1

    for line in code[start_index:]:
        lines_in_scope.append(line)
        if '{' in line:
            brace_count += 1
        if '}' in line:
            brace_count -= 1
        if brace_count == 0:
            break
    return lines_in_scope


def check_if_with_literal_and_cout(code: str) -> int:
    """
    Returns 1 if code has an if statement comparing to literals, followed by cout.
    Used for case 3: no testcases or solution
    """

    # Remove lines that are empty or are only a left brace
    lines = code.splitlines()
    lines = [line for line in lines if line.strip() not in ('', '{')]

    # Search every line for an 'if' comparing to a literal
    for i, line in enumerate(lines):
        if re.search(IF_WITH_LITERAL_REGEX, line):
            # Check for cout on same or next line
            if 'cout' in line or 'cout' in lines[i + 1]:
                return 1
    return 0


def check_hardcoded_testcase(code: str, testcase: tuple) -> int:
    """Checks whether a code submission hardcoded a testcase.

    Returns 1 if the code:
    - Has an if statement comparing to a literal, followed by cout
    - The literal contains the input testcase, or a part of the testcase
    - The cout outputs the output testcase

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
        if_with_literal_match = re.search(IF_WITH_LITERAL_REGEX, line)
        if if_with_literal_match:
            literal = if_with_literal_match.group(2)  # Isolate literal as a string
            input_hardcoded = input in literal or any(word in literal for word in input.split())

            # Look at all lines in the scope of the `if` statement
            lines_in_if_scope = get_lines_in_if_scope(lines, i)
            for if_line in lines_in_if_scope:
                # Ensure the output testcase occurs after "cout" in the line
                cout_index = if_line.find('cout')
                output_hardcoded = (cout_index != -1) and (if_line.find(output) > cout_index)
                if output_hardcoded:
                    break

            if input_hardcoded and output_hardcoded:
                return 1
    return 0


def get_hardcode_score_with_soln(code: str, testcases: set[tuple], solution_code: str) -> int:
    """Gets a hardcoding score for a submission to a lab with a solution and testcases.

    Returns 1 if the following are true for any testcase:
    - Code hardcodes a testcase in an 'if' statement
    - Solution code does not hardcode the same testcase
    - Solution code does not hardcode most of the testcases (based on percent threshold)

    Args:
        code (str): The student code to be evaluated
        testcases (set[tuple]): Set of testcases, each represented by a tuple of expected input and output
        solution_code (str): The assignment's solution code

    Returns:
        int: The hardcoding score, where 1 indicates the presence of hardcoding and 0 indicates no hardcoding
    """

    is_hardcoded = False
    testcases_in_soln = set()
    testcase_threshold = 0.5

    # Track which testcases are used in the solution
    for testcase in testcases:
        testcase_in_soln = check_hardcoded_testcase(solution_code, testcase)
        if testcase_in_soln:
            testcases_in_soln.add(testcase)

    percent_testcases_in_soln = len(testcases_in_soln) / len(testcases)
    soln_uses_many_testcases = percent_testcases_in_soln >= testcase_threshold

    # Check for hardcoding
    for testcase in testcases:
        testcase_in_code = check_hardcoded_testcase(code, testcase)
        testcase_in_soln = testcase in testcases_in_soln
        if testcase_in_code and not testcase_in_soln and not soln_uses_many_testcases:
            logger.debug(f'is_hardcoded is True for testcase {testcase}.')
            is_hardcoded = True  # TODO: return 1 here, True is for debugging

    if is_hardcoded:
        return 1
    return 0


def get_code_with_max_score(user_id, lab, submissions):
    max_score = 0
    code = submissions[user_id][lab][-1].code  # Choose a default submission
    for sub in submissions[user_id][lab]:
        if sub.max_score > max_score:
            max_score = sub.max_score
            code = sub.code
    return code


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
                    hardcode_score = check_hardcoded_testcase(code, testcase)
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
                hardcode_score = check_if_with_literal_and_cout(code)
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

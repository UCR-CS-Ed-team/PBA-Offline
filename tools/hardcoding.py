import logging
import re

import pandas as pd

from tools.utilities import (
	create_data_structure,
	download_code,
	get_selected_labs,
	write_output_to_csv,
)

use_standalone = False

# DEBUGGING
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(name)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

IF_WITH_LITERAL_REGEX = r'(if\s*\(\s*\w+\s*==\s*(?:(?:[\"\'][^\"\']*[\"\'])|\d+)\s*\))'


def check_if_literal(code: str) -> int:
	"""Returns 1 if code includes an if statement comparing to literals"""

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


def check_testcase_in_code(code: str, testcase: tuple) -> int:
	"""
	Checks whether a testcase is found within a string.
	Returns 1 if the testcase is found, else 0.
	"""
	input = testcase[0]
	output = testcase[1]

	# Remove lines that are empty or are only a left brace
	lines = code.splitlines()
	lines = [line for line in lines if line.strip() not in ('', '{')]

	# Search every line for an 'if' comparing to a literal
	for i, line in enumerate(lines):
		if re.search(IF_WITH_LITERAL_REGEX, line):
			# Ensure the output testcase occurs after "cout" in the line
			cout_index = line.find('cout')
			output_on_same_line = (cout_index != -1) and (line.find(output) > cout_index)
			cout_index = lines[i + 1].find('cout')
			output_on_next_line = (cout_index != -1) and (lines[i + 1].find(output) > cout_index)

			input_hardcoded = input in line or any(word in line for word in input.split())
			output_hardcoded = output_on_same_line or output_on_next_line
			if input_hardcoded and output_hardcoded:
				return 1
	return 0


def get_hardcode_score_with_soln(code: str, testcases: set, solution_code: str) -> int:
	"""
	Returns a score indicating whether student code used hardcoding, based on a logfile's testcases and solution.

	Args:
		code (str): The student code to be evaluated.
		testcases (set[tuple[str, str]]): List of testcases, each represented by a tuple of expected input and output.
		solution_code (str): The solution code for comparison.

	Returns:
		int: The hardcoding score, where 1 indicates the presence of hardcoding and 0 indicates no hardcoding.
	"""
	is_hardcoded = False

	for testcase in testcases:
		testcase_in_code = check_testcase_in_code(code, testcase)
		testcase_in_soln = check_testcase_in_code(solution_code, testcase)
		if testcase_in_code and not testcase_in_soln:
			logger.debug(f'is_hardcoded is True for testcase {testcase}.')
			is_hardcoded = True

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
	if testcases and solution_code:
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
	TESTCASE_USE_THRESHOLD = 0.6
	NUM_STUDENTS = len(data)

	for lab in selected_labs:
		for user_id in data:
			if user_id not in output:
				output[user_id] = {}
			if lab in data[user_id]:
				code = get_code_with_max_score(user_id, lab, data)
				output[user_id][lab] = [0, code, set()]
				for testcase in testcases:  # Track num times students hardcode testcases
					hardcode_score = check_testcase_in_code(code, testcase)
					output[user_id][lab][0] = hardcode_score
					if hardcode_score > 0:
						output[user_id][lab][2].add(testcase)
						testcase_use_counts[testcase] += 1
		for user_id in data:
			for testcase in testcases:
				hardcoded_testcases = output[user_id][lab][2]
				hardcoding_percentage = testcase_use_counts[testcase] / NUM_STUDENTS
				logger.debug(
					f'{testcase_use_counts[testcase]}/{NUM_STUDENTS}, or {round(hardcoding_percentage, 2) * 100}% hardcoded testcase {testcase}...'
				)
				if (testcase in hardcoded_testcases) and (hardcoding_percentage >= TESTCASE_USE_THRESHOLD):
					output[user_id][lab][2].remove(testcase)
					if len(output[user_id][lab][2]) <= 0:
						output[user_id][lab][0] = 0
	return output


def hardcoding_analysis_3(data, selected_labs):
	"""Case 3: no testcases or solution"""
	output = {}
	if_literal_use_count = 0
	IF_LITERAL_THRESHOLD = 0.6
	NUM_STUDENTS = len(data)

	for lab in selected_labs:
		for user_id in data:
			if user_id not in output:
				output[user_id] = {}
			if lab in data[user_id]:
				code = get_code_with_max_score(user_id, lab, data)
				hardcode_score = check_if_literal(code)
				output[user_id][lab] = [hardcode_score, code]
				if_literal_use_count += hardcode_score
		hardcoding_percentage = if_literal_use_count / NUM_STUDENTS
		logger.debug(
			f'{if_literal_use_count}/{NUM_STUDENTS}, or {round(hardcoding_percentage, 2) * 100}% compared to literals in an if statement...'
		)
		for user_id in data:
			if hardcoding_percentage > IF_LITERAL_THRESHOLD:
				output[user_id][lab][0] = 0
	return output


def hardcoding_analysis(data, selected_labs, testcases, solution_code):
	output = {}

	try:
		if testcases and solution_code:
			for lab in selected_labs:
				for user_id in data:
					if user_id not in output:
						output[user_id] = {}
					if lab in data[user_id]:
						code = get_code_with_max_score(user_id, lab, data)
						hardcode_score = get_hardcode_score_with_soln(code, testcases, solution_code)
						output[user_id][lab] = [hardcode_score, code]

		elif testcases and not solution_code:
			testcase_use_counts = {testcase: 0 for testcase in testcases}
			TESTCASE_USE_THRESHOLD = 0.6
			NUM_STUDENTS = len(data)

			for lab in selected_labs:
				for user_id in data:
					if user_id not in output:
						output[user_id] = {}
					if lab in data[user_id]:
						code = get_code_with_max_score(user_id, lab, data)
						output[user_id][lab] = [0, code, set()]
						for testcase in testcases:  # Track num times students hardcode testcases
							hardcode_score = check_testcase_in_code(code, testcase)
							output[user_id][lab][0] = hardcode_score
							if hardcode_score > 0:
								output[user_id][lab][2].add(testcase)
								testcase_use_counts[testcase] += 1

				for user_id in data:
					for testcase in testcases:
						hardcoded_testcases = output[user_id][lab][2]
						hardcoding_percentage = testcase_use_counts[testcase] / NUM_STUDENTS
						logger.debug(
							f'{testcase_use_counts[testcase]}/{NUM_STUDENTS}, or {round(hardcoding_percentage, 2) * 100}% hardcoded testcase {testcase}...'
						)
						if (testcase in hardcoded_testcases) and (hardcoding_percentage >= TESTCASE_USE_THRESHOLD):
							output[user_id][lab][2].remove(testcase)
							if len(output[user_id][lab][2]) <= 0:
								output[user_id][lab][0] = 0

		elif not testcases and not solution_code:
			if_literal_use_count = 0
			IF_LITERAL_THRESHOLD = 0.6
			NUM_STUDENTS = len(data)

			for lab in selected_labs:
				for user_id in data:
					if user_id not in output:
						output[user_id] = {}
					if lab in data[user_id]:
						code = get_code_with_max_score(user_id, lab, data)
						hardcode_score = check_if_literal(code)
						output[user_id][lab] = [hardcode_score, code]
						if_literal_use_count += hardcode_score

				hardcoding_percentage = if_literal_use_count / NUM_STUDENTS
				logger.debug(
					f'{if_literal_use_count}/{NUM_STUDENTS}, or {round(hardcoding_percentage, 2) * 100}% compared to literals in an if statement...'
				)
				for user_id in data:
					if hardcoding_percentage > IF_LITERAL_THRESHOLD:
						output[user_id][lab][0] = 0

		else:
			raise Exception('Unexpected input during hardcode analysis')

		return output

	except Exception as e:
		logger.error(f'Error: {e}')
		exit(1)


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
	
	Nested dictionary of students containg student_id and labs and their results
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
				for subObj in data[user_id][lab]:
					num_runs += 1
					# print(int(subObj.submission[0]))
					if int(subObj.submission[0]) == 1:
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
	# logfile_path = '/Users/abhinavreddy/Downloads/standalone_incdev_analysis/input/logfile1.csv'
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

import logging
import os
from tkinter import filedialog

import pandas as pd

import tools.hardcoding
from tools import incdev
from tools.anomaly import anomaly
from tools.quickanalysis import quick_analysis
from tools.roster import roster
from tools.stylechecker import stylechecker
from tools.utilities import (
	create_data_structure,
	download_code,
	download_solution,
	get_selected_labs,
	get_testcases,
	write_output_to_csv,
)

# DEBUGGING
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(name)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

if __name__ == '__main__':
	# Read logfile into a Pandas DataFrame
	file_path = filedialog.askopenfilename()
	folder_path = os.path.split(file_path)[0]
	filename = os.path.basename(file_path).split('/')[-1]
	logfile = pd.read_csv(file_path)

	# Locate solution in logfile and download its code
	solution_code = download_solution(logfile)

	# Save student submission URLs and selected labs
	logfile = logfile[logfile.role == 'Student']
	urls = logfile.zip_location.to_list()
	selected_labs = get_selected_labs(logfile)

	data = {}
	final_roster = {}
	prompt = (
		'\n1. Quick Analysis (averages for all labs) \n'
		'2. Basic statisics (roster for selected labs) \n'
		'3. Anomalies (selected labs) \n'
		'4. Coding Trails (all labs) \n'
		'6. Automatic anomaly detection (selected labs) \n'
		'7. Hardcoding detection (selected labs) \n'
		'8. Quit \n'
	)

	# TESTING
	hardcode_example = '#include <iostream>\n#include <vector>\nusing namespace std;\n\nint main() {\n   vector<int> userInput;\n   int minVal = 0;\n   unsigned int i;\n   \n   for(i = 0; i < userInput.size(); ++i) {\n      cin >> userInput.at(i);\n   }\n   \n   for(i = 0; i < userInput.size(); ++i) {\n      cout << userInput.at(i) << " ";\n   }\n   \n   cout << endl;\n      \n   \n   /*string x;\n   getline(cin, x);*/\n   \n   /*if(x == "5 10 5 3 21 2"){\n      cout << "2 3" << endl;\n   }\n   if(x == "4 1 2 31 15"){\n      cout << "1 2" << endl;\n   }\n   if(x == "5 1 8 91 23 7"){\n      cout << "1 7" << endl;\n   }*/\n   \n\n   return 0;\n}\n'

	while 1:
		print(prompt)
		inp = input()
		final_roster = {}
		input_list = inp.split(' ')
		for i in input_list:
			inp = int(i)

			# Quick analysis for every lab
			if inp == 1:
				quick_analysis(logfile)

			# Roster for selected labs
			elif inp == 2:
				final_roster = roster(logfile, selected_labs)

			# Anomalies for selected labs
			elif inp == 3:
				if data == {}:
					logfile = download_code(logfile)
					data = create_data_structure(logfile)
				anomaly_detection_output = anomaly(data, selected_labs, 0)
				for user_id in anomaly_detection_output:
					for lab in anomaly_detection_output[user_id]:
						anomalies_found = anomaly_detection_output[user_id][lab][0]
						anomaly_score = anomaly_detection_output[user_id][lab][1]
						if user_id in final_roster:
							final_roster[user_id]['Lab ' + str(lab) + ' anomalies found'] = anomalies_found
							final_roster[user_id]['Lab ' + str(lab) + ' anomaly score'] = anomaly_score
							final_roster[user_id][str(lab) + ' Student code'] = anomaly_detection_output[user_id][lab][
								2
							]
						else:
							final_roster[user_id] = {
								'User ID': user_id,
								'Last Name': data[user_id][lab][0].last_name[0],
								'First Name': data[user_id][lab][0].first_name[0],
								'Email': data[user_id][lab][0].email[0],
								'Role': 'Student',
								'Lab ' + str(lab) + ' anomalies found': anomalies_found,
								'Lab ' + str(lab) + ' anomaly score': anomaly_score,
								str(lab) + ' Student code': anomaly_detection_output[user_id][lab][2],
							}

			# Inc. development coding trails for all labs
			elif inp == 4:
				if data == {}:
					logfile = download_code(logfile)
					data = create_data_structure(logfile)
				# Generate nested dict of IncDev results
				incdev_output = incdev.run(data)
				for user_id in incdev_output:
					for lab_id in incdev_output[user_id]:
						lid = str(lab_id)
						score = incdev_output[user_id][lab_id]['incdev_score']
						score_trail = incdev_output[user_id][lab_id]['incdev_score_trail']
						loc_trail = incdev_output[user_id][lab_id]['loc_trail']
						time_trail = incdev_output[user_id][lab_id]['time_trail']
						code = incdev_output[user_id][lab_id]['Highest_code']
						if user_id in final_roster:
							final_roster[user_id][lid + ' incdev_score'] = score
							final_roster[user_id][lid + ' incdev_score_trail'] = score_trail
							final_roster[user_id][lid + ' loc_trail'] = loc_trail
							final_roster[user_id][lid + ' time_trail'] = time_trail
							final_roster[user_id][str(lid) + ' Student code'] = code
						else:
							final_roster[user_id] = {
								'User ID': user_id,
								'Last Name': data[user_id][lab_id][0].last_name[0],
								'First Name': data[user_id][lab_id][0].first_name[0],
								'Email': data[user_id][lab_id][0].email[0],
								'Role': 'Student',
								lid + ' incdev_score': score,
								lid + ' incdev_score_trail': score_trail,
								lid + ' loc_trail': loc_trail,
								lid + ' time_trail': time_trail,
								str(lab_id) + ' Student code': code,
							}

			# Style anomalies for selected labs using cpplint
			elif inp == 5:
				if data == {}:
					logfile = download_code(logfile)
					data = create_data_structure(logfile)
				stylechecker_output = stylechecker(data, selected_labs)
				for user_id in stylechecker_output:
					for lab_id in stylechecker_output[user_id]:
						if user_id in final_roster:
							final_roster[user_id][str(lab_id) + 'Style score'] = stylechecker_output[user_id][lab_id][0]
							final_roster[user_id][str(lab_id) + 'Style output'] = stylechecker_output[user_id][lab_id][
								1
							]
							final_roster[user_id][str(lab_id) + ' Student code'] = stylechecker_output[user_id][lab_id][
								2
							]
						else:
							final_roster[user_id] = {
								'User ID': user_id,
								'Last Name': data[user_id][lab_id][0].last_name[0],
								'First Name': data[user_id][lab_id][0].first_name[0],
								'Email': data[user_id][lab_id][0].email[0],
								'Role': 'Student',
								str(lab_id) + '  Style score': stylechecker_output[user_id][lab_id][0],
								str(lab_id) + '  Style output': stylechecker_output[user_id][lab_id][1],
								str(lab_id) + ' Student code': stylechecker_output[user_id][lab_id][2],
							}

			# Automatic anomaly detection for selected labs
			elif inp == 6:
				final_roster = {}  # Reset roster, fixme later
				if data == {}:
					logfile = download_code(logfile)
					data = create_data_structure(logfile)
				# Count of anomaly instances per-user, per-lab, per-anomaly, @ index 0
				anomaly_detection_output = anomaly(data, selected_labs, 1)

				# Populate anomaly counts for every user, for each lab
				for user_id in anomaly_detection_output:
					if user_id not in final_roster:
						final_roster[user_id] = {'User ID': user_id}  # Populate column of user IDs
					for lab in anomaly_detection_output[user_id]:
						# Instance count of every anomaly for [user_id][lab]
						anomalies_found = anomaly_detection_output[user_id][lab][0]
						# Create a column for each anomaly with the anomaly's count
						for anomaly in anomalies_found:
							final_roster[user_id][f'Lab {str(lab)} {anomaly}'] = anomalies_found[anomaly]

				# Count of users that use each anomaly, per-lab
				num_users_per_anomaly = {}
				for anomaly in anomalies_found:
					num_users_per_anomaly[anomaly] = {}

				# Count the *number of students* that used each anomaly, per-lab
				for user_id in final_roster:
					for lab in anomaly_detection_output[user_id]:
						for anomaly in num_users_per_anomaly:
							# Need to consider anomalies from every lab
							if lab not in num_users_per_anomaly[anomaly]:
								num_users_per_anomaly[anomaly][lab] = 0
							anomaly_count = final_roster[user_id][f'Lab {str(lab)} {anomaly}']
							if anomaly_count > 0:
								num_users_per_anomaly[anomaly][lab] += 1

				# Append a row at bottom for "totals"
				final_roster['Status'] = {}
				final_roster['Status']['User ID'] = 'Is Anomaly?'
				for anomaly in num_users_per_anomaly:
					for lab in num_users_per_anomaly[anomaly]:
						anomaly_count = num_users_per_anomaly[anomaly][lab]
						total_users = len(data)
						# If a clear majority uses an "anomaly", it's not anomalous
						if anomaly_count / total_users >= 0.8:
							final_roster['Status'][f'Lab {str(lab)} {anomaly}'] = 'No'
						else:
							final_roster['Status'][f'Lab {str(lab)} {anomaly}'] = 'Yes'

				# Outputs to its own file for now
				write_output_to_csv(final_roster, 'anomaly_counts.csv')

			# Hardcode detection for selected labs
			elif inp == 7:
				if data == {}:
					logfile = download_code(logfile)
					data = create_data_structure(logfile)

				# TESTING, set code to hardcoding example
				# set_code_in_logfile(data, hardcode_example, 0.8)

				# Tuple of testcases: (output, input)
				testcases = get_testcases(logfile)

				try:
					if testcases and solution_code:
						logger.debug('Case 1: testcases and solution')
						hardcoding_results = tools.hardcoding.hardcoding_analysis_1(
							data, selected_labs, testcases, solution_code
						)
					elif testcases and not solution_code:
						logger.debug('Case 2: testcases, no solution')
						hardcoding_results = tools.hardcoding.hardcoding_analysis_2(data, selected_labs, testcases)
					elif not testcases and not solution_code:
						logger.debug('Case 3: no testcases or solution')
						hardcoding_results = tools.hardcoding.hardcoding_analysis_3(data, selected_labs)
					else:
						raise Exception('Unexpected input during hardcode analysis')
				except Exception as e:
					logger.error(f'Error: {e}')
					exit(1)

				for user_id in hardcoding_results:
					for lab in hardcoding_results[user_id]:
						hardcoding_score = hardcoding_results[user_id][lab][0]
						student_code = hardcoding_results[user_id][lab][1]
						if user_id in final_roster:
							final_roster[user_id]['Lab ' + str(lab) + ' hardcoding score'] = hardcoding_score
							final_roster[user_id][str(lab) + ' Student code'] = student_code
						else:
							final_roster[user_id] = {
								'User ID': user_id,
								'Last Name': data[user_id][lab][0].last_name[0],
								'First Name': data[user_id][lab][0].first_name[0],
								'Email': data[user_id][lab][0].email[0],
								'Role': 'Student',
								'Lab ' + str(lab) + ' hardcoding score': hardcoding_score,
								str(lab) + ' Student code': student_code,
							}

			elif inp == 8:
				exit(0)

			else:
				print('Please select a valid option')

		if len(final_roster) != 0:
			write_output_to_csv(final_roster)

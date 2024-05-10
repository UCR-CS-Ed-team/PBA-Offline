from tkinter import filedialog

import pandas as pd

import tools.hardcoding
import tools.hardcoding_test
import tools.utilities as util
from tools.anomaly import anomaly
from tools.incdev import run
from tools.quickanalysis import quick_analysis
from tools.roster import roster
from tools.stylechecker import stylechecker


def main():
    logger = util.setup_logger(__name__)  # DEBUGGING

    # Read logfile into a Pandas DataFrame
    logfile_path = filedialog.askopenfilename(filetypes=[('CSV files', '*.csv')])
    if not logfile_path:
        print('No file selected. Goodbye!')
        exit(0)
    logfile = pd.read_csv(logfile_path)
    logfile = util.standardize_columns(logfile)

    solution_code = util.download_solution(logfile)
    selected_labs = util.get_selected_labs(logfile)
    logfile = logfile[logfile.role == 'Student']  # Filter by students only

    submissions = {}
    tool_result = {}
    output_file_name = 'roster.csv'
    prompt = (
        '\n1. Quick Analysis (averages for all labs) \n'
        '2. Basic statistics (roster for selected labs) \n'
        '3. Anomalies (selected labs) \n'
        '4. Coding Trails (all labs) \n'
        '6. Automatic anomaly detection (selected labs) \n'
        '7. Hardcoding detection (selected labs) \n'
        '8. Manual hardcoding test \n'
        '9. Quit \n'
    )

    while True:
        tool_result = {}
        print(prompt)

        while True:  # Validate user inputs
            all_valid = True
            input_list = [i.strip() for i in input().split()]
            for i in input_list:
                if not (i.isdigit() and 1 <= int(i) <= 9):
                    all_valid = False
                    print('Inputs must all be digits 1-9, please try again.')
                    break
            if all_valid:
                break

        for i in input_list:
            user_input = int(i)

            if user_input != 9 and submissions == {}:
                logfile_with_code = util.download_code(logfile)
                submissions = util.create_data_structure(logfile_with_code)

            # Quick analysis for every lab
            if user_input == 1:
                output_file_name = 'quick_analysis.csv'
                quick_analysis(logfile_with_code)  # TODO: this should return something

            # Roster for selected labs
            elif user_input == 2:
                output_file_name = 'roster.csv'
                tool_result = roster(logfile_with_code, selected_labs)

            # Anomalies for selected labs
            elif user_input == 3:
                output_file_name = 'anomalies.csv'
                anomaly_detection_output = anomaly(submissions, selected_labs)
                for user_id in anomaly_detection_output:
                    for lab in anomaly_detection_output[user_id]:
                        anomalies_found = anomaly_detection_output[user_id][lab][0]
                        anomaly_score = anomaly_detection_output[user_id][lab][1]
                        if user_id in tool_result:
                            tool_result[user_id][f'Lab {lab} anomalies found'] = anomalies_found
                            tool_result[user_id][f'Lab {lab} anomaly score'] = anomaly_score
                            tool_result[user_id][f'{lab} Student code'] = anomaly_detection_output[user_id][lab][2]
                        else:
                            tool_result[user_id] = {
                                'User ID': user_id,
                                'Last Name': submissions[user_id][lab][0].last_name[0],
                                'First Name': submissions[user_id][lab][0].first_name[0],
                                'Email': submissions[user_id][lab][0].email[0],
                                'Role': 'Student',
                                'Lab ' + str(lab) + ' anomalies found': anomalies_found,
                                'Lab ' + str(lab) + ' anomaly score': anomaly_score,
                                str(lab) + ' Student code': anomaly_detection_output[user_id][lab][2],
                            }

            # Inc. development coding trails for all labs
            elif user_input == 4:
                output_file_name = 'incdev.csv'
                # Generate nested dict of IncDev results
                incdev_output = run(submissions)
                for user_id in incdev_output:
                    for lab_id in incdev_output[user_id]:
                        lid = str(lab_id)
                        score = incdev_output[user_id][lab_id]['incdev_score']
                        score_trail = incdev_output[user_id][lab_id]['incdev_score_trail']
                        loc_trail = incdev_output[user_id][lab_id]['loc_trail']
                        time_trail = incdev_output[user_id][lab_id]['time_trail']
                        code = incdev_output[user_id][lab_id]['Highest_code']
                        if user_id in tool_result:
                            tool_result[user_id][lid + ' incdev_score'] = score
                            tool_result[user_id][lid + ' incdev_score_trail'] = score_trail
                            tool_result[user_id][lid + ' loc_trail'] = loc_trail
                            tool_result[user_id][lid + ' time_trail'] = time_trail
                            tool_result[user_id][str(lid) + ' Student code'] = code
                        else:
                            tool_result[user_id] = {
                                'User ID': user_id,
                                'Last Name': submissions[user_id][lab_id][0].last_name[0],
                                'First Name': submissions[user_id][lab_id][0].first_name[0],
                                'Email': submissions[user_id][lab_id][0].email[0],
                                'Role': 'Student',
                                lid + ' incdev_score': score,
                                lid + ' incdev_score_trail': score_trail,
                                lid + ' loc_trail': loc_trail,
                                lid + ' time_trail': time_trail,
                                str(lab_id) + ' Student code': code,
                            }

            # Style anomalies for selected labs using cpplint
            elif user_input == 5:
                output_file_name = 'cpp_style.csv'
                stylechecker_output = stylechecker(submissions, selected_labs)
                for user_id in stylechecker_output:
                    for lab_id in stylechecker_output[user_id]:
                        if user_id in tool_result:
                            tool_result[user_id][f'{lab_id} Style score'] = stylechecker_output[user_id][lab_id][0]
                            tool_result[user_id][f'{lab_id} Style output'] = stylechecker_output[user_id][lab_id][1]
                            tool_result[user_id][f'{lab_id} Student code'] = stylechecker_output[user_id][lab_id][2]
                        else:
                            tool_result[user_id] = {
                                'User ID': user_id,
                                'Last Name': submissions[user_id][lab_id][0].last_name[0],
                                'First Name': submissions[user_id][lab_id][0].first_name[0],
                                'Email': submissions[user_id][lab_id][0].email[0],
                                'Role': 'Student',
                                str(lab_id) + '  Style score': stylechecker_output[user_id][lab_id][0],
                                str(lab_id) + '  Style output': stylechecker_output[user_id][lab_id][1],
                                str(lab_id) + ' Student code': stylechecker_output[user_id][lab_id][2],
                            }

            # Automatic anomaly detection for selected labs
            elif user_input == 6:
                output_file_name = 'auto_anomaly.csv'
                tool_result = {}  # TODO: reset roster, fix later
                # Count of anomaly instances per-user, per-lab, per-anomaly, @ index 0
                anomaly_detection_output = anomaly(submissions, selected_labs, 1)

                # Populate anomaly counts for every user, for each lab
                for user_id in anomaly_detection_output:
                    if user_id not in tool_result:
                        tool_result[user_id] = {'User ID': user_id}  # Populate column of user IDs
                    for lab in anomaly_detection_output[user_id]:
                        # Instance count of every anomaly for [user_id][lab]
                        anomalies_found = anomaly_detection_output[user_id][lab][0]
                        # Create a column for each anomaly with the anomaly's count
                        for found_anomaly in anomalies_found:
                            tool_result[user_id][f'Lab {str(lab)} {found_anomaly}'] = anomalies_found[found_anomaly]

                # Count of users that use each anomaly, per-lab
                num_users_per_anomaly = {}
                for found_anomaly in anomalies_found:
                    num_users_per_anomaly[found_anomaly] = {}

                # Count the *number of students* that used each anomaly, per-lab
                for user_id in tool_result:
                    for lab in anomaly_detection_output[user_id]:
                        for found_anomaly in num_users_per_anomaly:
                            # Need to consider anomalies from every lab
                            if lab not in num_users_per_anomaly[found_anomaly]:
                                num_users_per_anomaly[found_anomaly][lab] = 0
                            anomaly_count = tool_result[user_id][f'Lab {str(lab)} {found_anomaly}']
                            if anomaly_count > 0:
                                num_users_per_anomaly[found_anomaly][lab] += 1

                # Append a row at bottom for "totals"
                tool_result['Status'] = {}
                tool_result['Status']['User ID'] = 'Is Anomaly?'
                for found_anomaly in num_users_per_anomaly:
                    for lab in num_users_per_anomaly[found_anomaly]:
                        anomaly_count = num_users_per_anomaly[found_anomaly][lab]
                        total_users = len(submissions)
                        # If a clear majority uses an "anomaly", it's not anomalous
                        if anomaly_count / total_users >= 0.8:
                            tool_result['Status'][f'Lab {str(lab)} {found_anomaly}'] = 'No'
                        else:
                            tool_result['Status'][f'Lab {str(lab)} {found_anomaly}'] = 'Yes'

                # Outputs to its own file for now
                util.write_output_to_csv(tool_result, 'anomaly_counts.csv')

            # Hardcode detection for selected labs
            elif user_input == 7:
                output_file_name = 'hardcoding.csv'

                # Dictionary of testcases, e.g. `lab_id : [('in1', 'out1'), ('in2', 'out2')]`
                testcases = util.get_testcases(logfile_with_code, selected_labs)

                try:
                    if testcases and solution_code:
                        logger.debug('Case 1: testcases and solution')
                        hardcoding_results = tools.hardcoding.hardcoding_analysis_1(
                            submissions, selected_labs, testcases, solution_code
                        )
                    elif testcases and not solution_code:
                        logger.debug('Case 2: testcases, no solution')
                        hardcoding_results = tools.hardcoding.hardcoding_analysis_2(
                            submissions, selected_labs, testcases
                        )
                    elif not testcases and not solution_code:
                        logger.debug('Case 3: no testcases or solution')
                        hardcoding_results = tools.hardcoding.hardcoding_analysis_3(submissions, selected_labs)
                    else:
                        raise Exception('Unexpected input during hardcode analysis')
                except Exception as e:
                    logger.error(f'Error: {e}')
                    exit(1)

                for user_id in hardcoding_results:
                    for lab in hardcoding_results[user_id]:
                        hardcoding_score = hardcoding_results[user_id][lab][0]
                        student_code = hardcoding_results[user_id][lab][1]
                        if user_id in tool_result:
                            tool_result[user_id]['Lab ' + str(lab) + ' hardcoding score'] = hardcoding_score
                            tool_result[user_id][str(lab) + ' Student code'] = student_code
                        else:
                            tool_result[user_id] = {
                                'User ID': user_id,
                                'Last Name': submissions[user_id][lab][0].last_name[0],
                                'First Name': submissions[user_id][lab][0].first_name[0],
                                'Email': submissions[user_id][lab][0].email[0],
                                'Role': 'Student',
                                'Lab ' + str(lab) + ' hardcoding score': hardcoding_score,
                                str(lab) + ' Student code': student_code,
                            }

            elif user_input == 8:
                output_file_name = 'hardcoding-test.csv'
                test_results = tools.hardcoding_test.manual_test(submissions, selected_labs)

                for user_id in test_results:
                    for lab in test_results[user_id]:
                        hardcoding_score = test_results[user_id][lab][0]
                        student_code = test_results[user_id][lab][1]
                        if user_id in tool_result:
                            tool_result[user_id]['Lab ' + str(lab) + ' hardcoded?'] = hardcoding_score
                            tool_result[user_id][str(lab) + ' Student code'] = student_code
                        else:
                            tool_result[user_id] = {
                                'User ID': user_id,
                                'Last Name': submissions[user_id][lab][0].last_name[0],
                                'First Name': submissions[user_id][lab][0].first_name[0],
                                'Email': submissions[user_id][lab][0].email[0],
                                'Role': 'Student',
                                'Lab ' + str(lab) + ' hardcoded?': hardcoding_score,
                                str(lab) + ' Student code': student_code,
                            }

            elif user_input == 9:
                exit(0)

            else:
                print('Please select a valid option')

        if len(tool_result) != 0:
            util.write_output_to_csv(tool_result, output_file_name)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Goodbye!')
        exit(0)

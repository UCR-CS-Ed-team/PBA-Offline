import os
import subprocess

import pandas as pd

from tools.utilities import (
    create_data_structure,
    download_code,
    get_selected_labs,
    write_output_to_csv,
)

use_standalone = False
cpplint_file = 'output/code.cpp'


def stylechecker(data, selected_labs):
    """
    stylechecker_output from user defined function structure
    Input:
    ------
        Accepts the students data and selected labs as an input

    Output:
    -------
        stylechecker_output = {
            student_id : {
                'Lab 1' : [style_score, output1, code],
                    ...
                'Lab 2' : [style_score, output1, code],
                    ...
                'Lab n' : [style_score, output1, code],
                    ...
            }
        }

    Note:
        Todo: This currently creates a new .cpp file and runs the package on that, modify it in
                    such a way to avoid creating a new file and directly use the code in data
    """
    output = {}
    for lab in selected_labs:
        for user_id in data:
            if lab in data[user_id]:
                max_score = 0
                for sub in data[user_id][lab]:
                    if sub.max_score > max_score:
                        max_score = sub.max_score
                        code = sub.code
                with open(cpplint_file, 'w') as file:
                    file.write(code)
                command = 'cpplint ' + cpplint_file
                output1 = subprocess.getoutput(command)
                style_score = 0
                if output1 != 'Done processing ' + cpplint_file:
                    lines = output1.splitlines()
                    style_score = lines[-1].split(':')[1].strip()
                os.remove(cpplint_file)
                output[user_id] = {lab: [style_score, output1, code]}
    return output


##############################
#           Control          #
##############################
if use_standalone:
    logfile_path = '/Users/abhinavreddy/Downloads/standalone_incdev_analysis/input/logfile.csv'
    logfile = pd.read_csv(logfile_path)
    logfile = logfile[logfile.role == 'Student']
    selected_labs = get_selected_labs(logfile)
    logfile = download_code(logfile)
    data = create_data_structure(logfile)
    summary_roster = {}
    cpplint_file = '../output/code.cpp'
    stylechecker_output = stylechecker(data, selected_labs)
    for user_id in stylechecker_output:
        for lab_id in stylechecker_output[user_id]:
            if user_id in summary_roster:
                summary_roster[user_id][str(lab_id) + ' Style score'] = stylechecker_output[user_id][lab_id][0]
                summary_roster[user_id][str(lab_id) + ' Style output'] = stylechecker_output[user_id][lab_id][1]
                summary_roster[user_id][str(lab_id) + ' Student code'] = stylechecker_output[user_id][lab_id][2]
            else:
                summary_roster[user_id] = {
                    'User ID': user_id,
                    'Last Name': data[user_id][lab_id][0].last_name[0],
                    'First Name': data[user_id][lab_id][0].first_name[0],
                    'Email': data[user_id][lab_id][0].email[0],
                    'Role': 'Student',
                    str(lab_id) + '  Style score': stylechecker_output[user_id][lab_id][0],
                    str(lab_id) + '  Style output': stylechecker_output[user_id][lab_id][1],
                    str(lab_id) + ' Student code': stylechecker_output[user_id][lab_id][2],
                }
    write_output_to_csv(summary_roster)

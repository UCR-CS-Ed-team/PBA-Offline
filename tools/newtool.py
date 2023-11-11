import pandas as pd

from tools.utilities import (
    create_data_structure,
    download_code,
    get_selected_labs,
    write_output_to_csv,
)

use_standalone = True


##############################
#       User Functions       #
##############################
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

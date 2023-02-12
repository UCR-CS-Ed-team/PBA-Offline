import subprocess
import os
import zipfile
import pandas as pd
import requests
from datetime import datetime
import csv
import io
import re
from urllib3 import Retry
from tools.submission import Submission
from concurrent.futures import ThreadPoolExecutor, as_completed

use_standalone = False

##############################
#       Helper Functions     #
##############################
class Not200Exception(Exception):
    """Raise this custom exception if we receive a "valid" response from the server, but no data is present"""
    pass

def get_valid_datetime(timestamp):
    '''
    There are lots of different datetime formats, this function accounts for those and returns the timestamp
    '''
    t = timestamp
    for fmt in ('%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S','%m/%d/%y %H:%M'):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            pass
    raise ValueError('Cannot recognize datetime format: ' + t)

def download_code_helper(url):
    '''
    Actual code which downloads the students code run using requests library
    '''
    # Define our retry strategy for all HTTP requests
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    file_name = url.split('/')[-1].strip('.zip')
    path = '../downloads/' + file_name +'.cpp'
    if not os.path.isfile(path):
        # print('downloading')
        try:
            response = session.get(url)
            if response.status_code > 200 and response.status_code < 300:
                raise Not200Exception
            zfile = zipfile.ZipFile(io.BytesIO(response.content))
            filenames = zfile.namelist()
            content = zfile.open(filenames[0], 'r').read()
            result = content.decode('utf-8')
            with open(path, 'w') as file:
                file.write(result)
            return (url, result)
        except Not200Exception:
            return (url, "Successfully received a response, but not data was received")
        except ConnectionError:
            return (url, "Max retries met, cannot retrieve student code submission")
    else:
        # print('not downloading')
        with open(path, 'r') as file:
            result = file.read()
        return (url, result)

def download_code(logfile):
    '''
    Iterates through the zybooks logfile dataframe and appends a new column "student_code" to the dataframe and return it 

    Note: This is the fastest way to download code submissions of all students at this time. We tried AsyncIO but it turned out to be slower than multithreading
    '''
    urls = logfile.zip_location.to_list()
    threads = []
    with ThreadPoolExecutor() as executor:
        for url in urls:
            threads.append(executor.submit(download_code_helper, url))
        student_code = []
        i = 0
        for task in as_completed(threads):
            # print(i)
            student_code.append(task.result())
            i += 1
    df = pd.DataFrame(student_code, columns = ['zip_location', 'student_code'])
    logfile = pd.merge(left=logfile, right=df, on=['zip_location'])
    return logfile

def get_selected_labs(logfile):
    '''
    Function to get selected labs from the user entered input
    '''
    lab_ids = logfile.content_section.unique()
    # Select the labs you want a roster for 
    print('Select the indexes you want a roster for seperated by a space: (Ex: 1 or 1 2 3 or 2 3)')
    labs_list = []
    i = 1
    for lab_id in lab_ids:
        print(i,' ', lab_id, logfile.query('content_section =='+ str(lab_id))['caption'].iloc[0])
        labs_list.append(lab_id)
        i += 1
    selected_options = input()
    selected_lab_index = selected_options.split(' ')
    selected_labs = []
    for selected_lab in selected_lab_index:
        selected_labs.append(labs_list[int(selected_lab)-1])
    return selected_labs

def write_output_to_csv(final_roster):
    '''
    This function writes our dataframe into a csv output file
    '''
    # # Writing the output to the csv file 
    now = str(datetime.now())
    csv_columns = []
    for id in final_roster:
        for column in final_roster[id]:
            csv_columns.append(column)
        break             
    try:
        csv_file = '../output/roster'+ now + '.csv'
        with open(csv_file, 'w') as f1:
            writer = csv.DictWriter(f1, fieldnames=csv_columns)
            writer.writeheader()
            for user_id in final_roster.keys():
                writer.writerow(final_roster[user_id])
    except IOError:
        print('IO Error')

def create_data_structure(logfile):
    '''
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
    '''
    data = {}
    for row in logfile.itertuples():
        if row.user_id not in data:
            data[int(row.user_id)] = {}
        if row.content_section not in data[row.user_id]:
            data[row.user_id][row.content_section] = []
        # url, result = get_code(row.zip_location)
        sub = Submission(
            student_id = row.user_id,
            crid = row.content_resource_id,
            caption = row.caption,
            first_name = row.first_name,
            last_name = row.last_name,
            email = row.email,
            zip_location = row.zip_location,
            submission = row.submission,
            max_score = row.max_score,
            lab_id = row.content_section,
            submission_id = row.zip_location.split('/')[-1],
            type = row.submission,
            code = row.student_code,
            sub_time = get_valid_datetime(row.date_submitted),
            anomaly_dict=None
        )
        data[row.user_id][row.content_section].append(sub)
    return data

##############################
#       User Functions       #
##############################

IF_WITH_LITERAL_REGEX = r"(if\s*\(\s*\w+\s*==\s*(?:(?:[\"\'][^\"\']*[\"\'])|\d+)\s*\))"

def get_hardcoding_score(code, testcases):
    lines = code.splitlines()

    # Remove lines that are empty or are only a left brace
    lines = [line for line in lines if line.strip() not in ('', '{')]

    for i, line in enumerate(lines):
        if re.search(IF_WITH_LITERAL_REGEX, line):
            cout_on_next_line = "cout" in lines[i+1] and any(testcase in lines[i+1] for testcase in testcases)
            cout_on_same_line = "cout" in line and any(testcase in line for testcase in testcases)
            if cout_on_next_line or cout_on_same_line:
                print(f"\n Hardcoding detected: \n {line} \n {lines[i+1]}")
                return 1

    return 0

def hardcoding_analysis(data, selected_labs, testcases):
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

                hardcode_score = get_hardcoding_score(code, testcases)
                output[user_id][lab] = [hardcode_score, code]
    return output

def newtool(data, selected_labs):
    '''
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
            
    '''
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
'''
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



'''
if use_standalone == True:
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
                                'Lab ' + str(lab) + ' Num of Submits': num_submits
                            }
    write_output_to_csv(student_roster)
import subprocess
import os
import zipfile
import pandas as pd
import requests
from datetime import datetime
import csv
import io
from urllib3 import Retry
from tools.submission import Submission
from concurrent.futures import ThreadPoolExecutor, as_completed

use_standalone = False
cpplint_file = 'output/code.cpp'

##############################
#       Helper Functions     #
##############################
class Not200Exception(Exception):
    """Raise this custom exception if we receive a "valid" response from the server, but no data is present"""
    pass

def get_valid_datetime(timestamp):
    t = timestamp
    for fmt in ('%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S','%m/%d/%y %H:%M'):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            pass
    raise ValueError('Cannot recognize datetime format: ' + t)

def download_code_helper(url):
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
def stylechecker(data, selected_labs):
    '''
    stylechecker_output from user defined function structure 
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
    '''
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
                command = 'cpplint '+ cpplint_file
                output1 = subprocess.getoutput(command)
                style_score = 0
                if output1 != 'Done processing ' + cpplint_file:
                    lines = output1.splitlines()
                    style_score = lines[-1].split(':')[1].strip()
                os.remove(cpplint_file)
                output[user_id] = { lab : [style_score, output1, code]}
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
                    str(lab_id) + '  Style score' : stylechecker_output[user_id][lab_id][0],
                    str(lab_id) + '  Style output' : stylechecker_output[user_id][lab_id][1],
                    str(lab_id) + ' Student code' : stylechecker_output[user_id][lab_id][2]
                }
    write_output_to_csv(summary_roster)
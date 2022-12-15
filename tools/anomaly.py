import pandas as pd
import re
import os
import requests
import zipfile
from datetime import datetime
import csv
import io
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
        print(f"Result stored at {csv_file}")
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
def get_anomaly_score(code):
    # Below is the format for the anomaly in question
    # [Count_instances, Points/instance, anomaly on/off, regex, whether its used for once (used for !count instances)]
    # Add to the hashmap Styleanomaly in case you need new anomaly to be detected
    Styleanomaly = {
        'Pointers': [1, 0.9, 1, r'(\(+)?((int)|(char)|(string)|(void)|(bool)|(float)|(double)){1}(\)+)?(\s+)?\*{1,2}(\s+)?[a-zA-Z]+(\s+)?(\=)?.*\;$', 0],
        'Infinite_loop': [0, 0.9, 1, r'(while(\s+)?\((true|1)\))|(for(\s+)?\(;;\))', 0],
        'Atypical Includes': [1, 0.1, 1, r'#(\s+)?include(\s+)?<((iomanip)|(algorithm)|(cstdlib)|(utility)|(limits)|(cmath))>', 0],
        'Atypical Keywords': [1, 0.3, 1, r'((break(\s+)?;)|(switch(\s+)?\(.*\)(\s+)?{)|(continue(\s+)?;)|(sizeof\(.*\))|(case\s+([a-zA-Z0-9]+(\s+)?:)))', 0],
        'Array Accesses': [1, 0.9, 1, r'([a-zA-Z0-9]+\[.*\])', 0],
        'Namespace Std': [1, 0.1, 1, r'(std::)', 0],
        'Brace Styling': [1, 0.1, 1, r'^((\s+)?{)', 0],
        'Escaped Newline': [1, 0.1, 1, r'(\\n)', 0],
        'User-Defined Functions': [1, 0.8, 1, r'^(((unsigned|signed|long|short)\s)?\S{3,}\s+\S+\(.*\))', 0],
        'Ternary Operator': [1, 0.2, 1, r'(.+\s+\?\s+.+\s+:\s+.+)', 0],
        'Command-Line Arguments': [1, 0.8, 1, r'(int argc, (char\s?\*\s?argv\[\]|char\s?\*\*\s?argv|char\s?\*\[\]\s?argv))', 0],
        'Nulls': [1, 0.4, 1, r'(?i)(nullptr|null|\\0)', 0],
        'Scope Operator': [1, 0.25, 1, r'(\S+::\S+)', 0]
    }
    
    anomaly_score = 0   # Initial anomaly Score
    anomalies_found = 0 # Counts the number of anamolies found 

    for line in code.splitlines():   # Reading through lines in the code and checking for each anomaly

        # Checks for while(1), while(true)
        if Styleanomaly['Infinite_loop'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Infinite_loop'][3], line):
                if Styleanomaly['Infinite_loop'][0] == 0 and Styleanomaly['Infinite_loop'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Infinite_loop'][1]
                    Styleanomaly['Infinite_loop'][4] += 1
                    anomalies_found += 1
                elif Styleanomaly['Infinite_loop'][0] == 1:
                    anomaly_score += Styleanomaly['Infinite_loop'][1]
                    anomalies_found += 1

        # Checks for int* var;, char** var;, and similar.
        if Styleanomaly['Pointers'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Pointers'][3], line):
                if Styleanomaly['Pointers'][0] == 0 and Styleanomaly['Pointers'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Pointers'][1]
                    Styleanomaly['Pointers'][4] += 1
                    anomalies_found += 1
                if Styleanomaly['Pointers'][0] == 1:
                    anomaly_score += Styleanomaly['Pointers'][1]
                    anomalies_found += 1

        # Checks for abnormal includes like <iomanip>, <algorithm>, <cstdlib>
        if Styleanomaly['Atypical Includes'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Atypical Includes'][3], line):
                if Styleanomaly['Atypical Includes'][0] == 0 and Styleanomaly['Atypical Includes'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Atypical Includes'][1]
                    Styleanomaly['Atypical Includes'][4] += 1
                    anomalies_found += 1
                if Styleanomaly['Atypical Includes'][0] == 1:
                    anomaly_score += Styleanomaly['Atypical Includes'][1]
                    anomalies_found += 1
        
        # Checks for keywords like switch(){, case:, continue; 
        if Styleanomaly['Atypical Keywords'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Atypical Keywords'][3], line):
                if Styleanomaly['Atypical Keywords'][0] == 0 and Styleanomaly['Atypical Keywords'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Atypical Keywords'][1]
                    Styleanomaly['Atypical Keywords'][4] += 1
                    anomalies_found += 1
                if Styleanomaly['Atypical Keywords'][0] == 1:
                    anomaly_score += Styleanomaly['Atypical Keywords'][1]
                    anomalies_found += 1

        # Checks for arr[], arr[x]
        if Styleanomaly['Array Accesses'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Array Accesses'][3], line):
                if Styleanomaly['Array Accesses'][0] == 0 and Styleanomaly['Array Accesses'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Array Accesses'][1]
                    Styleanomaly['Array Accesses'][4] += 1
                    anomalies_found += 1
                if Styleanomaly['Array Accesses'][0] == 1:
                    anomaly_score += Styleanomaly['Array Accesses'][1]
                    anomalies_found += 1

        # Checks for std::
        if Styleanomaly['Namespace Std'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Namespace Std'][3], line):
                if Styleanomaly['Namespace Std'][0] == 0 and Styleanomaly['Namespace Std'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Namespace Std'][1]
                    Styleanomaly['Namespace Std'][4] += 1
                    anomalies_found += 1
                if Styleanomaly['Namespace Std'][0] == 1:
                    anomaly_score += Styleanomaly['Namespace Std'][1]
                    anomalies_found += 1

        # Checks for { on its own line
        if Styleanomaly['Brace Styling'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Brace Styling'][3], line):
                if Styleanomaly['Brace Styling'][0] == 0 and Styleanomaly['Brace Styling'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Brace Styling'][1]
                    Styleanomaly['Brace Styling'][4] += 1
                    anomalies_found += 1
                if Styleanomaly['Brace Styling'][0] == 1:
                    anomaly_score += Styleanomaly['Brace Styling'][1]
                    anomalies_found += 1

        # Checks for use of \n
        if Styleanomaly['Escaped Newline'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Escaped Newline'][3], line):
                if Styleanomaly['Escaped Newline'][0] == 0 and Styleanomaly['Escaped Newline'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Escaped Newline'][1]
                    Styleanomaly['Escaped Newline'][4] += 1
                    anomalies_found += 1
                if Styleanomaly['Escaped Newline'][0] == 1:
                    anomaly_score += Styleanomaly['Escaped Newline'][1]
                    anomalies_found += 1

        # Checks for user-defined functions like `int add(int a)`, excludes `int main()`
        if Styleanomaly['User-Defined Functions'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['User-Defined Functions'][3], line) and not line.__contains__("main()"):
                if Styleanomaly['User-Defined Functions'][0] == 0 and Styleanomaly['User-Defined Functions'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['User-Defined Functions'][1]
                    Styleanomaly['User-Defined Functions'][4] += 1
                    anomalies_found += 1
                if Styleanomaly['User-Defined Functions'][0] == 1:
                    anomaly_score += Styleanomaly['User-Defined Functions'][1]
                    anomalies_found += 1

        # Checks for statements like `x == y ? True : False`
        if Styleanomaly['Ternary Operator'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Ternary Operator'][3], line):
                if Styleanomaly['Ternary Operator'][0] == 0 and Styleanomaly['Ternary Operator'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Ternary Operator'][1]
                    Styleanomaly['Ternary Operator'][4] += 1
                    anomalies_found += 1
                if Styleanomaly['Ternary Operator'][0] == 1:
                    anomaly_score += Styleanomaly['Ternary Operator'][1]
                    anomalies_found += 1

        # Checks for statements like `int main(int argc, char *argv[])`
        if Styleanomaly['Command-Line Arguments'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Command-Line Arguments'][3], line):
                if Styleanomaly['Command-Line Arguments'][0] == 0 and Styleanomaly['Command-Line Arguments'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Command-Line Arguments'][1]
                    Styleanomaly['Command-Line Arguments'][4] += 1
                    anomalies_found += 1
                if Styleanomaly['Command-Line Arguments'][0] == 1:
                    anomaly_score += Styleanomaly['Command-Line Arguments'][1]
                    anomalies_found += 1

        # Checks for use of null, i.e. `null`, `nullptr`, or `\0`
        if Styleanomaly['Nulls'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Nulls'][3], line):
                if Styleanomaly['Nulls'][0] == 0 and Styleanomaly['Nulls'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Nulls'][1]
                    Styleanomaly['Nulls'][4] += 1
                    anomalies_found += 1
                if Styleanomaly['Nulls'][0] == 1:
                    anomaly_score += Styleanomaly['Nulls'][1]
                    anomalies_found += 1

        # Checks for use of scope operator, i.e. `x::y`, excluding `string::npos` and not double-counting the Namespace Std check
        if Styleanomaly['Scope Operator'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Scope Operator'][3], line) and not line.__contains__("string::npos") and not line.__contains__("std::"):
                if Styleanomaly['Scope Operator'][0] == 0 and Styleanomaly['Scope Operator'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Scope Operator'][1]
                    Styleanomaly['Scope Operator'][4] += 1
                    anomalies_found += 1
                if Styleanomaly['Scope Operator'][0] == 1:
                    anomaly_score += Styleanomaly['Scope Operator'][1]
                    anomalies_found += 1
    return anomalies_found, anomaly_score

def anomaly(data, selected_labs): # Function to calculate the anomaly score
    output = {}
    # print(data)
    # print(selected_labs)
    for lab in selected_labs:
        for user_id in data:
            if user_id not in output:
                output[user_id] = {}
            if lab in data[user_id]:
                max_score = 0
                for sub in data[user_id][lab]:
                    if sub.max_score > max_score:
                        max_score = sub.max_score
                        code = sub.code
                anomalies_found, anomaly_score = get_anomaly_score(code)
                output[user_id][lab] = [anomalies_found, anomaly_score, code]
    # print(output)
    return output

##############################
#           Control          #
##############################
if use_standalone:
    logfile_path = input("Enter the path to the logfile: ")
    # logfile_path = '/Users/abhinavreddy/Downloads/standalone_incdev_analysis/input/logfile.csv'
    logfile = pd.read_csv(logfile_path)
    logfile = logfile[logfile.role == 'Student']
    selected_labs = get_selected_labs(logfile)
    print("Results stored at /Users/abhinavreddy/Desktop/Standalone apps v4/output/roster2022-12-07 12:54:19.720942.csv")
    logfile = download_code(logfile)
    data = create_data_structure(logfile)
    final_roster = {}
    anomaly_detection_output = anomaly(data, selected_labs)
    for user_id in anomaly_detection_output:
        for lab in anomaly_detection_output[user_id]:
            anomalies_found = anomaly_detection_output[user_id][lab][0]
            anomaly_score = anomaly_detection_output[user_id][lab][1]
            if user_id in final_roster:
                final_roster[user_id]['Lab ' + str(lab) + ' anomalies found'] = anomalies_found
                final_roster[user_id]['Lab ' + str(lab) + 'anomaly score'] = anomaly_score
                final_roster[user_id][str(lab) + ' Student code'] = anomaly_detection_output[user_id][lab][2]
            else:
                final_roster[user_id] = {
                    'User ID': user_id,
                    'Last Name': data[user_id][lab][0].last_name[0],
                    'First Name': data[user_id][lab][0].first_name[0],
                    'Email': data[user_id][lab][0].email[0],
                    'Role': 'Student',
                    'anomalies found' : anomalies_found,
                    'anomaly score' : anomaly_score,
                    str(lab) + ' Student code' : anomaly_detection_output[user_id][lab][2]
                }
    write_output_to_csv(final_roster)
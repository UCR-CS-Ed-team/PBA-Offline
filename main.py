import datetime
import pandas as pd
from tools.roster import roster
from tools.quickanalysis import quick_analysis
from tools.submission import Submission
import requests
import zipfile
import io
from tools.anomaly_detection.anomaly import compute_anomalies
from tools import incdev
import os
import csv
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_valid_datetime(timestamp):
    # print(timestamp)
    """ Get valid datetime based on given timestamp.
    
        Parameters
        ----------
        timestamp : `str`
            Timestamp of the given activity row
    
        Returns
        -------
        valid_datetime : `datetime.datetime`
            Valid datetime for the given timestamp
    
        Raises
        ------
        ValueError
            Raised if the timestamp given cannot be converted into a valid datetime.
    
        Notes
        -----
        Expected csv format: 2017-04-05 17:01:12
        Excel format: yyyy-mm-dd h:mm:ss
        New log file has extra time information after the h:mm:ss timestamp
    """
    t = timestamp
    # t_split = timestamp.split()
    # if t_split[1].find("-"):
    #     t_split[1] = t_split[1][0:t_split[1].find("-")]
    #     t = ' '.join(t_split)
    # print(t)
    # return datetime.strptime(t, '%d/%m/%Y %H:%M:%S')
    for fmt in ('%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S','%m/%d/%y %H:%M'):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            pass
    raise ValueError('Cannot recognize datetime format: ' + t)

def get_code(url):
    """ Download a student's code submission.

    Parameters
    ----------
    url : `str`
        URL of the zip file to be downloaded

    Returns
    -------
    url : `datetime.datetime`
        URL of the zip file that was downloaded

    result : `str`
        Code submission

    Raises
    ------
    ConnectionError
        Raised if the submission could not be downloaded
    
    """

    try:
        response = requests.get(url)
        zfile = zipfile.ZipFile(io.BytesIO(response.content))
        filenames = zfile.namelist()
        content = zfile.open(filenames[0], 'r').read()
        result = content.decode('utf-8')
        return (url, result)
    except ConnectionError:
        return (url, "Max retries met, cannot retrieve student code submission")

def write(summary_roster):
    # # Writing the output to the csv file 
    csv_columns = []
    for id in summary_roster:
        for column in summary_roster[id]:
            csv_columns.append(column)
        break             
    try:
        csv_file = 'output/roster.csv'
        with open(csv_file, 'w') as f1:
            writer = csv.DictWriter(f1, fieldnames=csv_columns)
            writer.writeheader()
            for user_id in summary_roster.keys():
                writer.writerow(summary_roster[user_id])
    except IOError:
        print('IO Error')

if __name__ == '__main__':
    # Read File into a pandas dataframe
    # file_path = input('Enter path to the file including file name: ')
    # Below is the static file path if you want to work on the same file
    file_path = '/Users/abhinavreddy/Downloads/standalone_incdev_analysis/input/logfile.csv'
    filename = os.path.basename(file_path)
    f = open(file_path, 'r')
    logfile = pd.read_csv(file_path)
    logfile = logfile[logfile.role == 'Student']
    urls = logfile.zip_location.to_list()
    # print(len(urls))
    threads = []
    with ThreadPoolExecutor() as executor:
        for url in urls:
            threads.append(executor.submit(get_code, url))
        student_code = []
        for task in as_completed(threads):
            student_code.append(task.result())
    # Now join the student code submission results back to the dataframe
    df = pd.DataFrame(student_code, columns = ['zip_location', 'student_code'])
    logfile = pd.merge(left=logfile, right=df, on=['zip_location'])
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
    while(1):
        print(" 1. Quick Analysis \n 2. Roster \n 3. Anomaly \n 4. Incremental Development Analysis \n 5. Quit \n 6. Fords anomaly")
        inp = int(input())
        print('input ', inp)
        if inp == 1:
            quick_analysis(logfile)
        elif inp == 2:
            summary_roster = roster(logfile, data)
        elif inp == 3:
            print('Tool not available, Work in progress')
        elif inp == 4:
             # Generate nested dict of IncDev results
            output = incdev.run(data)
            for user_id in output:
                for lab_id in output[user_id]:
                    lid = str(lab_id)
                    score = output[user_id][lab_id]['incdev_score']
                    score_trail = output[user_id][lab_id]['incdev_score_trail']
                    loc_trail = output[user_id][lab_id]['loc_trail']
                    time_trail = output[user_id][lab_id]['time_trail']
                    if user_id in summary_roster:
                        summary_roster[user_id][lid + ' incdev_score'] = score
                        summary_roster[user_id][lid + ' incdev_score_trail'] = score_trail
                        summary_roster[user_id][lid + ' loc_trail'] = loc_trail
                        summary_roster[user_id][lid + ' time_trail'] = time_trail
        elif inp == 5:
            break
        elif inp == 6:
            print("Tool not available, Work in progress")
            # x = compute_anomalies(data[27496988400][1.2][0])
            # print(x)
        else:
            print("Please select a valid option")
        write(summary_roster)

    
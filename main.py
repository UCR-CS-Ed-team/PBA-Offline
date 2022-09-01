import datetime
import email
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

if __name__ == '__main__':
    # Read File into a pandas dataframe
    file_path = input('Enter path to the file including file name: ')
    # Below is the static file path if you want to work on the same file
    # file_path = '/Users/abhinavreddy/Downloads/standalone_incdev_analysis/input/logfile2.csv'
    filename = os.path.basename(file_path)
    f = open(file_path, 'r')
    logfile = pd.read_csv(file_path)
    logfile = logfile[logfile.role == 'Student']
    # roster(logfile)
    data = {}
    # quick_analysis(dataframe)
    i = 0
    for row in logfile.itertuples():
        # print(i)
        if row.user_id not in data:
            data[int(row.user_id)] = {}
        if row.content_section not in data[row.user_id]:
            # data[row.user_id][row.content_section] = {}
            data[row.user_id][row.content_section] = []
        url, result = get_code(row.zip_location)
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
            code = result,
            sub_time = get_valid_datetime(row.date_submitted),
            anomaly_dict=None
        )
        data[row.user_id][row.content_section].append(sub)
        # i += 1
    # print(data)

    # TODO2: trying to implement fords stuff 
    # column_names = ["zybook_code", "content_resource_id", "content_section","caption", "user_id", "first_name", "last_name", 
    # "email", "class_section", "role", "date_submitted", "zip_location", "submission", "score", 
    # "max_score", "result", "query_info", "submission_id", "student_submission"]
    # df =  pd.DataFrame(columns = column_names)
    # for i in data:
    #     zybook_code = "anbdijbew"
    #     content_section = 1.2
    #     caption = data[i][1.2][0].caption
    #     user_id = i
    #     first_name = data[i][1.2][0].first_name
    #     last_name = data[i][1.2][0].last_name
    #     email1 = data[i][1.2][0].email
    #     class_section = '1'
    #     role = "student"
    #     date_submitted = data[i][1.2][0].sub_time
    #     zip_location = data[i][1.2][0].zip_location
    #     submission = 1
    #     score = 10
    #     max_score = 10
    #     result = ""
    #     query_info = "something"
    #     submission_id = "qnoiqwndoqwdq"
    #     student_submission = data[i][1.2][0]
    #     df.append(zybook_code,content_section,caption,user_id,first_name,last_name,email1,class_section,role,date_submitted,
    #     zip_location,submission,score,max_score,result,query_info,submission_id,student_submission)

    # Todo1: Seperating Anomaly from roster and having it as a standalone of its own 
    # Todo2: Integrating fords Anomaly detection code, so we don't have to reengineer stuff
    while(1):
        print(" 1. Quick Analysis \n 2. Roster \n 3. Anomaly \n 4. Incremental Development Analysis \n 5. Quit \n 6. Fords anomaly")
        inp = int(input())
        print('input ', inp)
        if inp == 1:
            quick_analysis(logfile)
        elif inp == 2:
            roster(logfile)
        elif inp == 3:
            print('Tool not available, Work in progress')
        elif inp == 4:
             # Generate nested dict of IncDev results
            output = incdev.run(data)
            # Create output directory if it doesn't already exist
            try:
                os.mkdir('output')
            except Exception:
                pass
            # Write IncDev results to csv
            with open(os.path.join('output', 'output_' + filename), 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['User ID', 'Lab ID', 'IncDev Score', 'IncDev Trail', 'LOC Trail', 'Time Trail'])
                for user_id in output:
                    uid = user_id
                    for lab_id in output[user_id]:
                        lid = lab_id
                        score = output[user_id][lab_id]['incdev_score']
                        score_trail = output[user_id][lab_id]['incdev_score_trail']
                        loc_trail = output[user_id][lab_id]['loc_trail']
                        time_trail = output[user_id][lab_id]['time_trail']
                    writer.writerow([uid, lid, score, score_trail, loc_trail, time_trail])
        elif inp == 5:
            break
        elif inp == 6:
            print("Tool not available, Work in progress")
            # x = compute_anomalies(data[27496988400][1.2][0])
            # print(x)
        else:
            continue

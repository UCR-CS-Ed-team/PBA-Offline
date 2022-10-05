from urllib.parse import uses_netloc
import pandas as pd 
from datetime import datetime,timedelta
import csv

use_standalone = False

##############################
#       Helper Functions     #
##############################
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

#Utility functions
def get_valid_date_time(t):
    for fmt in ('%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%m/%d/%y %H:%M'):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            pass
    raise ValueError('Cannot recognize datetime format: ' + t)

def time_to_minutes_seconds(time_list): # Converts time to minutes and seconds (ex: 1m 30s) ignores anything over the 10 minute interval
    time_spent_by_user = 0
    fmt = '%Y-%m-%d %H:%M:%S'
    for i in range(len(time_list)-1):
        # d1 = datetime.strptime(str(time_list[i]), fmt)
        # d2 = datetime.strptime(str(time_list[i+1]), fmt)
        d1 = get_valid_date_time(str(time_list[i]))
        d2 = get_valid_date_time(str(time_list[i+1]))
        diff = d2 -d1
        diff_minutes = (diff.days * 24 * 60) + (diff.seconds/60)
        if diff_minutes <= 10:
            time_spent_by_user += diff_minutes
    time_spent_seconds = time_spent_by_user * 60
    td = str(timedelta(seconds=time_spent_seconds))
    td_split = td.split(':')
    time_spent = td_split[1] +'m '+ td_split[2].split('.')[0] + 's'
    return time_spent

def add_total_time(total_time, lab_time): # Adds time to calculate total time spent by the user
    total_time_minutes = int(total_time.split(' ')[0].strip('m'))
    total_time_seconds = int(total_time.split(' ')[1].strip('s'))
    total_time = total_time_minutes * 60 + total_time_seconds
    lab_time_minutes = int(lab_time.split(' ')[0].strip('m'))
    lab_time_seconds = int(lab_time.split(' ')[1].strip('s'))
    lab_time = lab_time_minutes * 60 + lab_time_seconds
    total_time = total_time + lab_time
    td = str(timedelta(seconds=total_time))
    td_split = td.split(':')
    total_time = td_split[1] +'m '+ td_split[2].split('.')[0] + 's'
    return total_time

def roster(dataframe, selected_labs):
    df = dataframe

    # Identify unique labs 
    unique_lab_ids = set()
    for lab_id in df['content_resource_id']:
        unique_lab_ids.add(lab_id)

    summary_roster = {} #final hashmap where we will be storing the whole roster

    # Assuming everything is 0 at the beginning
    total_time_spent = 0
    total_runs = 0
    total_score = 0
    total_develops = 0
    total_submits = 0
    total_pivots = 0

    for selected_lab in selected_labs: # Iterating through the lab selected
        lab_df = df[df['content_section'] == selected_lab].reset_index() # Dataframe for that particular lab
        user_id = lab_df['user_id']
        user_id = set(user_id) # Set does not contain duplicates so here we get all user ids without repetition
        lab_name = lab_df['caption'][0]
        print(lab_name)
        section = str(lab_df['content_section'][0])

        for unique_id in user_id:   # Iterating through each user id in that lab
            user_df = lab_df[lab_df['user_id'] == unique_id] # Creating a seperate dataframe for that user in that lab
            user_id_df = user_df['user_id']
            user_id = user_id_df.iloc[0]
            first_name = user_df['first_name'].iloc[0]
            last_name = user_df['last_name'].iloc[0]
            email = user_df['email'].iloc[0]
            role = user_df['role'].iloc[0]
            num_of_runs = len(user_df)
            num_of_submits = 0
            if user_id == -1:   # Checking if the entry is a solution
                continue
            for submission in user_df['submission']:
                if submission == 1:
                    num_of_submits += 1
            num_of_devs = num_of_runs - num_of_submits
            max_score = 0
            max_score_idx = user_df['score'].idxmax(skipna=True)
            if not pd.isna(max_score_idx):  # Checking if the submission has a score 
                zip_location = user_df['zip_location'][max_score_idx]
                max_score = user_df['score'].max()
            else:
                zip_location = user_df['zip_location'].iloc[-1]
            max_score = 0
            code = ''
            # for sub in data[user_id][float(section)]:
            #     if sub.max_score > max_score:
            #         max_score = sub.max_score
            #         code = sub.code
            # anomaly_score, user_code, anamolies_found, style_score, stylechecker = anomalyScore(code)
            # print(anomaly_score)
            time_list = [] # Contains timestamps for that user 
            for time in user_df['date_submitted']:
                time_list.append(time)
            time_spent_by_user = time_to_minutes_seconds(time_list)
            total_pivots += 0
            if user_id not in summary_roster:   # First time entry into the map, implemented it this way so we do not need to reiterate through it to get all the timestamps and get the time spent 
                summary_roster[int(user_id)] = {
                    'User ID': user_id,
                    'Last Name': last_name,
                    'First Name': first_name,
                    'Email': email,
                    'Role': role,
                    'Time Spent(total)': time_spent_by_user,
                    'Total Runs': num_of_runs,
                    'Total Score': max_score,
                    'Total Develops': num_of_devs,
                    'Total Submits': num_of_submits,
                    'Total Pivots': total_pivots,
                    'Feat: Start date': 'x',
                    'Feat: End date': 'x',
                    'Feat: Work type': 'x',
                    'Feat: # Submits': 'x',
                    'Feat: Time spent': 'x',
                    'Feat: Suspicious': 'x',
                    'Lab'+section+' Time spent': time_spent_by_user,
                    'Lab'+section+' # of runs': num_of_runs,
                    'Lab'+section+' % score': max_score,
                    'Lab'+section+' # of devs': num_of_devs,
                    'Lab'+section+' # of subs': num_of_submits
                    # 'Lab'+section+' User Code': code,
                }
            else:   # Appending to the existing entries for that user. So we wont have to iterate through the whole user dataframe again
                summary_roster[user_id]['Lab'+section+' Time spent'] = time_spent_by_user
                summary_roster[user_id]['Lab'+section+' # of runs'] = num_of_runs
                summary_roster[user_id]['Lab'+section+' % score'] = max_score
                summary_roster[user_id]['Lab'+section+' # of devs'] = num_of_devs
                summary_roster[user_id]['Lab'+section+' # of subs'] = num_of_submits
                summary_roster[user_id]['Time Spent(total)'] = add_total_time(summary_roster[user_id]['Time Spent(total)'], 
                summary_roster[user_id]['Lab'+section+' Time spent'])
                summary_roster[user_id]['Total Runs'] += summary_roster[user_id]['Lab'+section+' # of runs']
                summary_roster[user_id]['Total Score'] += summary_roster[user_id]['Lab'+section+' % score']
                summary_roster[user_id]['Total Develops'] += summary_roster[user_id]['Lab'+section+' # of devs']
                summary_roster[user_id]['Total Submits'] += summary_roster[user_id]['Lab'+section+' # of subs']
    return summary_roster

##############################
#           Control          #
##############################
if use_standalone:
    logfile_path = '/Users/abhinavreddy/Downloads/standalone_incdev_analysis/input/logfile.csv'
    logfile = pd.read_csv(logfile_path)
    logfile = logfile[logfile.role == 'Student']
    selected_labs = get_selected_labs(logfile)
    final_roster = roster(logfile, selected_labs)
    write_output_to_csv(final_roster)

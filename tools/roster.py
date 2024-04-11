import math
from datetime import timedelta

from tools.utilities import get_valid_datetime


def time_to_minutes_seconds(time_list):
    # Converts time to minutes and seconds (ex: 1m 30s) ignores anything over the 10 minute interval
    time_spent_by_user = 0
    for i in range(len(time_list) - 1):
        d1 = time_list[i]
        d2 = time_list[i + 1]
        diff = d2 - d1
        diff_minutes = (diff.days * 24 * 60) + (diff.seconds / 60)
        if diff_minutes < 0:
            raise ValueError('Negative time difference found!')
        elif diff_minutes <= 10:
            time_spent_by_user += diff_minutes
    time_spent_seconds = time_spent_by_user * 60
    td = str(timedelta(seconds=time_spent_seconds))
    td_split = td.split(':')
    time_spent = td_split[0] + 'h ' + td_split[1] + 'm ' + td_split[2].split('.')[0] + 's'
    return time_spent


def add_total_time(total_time, lab_time):
    # Adds time to calculate total time spent by the user
    total_time_split = total_time.split(' ')
    total_time_hours = 0
    if len(total_time_split) > 2:  # Check if time has hours
        total_time_hours = int(total_time_split[0].strip('h'))
        total_time_minutes = int(total_time_split[1].strip('m'))
        total_time_seconds = int(total_time_split[2].strip('s'))
    else:
        total_time_minutes = int(total_time_split[0].strip('m'))
        total_time_seconds = int(total_time_split[1].strip('s'))
    total_time = (total_time_hours * 3600) + (total_time_minutes * 60) + total_time_seconds

    lab_time_split = lab_time.split(' ')
    lab_time_hours = 0
    if len(lab_time_split) > 2:  # Check if time has hours
        lab_time_hours = int(lab_time_split[0].strip('h'))
        lab_time_minutes = int(lab_time_split[1].strip('m'))
        lab_time_seconds = int(lab_time_split[2].strip('s'))
    else:
        lab_time_minutes = int(lab_time_split[0].strip('m'))
        lab_time_seconds = int(lab_time_split[1].strip('s'))
    lab_time = (lab_time_hours * 3600) + (lab_time_minutes * 60) + lab_time_seconds

    total_time = total_time + lab_time
    td = str(timedelta(seconds=total_time))
    td_split = td.split(':')
    if len(td_split) > 2:
        total_time = td_split[0] + 'h ' + td_split[1] + 'm ' + td_split[2] + 's'
    else:
        total_time = '0h ' + td_split[0] + 'm ' + td_split[2] + 's'
    return total_time


def get_ppm(time_spent, score):
    """
    Checks if a student scored too many points too quickly, Indicates suspicious activity (might have copied)
    Input:
    ------
    Accepts time spent on that lab and the maximum number of points scored by the student as an input
    Output:
    -------
    Returns a float points per minute
    """
    time = time_spent.split()
    hours = int(time[0].strip('h'))
    minutes = int(time[1].strip('m'))
    seconds = int(time[2].strip('s'))
    total_seconds = (hours * 3600) + (minutes * 60) + seconds
    if total_seconds == 0:
        return 10
    else:
        return round((score / (total_seconds)), 2)


def roster(dataframe, selected_labs):
    """
    Input:
    ------
            Accepts a logfile dataframe and selected labs as an input

    Output:
    -------
            Calculates the total time spent across selected labs, total time spent, total develops, total submits,
            and also details about time spent on each lab, number of submits in each lab, etc

    summary_roster = {
            user_id_1: {
                    'user_id': 121314141,
                    'last_name': 'Doe',
                    'first_name': 'John',
                    'Email': 'jdoe009@ucr.edu',
                    'Role': 'student',
                    'points_per_minute': 0.0,
                    'Time Spent(total)': '16m 00s',
                    'Total Runs': 17,
                    'Total Score': 10.0,
                    'Total Develops': 8,
                    'Total Submits': 9,
                    'Total Pivots': 0,
                    'Lab 1.2 Points per minute': 0.0,
                    'Lab 1.2 Time spent': '16m 00s',
                    'Lab 1.2 # of runs': 17,
                    'Lab 1.2 % score': 10.0,
                    'Lab 1.2 # of devs': 8,
                    'Lab 1.2 # of subs': 9,
                    ...
                    ...
                    ...
            },
            ...
            ...
            ...
    }
    """

    df = dataframe

    # Identify unique labs
    unique_lab_ids = set()
    if 'lab_id' in df:
        for lab_id in df['lab_id']:
            unique_lab_ids.add(lab_id)

    summary_roster = {}  # final hashmap where we will be storing the whole roster

    for selected_lab in selected_labs:  # Iterating through the lab selected
        lab_df = df[df['content_section'] == selected_lab].reset_index()  # Dataframe for that particular lab
        user_id = lab_df['user_id']
        user_id = set(user_id)  # Set does not contain duplicates so here we get all user ids without repetition
        section = str(lab_df['content_section'][0])

        for unique_id in user_id:  # Iterating through each user id in that lab
            user_df = lab_df[lab_df['user_id'] == unique_id]  # Creating a separate dataframe for that user in that lab
            user_id_df = user_df['user_id']
            user_id = user_id_df.iloc[0]
            first_name = user_df['first_name'].iloc[0]
            last_name = user_df['last_name'].iloc[0]
            email = user_df['email'].iloc[0]
            role = user_df['role'].iloc[0]
            num_of_runs = len(user_df)
            num_of_submits = 0
            if user_id == -1:  # Checking if the entry is a solution
                continue
            if 'is_submission' in user_df:
                for submission in user_df['is_submission']:
                    if submission == 1:
                        num_of_submits += 1
            num_of_devs = num_of_runs - num_of_submits
            max_score = user_df['score'].max()
            if math.isnan(max_score):
                max_score = 0
            time_list = []  # Contains timestamps for that user
            if 'date_submitted' in user_df:
                for time in user_df['date_submitted']:
                    time_list.append(get_valid_datetime(time))
            time_list.sort()  # Sort datetimes in ascending order
            time_spent_by_user = time_to_minutes_seconds(time_list)

            # Points per minute, Indicates if a student scores too many points too quickly, might have copied?
            ppm = get_ppm(time_spent_by_user, max_score)

            # Normalization zi = (xi - min(x)) / (max(x) – min(x))  | We assumed max(x) = 10 and min(x) = 0
            ppm_normalized = ppm / 10

            # First time entry into the map, implemented it this way so we do not need to reiterate through it
            # to get all the timestamps and get the time spent
            if user_id not in summary_roster:
                summary_roster[int(user_id)] = {
                    'User ID': user_id,
                    'Last Name': last_name,
                    'First Name': first_name,
                    'Email': email,
                    'Role': role,
                    'Points per minute': None,
                    'Time Spent(total)': time_spent_by_user,
                    'Total Runs': num_of_runs,
                    'Total Score': max_score,
                    'Total Develops': num_of_devs,
                    'Total Submits': num_of_submits,
                    'Lab' + section + ' Points per minute': round(ppm_normalized, 2),
                    'Lab' + section + ' Time spent': time_spent_by_user,
                    'Lab' + section + ' # of runs': num_of_runs,
                    'Lab' + section + ' % score': max_score,
                    'Lab' + section + ' # of devs': num_of_devs,
                }
            else:
                # Appending to the existing entries for that user.
                # So we wont have to iterate through the whole user dataframe again
                summary_roster[user_id]['Lab' + section + ' Points per minute'] = ppm_normalized
                summary_roster[user_id]['Lab' + section + ' Time spent'] = time_spent_by_user
                summary_roster[user_id]['Lab' + section + ' # of runs'] = num_of_runs
                summary_roster[user_id]['Lab' + section + ' % score'] = max_score
                summary_roster[user_id]['Lab' + section + ' # of devs'] = num_of_devs
                summary_roster[user_id]['Lab' + section + ' # of subs'] = num_of_submits
                summary_roster[user_id]['Time Spent(total)'] = add_total_time(
                    summary_roster[user_id]['Time Spent(total)'],
                    summary_roster[user_id]['Lab' + section + ' Time spent'],
                )
                summary_roster[user_id]['Total Runs'] += summary_roster[user_id]['Lab' + section + ' # of runs']
                summary_roster[user_id]['Total Score'] += summary_roster[user_id]['Lab' + section + ' % score']
                summary_roster[user_id]['Total Develops'] += summary_roster[user_id]['Lab' + section + ' # of devs']
                summary_roster[user_id]['Total Submits'] += summary_roster[user_id]['Lab' + section + ' # of subs']

    # Calculating and adding the total avg ppm
    for user_id in summary_roster:
        count_of_labs = 0
        ppm_sum = 0
        for lab in selected_labs:
            if 'Lab' + str(lab) + ' Points per minute' in summary_roster[user_id]:
                count_of_labs += 1
                ppm_sum += summary_roster[user_id]['Lab' + str(lab) + ' Points per minute']
        avg_ppm = ppm_sum / count_of_labs
        summary_roster[user_id]['Points per minute'] = round(avg_ppm, 2)

    return summary_roster

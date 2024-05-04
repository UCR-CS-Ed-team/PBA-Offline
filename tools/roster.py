import math
from datetime import datetime, timedelta

from tools.utilities import get_valid_datetime


def time_to_minutes_seconds(time_list: list[datetime]) -> str:
    """Calculates time spent from a list of submission times and returns it as a string.

    Args:
        time_list (list[datetime]): A list of submission datetimes for a student for an assignment.

    Returns:
        str: A string representation of time spent in minutes and seconds (e.g., "1h 30m 0s").

    Raises:
        ValueError: If a negative time difference is found in the input list.
    """
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


# TODO: Can we simplify this by summing `datetime` objects?
def add_total_time(total_time: str, lab_time: str) -> str:
    """Adds the given lab time to the total time and returns the updated total time.

    Args:
        total_time (str): The current total time in the format 'Xh Ym Zs' or 'Ym Zs'.
        lab_time (str): The lab time to be added in the format 'Xh Ym Zs' or 'Ym Zs'.

    Returns:
        str: The updated total time in the format 'Xh Ym Zs'.

    Example:
        >>> add_total_time('1h 30m 10s', '45m 20s')
        '2h 15m 30s'
    """
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


def get_ppm(time_spent: str, score: float) -> float:
    """Calculates points per minute (PPM) for a student based on time spent and max # of points scored.

    Parameters:
        time_spent (str): The time spent on the lab in the format "Xh Ym Zs".
        score (float): The maximum score the student achieved on a lab.

    Returns:
        float: The points per minute (PPM) for a student on an assignment.
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


def roster(dataframe: dict, selected_labs: list[float]) -> dict:
    """Calculates metrics for a roster for all students in a logfile.

    Args:
        dataframe (dict): The logfile containing submissions.
        selected_labs (list[float]): A list of lab IDs to consider.

    Returns:
        dict: A dictionary containing roster metrics for every student.
            Includes total time spent across selected labs, total time spent, total develops,
            total submits, details about time spent on each lab...

    Example:
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

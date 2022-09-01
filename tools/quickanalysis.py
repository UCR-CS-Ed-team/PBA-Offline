import pandas as pd
from datetime import datetime,timedelta
import csv

def write(summary):
    # Writing to the output csv
    try:
        csv_file = 'output/quickanalysis.csv'
        csv_columns = ['section', 'name', 'number_of_students', 'time_spent', 'num_of_runs', 'score', 'develops', 'num_of_submits', 'pivots']
        with open(csv_file, 'w') as f1:
            writer = csv.DictWriter(f1, fieldnames=csv_columns)
            writer.writeheader()
            for lab_id in summary.keys():
                # print(summary[lab_id])
                writer.writerow(summary[lab_id])
                # for value in summary[lab_id].keys():
                #     print(summary[lab_id][value])
    except IOError:
        print('IO Error')

def quick_analysis(dataframe):
    df = dataframe
    summary = {}
    unique_lab_ids = set()
    for lab_id in df['content_resource_id']:
        unique_lab_ids.add(lab_id)
    for lab_id in unique_lab_ids:   # This is going to be similar to the roster.py, better start with that file
        lab = df[df['content_resource_id'] == lab_id].reset_index()
        name = lab['caption'][0]
        user_id = lab['user_id']
        section = lab['content_section'][0]
        unique_user_id = set()
        for unique_id in user_id:
            if unique_id != -1:
                unique_user_id.add(unique_id)
        num_of_students = len(unique_user_id)
        num_of_runs = round(len(user_id)/len(unique_user_id))
        num_of_submits = 0
        total_score = 0
        time_spent = 0
        for unique_id in unique_user_id:
            user_df = lab[lab['user_id'] == unique_id]
            # print(user_df)
            max_score = 0
            time_spent_by_user = 0
            time_list = []
            for time in user_df['date_submitted']:
                time_list.append(time)
            # print(time_list)
            # fmt = '%Y-%m-%d %H:%M:%S'
            fmt = '%d/%m/%y %H:%M'
            for i in range(len(time_list)-1):
                d1 = datetime.strptime(str(time_list[i]), fmt)
                d2 = datetime.strptime(str(time_list[i+1]), fmt)
                diff = d2 -d1
                diff_minutes = (diff.days * 24 * 60) + (diff.seconds/60)
                if diff_minutes <= 10:
                    time_spent_by_user += diff_minutes
            # print(time_spent)
            for score in user_df['score']:
                if not pd.isna(score):
                    # print(type(score))
                    max_score = max(score, max_score)
            for submission in user_df['submission']:
                if submission == 1:
                    num_of_submits += 1
            total_score += max_score
            time_spent += time_spent_by_user
        avg_time_spent_minutes = time_spent/num_of_students
        avg_time_spent_seconds = avg_time_spent_minutes*60
        td = str(timedelta(seconds=avg_time_spent_seconds))
        td_split = td.split(':')
        avg_time_spent = td_split[1] +'m '+ td_split[2].split('.')[0] + 's'
        avg_score = int(round(total_score/num_of_students)/10*100)
        avg_num_of_submits = round(num_of_submits/len(unique_user_id))
        num_of_develops = num_of_runs - avg_num_of_submits
        # print(name, num_of_students, num_of_runs, avg_score, avg_num_of_submits)
        summary[lab_id] = {
                'section': section,
                'name': name,
                'number_of_students': num_of_students,
                'time_spent': avg_time_spent,
                'num_of_runs': num_of_runs,
                'score': avg_score,
                'develops': num_of_develops,
                'num_of_submits': avg_num_of_submits,
                'pivots': 'x',
        }
    write(summary)
    
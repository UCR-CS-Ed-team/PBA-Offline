def newtool(data: dict, selected_labs: list[float]) -> dict:
    """Example function for a new tool.

    Args:
        data (dict): Nested dictionary containing a Submission object for every submission.
            A particular submission can be accessed with data[user_id][lab_id][n].

    Returns:
        dict: Nested dictionary of students containing student_id and labs and their results.

    Example:
        newtool_output = {
            'student_id(1)' : {
                'lab1' : [num_runs, num_develops, num_submits],
                'lab2' : [num_runs, num_develops, num_submits],
                .
                .
                'labn' : [num_runs, num_develops, num_submits]
            }
        }
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
                for submission_object in data[user_id][lab]:
                    num_runs += 1
                    if int(submission_object.submission[0]) == 1:
                        num_submits += 1
                num_develops = num_runs - num_submits
            newtool_output[user_id][lab] = [num_runs, num_develops, num_submits]
    return newtool_output


"""
Data from create_data_structure function:
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

newtool_output from user defined function structure:
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

summary_output structure to be sent to write_output_to_csv function:
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

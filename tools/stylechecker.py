import os
import subprocess

cpplint_file = 'output/code.cpp'


def stylechecker(data: dict, selected_labs: list[float]) -> dict:
    """Check each student's code style with cpplint and return its result.

    Args:
        data (dict): The log of all student submissions.
        selected_labs (list[float]): A list of lab IDs to consider.

    Returns:
        dict: A dictionary containing the stylechecker output for each student and lab.

    Example:
        student_id : {
            'Lab 1' : [style_score, output1, code],
            'Lab 2' : [style_score, output1, code],
            'Lab n' : [style_score, output1, code],
            ...
        }

    Note:
        This function currently creates a new .cpp file and runs cpplint on that.
        TODO: Modify it to instead directly use the student's code from the logfile.
    """
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
                command = 'cpplint ' + cpplint_file
                output1 = subprocess.getoutput(command)
                style_score = 0
                if output1 != 'Done processing ' + cpplint_file:
                    lines = output1.splitlines()
                    style_score = lines[-1].split(':')[1].strip()
                os.remove(cpplint_file)
                output[user_id] = {lab: [style_score, output1, code]}
    return output

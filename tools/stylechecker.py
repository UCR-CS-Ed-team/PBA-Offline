import os
import subprocess

cpplint_file = 'output/code.cpp'


def stylechecker(data, selected_labs):
    """
    stylechecker_output from user defined function structure
    Input:
    ------
        Accepts the students data and selected labs as an input

    Output:
    -------
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

    Note:
        Todo: This currently creates a new .cpp file and runs the package on that, modify it in
                    such a way to avoid creating a new file and directly use the code in data
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

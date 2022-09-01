import pandas as pd
import difflib
import os

def run(data):
    """ Iterates through all students and labs, assigning IncDev score and trails for each.

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

        Parameters
        ----------
        data: `dict` [`str`, `dict`]
            Nested dictionary containing all student submission objects
            Particular submission can be accessed with data[user_id][lab_id][n]

        Returns
        -------
        incdev_data : `dict` [`str`, `dict`]
            Nested dictionary of students' incdev score and trails
    """

    incdev_data = {}

    incdev_data_fields = ['incdev_score', 'incdev_score_trail', 'loc_trail', 'time_trail']

    for user_id in data:
        if user_id not in incdev_data:
            incdev_data[user_id] = {}

        for lab_id in data[user_id]:
            if lab_id not in incdev_data[user_id]:
                incdev_data[user_id][lab_id] = {}
                for field in incdev_data_fields:
                    incdev_data[user_id][lab_id][field] = 0

            incdev_data[user_id][lab_id]['incdev_score'] = assign_inc_dev_score(data[user_id][lab_id])
            incdev_data[user_id][lab_id]['incdev_score_trail'] = assign_inc_dev_score_trail(data[user_id][lab_id])
            incdev_data[user_id][lab_id]['loc_trail'] = assign_loc_trail(data[user_id][lab_id])
            incdev_data[user_id][lab_id]['time_trail'] = assign_time_trail(data[user_id][lab_id])

    return incdev_data

def assign_inc_dev_score(runs):
    """ Assigns an IncDev score for a particular student on a particular lab.

        Parameters
        ----------
        runs : `list` [`submission object`]
            Dictionary of runs for a particular student and lab

        Returns
        -------
        score : `float`
            Incremental development score
    """

    score = 1
    prev_lines = 0

    for run in runs:
        # Remove blank lines
        code = os.linesep.join([s for s in run.code.splitlines() if s.strip()])
        line_count = len(code.splitlines())

        # If > 20 new lines added, decrement score
        if line_count - prev_lines > 20:
            lines_over = line_count - prev_lines - 20
            score -= .04 * lines_over
        # If <= 20 new lines added, increment score
        else:
            score += .1

        # If score > 1, set score to 1
        score = adjust_score(score)
        prev_lines = line_count

    # Score bottoms out at 0
    if score < 0:
        score = 0

    score = round(score, 2)
    return score

def assign_inc_dev_score_trail(runs):
    """ Generates an IncDev trail for a particular student on a particular lab.
        Trail consists of the line count for each run and the IncDev score after each run.
        '^' characters denote drastic change.

        Trail format: line count (score), line count 2 (score 2), ^line count 3 (score 3)
        Example: 13 (1), 45 (.52), ^55 (.62)

        Parameters
        ----------
        runs : `list` [`submission object`]
            Dictionary of runs for a particular student and lab

        Returns
        -------
        trail : `string`
            IncDev trail for a particular student/lab
    """

    trail = ""
    score = 1
    prev_lines = 0
    prev_code = ''

    for run in runs:
        code = os.linesep.join([s for s in run.code.splitlines() if s.strip()])
        line_count = len(code.splitlines())

        if prev_code != '':
            change = get_diff(prev_code, code)
            if change > .5:
                trail += '^'

        trail += str(line_count) + " "

        if line_count - prev_lines > 20:
            lines_over = line_count - prev_lines - 20
            score -= .04 * lines_over
            trail += '(' + str(round(score, 2)) + '), '
        else:
            score += .1
            if score > 1:
                score = 1
            trail += '(' + str(round(score, 2)) + '), '

        prev_lines = line_count
        prev_code = code
    trail = trail[:-2]
    return trail

def assign_loc_trail(runs):
    """ Generates a 'lines of code' trail for a particular student on a particular lab.
        Trail consists of the line count for each run.
        Less notable runs are replaced by a '.' character for brevity.
        '^' characters denote drastic change, '*' characters denote IncDev violation.

        Trail format: line count, line count 2, ^line count 3
        Example: 13,25...^55

        Parameters
        ----------
        runs : `list` [`submission object`]
            Dictionary of runs for a particular student and lab

        Returns
        -------
        trail : `string`
            LOC trail for a particular student/lab
    """

    lines = []
    drastic_change = [0]
    prev_code = ''
    for run in runs:
        code = os.linesep.join([s for s in run.code.splitlines() if s.strip()])

        lines.append(len(code.splitlines()))

        if prev_code != '':
            diff = get_diff(prev_code, code)
            if diff > .7:
                drastic_change.append(1)
            else:
                drastic_change.append(0)
        prev_code = code

    relevance_list = [1]

    # Create preliminary list of notable runs
    for i in range(1, len(lines) - 1):
        # IncDev violation, >20 new lines added
        if (lines[i] - lines[i - 1]) > 20:
            relevance_list[-1] = 1
            relevance_list.append(2)
        # Less than 20 new lines added, but run is still notable
        elif abs(lines[i] - lines[i - 1]) > 10 or drastic_change[i] == 1:
            relevance_list[-1] = 1
            relevance_list.append(1)
        # Run is not notable
        else:
            relevance_list.append(0)
    relevance_list.append(1)

    # Update list to account for sub-sequence rules
    relevance_list = check_subsequence_values(relevance_list, lines)
    relevance_list = check_subsequence_length(relevance_list)

    line_trail = str(lines[0])
    for i in range(1, len(lines)):
        if relevance_list[i] == 0:
            line_trail += '.'
        else:
            if line_trail[-1] != '.':
                line_trail += ','
            if drastic_change[i] == 1:
                line_trail += '^'
            if relevance_list[i] == 1:
                line_trail += str(lines[i])
            else:
                line_trail += str(lines[i]) + '*'
    return line_trail

def assign_time_trail(runs):
    """ Generates a 'time between submissions' trail for a particular student on a particular lab.
        Trail consists of the the number of minutes between submissions.
        'Develop' runs are denoted by '-' characters.
        Session breaks (>30 minutes since last run) are denoted by '/' characters.

        Example: ---0,2,1 / 0,8,4

        Parameters
        ----------
        runs : `list` [`submission object`]
            Dictionary of runs for a particular student and lab

        Returns
        -------
        trail : `string`
            Time between submissions trail for a particular student/lab
    """

    special_chars = ['-', ',', '/', ' ']
    sub_times = []
    all_times = []

    # Fill all_times and sub_times lists
    for run in runs:
        all_times.append(run.sub_time)
        if run.type == 1:
            sub_times.append(run.sub_time)
        else:
            sub_times.append(-1)
    session_breaks = get_sub_sessions(all_times)

    sub_time_trail = ''
    prev = None
    for i in range(len(sub_times)):
        if session_breaks[i] == 1:
            sub_time_trail += ' / '
            prev = None
        # Develop run
        if sub_times[i] == -1:
            sub_time_trail += '-'
        # Submit run
        else:
            if sub_time_trail != '' and sub_time_trail[-1] not in special_chars:
                sub_time_trail += ','
            # First submission during this session, add 0 to trail
            if prev == None:
                sub_time_trail += '0'
                prev = sub_times[i]
            # Not first submission of session, find diff and add to trail
            else: 
                diff = get_submission_time_diff(prev, sub_times[i])
                diff /= 60
                sub_time_trail += str(round(diff))
                prev = sub_times[i]

    return sub_time_trail

##################################################
# HELPER FUNCTIONS #
##################################################

def get_diff(sub1, sub2):
    """ Uses difflib's Differ function to generate a diff between two student submissions.

        Parameters
        ----------
        sub1, sub2 : `str`
            Student code submissions

        Returns
        -------
        percentChange : `float`
            Amount of change as calculated by (lines generated by Differ / total lines in sub2)
    """

    lineChanges = 0
    diff = difflib.Differ()

    for line in diff.compare(sub1.splitlines(keepends=True), sub2.splitlines(keepends=True)):
        if (line.startswith("+ ") or line.startswith("- ")) and not line[2:].isspace(): # Ignore blank lines
            lineChanges += 1

    lineCount = (line.rstrip() for line in sub1.splitlines(keepends=True)) # Remove whitespace
    lineCount = len(list(line for line in lineCount if line)) # Get length of list excluding blank lines
    percentChange = lineChanges / lineCount
    return percentChange

def check_subsequence_length(relevance_list):
    """ Updates relevance_list to avoid omitting LOC when there are less than 3 subsequent omissions or greater than 10 omitted runs in a row.

        Example: [2, 0, 0, 0, 1, 0, 0, 2] will be changed to [2, 0, 0, 0, 1, 1, 1, 2]

        Parameters
        ----------
        relevance_list : `list` [`int`]
            List defining which runs are notable (1, 2) and which are not (0)

        Returns
        -------
        relevance_list : `list` [`int`]
            Updated list defining which runs are notable (1, 2) and which are not (0)
    """

    start_loc = None
    end_loc = None
    for i in range(1, len(relevance_list)):
        # Start of sub-sequence
        if relevance_list[i] == 0 and relevance_list[i - 1] > 0:
            start_loc = i
        # End of sub-sequence
        elif relevance_list[i] > 0 and relevance_list[i - 1] == 0:
            end_loc = i - 1
        # Never omit >10 subsequent runs
        elif start_loc and i - start_loc == 10:
            relevance_list[i] = 1
            start_loc = None
        if start_loc and end_loc:
            # Sub-sequence too small, mark runs as notable
            if end_loc - start_loc < 2:
                for j in range(start_loc, end_loc + 1):
                    relevance_list[j] = 1
            start_loc = None
            end_loc = None
    return relevance_list

def check_subsequence_values(relevance_list, lines):
    """ Updates relevance_list to highlight runs that don't follow LOC trend exhibited by sub-sequence endpoints.

        Parameters
        ----------
        relevance_list : `list` [`int`]
            List defining which runs are notable (1, 2) and which are not (0)
        
        lines : `list` [`int`]
            List of line counts from each run

        Returns
        -------
        relevance_list : `list` [`int`]
            Updated list defining which runs are notable (1, 2) and which are not (0)
    """

    start_loc = None
    end_loc = None
    for i in range(1, len(relevance_list)):
        # Start of sub-sequence
        if relevance_list[i] == 0 and relevance_list[i - 1] > 0:
            start_loc = i
        # End of sub-sequence
        elif relevance_list[i] > 0 and relevance_list[i - 1] == 0:
            end_loc = i - 1
        if start_loc and end_loc:
            for j in range(start_loc, end_loc + 1):
                # Increasing LOC trend from start to end
                if lines[start_loc] < lines[end_loc]:
                    # Sub-sequence element doesn't follow increasing trend
                    if lines[j] < lines[start_loc] or lines[j] > lines[end_loc]:
                        relevance_list[j] = 1
                        start_loc = j + 1
                # Decreasing LOC trend from start to end
                else:
                    # Sub-sequence element doesn't follow decreasing trend
                    if lines[j] > lines[start_loc] or lines[j] < lines[end_loc]:
                        relevance_list[j] = 1
                        start_loc = j + 1
            start_loc = None
            end_loc = None 
    return relevance_list

# Create list of submission sessions
def get_sub_sessions(run_times):
    """ Generates a list of 1's and 0's, where 1's represent runs directly following a session break (>30 minutes since previous run).
        0's indicate that a new session has not begun.

        Parameters
        ----------
        run_times : `dict` [`pandas.Timestamp`]
            Chronological list of all run times

        Returns
        -------
        session_breaks : `list` [`int`]
            List showing where session breaks occurred
    """

    session_breaks = [0]
    for i in range(1, len(run_times)):
        diff = get_submission_time_diff(run_times[i - 1], run_times[i])
        if diff <= 1800:
            session_breaks.append(0)
        else:
            session_breaks.append(1)
    return session_breaks

def get_submission_time_diff(prev, curr):
    """ Get diff in seconds between two timestamps.

        Parameters
        ----------
        prev, curr : `pandas.Timestamp`
            Timestamps from two distinct runs

        Returns
        -------
        time : `float`
            Diff between passed in timestamps
    """

    if curr == -1:
        time = -1
    else:
        time = pd.Timedelta(curr - prev).total_seconds()
    return time

def adjust_score(score):
    """ Adjust IncDev score if greater than 1.

        Parameters
        ----------
        score : `float`
            Score before adjustment

        Returns
        -------
        score : `float`, `int`
            IncDev score after adjustment, becomes int if 'if' statement executes
    """

    if score > 1:
        score = 1
    return score
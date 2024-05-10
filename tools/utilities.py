import csv
import io
import json
import logging
import os
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from logging import Logger

import pandas as pd
import requests
from dateutil import parser
from pandas import DataFrame
from tqdm import tqdm
from urllib3 import Retry

from tools.submission import Submission


class Not200Error(Exception):
    """Raise this custom exception if we receive a "valid" response from the server, but no data is present"""

    pass


def setup_logger(name: str, log_level=logging.DEBUG, log_format='%(name)s : %(message)s') -> Logger:
    """Set up a logger with a given name, for debugging purposes.

    This can be helpful for outputting messages during debugging
    as an alternative to simple print statements.

    Args:
        name (str): The name of the logger.
        log_level (int, optional): The log level for the logger. Defaults to logging.DEBUG.
        log_format (str, optional): The log format for the logger. Defaults to '%(name)s : %(message)s'.

    Returns:
        Logger: The configured logger object.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(log_format))
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.addHandler(handler)
    return logger


def print_menu(options: list[str]) -> None:
    """Prints a menu with the given options."""
    for i, option in enumerate(options, start=1):
        print(f'{i}) {option}')
    print()


def get_code_with_max_score(user_id: int, lab: float, submissions: dict) -> str:
    """Returns the first highest-scoring code submission for a student for a lab.

    The "first" highest-scoring submission means the oldest submission with the highest score.

    Args:
        user_id (int): Find the highest-scoring submission for the student with this ID.
        lab (float): Find the highest-scoring submission for this lab, e.g. lab 3.12.
        submissions (dict): All of the student's submissions for this lab.

    Returns:
        str: The code for the first highest-scoring submission.
    """
    max_score = 0
    code = submissions[user_id][lab][-1].code  # Choose a default submission
    for sub in submissions[user_id][lab]:
        if sub.max_score > max_score:
            max_score = sub.max_score
            code = sub.code
    return code


def standardize_columns(logfile: DataFrame) -> DataFrame:
    """Standardizes the column names in a zyBooks logfile (Pandas DataFrame).

    Changes the following column names:
    - date_submitted(UTC) etc. -> date_submitted
    - submission -> is_submission
    - content_resource_id -> lab_id

    Args:
        logfile (DataFrame): The log of all student submissions.

    Returns:
        DataFrame: The DataFrame for the logfile, edited in-place.
    """
    for column in logfile.columns:
        if 'date_submitted' in column:
            logfile.rename(columns={column: 'date_submitted'}, inplace=True)
        elif 'submission' in column:
            logfile.rename(columns={column: 'is_submission'}, inplace=True)
        elif 'content_resource_id' in column:
            logfile.rename(columns={column: 'lab_id'}, inplace=True)
    return logfile


def get_valid_datetime(timestamp: str) -> datetime:
    """Returns a datetime object for a submission timestamp.

    Uses the dateutil.parser module to handle many common datetime formats.

    Args:
        timestamp (str): A timestamp, e.g. 'YYYY-MM-DD HH:MM:SS'.

    Returns:
        datetime: A datetime object representing the given timestamp.

    Raises:
        ParserError: If the datetime format cannot be recognized.
    """
    try:
        return parser.parse(timestamp)
    except parser.ParserError:
        raise parser.ParserError(f'Cannot recognize datetime format: {timestamp}')


def download_solution(logfile: DataFrame) -> str | None:
    """Return the solution code from a logfile, if present.

    Args:
        logfile (DataFrame): The logfile containing submissions.

    Returns:
        str | None: The solution code, or None if not found.
    """
    solution = None
    for row in logfile.itertuples():
        if row.user_id == -1:
            solution = row
            break
    if solution and not pd.isnull(solution.zip_location):
        solution_code = download_code_helper(solution.zip_location)[1]
        return solution_code
    return None


def download_code_helper(url: str) -> tuple[str, str]:
    """Downloads student code from a given URL and returns the code with the URL.

    Args:
        url (str): The URL from which to download the code.

    Returns:
        tuple[str, str]: A tuple containing the URL and the downloaded code.

    Raises:
        Not200Error: If the response status code is not 200 (no data received).
        ConnectionError: If the maximum number of retries is reached and the code cannot be retrieved.
    """
    retry_strategy = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    file_name = url.split('/')[-1].strip('.zip')
    path = 'downloads/' + file_name + '.cpp'
    if not os.path.isfile(path):
        try:
            response = session.get(url)
            if response.status_code > 200 and response.status_code < 300:
                raise Not200Error
            zfile = zipfile.ZipFile(io.BytesIO(response.content))
            filenames = zfile.namelist()
            content = zfile.open(filenames[0], 'r').read()
            result = content.decode('utf-8')
            with open(path, 'w', encoding='utf-8') as file:
                file.write(result)
            return (url, result)
        except Not200Error:
            return (url, 'Retrieved a response, but no data was received.')
        except ConnectionError:
            return (url, 'Max number of retries met while retrieving student code.')
    else:
        with open(path, 'r', errors='replace') as file:
            result = file.read()
        return (url, result)


def download_code(logfile: DataFrame) -> DataFrame:
    """Downloads the code for each submission and appends a new column to a logfile for the code.

    Args:
        logfile (DataFrame): The log of all student submissions.

    Returns:
        DataFrame: The updated logfile with a new column for the downloaded code.

    Note:
        This is the fastest way to download code submissions that we found.
        We tried AsyncIO but it turned out to be slower than multithreading.
    """
    urls = logfile.zip_location.to_list()
    threads = []
    with ThreadPoolExecutor() as executor:
        for url in urls:
            threads.append(executor.submit(download_code_helper, url))
        student_code = []
        with tqdm(total=len(threads), desc='Downloading student code') as pbar:
            for task in as_completed(threads):
                student_code.append(task.result())
                pbar.update(1)
    df = pd.DataFrame(student_code, columns=['zip_location', 'student_code'])
    logfile = pd.merge(left=logfile, right=df, on=['zip_location'])
    return logfile


# TODO: validate input, what if input is non-integer?
def get_selected_labs(logfile: DataFrame) -> list[str]:
    """Gets a list of labs specified by user input.

    Args:
        logfile (DataFrame): The log of all student submissions.

    Returns:
        list[str]: A list of selected lab IDs
    """
    i = 0
    labs_list = []
    lab_ids = logfile.content_section.unique()
    print('Select the labs to evaluate, separated by a space: (Ex: 1 or 1 2 3 or 2 3)')
    print(f'{i})  Select all labs')
    i += 1
    for lab_id in lab_ids:
        lab_caption = logfile.query('content_section ==' + str(lab_id))['caption'].iloc[0]
        print(f'{i}) {lab_id:.2f}: {lab_caption}')
        labs_list.append(lab_id)
        i += 1

    # TODO: Make this a helper function
    while True:  # Validate user inputs
        all_options_valid = True
        selected_options = [i.strip() for i in input().split()]
        for option in selected_options:
            if not (option.isdigit() and 0 <= int(option) <= i - 1):
                all_options_valid = False
                print(f'Inputs must all be digits 0-{i - 1}, please try again.')
                break
        if all_options_valid:
            break

    selected_labs = []
    if selected_options[0] == '0':
        for lab in labs_list:
            selected_labs.append(lab)
    else:
        for selected_lab in selected_options:
            selected_labs.append(labs_list[int(selected_lab) - 1])
    return selected_labs


def write_output_to_csv(final_roster: dict, file_name: str = 'roster.csv') -> None:
    """Saves the final roster (result) dictionary as a CSV file.

    Args:
        final_roster (dict): A dictionary containing the final roster data.
        file_name (str): The name of the output CSV file. Default is 'roster.csv'.

    Returns: None

    Raises:
        IOError: If there is an error while writing the CSV file.
    """
    csv_columns = []
    for id in final_roster:
        for column in final_roster[id]:
            if column not in csv_columns:
                csv_columns.append(column)
    try:
        csv_file = f'output/{file_name}'
        with open(csv_file, 'w', newline='', encoding='utf-8') as f1:
            writer = csv.DictWriter(f1, fieldnames=csv_columns)
            writer.writeheader()
            for user_id in final_roster.keys():
                writer.writerow(final_roster[user_id])
    except IOError as err:
        print(err)


def create_data_structure(logfile: DataFrame) -> dict:
    """
    Returns a data structure which stores all Submission objects for each student.

    Args:
        logfile (DataFrame): The log of all student submissions.

    Returns:
        dict: A data structure that stores all Submission objects for each student.

    Example:
        data = {
            user_id_1: {
                lab_id_1 : [submission, submission, submission],
                lab_id_2 : [submission, submission, submission]
            }
            user_id_2: {
                lab_id_1 : [submission, submission, submission],
                lab_id_2 : [submission, submission, submission]
            }
            ...
        }
    """
    data = {}
    for row in logfile.itertuples():
        if row.user_id not in data:
            data[int(row.user_id)] = {}
        if row.content_section not in data[row.user_id]:
            data[row.user_id][row.content_section] = []
        sub = Submission(
            student_id=row.user_id,
            crid=row.lab_id,
            caption=row.caption,
            first_name=row.first_name,
            last_name=row.last_name,
            email=row.email,
            zip_location=row.zip_location,
            submission=row.is_submission,
            max_score=row.score,
            lab_id=row.content_section,
            submission_id=row.zip_location.split('/')[-1],
            type=row.is_submission,
            code=row.student_code,
            sub_time=get_valid_datetime(row.date_submitted),
            anomaly_dict=None,
        )
        data[row.user_id][row.content_section].append(sub)
    return data


def get_testcases(logfile: DataFrame, selected_labs: list[float]) -> dict[float, set[tuple]]:
    """Returns a set of test cases from a student submission logfile.

    Args:
        logfile (DataFrame): The student submission logfile.
        selected_labs (list[float]): A list of lab IDs to extract testcases for.

    Returns:
        dict[float, set[tuple]]: A dictionary of a set of tuples. Each key is a lab ID, and each tuple is the
            (input, output) of a testcase for that lab ID. Tuple is [str, str].

    Example:
        testcases_per_lab = {
            lab_id_1 : {
                (input1, output1),
                (input2, output2)
            }
            lab_id_2 : {
                (input1, output1),
                (input2, output2)
            }
        }
    """
    testcases_per_lab = dict()
    submissions = logfile[logfile['is_submission'] == 1]

    for lab_id in selected_labs:
        testcases = set()
        lab_submissions = submissions[submissions['content_section'] == lab_id]
        for row in lab_submissions.itertuples():  # Pick first student submission in logfile
            if pd.isnull(row.result):  # Check that 'results' column isn't empty
                continue
            try:
                result = json.loads(row.result)
            except json.JSONDecodeError:  # If `results` is malformed, try next submission
                continue
            for test in result['config']['test_bench']:
                if test.get('options'):  # Check that the entry has the ['options'] fields
                    # Save input/output for each test case
                    if test['options'].get('input') and test['options'].get('output'):
                        input = test['options']['input'].strip()
                        output = test['options']['output'].strip()
                        testcases.add((input, output))
            testcases_per_lab[lab_id] = testcases
            break
    return testcases_per_lab

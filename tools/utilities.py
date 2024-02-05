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


def standardize_columns(logfile: DataFrame) -> DataFrame:
    """
    Standardizes the column names in a logfile (Pandas DataFrame).
    Returns the standardized DataFrame, edited in-place.

    - date_submitted(UTC) etc. -> date_submitted
    - submission -> is_submission
    - content_resource_id -> lab_id
    """
    for column in logfile.columns:
        if 'date_submitted' in column:
            logfile.rename(columns={column: 'date_submitted'}, inplace=True)
        elif 'submission' in column:
            logfile.rename(columns={column: 'is_submission'}, inplace=True)
        elif 'content_resource_id' in column:
            logfile.rename(columns={column: 'lab_id'}, inplace=True)
    return logfile


def setup_logger(name: str, log_level=logging.DEBUG, log_format='%(name)s : %(message)s') -> Logger:
    """Set up a logger with a given name."""
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(log_format))
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    logger.addHandler(handler)
    return logger


def get_valid_datetime(timestamp: str) -> datetime:
    """
    Returns a datetime object for a submission timestamp.

    dateutil.parser handles many common datetime formats.
    A ParserError is raised if the datetime cannot be parsed.
    """
    try:
        return parser.parse(timestamp)
    except parser.ParserError:
        raise parser.ParserError(f'Cannot recognize datetime format: {timestamp}')


def download_solution(logfile: DataFrame) -> str | None:
    """Return solution code in a logfile, if present"""
    for row in logfile.itertuples():
        if row.user_id == -1:
            solution = row
            break

    if solution and not pd.isnull(solution.zip_location):
        solution_code = download_code_helper(solution.zip_location)[1]
        return solution_code
    return None


def download_code_helper(url: str) -> tuple[str, str]:
    """
    Actual code which downloads the students code run using requests library
    """
    # Define our retry strategy for all HTTP requests
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
            return (url, 'Successfully received a response, but not data was received')
        except ConnectionError:
            return (url, 'Max retries met, cannot retrieve student code submission')
    else:
        with open(path, 'r', errors='replace') as file:
            result = file.read()
        return (url, result)


def download_code(logfile: DataFrame) -> DataFrame:
    """
    Iterates through the zybooks logfile dataframe, appends a new column "student_code" to the dataframe and returns it

    Note: This is the fastest way to download code submissions of all students at this time.
    We tried AsyncIO but it turned out to be slower than multithreading
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
    """
    Function to get selected labs from the user entered input
    """
    lab_ids = logfile.content_section.unique()
    # Select the labs you want a roster for
    print('Select the indexes you want a roster for separated by a space: (Ex: 1 or 1 2 3 or 2 3)')
    labs_list = []
    i = 0
    print(i, '  select all labs')
    i += 1
    for lab_id in lab_ids:
        print(i, ' ', lab_id, logfile.query('content_section ==' + str(lab_id))['caption'].iloc[0])
        labs_list.append(lab_id)
        i += 1
    selected_options = input()
    selected_labs = []
    if selected_options.split()[0] == '0':
        for lab in labs_list:
            selected_labs.append(lab)
    else:
        selected_lab_index = selected_options.split()
        for selected_lab in selected_lab_index:
            selected_labs.append(labs_list[int(selected_lab) - 1])
    return selected_labs


def write_output_to_csv(final_roster, file_name='roster.csv'):
    """
    This function writes our dataframe into a csv output file
    """
    # # Writing the output to the csv file
    # now = str(datetime.now())
    csv_columns = []
    for id in final_roster:
        for column in final_roster[id]:
            # print(summary_roster[id])
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
    Creates a data structure which stores all submission objects of each student

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


# TODO: verify this works correctly for hardcoding
def get_testcases(logfile: DataFrame) -> set[tuple]:
    # Pick first student submission in logfile
    testcases = set()
    submissions = logfile[logfile['is_submission'] == 1]
    for row in submissions.itertuples():
        if not pd.isnull(row.result):  # Check that 'results' column isn't empty
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
            break
    return testcases

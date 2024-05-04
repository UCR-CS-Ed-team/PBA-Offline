from datetime import datetime


# TODO: Remove redundant attributes and improve naming.
class Submission:
    """
    Represents a submission made by a student.

    Attributes:
        student_id (int): The ID of the student.
        crid (int): The ID of the content resource on zyBooks.
        lab_id (float): The ID of the lab.
        submission_id (int): The ID of the file containing the submission code.
            Example: '63880560-9d25-4ea2-8321-df9cbb0dd278.zip'
        type (int): The type of the submission (1 for submission, 0 for development run).
        code (str): The code submitted.
        sub_time (str): The submission datetime.
        caption (str): The caption (title) of the assignment.
        first_name (str): The first name of the student.
        last_name (str): The last name of the student.
        email (int): The email of the student.
        zip_location (str): The URL of the zip file containing the student code.
        submission (int): The type of the submission (1 for submission, 0 for development run).
        max_score (int): The highest score achieved as of a particular submission.
        anomaly_dict (dict, optional): A dictionary containing any anomalies in the submission.
    """

    def __init__(
        self,
        student_id: int,
        crid: int,
        lab_id: float,
        submission_id: int,
        type: int,
        code: str,
        sub_time: datetime,
        caption: str,
        first_name: str,
        last_name: str,
        email: int,
        zip_location: str,
        submission: int,
        max_score: int,
        anomaly_dict: dict = None,
    ):
        self.student_id = student_id
        self.crid = crid
        self.lab_id = lab_id
        self.submission_id = submission_id
        self.type = type
        self.code = code
        self.sub_time = sub_time
        self.anomaly_dict = anomaly_dict
        self.caption = (caption,)
        self.first_name = (first_name,)
        self.last_name = (last_name,)
        self.email = (email,)
        self.zip_location = (zip_location,)
        self.submission = (submission,)
        self.max_score = max_score

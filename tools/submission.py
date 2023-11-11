""""
Submission object to represent student code submissions containing all sorts of data
"""


class Submission:
    def __init__(
        self,
        student_id: int,
        crid: int,
        lab_id: float,
        submission_id: int,
        type: int,
        code: str,
        sub_time: str,
        caption: str,
        first_name: str,
        last_name: str,
        email: int,
        zip_location: str,
        submission: int,
        max_score: int,
        anomaly_dict=None,
        suspicious=None,
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

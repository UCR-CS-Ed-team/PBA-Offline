# Programming Behavior Analysis (PBA)

Programming Behavior Analysis (PBA) is a set of tools used to find students that are potentially cheating in CS courses without using code similarity. Instead, this project finds metrics which *complement* code similarity in finding cheating.

## Features

**Style Anomalies**: Finds unusual code styles that are not taught in a course. Styles are easily configurable with RegEx and can be given different weights.

**Hardcoding Detection**: Finds students that are abusing automated grading systems by hardcoding to testcases in code.

**Incremental Development**: Measures how "incrementally" students are developing their solution. Finds students that may be copying a solution instead of slowly developing their own.

**Quick Analysis**: Gives averages for each assignment: time spent, number of times code was submitted or tested, and assignment score.

**Roster**: Gives statistics for each student in a class: points earned per minute, total time spent, score, number of submissions and tests, and the same metrics per assignment.

## Getting Started

This project is currently meant to be used with introductory CS courses that teach C++ using zyBooks. PBA needs a zyBooks logfile (`.csv`) for an assignment as input, and most tools expect C++ code.

### Prerequisites

You need the following to use PBA:
- Git (download and install [here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git))
- Python 3.6+ (download and install [here](https://www.python.org/downloads/))
- A zyBooks C++ course
- A `.csv` zyBooks logfile of student submissions for an assignment(s)

For PBA to analyze submissions for an assignment, you need a logfile of student submissions in `.csv` format for that assignment. To get this, follow the GIF below, or do the following:
1. Go to the lab assignment in your zyBook
2. Scroll down to "Class statistics", expand the section
3. Click "Download log of all runs"

![Downloading zyBooks logfile GIF](.github/zybooks-download-logfile.gif)

The contents of the logfile should look like this:

| zybook_code         |   lab_id |   content_section | caption              |   user_id | first_name   | last_name   | email            |   class_section | role    | date_submitted(UTC)   | zip_location                                                                         |   is_submission |   score |   max_score | result   |   ip_address |
|:--------------------|---------:|------------------:|:---------------------|----------:|:-------------|:------------|:-----------------|----------------:|:--------|:----------------------|:-------------------------------------------------------------------------------------|----------------:|--------:|------------:|:---------|-------------:|
| CS1OnlineSpring2023 | 72217180 |               3.2 | LAB: How many digits |        -1 | Solution     | Solution    | nan              |             nan | nan     | nan                   | https://programming-submissions.zybooks.com/b0cee7c8-d82b-43ac-8ed3-8b1a93c91c4c.zip |             nan |     nan |         nan | …        |          nan |
| CS1OnlineSpring2023 | 72217180 |               3.2 | LAB: How many digits |    604387 | Benjamin     | Denzler     | bdenz001@ucr.edu |             nan | Student | 4/24/2023 3:47        | https://programming-submissions.zybooks.com/60b7ea17-e5e6-472b-9c5e-5ebc0c723487.zip |               1 |       0 |          10 | …        |          nan |
| CS1OnlineSpring2023 | 72217180 |               3.2 | LAB: How many digits |    604387 | Benjamin     | Denzler     | bdenz001@ucr.edu |             nan | Student | 4/24/2023 3:47        | https://programming-submissions.zybooks.com/b7a57fb8-7159-460c-8e24-6bc3782423c6.zip |               1 |       8 |          10 | …        |          nan |
| CS1OnlineSpring2023 | 72217180 |               3.2 | LAB: How many digits |    604387 | Benjamin     | Denzler     | bdenz001@ucr.edu |             nan | Student | 4/24/2023 3:47        | https://programming-submissions.zybooks.com/16478868-0a97-47d5-a31f-34dc13b3813f.zip |               1 |      10 |          10 | …        |          nan |

### 1. Clone the repository

```
git clone https://github.com/UCR-CS-Ed-team/PBA-Offline
cd PBA-Offline
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Run PBA
```
python main.py
```

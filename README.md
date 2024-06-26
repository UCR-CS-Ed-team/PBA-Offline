<div align="center">
  <h1 align="center">Programming Behavior Analysis (PBA)</h1>
  <h3 align="center">Find potential cheating without similarity.</h3>
</div>

This project finds students that are potentially cheating in CS courses using metrics beyond code similarity. Instructors can prioritize their time when investigating cheating cases by looking at top students in these metrics.

> **IMPORTANT**: Students flagged by this program are not always cheating. A student might have prior experience with different code styles, or codes very quickly, etc. Instructors should always thoroughly investigate flagged students before making a cheating determination.

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

### 0. Downloading zyBooks logfiles

For PBA to generate metrics for an assignment, you need a logfile of student submissions in `.csv` format for that assignment. To get this, follow the GIF below:

![Downloading zyBooks logfile GIF](.github/zybooks-download-logfile.gif)

To analyze multiple assignments, download a logfile like so:

![Downloading zyBooks logfile for multiple assignments GIF](.github/zybooks-multi-download-logfile.gif)

The logfile will be called `zylab_log_CourseNameHere_DateHere.csv` with contents like this:

```
| zybook_code   |   lab_id |   content_section | caption         |   user_id | first_name   | last_name   | email            | class_section   | role    | date_submitted(UTC)   | zip_location   | is_submission   | score   | max_score   | result   | ip_address   |
|:--------------|---------:|------------------:|:----------------|----------:|:-------------|:------------|:-----------------|:----------------|:--------|:----------------------|:---------------|:----------------|:--------|:------------|:---------|:-------------|
| CS1Class      |      123 |               3.2 | How many digits |        -1 | Solution     | Solution    |                  |                 |         |                       | url1           |                 |         |             | …        |              |
| CS1Class      |      123 |               3.2 | How many digits |       345 | Benjamin     | Denzler     | bdenz001@ucr.edu |                 | Student | 4/24/2023 3:47        | url2           | 1.0             | 0.0     | 10.0        | …        |              |
| CS1Class      |      123 |               3.2 | How many digits |       345 | Benjamin     | Denzler     | bdenz001@ucr.edu |                 | Student | 4/24/2023 3:47        | url3           | 1.0             | 8.0     | 10.0        | …        |              |
| CS1Class      |      123 |               3.2 | How many digits |       345 | Benjamin     | Denzler     | bdenz001@ucr.edu |                 | Student | 4/24/2023 3:47        | url4           | 1.0             | 10.0    | 10.0        | …        |              |
```

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

A window will appear for you to select a zyBooks logfile to analyze. Choose the `.csv` file you downloaded, then follow the instructions to choose metrics to evaluate.

The tool's output will be in the folder `output`. The tool tells you the output filename after it completes:

```
Done! Wrote output to output/{file}.csv
```

## PBA's Cheating Metrics

PBA can generate these metrics for assignments:

### Style Anomalies

Style anomalies are unusual code styles that are not taught in a class.  For example:

```cpp
// Expected style taught in class
int main() {
    int x;
    cin >> x;
    while (x > 0) {
        cout << x * x;
        cin >> x;
    }
}
```

```cpp
// Code with style anomalies
int main() {
    int x;
    cin >> x;
    while (true)    // Anomaly
    {               // Anomaly; brace style
cout << x * x;      // Anomaly; spacing
        cin >> x;
        if (x <= 0) {
            break;  // Anomaly; untaught construct
        }
    }
}
```

In our experience, an abundance of style anomalies suggests a student copied from ChatGPT, Chegg, etc.

PBA comes with style anomalies specific to CS1 courses at UC Riverside. These are in `tools/anomaly.py` in the list `style_anomalies`. To add your own style anomalies, add a `StyleAnomaly` object to the list, providing the following:
- Name of the style anomaly
- A regular expression to find the anomaly in code; will search one line at a time
- (`True/False`) Should the anomaly be enabled?
- A weight to give the anomaly
- A cap on the number of instances of this anomaly to find per-student, defaults to `-1` (no cap)

Each style anomaly has its own weight. PBA will scan each line of a student's submission to find style anomalies. For each style anomaly found for a student, the anomaly's weight gets added to the student's Style Anomaly Score, and their Style Anomaly Count increases by 1. 

Optionally, a style anomaly can be configured to only be counted up to `X` times for each student. This can prevent one style anomaly from being counted an excessive number of times. There is no cap initially, but it can be enabled by changing `-1` to `X` in the last parameter for an anomaly:

```py
style_anomalies = [                                 # --V-- change -1 to X
    StyleAnomaly('Pointers', POINTERS_REGEX, True, 0.9, X),
    StyleAnomaly('Infinite Loop', INFINITE_LOOP_REGEX, True, 0.9, -1),
    ...
]
```

The tool's output looks like:

```
|   User ID | Last Name   | First Name   | Email            | Role    |   Lab 2.24 anomalies found |   Lab 2.24 anomaly score | 2.24 Student code   |   Lab 2.25 anomalies found |   Lab 2.25 anomaly score | 2.25 Student code   |   Lab 2.26 anomalies found |   Lab 2.26 anomaly score | 2.26 Student code   |
|----------:|:------------|:-------------|:-----------------|:--------|---------------------------:|-------------------------:|:--------------------|---------------------------:|-------------------------:|:--------------------|---------------------------:|-------------------------:|:--------------------|
|    604387 | Benjamin    | Denzler      | bdenz001@ucr.edu | Student |                          1 |                      0.3 | {code here}         |                          3 |                      0.5 | {code here}         |                          6 |                      0.6 | {code here}         |
```

### Hardcoding Detection

The Hardcoding tool finds students that have hardcoded outputs to get points on auto-graders without implementing a correct program. For example, if an autograder gives an input `123` and expects output `abc`, hardcoding looks like:

```cpp
int main() {
    if (x == "123") {   // Input
        cout << "abc";  // Output
    }
}
```

Even this might get points for that testcase:
```cpp
int main() {
    cout << "123";  // Output only
    return 0;
}
```

The tool's output looks like:

```
|   User ID | Last Name   | First Name   | Email            | Role    |   Lab 2.24 hardcoding score | 2.24 Student code   |
|----------:|:------------|:-------------|:-----------------|:--------|----------------------------:|:--------------------|
|    604387 | Denzler     | Benjamin     | bdenz001@ucr.edu | Student |                           1 | {code here}         |
```

Hardcoding detection works best if an assignment has both a solution and testcases. The tool will work differently in three cases:

#### With Solution and Testcases (Most Accurate)

If a student hardcodes exactly the output of a testcase *and* the solution does not, flag the student for hardcoding. The tool assumes that if the solution hardcodes the same output, then it is a valid way to solve the assignment and shoudln't be flagged. The hardcoded output can look like any of the following:

```cpp
// Example 1
cout << "Testcase output exactly" << endl;

/* 
  Example 2
  Expected testcase input: "123"
  Expected testcase output: "123 is the testcase input"
*/
if (x == "123") {
    cout << x << " is the testcase input.";
}

// Example 3
if (year == 1980) {
    cout << "No championship" << endl;
}
```

#### With Testcases, but No Solution (Less Accurate)

Without a solution to reference, the tool uses other students' submissions to determine whether code that appears hardcoded is a valid solution. The tool first finds the same examples of hardcoding listed above. Then, if at least 60% of the class hardcoded the same testcase, that testcase isn't considered for hardcoding. The 60% threshold is configurable as `testcase_use_threshold` in function `hardcoding_analysis_2()`.

#### No Testcases or Solution (Least Accurate)

This is an unlikely use case considering students are unlikely to hardcode if there is no automated grading system. Still, we include this for flexibility.

The tool will look for `if` statements that compare to literals in the condition, and then output a literal inside the body. The literals can be strings, ints, or floats. For example:

```cpp
if (x == 7) {         // Input
    cout << "Prime";  // Output
}
```

Students that do so are flagged for hardcoding, unless at least 60% of the class also does this. The 60% threshold is configurable as `if_literal_threshold` in function `hardcoding_analysis_3()`.

### Incremental Development

> This tool was created by Lizbeth Areizaga ([liz-areizaga](https://github.com/liz-areizaga)) from UC Riverside.

Ideally, students would gradually make small, *incremental* changes to their code and test their changes before submitting a solution. This is especially true at UC Riverside, where students are required to do all development in the online zyBooks IDE.

The Incremental Development tool measures how incrementally a student developed their code. It aims to find students that immediately submit large working solutions or suddenly edit a large part of their code; these students might be copying code.

This tool provides several metrics:

#### Incremental Development Score

A float between 0 and 1 where 1 means the student developed very incrementally, and 0 means the student's code changed very quickly.

#### Incremental Development Score Trail

A visualization of the student's development history across all submissions. These are metrics about each submission separated by commas. Formatted as:

```
line count 1 (inc dev score 1), ^line count 2 (inc dev score 2), ...
```
A `^` before a line count means that more than 50% of lines in this submission were added, deleted, or modified since the last submission. An example:
```
7 (1), ^36 (0.64), ^7 (0.74)
```
This student first submitted 7 lines with an inc. dev score of 1, then submitted 36 lines (more than 50% were different from last submission) with an inc. dev score of 0.64, then submitted 7 lines (more than 50% were different again) with an inc. dev score of 0.74.

#### Lines of Code Trail

A visualization of the lines of code in each submission for a student's development history. Formatted as:

```
line count 1, line count 2 ... ^line count 3
```
A `^` before a line count again means that more than 50% of lines in this submission were added, deleted, or modified since the last submission. Uninteresting runs (few changes from the last) are shown as `.` for brevity. An example:
```
26,^24...^26
```
This student first submitted 26 lines, then 24 lines and changed more than 50% of the lines from the first, then submitted 3 very similar runs, then 26 lines and changed more than 50% of the lines from the last.

#### Time Trail

A visualization of the time in minutes between submissions for a student's development history. Submissions that were just to test the code (not for points) are denoted as `-`. Breaks (>30 min since last run) are denoted by `/`. For example:

```
---0,1 / 0,8
```
This student tested their code 3 times, submitted <1 minute later, then 1 minute later, took a break for over 30 minutes before submitting, submitted <1 minute later, then 8 minutes later.

### Quick Analysis

This tool gives the following metrics for each lab selected:
- Number of students that submitted code
- Average time spent working on the assignment
- Average score on the assignment
- Average number of code runs; either submissions for points, or to test their code
- Average number of develop runs; tests that were not for points
- Average number of submission runs; submissions for points

### Roster

This tool gives the following metrics for each student that submitted to the selected labs:
- Total time spent across all selected labs
- Total score across all selected labs
- Average points earned per minute (PPM) across all selected labs
- Total number of code runs; either submissions for points, or to test their code
- Total number of develop runs; tests that were not for points
- Total number of submission runs; submissions for points
- All of the same metrics for *each* assignment (e.g. Lab 2 time spent, lab 3 time spent, ...)

## Tips for Contributing

PBA uses [Ruff](https://docs.astral.sh/ruff/) for formatting code, which is installed as a dependency when you set up the project. Before pushing code, please run `ruff format .` in the project directory to format the project files. This keeps code style consistent!

You can install extensions to integrate Ruff into your IDE [here](https://docs.astral.sh/ruff/integrations/).

## Contributors

<a href="https://github.com/UCR-CS-Ed-team/PBA-Offline/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=UCR-CS-Ed-team/PBA-Offline" />
</a>

The Incremental Development tool was made by Lizbeth Areizaga ([liz-areizaga](https://github.com/liz-areizaga)) from UC Riverside.

Made with [contrib.rocks](https://contrib.rocks).

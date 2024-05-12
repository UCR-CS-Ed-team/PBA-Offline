# Programming Behavior Analysis (PBA)

Programming Behavior Analysis (PBA) is a set of tools used to find students that are potentially cheating in CS courses without using code similarity. Instead, this project finds metrics which *complement* code similarity in finding cheating.

## Features

**Style Anomalies**: Finds unusual code styles that are not taught in a course. Styles are easily configurable with RegEx and can be given different weights.

**Hardcoding Detection**: Finds students that are abusing automated grading systems by hardcoding to testcases in code.

**Incremental Development**: Measures how "incrementally" students are developing their solution. Finds students that may be copying a solution instead of slowly developing their own.

**Quick Analysis**: Gives averages for each assignment: time spent, number of times code was submitted or tested, and assignment score.

**Roster**: Gives statistics for each student in a class: points earned per minute, total time spent, score, number of submissions and tests, and the same metrics per assignment.

## Getting Started

This project is currently meant to be used with introductory CS courses that teach C++ using zyBooks. PBA expect a zyBooks logfile (`.csv`) for an assignment as input, and most tools expect C++ code.

### Prerequisites

You need the following to use PBA:
- Git (download and install [here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git))
- Python 3.6+ (download and install [here](https://www.python.org/downloads/))
- A zyBooks C++ course

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

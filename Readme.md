# Programming Behavior Analysis (PBA)

This is the offline, terminal-based version of the Programming Behavior Analysis tool suite.

This project is a work in progress! A more finished version should be ready by June 2024.

Given a logfile (`.csv`) of all student submissions for a zyBooks assignment, this tool produces one or more metrics to help instructors determine the likelihood a student is cheating on an assginment.

Metrics include:

- **Style anomalies**: To what extent did a student's code style deviate from what we teach in class? E.g. using advanced constructs, different brace styles...
- **Hardcoding detection**: Did a student hardcode to a test case to get points? E.g. if (input == 'abc') output 'xyz'
- **Incremental development**: Did a student incrementally make small changes, or did they change large blocks of code at once? Changing lots of code between submissions suggests copy-pasting a solution.
- **Quick analysis**: Gives a one-line summary of averages for an assignment, e.g. avg # of submits, runs, score...
- **Roster**: The same info from "Quick analysis" but for each student. Can see each student's # of runs, submissions, score, time taken...

Each metric is produced by a module in the `tools` directory. `main.py` takes a zyBooks logfile as input, and uses the modules in `tools` depending on what metrics you ask for.

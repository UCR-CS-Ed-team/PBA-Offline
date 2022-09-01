# Python imports
from threading import Thread
import pandas as pd
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# User imports
# from application.programming_behavior_analysis.student_code_load.submission import Submission
from tools import submission as Submission
from tools.anomaly_detection.helpers import c_plus_plus as cpp
from tools.anomaly_detection.helpers.util import pairwise


# TODO - we'll likely want to abstract the anomaly detection algorithm behind a factory so that the user can simply specify what programming language they
# want to use to run anomaly detection on, but for now we'll call a generic function that only processes C++ code submissions
#@celery.task()
def anomaly(submission:Submission) -> None:
    """
    Each Submission object is loaded with an "anomaly_dict" which defines the anomalies the user wants to search for, the point "penalty" we should assign to each
    instance of those anomalies that have been found, as well as whether or not we should "count" certain anomalies
    """
    # print(submission)
    # instantiate regex expressions
    pointer_declaration_regex = re.compile(r'(\(+)?((int)|(char)|(string)|(void)|(bool)|(float)|(double)){1}(\)+)?(\s+)?\*{1,2}(\s+)[a-zA-Z]+(\s+)?(\=)?.*\;$')
    pointer_use_regex = re.compile(r'^(\*{1,2}[a-zA-Z_]+)|[a-zA-Z_]+(\s+)?\=(\s+)?(\&|\*{1,2})[a-zA-Z_]+')
    array_regex = re.compile(r'[a-zA-Z]+\[\d*\]')
    post_regex = re.compile(r'[a-zA-Z]+((\+{2})|(\-{2}))')
    #ternary_regex = re.compile(r'(\(+)?(([a-zA-Z]+)|([0-9]+))(\s+)?((\<)|(\>)|(\<=)|(\>=)|(==))(\s+)?(([a-zA-Z]+)|([0-9]+))(\)+)?(\s+)?\?.*\:.*')
    const_dec_regex = re.compile(r'const(\s+)((int)|(char)|(string)|(void)|(bool)|(float)|(double)){1}.*;')
    upper_dec_regex = re.compile(r'(\s+)((int)|(char)|(string)|(void)|(bool)|(float)|(double)){1}(\s+)[A-Z]+\_*[A-Z]*;')
    camel_case_regex = re.compile(r'((int)|(char)|(string)|(void)|(bool)|(float)|(double)){1}(\s+)([a-z]+[A-Z][a-z]+)+;')
    lower_case_regex = re.compile(r'(\s+)((int)|(char)|(string)|(void)|(bool)|(float)|(double)){1}(\s+)[a-z]+\_*[a-z]*;')
    cin_stream_regex = re.compile(r'(cin){1}(\s)+(\>\>).+(\>\>).+')
    inf_loop_regex = re.compile(r'while(\s+)?\((true|1)\)')
    while_cin_regex = re.compile(r'.*while(\s+)?\((\s)+(cin)(\s+)?\>\>(\s+)?.+\).*')

    # get the list of tokens in the student's code submission
    tokenDict = cpp.getTokens(submission.code)
  
    """Anomalies should only be computed once on a student's code submission"""
    if not submission.check_if_anomaly_computed():
        # Check for illegal keywords, pre-processor directives, and UDFs
        for key, value in tokenDict.items():
            if key == 'function':
                for item in value:
                    # We don't count "main" as a UDF, obviously
                    if 'main' in item:
                        continue
                    submission.udf_count += 1
                    submission.udf_list.append(item)
                    
            if key == 'preproc':
                for item in value:
                    if item not in cpp.PREPROCESSING_DIRECTIVES:
                        submission.illegal_includes += 1
                        submission.illegal_includes_list.append(item)
                    
            if key in ['STLfunction','keywords']:
                for item in value:
                    if item in cpp.KEYWORDS:
                        submission.illegal_keywords += 1
                        submission.illegal_keywords_list.append(item)

            if key == 'operators':
                if '?' in value:
                    submission.ternary_operators += value.count('?')

        # Variables to hold values while processing
        line_formatting = [] # Holds tuples representing the code line string, and relevant styling of that code line
        spacing = 0 # Used to count spacing on a line
        i = 0 # Counts the total number of "valid" code lines (e.g. ignoring comments, things of that nature)
        multiLineComment = False
        start_bracket = 0 # Keep track of brackets used in code
        line_count = 0
        word_count = 0
        max_var_name = 0

        # Now process the student's code submission line-by-line
        # Quickly iterate through and see if there are conditionals that do not have any brackets
        temp_lines = [item for item in submission.code.splitlines() if item.strip() not in '']
        temp_lines = [item[:item.find("//")] if item.find("//") != -1 else item[:item.find("/*")] if item.find("/*") != -1 else item for item in temp_lines]
        for i in range(len(temp_lines)-1):
            cur = temp_lines[i]
            next = temp_lines[i+1]
            if 'if' in cur and '{' not in cur and '{' not in next and 'std::' not in cur:
                submission.no_brackets += 1
                continue
            if 'else' in cur and '{' not in cur and '{' not in next and 'std::' not in cur:
                submission.no_brackets += 1

        s = iter(submission.code.splitlines())
        for line in s:
            indentation = 0
            i += 1
            # Look for newline characters first
            if "\\n" in line:
                submission.newline_count += 1
            if line == " " or line.strip() == "":
                spacing += 1
                continue
            for c in line:
                if c == '\t' or c.isspace():
                    indentation += 1
                else:
                    # Break on the first character encountered in the line
                    break
            line_formatting.append(tuple([line, i, indentation])) 

            # Strip the line of whitespace and perform additional processing
            l = line.strip()

            # Check for pre-processor directives
            if l.startswith("using namespace"):
                submission.has_namespace = True

            # Check to see if the main() function has been passed with command-line arguments argc/argv
            if "main" in l:
                if "int argc" in l or "char* argv[]" in l or "char** argv" in l:
                    submission.command_line_args = True
                    
            # Count the number of comments the student introduced into their code, but we don't count them as valid lines of code
            # Count comments, but don't count them as valid lines of code
            if l.startswith("/*"):
                multiLineComment = True
                submission.num_comments += 1
                if l.endswith("*/"):
                    multiLineComment = False
                    continue
                continue
            if l != "*/" and not l.endswith("*/") and multiLineComment:
                # Continue skipping lines until we find the end symbol */
                continue
            if l == "*/" or l.endswith("*/"):
                multiLineComment = False
                continue
            if l.startswith("//"):
                submission.num_comments += 1
                continue
            if "//" in l:
                submission.num_comments += 1
            if l == "{":
                # Found a bracket on a single line, begin processing
                start_bracket += 1
                continue
            if l == "}":
                # Found an end bracket on a single line, 
                if start_bracket > 0:
                    start_bracket -= 1
                    submission.single_line_brackets += 1
                continue
            # Once we get here, we're good to start counting lines of code
            line_count += 1

            # Begin checking for constructs not taught in the course
            """
                1. :: operator
                2. array accesses using [] instead of vector<T>.at()
                3. Null character (\0) or null/nullptr keywords
                5. Pointers (e.g. int* x)
                6. Post-increment or post-decrement operator - in class they're taught ++x or --x, instead of using x++ or x--
                7. break, continue, switch, goto - note that the tokenizer function won't pick these up as specific keywords
            """
            if any(x in l for x in ["NULL","\\0","nullptr","null"]):
                submission.nulls += 1
            if "::" in l:
                if not "string::npos" in l:
                    submission.scope_operators += l.count("::")
            if "endl" in l:
                submission.endl_count += 1
            if any(x in l for x in ["[","]"]):
                submission.array_accesses += l.count("[")
            if inf_loop_regex.search(l):
                submission.infloop_count += 1
                submission.infloop_list.append(inf_loop_regex.search(l).group())
            if pointer_declaration_regex.search(l) or pointer_use_regex.search(l):
                submission.pointers += 1
            # if ternary_regex.search(l):
            #     submission.ternary_operators += 1
            if post_regex.search(l):
                submission.post_operators += 1
            if const_dec_regex.search(l):
                submission.const_declarations += 1
                var = cpp.getVarName(l)
                if len(var) > max_var_name:
                    max_var_name = len(var)
            if upper_dec_regex.search(l):
                submission.upper_case_declarations += 1
                var = cpp.getVarName(l)
                if len(var) > max_var_name:
                    max_var_name = len(var) 
            if camel_case_regex.search(l):
                submission.camel_case_declarations += 1
                var = cpp.getVarName(l)
                if len(var) > max_var_name:
                    max_var_name = len(var)
            if lower_case_regex.search(l):
                submission.lower_case_declarations += 1
                var = cpp.getVarName(l)
                if len(var) > max_var_name:
                    max_var_name = len(var)

            # Generate a word count
            delimiters = ";", ",", "}", "{", "<<", ">>", "(", ")", " "
            regexPattern = '|'.join(map(re.escape, delimiters))
            words = re.split(regexPattern, l)
            while '' in words:
                words.remove('')
            for word in words:
                word_count += 1

            # Process user-provided regex
            # regex[0] = regex key (user_regex1, user_regex2, etc.), regex[1] = re.compile regex expression 
            for regex in submission.get_user_regex():
                if regex[1].search(l):
                    setattr(submission, regex[0], getattr(submission, regex[0]) + 1)
                    setattr(submission, regex[0]+'_list', getattr(submission, regex[0]+'_list') + regex[1].findall(l))                
                    
        # Processing complete - set internal members to computed values
        submission.line_count = line_count
        submission.word_count = word_count
        submission.num_line_breaks = spacing
        submission.max_var_length = max_var_name
        

        # Check for styling irregularities if the styling option was submitted by the user
        # Note we should skip this section altogether if we weren't able to retrieve the student's code submission OR their is no "main" block
        if 'Server disconnected' not in submission.code:
            if 'main' in tokenDict['function']:
                check = [x for x,y in enumerate(line_formatting) if "int main" in y[0].strip()]
                if not check:
                    # Didn't find "int main" on a single line, so it's declared another way
                    i = 1
                    while (i < len(line_formatting)):
                        if "main" in line_formatting[i][0] and "int" in line_formatting[i-1][0]:
                            check = i
                            break
                        i += 1
                else:
                    if isinstance(check, list):
                        check = check[0]


                # Check if the code submission had no indentation at all in main()
                if isinstance(check, int):
                    try:
                        if line_formatting[check + 2][2] == 0:
                            check_indentation = True
                        else:
                            check_indentation = False
                        for i in range(check + 2, len(line_formatting)):
                            if line_formatting[i][2] != line_formatting[i-1][2]:
                                check_indentation = False
                                break
                            if "return 0" in line_formatting[i][0]:
                                break
                    except Exception as e:
                        logging.error("Exception in processing indentation in main: {}, code submission is: {}".format(str(e), submission.code))
                        check_indentation = False
                    submission.no_indentation_in_main = check_indentation

                    # Check if the code submission had the same level of indentation in all of main()
                    check_indentation = True
                    for i in range(check + 2, len(line_formatting)):
                        if line_formatting[i][2] != line_formatting[i-1][2]:
                            check_indentation = False
                            break
                        if "return 0" in line_formatting[i][0]:
                            break
                    submission.same_indentation_in_main = check_indentation

        # Check for general indentation present in the code submission
        lines_indented = 0
        for indent in line_formatting:
            if indent[2] > 0:
                lines_indented += 1
        submission.num_lines_indented = lines_indented

        # Set the private member to indicate that the anomaly score has been computed
        submission.set_anomaly_as_computed()

    # For simplicity, return the submission object that was passed in
    return submission
    
def score_anomalies(submission: Submission):
    # Compute anomaly score and generate the list of anomalies found
    submission.compute_anomaly_score()
    # Return the class object as a list.  We can convert a list of lists to a pandas df
    return submission.list_representation()
    
def compute_anomalies(student_data: pd.DataFrame) -> pd.DataFrame:
    """
    Main driver function
    @ Param1: pd.DataFrame student_data - DataFrame of student records + student Submission object
    
    @ Return: pd.DataFrame object that can be converted to JSON for rendering on the front end
    """
    # student_subs = student_data.student_submission.to_list()
    student_subs = [student_data]
    threads = []
    with ThreadPoolExecutor() as executor:
        """Compute anomalies"""
        for sub in student_subs:
            threads.append(executor.submit(anomaly, sub))

        anomalies = []
        for task in as_completed(threads):
            anomalies.append(task.result())
        
        """Compute anomaly score"""
        threads.clear()
        for sub in anomalies:
            threads.append(executor.submit(score_anomalies, sub))

        scored_anomalies = []
        for task in as_completed(threads):
            scored_anomalies.append(task.result())
    
    columns = ['user_id','submission_id','submission_code','num_anomalies','anomaly_score','anomaly_list']
    df = pd.DataFrame(scored_anomalies, columns=columns)
    return df
import pandas as pd
from zipfile import ZipFile
import re
from tools.stylechecker import stylechecker

def anomalyScore(code): # Function to calculate the anomaly score
    # Below is the format for the anomaly in question
    # [Count_instances, Points/instance, anomaly on/off, regex, whether its used for once (used for !count instances)]
    # Add to the hashmap Styleanomaly in case you need new anomaly to be detected
    Styleanomaly = {
        'Pointers': {0:1, 1:0.9, 2:1, 3:r'(\(+)?((int)|(char)|(string)|(void)|(bool)|(float)|(double)){1}(\)+)?(\s+)?\*{1,2}(\s+)?[a-zA-Z]+(\s+)?(\=)?.*\;$', 4:0},
        'Infinite_loop': {0:0, 1:0.9, 2:1, 3:r'(while(\s+)?\((true|1)\))|(for(\s+)?\(;;\))', 4:0},
        'Atypical Includes': {0:1, 1:0.1, 2:1, 3:r'#(\s+)?include(\s+)?<((iomanip)|(algorithm)|(cstdlib)|(utility)|(limits)|(cmath))>', 4:0},
        'Atypical Keywords': {0:1, 1:0.3, 2:1, 3:r'((break(\s+)?;)|(switch(\s+)?\(.*\)(\s+)?{)|(continue(\s+)?;)|(sizeof\(.*\))|(case\s+([a-zA-Z0-9]+(\s+)?:)))', 4:0},
        'Array Accesses': {0:1, 1:0.9, 2:1, 3:r'([a-zA-Z0-9]+\[.*\])', 4:0},
        'Namespace Std': {0:1, 1:0.1, 2:1, 3:r'(std::)', 4:0},
        'Brace Styling': {0:1, 1:0.1, 2:1, 3:r'^((\s+)?{)', 4:0},
        'Escaped Newline': {0:1, 1:0.1, 2:1, 3:r'(\\n)', 4:0},
        'User-Defined Functions': {0:1, 1:0.8, 2:1, 3:r'^(((unsigned|signed|long|short)\s)?\S{3,}\s+\S+\(.*\))', 4:0},
        'Ternary Operator': {0:1, 1:0.2, 2:1, 3:r'(.+\s+\?\s+.+\s+:\s+.+)', 4:0},
        'Command-Line Arguments': {0:1, 1:0.8, 2:1, 3:r'(int argc, (char\s?\*\s?argv\[\]|char\s?\*\*\s?argv|char\s?\*\[\]\s?argv))', 4:0},
        'Nulls': {0:1, 1:0.4, 2:1, 3:r'(?i)(nullptr|null|\\0)', 4:0},
        'Scope Operator': {0:1, 1:0.25, 2:1, 3:r'(\S+::\S+)', 4:0},
        'Line Spacing': {0:1, 1:0.1, 2:1, 3:r'(^\S+)', 4:0}
    }

    submission_code = code    # Used to return the user code to roster.py

    anomaly_score = 0   # Initial anomaly Score
    anamolies_found = 0 # Counts the number of anamolies found 
    in_main = False     # Tracks whether the line is inside main()

    for line in code.splitlines():   # Reading through lines in the code and checking for each anomaly

        # Checks for while(1), while(true)
        if Styleanomaly['Infinite_loop'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Infinite_loop'][3], line):
                if Styleanomaly['Infinite_loop'][0] == 0 and Styleanomaly['Infinite_loop'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Infinite_loop'][1]
                    Styleanomaly['Infinite_loop'][4] += 1
                    anamolies_found += 1
                elif Styleanomaly['Infinite_loop'][0] == 1:
                    anomaly_score += Styleanomaly['Infinite_loop'][1]
                    anamolies_found += 1

        # Checks for int* var;, char** var;, and similar.
        if Styleanomaly['Pointers'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Pointers'][3], line):
                if Styleanomaly['Pointers'][0] == 0 and Styleanomaly['Pointers'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Pointers'][1]
                    Styleanomaly['Pointers'][4] += 1
                    anamolies_found += 1
                if Styleanomaly['Pointers'][0] == 1:
                    anomaly_score += Styleanomaly['Pointers'][1]
                    anamolies_found += 1

        # Checks for abnormal includes like <iomanip>, <algorithm>, <cstdlib>
        if Styleanomaly['Atypical Includes'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Atypical Includes'][3], line):
                if Styleanomaly['Atypical Includes'][0] == 0 and Styleanomaly['Atypical Includes'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Atypical Includes'][1]
                    Styleanomaly['Atypical Includes'][4] += 1
                    anamolies_found += 1
                if Styleanomaly['Atypical Includes'][0] == 1:
                    anomaly_score += Styleanomaly['Atypical Includes'][1]
                    anamolies_found += 1
        
        # Checks for keywords like switch(){, case:, continue; 
        if Styleanomaly['Atypical Keywords'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Atypical Keywords'][3], line):
                if Styleanomaly['Atypical Keywords'][0] == 0 and Styleanomaly['Atypical Keywords'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Atypical Keywords'][1]
                    Styleanomaly['Atypical Keywords'][4] += 1
                    anamolies_found += 1
                if Styleanomaly['Atypical Keywords'][0] == 1:
                    anomaly_score += Styleanomaly['Atypical Keywords'][1]
                    anamolies_found += 1

        # Checks for arr[], arr[x]
        if Styleanomaly['Array Accesses'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Array Accesses'][3], line):
                if Styleanomaly['Array Accesses'][0] == 0 and Styleanomaly['Array Accesses'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Array Accesses'][1]
                    Styleanomaly['Array Accesses'][4] += 1
                    anamolies_found += 1
                if Styleanomaly['Array Accesses'][0] == 1:
                    anomaly_score += Styleanomaly['Array Accesses'][1]
                    anamolies_found += 1

        # Checks for std::
        if Styleanomaly['Namespace Std'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Namespace Std'][3], line):
                if Styleanomaly['Namespace Std'][0] == 0 and Styleanomaly['Namespace Std'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Namespace Std'][1]
                    Styleanomaly['Namespace Std'][4] += 1
                    anamolies_found += 1
                if Styleanomaly['Namespace Std'][0] == 1:
                    anomaly_score += Styleanomaly['Namespace Std'][1]
                    anamolies_found += 1

        # Checks for { on its own line
        if Styleanomaly['Brace Styling'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Brace Styling'][3], line):
                if Styleanomaly['Brace Styling'][0] == 0 and Styleanomaly['Brace Styling'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Brace Styling'][1]
                    Styleanomaly['Brace Styling'][4] += 1
                    anamolies_found += 1
                if Styleanomaly['Brace Styling'][0] == 1:
                    anomaly_score += Styleanomaly['Brace Styling'][1]
                    anamolies_found += 1

        # Checks for use of \n
        if Styleanomaly['Escaped Newline'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Escaped Newline'][3], line):
                if Styleanomaly['Escaped Newline'][0] == 0 and Styleanomaly['Escaped Newline'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Escaped Newline'][1]
                    Styleanomaly['Escaped Newline'][4] += 1
                    anamolies_found += 1
                if Styleanomaly['Escaped Newline'][0] == 1:
                    anomaly_score += Styleanomaly['Escaped Newline'][1]
                    anamolies_found += 1

        # Checks for user-defined functions like `int add(int a)`, excludes `int main()`
        if Styleanomaly['User-Defined Functions'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['User-Defined Functions'][3], line) and not line.__contains__("main()"):
                if Styleanomaly['User-Defined Functions'][0] == 0 and Styleanomaly['User-Defined Functions'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['User-Defined Functions'][1]
                    Styleanomaly['User-Defined Functions'][4] += 1
                    anamolies_found += 1
                if Styleanomaly['User-Defined Functions'][0] == 1:
                    anomaly_score += Styleanomaly['User-Defined Functions'][1]
                    anamolies_found += 1

        # Checks for statements like `x == y ? True : False`
        if Styleanomaly['Ternary Operator'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Ternary Operator'][3], line):
                if Styleanomaly['Ternary Operator'][0] == 0 and Styleanomaly['Ternary Operator'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Ternary Operator'][1]
                    Styleanomaly['Ternary Operator'][4] += 1
                    anamolies_found += 1
                if Styleanomaly['Ternary Operator'][0] == 1:
                    anomaly_score += Styleanomaly['Ternary Operator'][1]
                    anamolies_found += 1

        # Checks for statements like `int main(int argc, char *argv[])`
        if Styleanomaly['Command-Line Arguments'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Command-Line Arguments'][3], line):
                if Styleanomaly['Command-Line Arguments'][0] == 0 and Styleanomaly['Command-Line Arguments'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Command-Line Arguments'][1]
                    Styleanomaly['Command-Line Arguments'][4] += 1
                    anamolies_found += 1
                if Styleanomaly['Command-Line Arguments'][0] == 1:
                    anomaly_score += Styleanomaly['Command-Line Arguments'][1]
                    anamolies_found += 1

        # Checks for use of null, i.e. `null`, `nullptr`, or `\0`
        if Styleanomaly['Nulls'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Nulls'][3], line):
                if Styleanomaly['Nulls'][0] == 0 and Styleanomaly['Nulls'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Nulls'][1]
                    Styleanomaly['Nulls'][4] += 1
                    anamolies_found += 1
                if Styleanomaly['Nulls'][0] == 1:
                    anomaly_score += Styleanomaly['Nulls'][1]
                    anamolies_found += 1

        # Checks for use of scope operator, i.e. `x::y`, excluding `string::npos` and not double-counting the Namespace Std check
        if Styleanomaly['Scope Operator'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Scope Operator'][3], line) and not line.__contains__("string::npos") and not line.__contains__("std::"):
                if Styleanomaly['Scope Operator'][0] == 0 and Styleanomaly['Scope Operator'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Scope Operator'][1]
                    Styleanomaly['Scope Operator'][4] += 1
                    anamolies_found += 1
                if Styleanomaly['Scope Operator'][0] == 1:
                    anomaly_score += Styleanomaly['Scope Operator'][1]
                    anamolies_found += 1

        # "Line Spacing" should only check lines inside main()
        if line.__contains__("int main"):
            in_main = True
        elif re.search(r'(^}(\s+)?$)', line): # Closing brace
            in_main = False

        # Checks for non-indented lines inside main(), up to the first non-indented closing brace
        # FIXME: Improve this to include all code within main()
        if Styleanomaly['Line Spacing'][2] != 0 and in_main and not line.__contains__("int main"): #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Line Spacing'][3], line) and not re.search(r'(^{(\s+)?$)', line):    #Don't count single opening brace
                if Styleanomaly['Line Spacing'][0] == 0 and Styleanomaly['Line Spacing'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Line Spacing'][1]
                    Styleanomaly['Line Spacing'][4] += 1
                    anamolies_found += 1
                if Styleanomaly['Line Spacing'][0] == 1:
                    anomaly_score += Styleanomaly['Line Spacing'][1]
                    anamolies_found += 1
            
    # print(submission_code)
    style_anamolies = stylechecker(submission_code)
    return anomaly_score, submission_code, anamolies_found, style_anamolies
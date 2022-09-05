import pandas as pd
import requests 
from zipfile import ZipFile
import re
import os 
from io import BytesIO
from tools.stylechecker import stylechecker

def download_url(url, save_path, chunk_size=128): # Function to down the zip from the url 
    r = requests.get(url, stream=True)
    # with open(save_path, 'wb') as fd:
    #     for chunk in r.iter_content(chunk_size=chunk_size):
    #         fd.write(chunk)
    zipfile = ZipFile(BytesIO(r.content))
    return zipfile.open('main.cpp')

def anomalyScore(zip_location): # Function to calculate the anomaly score
    # Below is the format for the anomaly in question
    # [Count_instances, Points/instance, anomaly on/off, regex, whether its used for once (used for !count instances)]
    # Add to the hashmap Styleanomaly in case you need new anomaly to be detected
    Styleanomaly = {
        'Pointers': {0:1, 1:0.9, 2:1, 3:r'(\(+)?((int)|(char)|(string)|(void)|(bool)|(float)|(double)){1}(\)+)?(\s+)?\*{1,2}(\s+)?[a-zA-Z]+(\s+)?(\=)?.*\;$', 4:0},
        'Infinite_loop': {0:0, 1:0.9, 2:1, 3:r'(?i)(while(\s+)?\((true|1)\))|(for(\s+)?\(;;\))', 4:0},
        'Atypical Includes': {0:1, 1:0.1, 2:1, 3:r'#(\s+)?include(\s+)?<((iomanip)|(algorithm)|(cstdlib)|(utility)|(limits)|(cmath))>', 4:0},
        'Atypical Keywords': {0:1, 1:0.3, 2:1, 3:r'((break(\s+)?;)|(switch(\s+)?\(.*\)(\s+)?{)|(continue(\s+)?;)|(sizeof\(.*\))|(case\s+([a-zA-Z0-9]+(\s+)?:)))', 4:0},
        'Array Accesses': {0:1, 1:0.9, 2:1, 3:r'([a-zA-Z0-9]+\[.*\])', 4:0},
        'Namespace Std': {0:1, 1:0.1, 2:1, 3:r'(std::)', 4:0},
        'Brace Styling': {0:1, 1:0.1, 2:1, 3:r'^((\s+)?{)', 4:0},
        'Escaped Newline': {0:1, 1:0.1, 2:1, 3:r'(\\n)', 4:0},
        'User-Defined Functions': {0:1, 1:0.8, 2:1, 3:r'^(((unsigned|signed|long|short)\s)?\S{3,}\s+\S+\(.*\))'}
    }

    code = download_url(zip_location, 'output/code.zip')
    # print(code.readlines())

    # with ZipFile('output/code.zip', 'r') as zipObj: # Extracts the downloaded zip
    #     zipObj.extractall('output/')
    # os.remove('output/code.zip')    # Removes the downloaded zip
    
    # code = open('output/main.cpp', 'r') # Reads all the lines into code variable
    # os.remove('output/main.cpp')    # Removes the extracted cpp file

    submission_code = ''    # Used to return the user code to roster.py

    anomaly_score = 0   # Initial anomaly Score
    anamolies_found = 0 # Counts the number of anamolies found 

    for line in code.readlines():   # Reading through lines in the code and checking for each anomaly
        line = str(line, 'UTF-8')
        submission_code += line

        # Checks for while(1), while(true), while(True)
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
            if re.search(Styleanomaly['User-Defined Functions'][3], line) and not line.__contains__("main"):
                if Styleanomaly['User-Defined Functions'][0] == 0 and Styleanomaly['User-Defined Functions'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['User-Defined Functions'][1]
                    Styleanomaly['User-Defined Functions'][4] += 1
                    anamolies_found += 1
                if Styleanomaly['User-Defined Functions'][0] == 1:
                    anomaly_score += Styleanomaly['User-Defined Functions'][1]
                    anamolies_found += 1
            
    # print(submission_code)
    style_anamolies = stylechecker(submission_code)
    return anomaly_score, submission_code, anamolies_found, style_anamolies

# def anomalyScore(zip_location):
#     download_url(zip_location, 'output/code.zip')
#     return 0,'hello',0
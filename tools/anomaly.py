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
        'Pointers': [1, 0.9, 1, r'(\(+)?((int)|(char)|(string)|(void)|(bool)|(float)|(double)){1}(\)+)?(\s+)?\*{1,2}(\s+)[a-zA-Z]+(\s+)?(\=)?.*\;$', 0],
        'Infinite_loop': [0, 0.9, 1, r'while(\s+)?\((true|1)\)', 0],
        'Atypical Includes': [0, 0.1, 1, r'while(\s+)?\((true|1)\)', 0]
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
        if Styleanomaly['Infinite_loop'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Infinite_loop'][3], line):
                if Styleanomaly['Infinite_loop'][0] == 1 and Styleanomaly['Infinite_loop'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Infinite_loop'][1]
                    Styleanomaly['Infinite_loop'][4] += 1
                    anamolies_found += 1
                elif Styleanomaly['Infinite_loop'][0] == 0:
                    anomaly_score += Styleanomaly['Infinite_loop'][1]
                    anamolies_found += 1
        if Styleanomaly['Pointers'][2] != 0: #Check if the anomaly is turned on 
            if re.search(Styleanomaly['Pointers'][3], line):
                if Styleanomaly['Pointers'][0] == 1 and Styleanomaly['Pointers'][4] == 0: #Count instances and counted instances
                    anomaly_score += Styleanomaly['Infinite_loop'][1]
                    Styleanomaly['Pointers'][4] += 1
                    anamolies_found += 1
                if Styleanomaly['Pointers'][0] == 0:
                    anomaly_score += Styleanomaly['Pointers'][1]
                    anamolies_found += 1
            
    # print(submission_code)
    style_anamolies = stylechecker(submission_code)
    return anomaly_score, submission_code, anamolies_found, style_anamolies

# def anomalyScore(zip_location):
#     download_url(zip_location, 'output/code.zip')
#     return 0,'hello',0


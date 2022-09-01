This code is written by Abhinav Reddy Palle

If you have any questions please do not hesistate to contact me: 
Email: apall009@ucr.edu

Requirements: 
1. Python v3
2. Pandas (pip3 install pandas)
3. datetime (pip3 install datetime)
4. requests (pip3 install requests)
5. cpplint (pip3 install cpplint)

Instructions to run: 
1. Download all the files quickanalysis.py, roster.py and anomaly.py into the same directory
2. Run quickanalysis.py using the command (python3 quickanalysis.py) to get a quick overview into the zybooklog 
3. You should see a new folder output created and quickanalysis.csv saved
4. Run roster.py using the command (python3 roster.py) and then enter the path to the zybook log file
5. You should see a new file roster.csv created in the output folder 


Things to note: 

Running the file roster.py is slow because we are downloading the zipped file into the secondary memory in
anomaly detection and then reading each line individually and then comparing with a regex. 
I will try to make it faster in the future by letting the file read directly into the main memory

If you do not want this anomaly detection functionality, Please delete the entries 
'# of Anamolies','anomaly Score', 'User Code' in line 81 
Comment out lines 120, 151, 152 and 153 


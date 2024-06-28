#!/usr/bin/env python3
import sys
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
import json
import joblib
from datetime import datetime




def extract_values(log_line):
    """
    Extracts the values of the line
    [tx_mean] [rx_mean] [tx_var] [rx_var] [ms_mean] [ms_var] [open_connections] [closed_connections] [mean_time] [variance_time]
    """
    # Split the log line by tabs
    parts = log_line.split('\t')
    
    # Extract the JSON part of the log line
    json_str = parts[-1].strip()
    
    # Load the JSON object
    data = json.loads(json_str)
    
    # Extract values from the dictionary
    values = list(data.values())
    
    # Exclude the first two value
    values_except_first = values[2:]
    
    # Convert values to NumPy array and reshape it to (1, 10). This shape is needed for the model
    values_array = np.array(values_except_first).reshape(1, -1)
    
    return values_array

def process_log_line(log_line):
    """
    Classifies the probability of the entry of beeing not-malicious or malicious
    """
    
    # Extract values from the log line
    values = extract_values(log_line)
    
    # Scale the data with the same scaler of the training set
    fields_scaled = scaler.transform(values)
    
    # Predict using the classifier
    y = classifierLoad.predict(fields_scaled)
    
    return y

# Load the model
classifierLoad = tf.keras.models.load_model('/shared-volume/prediction/MLP_11agosto.keras', compile=False)

# Load the StandardScaler
scaler = joblib.load('/shared-volume/prediction/std_scaler.bin')


if len(sys.argv) > 1:
    # The result is appended in a file 
    pathfile = "/shared-volume/prediction/livePrediction/" + datetime.now().strftime('%Y-%m-%d')
    output = open(pathfile, "a")
    try:
        # In input receives the buffer defined in the fluent.conf file
        # The buffer contains the entries and is read as a file
        input = open(sys.argv[-1],'r')
        # Process each command-line argument (each log line)
    except IOError as e:
        output.write(str(e))

    lines = input.readlines()

    for line in lines:
        # The line is processed here
        res = 0
        res = process_log_line(line)
        
        if res < 0.2:
            res_str = 'NO'
        elif res > 0.8:
            res_str = 'YES'
        else:
            res_str = 'MAYBE'

        output.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\t' + line.strip() + '\n' + 'result: ' + str(res) + res_str + '\n')

    output.close()
    input.close()
else:
    output = open("/shared-volume/prediction/temp.txt", "a")
    print("No log data received.")
    output.write("No log data received \n")


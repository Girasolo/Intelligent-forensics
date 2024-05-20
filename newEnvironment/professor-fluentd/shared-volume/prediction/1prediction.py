#!/usr/bin/env python3
import sys
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
import json
import joblib




def extract_values(log_line):
    # Split the log line by tabs
    parts = log_line.split('\t')
    
    # Extract the JSON part of the log line
    json_str = parts[-1].strip()
    
    # Load the JSON object
    data = json.loads(json_str)
    
    # Extract values from the dictionary
    values = list(data.values())
    
    # Exclude the first value
    values_except_first = values[1:]
    
    # Convert values to NumPy array and reshape it to (1, 10)
    values_array = np.array(values_except_first).reshape(1, -1)
    
    return values_array

def process_log_line(log_line):

    
    # Extract values from the log line
    values = extract_values(log_line)
    
    # Scale the data
    fields_scaled = scaler.transform(values)
    
    # Predict using the classifier
    y = classifierLoad.predict(fields_scaled)
    
    return y

# Check if there are command-line arguments
classifierLoad = tf.keras.models.load_model('/shared-volume/prediction/MLP_11agosto.keras', compile=False)

# Load the StandardScaler
scaler = joblib.load('/shared-volume/prediction/std_scaler.bin')


if len(sys.argv) > 1:
    
    output = open("/shared-volume/prediction/temp.txt", "a")
    try:
        input = open(sys.argv[-1],'r')
        # Process each command-line argument (each log line)
    except IOError as e:
        output.write(str(e))

    lines = input.readlines()

    for line in lines:
        # Process the line here
        res = 0
        res = process_log_line(line)

        output.write("Received line: " + line.strip() + '\n' + 'result: ' + str(res) + '\n')

    output.close()
    input.close()
else:
    output = open("/shared-volume/prediction/temp.txt", "a")
    print("No log data received.")
    output.write("No log data received \n")


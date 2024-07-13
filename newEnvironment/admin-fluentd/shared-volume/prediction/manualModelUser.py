import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
import json
import joblib

# Load the trained model
classifierLoad = tf.keras.models.load_model('/shared-volume/prediction/MLP_11agosto.keras', compile=False)

# Load the StandardScaler
scaler = joblib.load('/shared-volume/prediction/std_scaler.bin')

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
    
    # Exclude the first value
    values_except_first = values[2:]
    
    # Convert values to NumPy array and reshape it to (1, 10)
    values_array = np.array(values_except_first).reshape(1, -1)
    
    return values_array

def process_log_lines():
    """
    Classifies the probability of the entry of being not-malicious or malicious.
    Processes log lines until 'exit' is entered.
    """
    while True:
        log_line = input("Enter log line (or 'exit' to quit): ")
        if log_line == 'exit':
            break
        
        # Extract values from the log line
        values = extract_values(log_line)
        
        # Scale the data
        fields_scaled = scaler.transform(values)
        
        # Predict using the classifier
        y = classifierLoad.predict(fields_scaled)
        
        if y < 0.2:
            res_str = 'NO'
        elif y > 0.8:
            res_str = 'YES'
        else:
            res_str = 'MAYBE'
        
        print("Prediction:", y, " ", res_str)

# Call the function to process log lines
process_log_lines()

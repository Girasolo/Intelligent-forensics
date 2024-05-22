import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
import json
import joblib


def select_lines_by_time(lines, time_range):
    '''
    Selects the lines with a specific time range.
    '''
    selected_lines = []
    
    for line in lines:
        # Extract timestamp from the line
        timestamp = line.split('\t')[0]
        
        # Extract hour and minute from the timestamp
        hour_minute = timestamp.split('T')[1][:5]
        
        # Check if the timestamp falls within the specified time range
        if time_range[0] <= hour_minute <= time_range[1]:
            selected_lines.append(line)
        elif hour_minute > time_range[1]:
            # If the timestamp is beyond the end of the time range, stop processing
            break
    
    return selected_lines

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
    values_except_first = values[1:]
    
    # Convert values to NumPy array and reshape it to (1, 10)
    values_array = np.array(values_except_first).reshape(1, -1)
    
    return values_array

def process_log_line(log_line):
    """
    Classifies the probability of the entry of beeing not-malicious or malicious
    """
    
    # Extract values from the log line
    values = extract_values(log_line)
    
    # Scale the data
    fields_scaled = scaler.transform(values)
    
    # Predict using the classifier
    y = classifierLoad.predict(fields_scaled)
    
    print("Prediction:", y)

def main(log_file):
    '''
    Main function:
    * open the file
    * select the interested lines
    * process the entries
    * print the result for each line
    '''
    # Open the log file
    with open(log_file, 'r') as file:
        # Read lines until the first line that falls outside the time interval
        # for line in file:
        #     timestamp = line.split('\t')[0]
        #     hour_minute = timestamp.split('T')[1][:5]
        #     if hour_minute > end_time:
        #         break
        #     else:
        #     # If the loop completes without breaking, rewind the file pointer
        #     file.seek(0)
        
        # Read the remaining lines and select those within the time interval
        selected_lines = select_lines_by_time(file, (start_time, end_time))
        
        # Print selected lines and the prediction
        if selected_lines:
            for line in selected_lines:
                process_log_line(line)
                print(line.strip())
        else:
            print("No log lines found for the specified time or time interval.")

if __name__ == "__main__":
    import argparse
    
    # Create argument parser
    parser = argparse.ArgumentParser(description="Select log lines based on time.")
    
    # Add arguments : the name of the logfile
    parser.add_argument("log_file", type=str, help="Path to the log file")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Prompt the user to enter the time or time interval
    start_time, end_time = None, None

    # Load the model
    classifierLoad = tf.keras.models.load_model('MLP_11agosto.keras', compile=False)

    # Load the StandardScaler
    scaler = joblib.load('std_scaler.bin')

    while True:
        time_input = input("Enter time or time interval (HH:MM or HH:MM - HH:MM), or 'exit'/'quit' to quit: ")
        
        if time_input == 'exit' or time_input == 'quit':
            break
        
        # Extract time range
        # If only one time is given it will be considered as start and end time
        if len(time_input.split()) == 1:
            start_time = time_input
            end_time = time_input
        elif len(time_input.split()) == 3 and time_input.split()[1] == '-':
            start_time = time_input.split()[0]
            end_time = time_input.split()[2]
        else:
            print("Invalid time range format. Please use either 'HH:MM' or 'HH:MM - HH:MM'")
            continue
        
        # Run the main function
        main(args.log_file)


import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler

# Load the trained model
classifierLoad = tf.keras.models.load_model('MLP_11agosto.keras', compile=False)


import json
import joblib
def extract_values(log_line):
    # Split the log line by tabs
    parts = log_line.split('\t')

    print(parts)
    
    # Extract the JSON part of the log line
    json_str = parts[-1].strip()
    print(json_str)
    
    # Load the JSON object
    data = json.loads(json_str)
    print(data)
    values= list(data.values())
    # Extract values from tx_mean to the end
    values = np.array(values[1:]).reshape(1,-1)
    
    return values

# Example log line
log_line = '2024-05-14T15:53:39+00:00\tdos.tracer.logs\t{"final result":"10.100.0.2","tx_mean":0.0,"rx_mean":3.0,"tx_var":0.0,"rx_var":0.0,"ms_mean":60778.02,"ms_var":0.0,"open_connections":0,"closed_connections":3,"mean_time":1.6346666666666667,"variance_time":2.739668222222223}'
log_line2 ='2024-05-14T15:53:14+00:00\tdos.tracer.logs\t{"final result":"10.100.0.2","tx_mean":0,"rx_mean":0,"tx_var":0,"rx_var":0,"ms_mean":0,"ms_var":0,"open_connections":1,"closed_connections":0,"mean_time":0.0,"variance_time":0.0}'
#log_line = '2024-05-14T15:53:39+00:00 dos.tracer.logs {"final result":"10.100.0.2","tx_mean":0.0,"rx_mean":3.0,"tx_var":0.0,"rx_var":0.0,"ms_mean":60778.02,"ms_var":0.0,"open_connections":0,"closed_connections":3,"mean_time":1.6346666666666667,"variance_time":2.739668222222223}'

# Extract values
values = extract_values(log_line2)

print(values)

example2 = np.array(['0.0', '0.0', '0.0', '0.0', '0.023', '0.00012100000000000003', '0', '2', '3.675669603999956', '13.50954112864207'])

# Scale the data if needed
scaler = joblib.load('std_scaler.bin')
fields_scaled = scaler.transform(values)

# Predict using the classifier
y = classifierLoad.predict(fields_scaled)
temp = classifierLoad.predict(scaler.transform(example2.reshape(1,-1)))
print(y)
print(temp)

import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler

# Load the trained model
classifierLoad = tf.keras.models.load_model('MLP_11agosto.h5', compile=False)

# Function to parse resultLife file
def parse_result_life(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        metrics = {}
        for line in lines[1:]:
            parts = line.strip().split('\t')
            metric = parts[0]
            mean = float(parts[1])
            variance = float(parts[2])
            metrics[metric] = (mean, variance)
        return metrics

# Function to parse resultTrace file
def parse_result_trace(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        open_connections = int(lines[0].split(':')[1].strip())
        closed_connections = int(lines[1].split(':')[1].strip())
        mean_time = float(lines[2].split(':')[1].strip())
        variance_time = float(lines[3].split(':')[1].strip())
        return open_connections, closed_connections, mean_time, variance_time

# Paths to result files
resultLife_path = 'resultLife.txt'
resultTrace_path = 'resultTrace.txt'

# Parse resultLife and resultTrace files
resultLife_data = parse_result_life(resultLife_path)
resultTrace_data = parse_result_trace(resultTrace_path)

# Extract required values
mediabtx, varbtx = resultLife_data.get('TX', (0.0, 0.0))
mediabrx, varbrx = resultLife_data.get('RX', (0.0, 0.0))
medialat, varlat = resultLife_data.get('MS', (0.0, 0.0))
openC, closedC, mean_time, variance_time = resultTrace_data

# Define fields list
fields = [float(mediabtx), float(mediabrx), float(varbtx), float(varbrx), float(medialat),
          float(varlat), float(openC), float(closedC), float(mean_time, float(variance_time))]

# Scale the data if needed
scaler = StandardScaler()
fields_scaled = scaler.fit_transform(np.array(fields).reshape(1, -1))

# Predict using the classifier
y = classifierLoad.predict(fields_scaled)
print(y)
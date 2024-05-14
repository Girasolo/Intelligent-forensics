import os
import time

fifo_path = '/fluentd/output/DoS/dospredictorPIPE'

# Open the named pipe file for reading
with open(fifo_path, 'r') as fifo:
    # Loop indefinitely to continuously read log lines from the named pipe
    with open('temp.txt','a') as file:
        while True:
            # Read a line from the named pipe
            line = fifo.readline()
            
            # Check if the line is not empty
            if line:
                # Process the log line here
                # For demonstration purposes, let's just print the log line
                print("kjadfj")
                file.write("Received log line:", line.strip())
                # Perform your custom processing on the log line
                # Replace this with your actual processing logic
            else:
                # If the line is empty, it means there's no more data in the pipe
                # Wait for a short duration before checking again
                time.sleep(0.1)  # Adjust the sleep duration as needed

#!/usr/bin/env python3
import sys

# Check if there are command-line arguments
if len(sys.argv) > 1:
    input = open(sys.argv[-1],'r')
    output = open("/shared-volume/prediction/temp.txt", "a")
        # Process each command-line argument (each log line)
    lines = input.readlines()

    for line in lines:
        # Process the line here
        print("Received line:", line.strip())  # Example processing, printing the line
        # You can replace the print statement with your actual processing logic
        output.write("Received line: " + line.strip() + '\n')
else:
    output = open("/shared-volume/prediction/temp.txt", "a")
    print("No log data received.")
    output.write("No log data received \n")


#!/bin/bash

# Get the current date
current_date=$(date +%Y-%m-%d)

# Define the file path with the current date as the file name
file_path="/shared-volume/prediction/livePrediction/${current_date}.txt"

# Create the file
touch "$file_path"



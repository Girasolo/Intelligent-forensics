import subprocess
import time
import os
import fcntl

# Define the path to the folder containing the program or command
folder_path = "/sbin"

# Define the command or program to run
command = ["tcplife-bpfcc", "-T"]  # Replace with the actual command or program name

# Run the command using subprocess and redirect the output to a pipe
process = subprocess.Popen(command, stdout=subprocess.PIPE, cwd=folder_path)
#fcntl.fcntl(process.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
time.sleep(5)
# Infinite loop to store a file every 5 seconds
while True:
    # Generate a timestamp string
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    print(timestamp)
    # Construct the full path for the output file
    output_filex = f"{timestamp}.txt"

    with open("/servidor/output/DoSdetector" + "/" + output_filex, "w") as output_file:
        try:
            output = process.stdout.readline()
            if output == b'' and process.poll() is not None:
                continue
            if output:
                output_file.write(output.decode("utf-8"))
        except Exception as e:
            print("Error:", e)

    # Wait for 5 seconds before the next execution
    time.sleep(5)


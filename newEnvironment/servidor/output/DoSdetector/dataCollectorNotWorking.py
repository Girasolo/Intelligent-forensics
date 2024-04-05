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
fcntl.fcntl(process.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
# Infinite loop to store a file every 5 seconds
while True:
    # Wait for 5 seconds before the next execution
    time.sleep(5)
    # Generate a timestamp string
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    print(timestamp)
    # Construct the full path for the output file
    output_filex = f"{timestamp}.txt"
     
    output = process.stdout.readline()
    print("oi"+ output.decode("utf-8"))
    if output == b'' and process.poll() is not None:
    	print("primo if")
    	continue
    with open("/servidor/output/DoSdetector" + "/" + output_filex, "w") as output_file:
        try:
            print("try")
            output_file.write(output.decode("utf-8"))
        except Exception as e:
            print("Error:", e)



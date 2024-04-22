import subprocess
import queue
import threading
import time
import os
from datetime import datetime

lock = threading.Lock()
# Define the queue to store output
output_queue = queue.Queue(maxsize=5)  # Lock for synchronizing access to output_queue

def run_tcplife():
    # Run tcplife-bpfcc and store its output in the queue
    process = subprocess.Popen(['/sbin/tcplife-bpfcc'], stdout=subprocess.PIPE, text=True)
    print("before loop")
    while True:
        print("pre-lock-tcplife")
        lock.acquire()
        print("in-lock-savefile")
        line = process.stdout.readline()
        #if True:
        #    for i, line in enumerate(process.stdout.readline, 0):
        #        print(str(i) + " " + line.strip())
        #        output_queue.put(line.strip())
        line = line.strip()
        print(line)
        output_queue.put(line)
        lock.realease()

    process.wait()  # Wait for the process to finish before returning

def save_output_to_file():

    while True:
        time.sleep(5)
        # Create a new file with a timestamp as the name
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'/servidor/output/DoSdetector/{timestamp}.txt'
        print("pre-lock-savefile")
        lock.acquire()
        print("in-lock-savefile")
        # Open the file in write mode and save the content of the queue
        with open(filename, 'a') as f:
            while not output_queue.empty():
                output_line = output_queue.get()
                print(output_line)
                f.write(output_line + '\n')
        # Optional: You can clear the queue after saving its content
        output_queue.queue.clear()
        print("clear queue-savefile")
        lock.realease()
        print("post-lock-savefile")


# Start a thread to continuously run tcplife-bpfcc
tcplife_thread = threading.Thread(target=run_tcplife)
lifesave_thread = threading.Thread(target=save_output_to_file)

lifesave_thread.daemon = True
tcplife_thread.daemon = True

#lifesave_thread.start()
#tcplife_thread.start()

original_cflags = os.environ.get('CFLAGS', '')

try:
    # Set the CFLAGS environment variable
    os.environ['CFLAGS'] = '-Wno-macro-redefined'

    # Execute tcplife-bpfcc
    process = subprocess.Popen(['/sbin/tcplife-bpfcc'])

    # Read the output
    for line in process.stdout:
        print(line.strip())

    # Wait for the process to finish
    process.wait()

finally:
    # Restore the original value of CFLAGS
    os.environ['CFLAGS'] = original_cflags
# Keep running save_output_to_file every 5 seconds
input("Press Enter to exit...")

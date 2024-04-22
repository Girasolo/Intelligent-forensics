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
   
    print("before loop")
    while True:
        print("pre-lock-tcplife")
        lock.acquire()
        proc = subprocess.Popen(['/sbin/tcplife-bpfcc'], bufsize=0, stdout=subprocess.PIPE)
        time.sleep(25)
        for line in iter(proc.stdout.readline, b''):
          print(line)
          output_queue.put(line)
          log.info(line.decode('utf-8')[:-1]) # [:-1] to cut off newline char
        proc.stdout.close()
        proc.terminate()
        lock.release()

        
          
def save_output_to_file():

    while True:
        # Create a new file with a timestamp as the name
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'/servidor/output/DoSdetector/{timestamp}.txt'
        print("savefile-pre-lock")
        lock.acquire()
        print("savefile-in-lock")
        # Open the file in write mode and save the content of the queue
        if not output_queue.empty():
          with open(filename, 'w') as f:
              while not output_queue.empty():
                  output_line = output_queue.get()
                  print(output_line)
                  f.write(output_line + '\n')
          # Optional: You can clear the queue after saving its content
          output_queue.queue.clear()
          print("savefile-clear queue")
        lock.release()
        print("savefile-post-lock")


# Start a thread to continuously run tcplife-bpfcc
tcplife_thread = threading.Thread(target=run_tcplife)
lifesave_thread = threading.Thread(target=save_output_to_file)

lifesave_thread.daemon = True
tcplife_thread.daemon = True

lifesave_thread.start()
tcplife_thread.start()

#original_cflags = os.environ.get('CFLAGS', '')

#try:
    # Set the CFLAGS environment variable
 #   os.environ['CFLAGS'] = '-Wno-macro-redefined'

    # Execute tcplife-bpfcc
  #  process = subprocess.Popen(['/sbin/tcplife-bpfcc'])

    # Read the output
  #  for line in process.stdout:
 #       print(line.strip())

    # Wait for the process to finish
  #  process.wait()

#finally:
    # Restore the original value of CFLAGS
 #   os.environ['CFLAGS'] = original_cflags
# Keep running save_output_to_file every 5 seconds
input("Press Enter to exit...")

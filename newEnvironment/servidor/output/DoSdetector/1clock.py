import signal
import subprocess
import multiprocessing as mp
import time

def send_signal(pids, event):
    while True:
        print("Waiting for signal...")
        event.wait()  # Wait for the event to be set
        for pid in pids:
            print("Sending signal to subprocess", pid)
            subprocess.run(['kill', '-SIGUSR1', str(pid)])
        event.clear()

if __name__ == "__main__":
    try:
        # Start two subprocesses
        subprocesses = []
        
        life = subprocess.Popen(['python3', 'tcplife.py', '-f'])
        subprocesses.append(life)
        trace = subprocess.Popen(['python3', 'tcptracer.py', '-f'])
        subprocesses.append(trace)


        # Create an event
        event = mp.Event()

        # Start the signal sending process
        signal_process = mp.Process(target=send_signal, args=([p.pid for p in subprocesses], event))
        signal_process.start()

        # Start sending signals repeatedly
        time.sleep(25)
        while True:
            event.set()  # Send the signal to both subprocesses simultaneously
            time.sleep(25)  # Delay for 25 seconds before sending the next signal
    except KeyboardInterrupt:
        print("Terminating...")
        # Clean up resources and terminate the program gracefully
    finally:
        # Ensure all subprocesses are terminated
        for process in subprocesses:
            process.terminate()
        if signal_process.is_alive():
            signal_process.terminate()


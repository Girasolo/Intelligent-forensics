import signal
import subprocess
import multiprocessing as mp
import time

def send_signal(pids, event):
    print("Waiting for signal...")
    event.wait()  # Wait for the event to be set
    for pid in pids:
        print("Sending signal to subprocess", pid)
        subprocess.run(['kill', '-SIGUSR1', str(pid)])

if __name__ == "__main__":
    # Start two subprocesses
    subprocesses = []
    for _ in range(2):
        process = subprocess.Popen(['python', 'program2.py'], stdout=subprocess.PIPE)
        subprocesses.append(process)

    # Create an event
    event = mp.Event()

    # Start the signal sending process
    signal_process = mp.Process(target=send_signal, args=([p.pid for p in subprocesses], event))
    signal_process.start()

    # Send the signal to both subprocesses simultaneously
    event.set()

    # Wait for the signal process to finish
    signal_process.join()

    # Wait for the subprocesses to finish
    for process in subprocesses:
        process.wait()


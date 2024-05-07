import signal
import subprocess
import multiprocessing as mp
import time
import numpy as np
import threading

import socket

#added by Girasolo
def send_interrupt(time):
    #open a new file each 25 secs. If the file fails to open continue to write on the previous one
    def handler(signum, frame):
        print("Timeout reached. Sending KeyboardInterrupt.")
        raise KeyboardInterrupt

    # Set up the signal handler for SIGALRM
    signal.signal(signal.SIGALRM, handler)

    # Set the alarm to go off after 25 seconds
    signal.alarm(time)
#

def compute_mean_variance(data):
    tx_kb = [entry[0] for entry in data]
    rx_kb = [entry[1] for entry in data]
    ms = [entry[2] for entry in data]
    
    tx_mean = np.mean(tx_kb)
    rx_mean = np.mean(rx_kb)
    ms_mean = np.mean(ms)
    
    tx_var = np.var(tx_kb)
    rx_var = np.var(rx_kb)
    ms_var = np.var(ms)
    
    return (tx_mean, rx_mean, ms_mean), (tx_var, rx_var, ms_var)

def send_signal(pids, event):
    while True:
        print("Waiting for signal...")
        event.wait()  # Wait for the event to be set
        for pid in pids:
            print("Sending signal to subprocess", pid)
            subprocess.run(['kill', '-SIGUSR1', str(pid)])
        event.clear()

def manageEvent(event):
    while True:
        time.sleep(25)  # Delay for 25 seconds before sending the next signal
        event.set()  # Send the signal to both subprocesses simultaneously
        


def receive_line(sock):
    """
    Receive a single line terminated by a newline character ('\n').
    """
    data = b''
    while True:
        received_byte = sock.recv(1)
        if received_byte == b'\n':
            break
        data += received_byte
    return data
if __name__ == "__main__":
    try:
        # Define host and port
        HOST = '127.0.0.1'
        PORT = 65432
        lifedata = []
        tracerTimes = []
        open_connections = 0
        closed_connections = 0
        # Create a socket object
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        # Bind the socket to the address and port
        server_socket.bind((HOST, PORT))
        # Listen for incoming connections
        server_socket.listen()
        print("Server is listening for incoming connections...")
        # Accept a connection
        # Start two subprocesses
        subprocesses = []
        #TODO: put the socket host and port as arguments
        #life = subprocess.Popen(['python3', 'tcplife.py', '-sc'])
        #subprocesses.append(life)
        tracer = subprocess.Popen(['python3', 'tcptracer.py', '-t' ,'-sc'])
        subprocesses.append(tracer)

        event = mp.Event()
        # Create a new thread for the send_signal function
        signal_thread = threading.Thread(target=manageEvent, args=[event])
        # Set the daemon flag to True so that the thread will exit when the main program exits
        signal_thread.daemon = True
        # Start the thread
        # Create an event

        # Start the signal sending process
        signal_process = mp.Process(target=send_signal, args=([p.pid for p in subprocesses], event))
        signal_process.start()

        client_socket, client_address = server_socket.accept()
        #time.sleep(25)
        signal_thread.start()
        print("Connected by:", client_address)
        """
        while True:
            # Receive data from the client
            data = client_socket.recv(1024)
            data = receive_line(client_socket)
            #print("Received:", data.decode())
            if not data:
                break
            data = data.decode()
            if data == "SIGNAL HERE ---":
                print("25 sec: " ,  lifedata)
                if lifedata != []:
                    mean, variance = compute_mean_variance(lifedata)
                    print("mean: ", mean, "variance", variance)
                lifedata = []
                continue
            data = data.strip().split()
            #print(data)
            tx_kb = float(data[6])
            rx_kb = float(data[7])
            ms = float(data[8])
            lifedata.append((tx_kb, rx_kb, ms))
            # Print the received data
        """
        while True:
            # Receive data from the client
            #data = client_socket.recv(1024)
            data = receive_line(client_socket)
            print("Received:", data.decode())
            if not data:
                break
            data = data.decode()
            if data == "SIGNAL HERE ---":
                print("25 sec: " , open_connections, closed_connections, tracerTimes)
                if tracerTimes != []:
                    mean_time = np.mean(tracerTimes)
                    variance_time = np.var(tracerTimes)
                    print("openC: ", open_connections, "closedC", closed_connections, "mean: ", mean_time, "variance", variance_time)
                tracerTimes = []
                open_connections = 0
                closed_connections = 0
                continue
            data = data.strip().split()
            #print(data)
            if data[1] == 'C':
                open_connections += 1
            elif data[1] == 'X':
                closed_connections += 1
            tracerTimes.append(float(data[0]))
            # Print the received data
            
    except KeyboardInterrupt:
        print("Terminating...")
        # Clean up resources and terminate the program gracefully
    finally:
        client_socket.close()
        server_socket.close()
        # Ensure all subprocesses are terminated
        for process in subprocesses:
            process.terminate()
        if signal_process.is_alive():
            signal_process.terminate()


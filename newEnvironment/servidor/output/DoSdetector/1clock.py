import signal
import subprocess
import multiprocessing as mp
import time
import numpy as np
import threading
import logging
from fluent import sender

import socket


def send_interrupt(time):
    """
    Send an alarm after 25 second. The handler receives the signal and send a keyboard interrupt
    """
    #open a new file each 25 secs. If the file fails to open continue to write on the previous one
    def handler(signum, frame):
        print("Timeout reached. Sending KeyboardInterrupt.")
        raise KeyboardInterrupt

    # Set up the signal handler for SIGALRM
    signal.signal(signal.SIGALRM, handler)

    # Set the alarm to go off after 25 seconds
    signal.alarm(time)


def compute_mean_variance(data):
    """
    Computes mean and variance for tcplife data packet:
    Bytes transmitted, bytes received, duration of connection
    """
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
    """
    Send simultaneous signal to a list of pid. Works by means of an event set every 25 secs. The event gets unset when the signals are sent
    """
    while True:
        #print("Waiting for signal...")
        event.wait()                                            #Wait for the event to be set. Once set it preceed with the function
        for pid in pids:
            print("Sending signal to subprocess", pid)
            subprocess.run(['kill', '-SIGUSR1', str(pid)])      #Send sigusr1 to all the listed pid
        event.clear()                                           #Unset the event

def manageEvent(event):
    """
    Set the event for sending SIGUSR1 every 25 secs
    """
    while True:
        time.sleep(25)      # Delay for 25 seconds before sending the next signal
        event.set()         # Send the signal to both subprocesses simultaneously
        
def sendResult():
    """
    Send the dos.log entry to fluentd
    """
    global mean, variance, open_connections, closed_connections, mean_time, variance_time, logger           # Global variable, so that they get modified by other thread and sent here to fluentd 
    while True:
        barrier_result.wait()                                                                               # Barrier1: waits for tcplife and tcptrace to send their data
        #mediaBT	mediaRX	varBT	varRX	medialat	varlat	Open	Close	mediadift	varDifT	Attack
        dataToSend = {
                'final result' : socket.gethostbyname(socket.gethostname()),
                'tx_mean' : mean[0],
                'rx_mean' : mean[1],
                "tx_var" : variance[0],
                "rx_var" : variance[1],
                "ms_mean" : mean[2],
                "ms_var" : variance[2],
                'open_connections' : open_connections,
                'closed_connections' : closed_connections,
                "mean_time" : mean_time,
                "variance_time" : variance_time
                }                                                                                           # Collect data in a library
                # Send data to Fluentd
        print(dataToSend)
        logger.emit('tracer.logs', dataToSend)                                                              # Send it with the right tag
        barrier_result.wait()                                                                               # Barrier2: Tell tcplife and tcptrace that can go to the next set of data


def receive_line(sock):
    """
    Receive a single line terminated by a newline character ('\n').
    """
    data = b''
    while True:
        received_byte = sock.recv(1)                                                # Receive char by char 
        if received_byte == b'\n':
            break
        data += received_byte
    return data


def tcplife_receiver(client_socket):
    """
    Set the tuples mean and variance receiving data from tcplife (transmitted bytes, received bytes and duration of connection).
    """
    global mean, variance                                                       # Global so that they can comunicate the result to the thread resposible of the sending
    lifedata = []                                                               # List of tuple (tx_kb, rx_kb, ms)
    print("life thread works")
    try:
        while True:
                # Receive data from the client
                data = receive_line(client_socket)                              # Receive a line from the tcplife socket
                #print("LIFE\tReceived:", data.decode())
                if not data:
                    break
                data = data.decode()
                if data == "SIGNAL HERE ---":                                   # If this string is received it means that tcplife received the sigusr1 after the 25 secs
                    #print("LIFE\t25 sec: " ,  lifedata)
                    if lifedata != []:
                        mean, variance = compute_mean_variance(lifedata)        # Compute mean and variance of (tx_kb, rx_kb, ms)
                        '''
                        data = {
                        'life' : socket.gethostbyname(socket.gethostname()),
                        'tx_mean' : mean[0],
                        'rx_mean' : mean[1],
                        "ms_mean" : mean[2],
                        "tx_var" : variance[0],
                        "rx_var" : variance[1],
                        "ms_var" : variance[2]
                        }
                        # Send data to Fluentd
                        logger.emit('tracer.logs', data)
                        '''
                        #print("LIFE\tmean: ", mean, "variance", variance)
                    barrier_result.wait()                                       # Barrier1: communicate that the job is done
                    barrier_result.wait()                                       # Barrier2: wait for the data to be sent to fluentd
                    lifedata = []                                               # Get ready for the next interval
                    mean, variance = [(0,0,0),(0,0,0)]
                else:
                    data = data.strip().split()                                 # Collect data from tcplife
                    #print(data)
                    tx_kb = float(data[6])
                    rx_kb = float(data[7])
                    ms = float(data[8])
                    lifedata.append((tx_kb, rx_kb, ms))
                # Print the received data
    finally:
        client_socket.close()                                                   # If something goes wrong or the thread is closed, close the socket



def tcptracer_receiver(client_socket):
    """
    Set the mean and variance of difference of time between open/accept/close connection event, 
    the number open connection and the number of closed connection, receiving data from tcptracer.
    """
    global mean_time, variance_time, open_connections, closed_connections       # Global so that they can comunicate the result to the thread resposible of the sending
    tracerTimes = []                                                            # List of difference of time
    print("tracer thread works")
    try:
        while True:
            
            data = receive_line(client_socket)                                  # Receive data from the tcptracer socket
            #print("TRACER\tReceived:", data.decode())
            if not data:
                break
            data = data.decode()
            if data == "SIGNAL HERE ---":                                       # If this string is received it means that tcptracer received the sigusr1 after the 25 secs
                #print("TRACER\t25 sec: " , open_connections, closed_connections, tracerTimes)
                if tracerTimes != []:
                    mean_time = np.mean(tracerTimes)                            # Compute mean and variance of difference of time
                    variance_time = np.var(tracerTimes)
                    '''
                    data = {
                        'tracer' : socket.gethostbyname(socket.gethostname()),
                        'open_connections' : open_connections,
                        'closed_connections' : closed_connections,
                        "mean_time" : mean_time,
                        "variance_time" : variance_time
                        }
                    # Send data to Fluentd
                    logger.emit('tracer.logs', data)
                    '''
                    #print("TRACER\topenC: ", open_connections, "closedC", closed_connections, "mean: ", mean_time, "variance", variance_time)
                barrier_result.wait()                                           # Barrier1: communicate that the job is done
                barrier_result.wait()                                           # Barrier2: wait for the data to be sent to fluentd
                tracerTimes = []
                open_connections = 0
                closed_connections = 0
                mean_time ,variance_time = 0,0
            else:
                data = data.strip().split()                                     # Collect data
                #print(data)
                if data[1] == 'C':
                    open_connections += 1
                elif data[1] == 'X':
                    closed_connections += 1
                tracerTimes.append(float(data[0]))
            # Print the received data
    finally:
        client_socket.close()                                                   # If something goes wrong or the thread is closed, close the socket

if __name__ == "__main__":
    try:
        # Define host and port
        HOST = '127.0.0.1'                                                      # The connection happens on the localhost
        PORTLIFE = 65432                                                        # On these ports
        PORTTRACER = 65433 

        mean , variance = (0,0,0),(0,0,0)                                       # Mean and variance of (tx_kb, rx_kb, ms) - used for tcplife
        open_connections, closed_connections, mean_time , variance_time = 0,0,0,0 #Used for tcptracer
        
        barrier_result = threading.Barrier(3)                                   # Barrier used as barrier1 and barrier2 by tcplife, tcptracer and sendresult 
        
        server_socketLife = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Create a socket object        
        server_socketLife.bind((HOST, PORTLIFE))                                # Bind the socket to the address and port        
        server_socketLife.listen()                                              # Listen for incoming connections

        server_socketTracer = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # The same for tcptracer        
        server_socketTracer.bind((HOST, PORTTRACER))       
        server_socketTracer.listen()


        print("Servers are listening for incoming connections...")
        
        subprocesses = []                                                       # List of subprocesses (tcplife and tcptracer)
        
        #TODO: put the socket host and port as arguments
        life = subprocess.Popen(['python3', 'tcplife.py', '-sc'])               # Start two subprocesses
        #life = subprocess.Popen(['python3', 'tcplife.py'])
        subprocesses.append(life)
        tracer = subprocess.Popen(['python3', 'tcptracer.py', '-t' ,'-sc'])
        #tracer = subprocess.Popen(['python3', 'tcptracer.py', '-t'])
        subprocesses.append(tracer)

        print("PID: ", [p.pid for p in subprocesses])

        event = mp.Event()                                                      # Create an event used to synchronize the sending of SIGUSR1       
        signal_thread = threading.Thread(target=manageEvent, args=[event])      # Create the thread that manage the event (sets the event as true and waits for 25 sec)
        signal_thread.daemon = True                                             # Set the daemon flag to True so that the thread will exit when the main program exits
        # Create an event

        # Start the signal synchronization process
        signal_process = mp.Process(target=send_signal, args=([p.pid for p in subprocesses], event)) #Create a new thread for the send_signal function (send SIGUSR1 for the listed PID)
        signal_process.start()                                                  # Start the process

        
        client_socketLife, client_addressLife = server_socketLife.accept()      # Accept a connection for tcplfe and tcptracer
        client_socketTracer, client_addressTracer = server_socketTracer.accept()

        print("Connected by:", client_addressLife)
        print("Connected by:", client_addressTracer)


        lifereceiver_thread = threading.Thread(target=tcplife_receiver, args=[client_socketLife]) #Creat a thread that receive the entries by tcplife        
        lifereceiver_thread.daemon = True                                       # Set the daemon flag to True so that the thread will exit when the main program exits
        tracerreceiver_thread = threading.Thread(target=tcptracer_receiver, args=[client_socketTracer]) #Create a thread that receive the entries by tcptracer        
        tracerreceiver_thread.daemon = True                                     # Set the daemon flag to True so that the thread will exit when the main program exits


        sendResult_thread = threading.Thread(target=sendResult)                 # Create the thread that send the result
        sendResult_thread.daemon = True                                         # Set the daemon flag to True so that the thread will exit when the main program exits
        logger = sender.FluentSender('dos', host='10.200.0.2', port=24224)      # Create the logger to send data to fluentd
        
        
        signal_thread.start()                                                   # Start the signaling


        lifereceiver_thread.start()                                             # Start the thread to receive from tcplife
        tracerreceiver_thread.start()                                           # Start the thread to receive from tcptracer
        sendResult_thread.start()                                               # Start the thread that send the result to fluentd

        lifereceiver_thread.join()                                              # Join operations
        tracerreceiver_thread.join()
        sendResult_thread.join()
            
    except KeyboardInterrupt:                                                   
        print("Terminating...")
    finally:
        server_socketLife.close()                                               # Close everything
        server_socketTracer.close()
        for process in subprocesses:
            process.terminate()
        if signal_process.is_alive():
            signal_process.terminate()


import signal
import subprocess
import multiprocessing as mp
import time
import numpy as np
import threading
import logging
from fluent import sender

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
        #print("Waiting for signal...")
        event.wait()  # Wait for the event to be set
        for pid in pids:
            print("Sending signal to subprocess", pid)
            subprocess.run(['kill', '-SIGUSR1', str(pid)])
        event.clear()

def manageEvent(event):
    while True:
        time.sleep(25)  # Delay for 25 seconds before sending the next signal
        event.set()  # Send the signal to both subprocesses simultaneously
        
def sendResult():
    global mean, variance, open_connections, closed_connections, mean_time, variance_time, logger
    while True:
        barrier_result.wait()
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
                }
                # Send data to Fluentd
        logger.emit('tracer.logs', dataToSend)
        barrier_result.wait()


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


def tcplife_receiver(client_socket):
    global mean, variance
    lifedata = []
    print("life thread works")
    try:
        while True:
                # Receive data from the client
                #data = client_socket.recv(1024)
                data = receive_line(client_socket)
                #print("LIFE\tReceived:", data.decode())
                if not data:
                    break
                data = data.decode()
                if data == "SIGNAL HERE ---":
                    #print("LIFE\t25 sec: " ,  lifedata)
                    if lifedata != []:
                        mean, variance = compute_mean_variance(lifedata)
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
                        print("LIFE\tmean: ", mean, "variance", variance)
                    else:
                        #mean, variance = [(0,0,0),(0,0,0)]
                        
                        print("LIFE\tmean: ", mean, "variance", variance)
                    barrier_result.wait()
                    barrier_result.wait()
                    lifedata = []
                    mean, variance = [(0,0,0),(0,0,0)]

#                    printBarrirer.wait()
                    continue
                data = data.strip().split()
                #print(data)
                tx_kb = float(data[6])
                rx_kb = float(data[7])
                ms = float(data[8])
                lifedata.append((tx_kb, rx_kb, ms))
                # Print the received data
    finally:
        client_socket.close()



def tcptracer_receiver(client_socket):
    global mean_time, variance_time, open_connections, closed_connections
    tracerTimes = []
    print("tracer thread works")
    try:
        while True:
            # Receive data from the client
            #data = client_socket.recv(1024)
            data = receive_line(client_socket)
            #print("TRACER\tReceived:", data.decode())
            if not data:
                break
            data = data.decode()
            #provare a cambiare come vengono inviati i dati e usare variabili invece che stringhe come variabli
            #oppure riempire le stringhe inviate in modo tale da leggere sempre la
            if data == "SIGNAL HERE ---":
                #print("TRACER\t25 sec: " , open_connections, closed_connections, tracerTimes)
                if tracerTimes != []:
                    mean_time = np.mean(tracerTimes)
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
                    print("TRACER\topenC: ", open_connections, "closedC", closed_connections, "mean: ", mean_time, "variance", variance_time)
                else:
                    #mean_time ,variance_time = 0,0
                    # Send data to Fluentd
                    logger.emit('tracer.logs', data)
                    print("TRACER\topenC: ", open_connections, "closedC", closed_connections, "mean: ", mean_time, "variance", variance_time)
                barrier_result.wait()
                barrier_result.wait()
                tracerTimes = []
                open_connections = 0
                closed_connections = 0
                mean_time ,variance_time = 0,0

#                printBarrirer.wait()
                continue
            data = data.strip().split()
            #print(data)
            if data[1] == 'C':
                open_connections += 1
            elif data[1] == 'X':
                closed_connections += 1
            tracerTimes.append(float(data[0]))
            # Print the received data
    finally:
        client_socket.close()

if __name__ == "__main__":
    try:
        # Define host and port
        HOST = '127.0.0.1'
        PORTLIFE = 65432
        PORTTRACER = 65433

        mean , variance = (0,0,0),(0,0,0)
        open_connections, closed_connections, mean_time , variance_time = 0,0,0,0
        
        barrier_result = threading.Barrier(3)
        # Create a socket object
        server_socketLife = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        # Bind the socket to the address and port
        server_socketLife.bind((HOST, PORTLIFE))
        # Listen for incoming connections
        server_socketLife.listen()

        server_socketTracer = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        # Bind the socket to the address and port
        server_socketTracer.bind((HOST, PORTTRACER))
        # Listen for incoming connections
        server_socketTracer.listen()


        print("Servers are listening for incoming connections...")
        # Start two subprocesses
        subprocesses = []
        #TODO: put the socket host and port as arguments
        life = subprocess.Popen(['python3', 'tcplife.py', '-sc'])
        #life = subprocess.Popen(['python3', 'tcplife.py'])
        subprocesses.append(life)
        tracer = subprocess.Popen(['python3', 'tcptracer.py', '-t' ,'-sc'])
        #tracer = subprocess.Popen(['python3', 'tcptracer.py', '-t'])
        subprocesses.append(tracer)

        print("PID: ", [p.pid for p in subprocesses])

        event = mp.Event()
        printBarrirer = threading.Barrier(2)
        # Create a new thread for the send_signal function
        signal_thread = threading.Thread(target=manageEvent, args=[event])
        # Set the daemon flag to True so that the thread will exit when the main program exits
        signal_thread.daemon = True
        # Create an event

        # Start the signal synchronization process
        signal_process = mp.Process(target=send_signal, args=([p.pid for p in subprocesses], event))
        signal_process.start()

        # Accept a connection
        client_socketLife, client_addressLife = server_socketLife.accept()
        client_socketTracer, client_addressTracer = server_socketTracer.accept()

        print("Connected by:", client_addressLife)
        print("Connected by:", client_addressTracer)


        lifereceiver_thread = threading.Thread(target=tcplife_receiver, args=[client_socketLife])
        # Set the daemon flag to True so that the thread will exit when the main program exits
        lifereceiver_thread.daemon = True

        tracerreceiver_thread = threading.Thread(target=tcptracer_receiver, args=[client_socketTracer])
        # Set the daemon flag to True so that the thread will exit when the main program exits
        tracerreceiver_thread.daemon = True


        sendResult_thread = threading.Thread(target=sendResult)
        # Set the daemon flag to True so that the thread will exit when the main program exits
        sendResult_thread.daemon = True
        #time.sleep(25)
        # Start the signaling
        signal_thread.start()

        logger = sender.FluentSender('dos', host='10.200.0.2', port=24224)

        lifereceiver_thread.start()
        tracerreceiver_thread.start()
        sendResult_thread.start()

        lifereceiver_thread.join()
        tracerreceiver_thread.join()
        sendResult_thread.join()
            
    except KeyboardInterrupt:
        print("Terminating...")
        # Clean up resources and terminate the program gracefully
    finally:
        server_socketLife.close()
        server_socketTracer.close()
        # Ensure all subprocesses are terminated
        for process in subprocesses:
            process.terminate()
        if signal_process.is_alive():
            signal_process.terminate()


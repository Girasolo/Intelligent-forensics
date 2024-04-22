import sys
import numpy as np

def read_network_file(filename):
    data = []
    with open(filename, 'r') as file:
        headers = file.readline().strip().split()  # Extract headers
        for line in file:
            line_data = line.strip().split()
            tx_kb = float(line_data[-3])
            rx_kb = float(line_data[-2])
            ms = float(line_data[-1])
            data.append((tx_kb, rx_kb, ms))
    return data

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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <filename>")
        sys.exit(1)
    
    filename = sys.argv[1]
    network_data = read_network_file(filename)
    mean, variance = compute_mean_variance(network_data)
    
    with open("resultLife.txt", "w") as result_file:
        result_file.write("Metric\tMean\tVariance\n")
        result_file.write("TX\t{:.2f}\t{:.2f}\n".format(mean[0], variance[0]))
        result_file.write("RX\t{:.2f}\t{:.2f}\n".format(mean[1], variance[1]))
        result_file.write("MS\t{:.2f}\t{:.2f}\n".format(mean[2], variance[2]))
    
    print("Results written to result.txt")

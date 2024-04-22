import sys
import csv
import numpy as np

def calculate_statistics(source_file):
    open_connections = 0
    closed_connections = 0
    times = []

    with open(source_file, 'r') as file:
        # Extract headers
        headers = file.readline().strip().split()
        headers = file.readline().strip().split()
        for line in file:
            line_data = line.strip().split()
            if line_data[1] == 'C':
                open_connections += 1
            elif line_data[1] == 'X':
                closed_connections += 1
            times.append(float(line_data[0]))

    mean_time = np.mean(times)
    variance_time = np.var(times)

    return open_connections, closed_connections, mean_time, variance_time

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <source_file>")
        return

    source_file = sys.argv[1]
    open_connections, closed_connections, mean_time, variance_time = calculate_statistics(source_file)

    with open("resultTrace.txt", 'w') as result_file:
        result_file.write("Open Connections: {}\n".format(open_connections))
        result_file.write("Closed Connections: {}\n".format(closed_connections))
        result_file.write("Mean Time: {:.3f}\n".format(mean_time))
        result_file.write("Variance Time: {:.3f}\n".format(variance_time))

if __name__ == "__main__":
    main()

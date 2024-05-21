# 1clock.py
It's the manager script.
It launches the script tcplife.py and tcptracer.py and periodically send them a SIGUSR1. It communicates with them by means of socket connections.
It is also run a send_result thread in order to send the result entry to the fluentd node.

# tcplife.py
Script in charge of sending the transmitted bytes, received bytes and duration of each tcp connection. With the argument -sc it connects to the server 1clock.py and communicate the result. Periodically it receive a SIGUSR1 in response to which sends a SIGNAL HERE message. It get recognised by the 1clock.py script which save the result and send them to the fluentd node

# tcptracer.py
Script in charge of sending the number of open connection, the number of closed connection and time interval between an open/accept/close event and the next. With the argument -sc it connects to the server 1clock.py and communicate the result. Periodically it receive a SIGUSR1 in response to which sends a SIGNAL HERE message. It get recognised by the 1clock.py script which save the result and send them to the fluentd node
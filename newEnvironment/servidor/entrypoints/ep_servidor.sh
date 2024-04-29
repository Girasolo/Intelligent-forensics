#!/bin/bash


apt-get install -y linux-headers-$(uname -r)

mount -t debugfs none /sys/kernel/debug

#ip route change default via 10.100.0.10
ip route add 10.0.0.0/8 via 10.100.0.10

cd app

npm start

#hping3 -c 3 -S --flood 127.0.0.1 &
#hping3 -c 3 -2 -p 80 --flood 127.0.0.1 &
#hping3 -c 3 -1 -a 8.8.8.8 --flood 127.0.0.1 &
#hping3 -c 3 -A --flood 127.0.0.1 &


/bin/sleep infinity

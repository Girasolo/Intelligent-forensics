#!/bin/bash

apt-get update
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

iptables -A INPUT -i lo -p tcp --dport 65432 -j ACCEPT
iptables -A INPUT -i lo -p tcp --dport 65433 -j ACCEPT
iptables -A OUTPUT -o lo -p tcp --sport 65432 -j ACCEPT
iptables -A OUTPUT -o lo -p tcp --sport 65433 -j ACCEPT
sysctl -w net.ipv4.tcp_syncookies=1


/bin/sleep infinity

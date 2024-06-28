#!/bin/bash

apt-get update
apt-get install -y linux-headers-$(uname -r)                    #needed to use the ebpf tools. Since they are often updated 
                                                                #it's necessary to update the repositories

mount -t debugfs none /sys/kernel/debug                         #mandatory to work with ebpf, gain access to tools and information about the kernel

#ip route change default via 10.100.0.10
ip route add 10.0.0.0/8 via 10.100.0.10                         #set as route for the entire interval the routerA


cd app                                                          #start the server
npm start

#hping3 -c 3 -S --flood 127.0.0.1 &                             #temporary flood attack
#hping3 -c 3 -2 -p 80 --flood 127.0.0.1 &
#hping3 -c 3 -1 -a 8.8.8.8 --flood 127.0.0.1 &
#hping3 -c 3 -A --flood 127.0.0.1 &

#iptables -A INPUT -i lo -p tcp --dport 65432 -j ACCEPT          #set firewall rules to protect the node on the ports used by 1clock, tcplife and tcptracer 
#iptables -A INPUT -i lo -p tcp --dport 65433 -j ACCEPT
#iptables -A OUTPUT -o lo -p tcp --sport 65432 -j ACCEPT
#iptables -A OUTPUT -o lo -p tcp --sport 65433 -j ACCEPT

#sysctl -w net.ipv4.tcp_syncookies=1                             #enable syn coockies to protect the node


/bin/sleep infinity

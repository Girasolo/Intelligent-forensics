#!/bin/sh


#ip route change default via 10.200.0.10
ip route add 10.0.0.0/8 via 10.200.0.10
chmod 666 /shared-volume/prediction/temp.txt

/usr/bin/fluentd -c /fluentd/etc/fluent.conf &



sleep infinity

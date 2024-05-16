#!/bin/bash


#ip route change default via 10.200.0.10
ip route add 10.0.0.0/8 via 10.200.0.10
touch /shared-volume/prediction/temp.txt

#/usr/bin/fluentd -c /fluentd/etc/fluent.conf & alpine version

#fluentd -c /fluentd/etc/fluent.conf &
/usr/local/bundle/gems/fluentd-1.17.0/bin/fluentd -c /fluentd/etc/fluent.conf & 



/bin/sleep infinity

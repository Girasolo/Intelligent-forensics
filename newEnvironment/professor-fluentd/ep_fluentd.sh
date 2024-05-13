#!/bin/sh

/usr/bin/fluentd -c fluentd/etc/fluent.conf &

#ip route change default via 10.200.0.10
ip route add 10.0.0.0/8 via 10.200.0.10




sleep infinity

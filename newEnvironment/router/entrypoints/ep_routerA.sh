#!/bin/bash

service syslog-ng start                     #start the syslog
service frr start                           #start frr (routing service)

#set frr and set the frrRouter log
vtysh << EOF
conf t
log file /shared-volume/frr/frrRouterA.log
router ospf
network 10.100.0.0/24 area 0
network 10.200.0.0/24 area 0
network 10.1.0.0/24 area 0
end
EOF



/bin/sleep infinity
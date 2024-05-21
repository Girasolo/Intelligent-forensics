#!/bin/bash

service syslog-ng start         #start the syslog
service frr start               #start frr (routing service)

#set frr and set the frrRouter log
vtysh << EOF
conf t
router ospf 
network 10.1.0.0/24 area 0
network 10.2.0.0/24 area 0
network 10.3.0.0/24 area 0
end
EOF




/bin/sleep infinity
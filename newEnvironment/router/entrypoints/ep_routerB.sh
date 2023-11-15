#!/bin/bash

service syslog-ng start
service frr start


vtysh << EOF
conf t
router ospf 
network 10.1.0.0/24 area 0
network 10.2.0.0/24 area 0
network 10.3.0.0/24 area 0
end
EOF




/bin/sleep infinity
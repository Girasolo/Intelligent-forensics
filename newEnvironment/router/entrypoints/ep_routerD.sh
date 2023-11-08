#!/bin/bash

service syslog-ng start
service frr start


vtysh << EOF
conf t
router ospf 
network 10.3.0.0/30 area 0
network 10.0.3.0/24 area 0
network 10.0.4.0/24 area 0
end
EOF




/bin/sleep infinity
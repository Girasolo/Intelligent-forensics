#!/bin/bash

#ip route change default via 10.0.1.10 # set as default the address of routerC
ip route add 10.0.0.0/8 via 10.0.1.10

/bin/sleep infinity # in this way the container doesn't shut down

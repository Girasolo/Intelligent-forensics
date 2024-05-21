#!/bin/bash

ip route change default via 10.0.1.10 # set as default the address of routerC

/bin/sleep infinity # in this way the container doesn't shut down

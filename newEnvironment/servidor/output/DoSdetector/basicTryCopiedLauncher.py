#!/usr/bin/python3
from bcc import BPF #1
import socket
import os
from time import sleep
from bcc.utils import printb

interface = "lo" #2
b = BPF(src_file="basicTryCopied.bpf.c") #3
fx = b.load_func("udp_counter", BPF.XDP) #4
BPF.attach_xdp(interface, fx, 0) #5

try:
    b.trace_print() #6
except KeyboardInterrupt: #7

    dist = b.get_table("counter") #8
    for k, v in sorted(dist.items()): #9
        print("DEST_PORT : %10d, COUNT : %10d" % (k.value, v.value)) #10

BPF.remove_xdp(interface, 0) #11

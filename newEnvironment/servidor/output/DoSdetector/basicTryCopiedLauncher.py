#!/usr/bin/python3
from bcc import BPF #1
import socket
import os
from time import sleep
from bcc.utils import printb

interface = "lo" #2
kernel_headers = "/usr/src/linux-headers-6.5.0-21-generic/include/"
b = BPF(src_file="basicTryCopied.bpf.c", cflags=["-I", kernel_headers]) #3
fx = b.load_func("udp_counter", BPF.XDP) #4
BPF.attach_xdp(interface, fx, 0) #5

try:
    b.trace_print() #6
except KeyboardInterrupt: #7

    dist = b.get_table("packet_info_map") #8
    for k, v in sorted(dist.items(), key=lambda item: item[0].value):
    	packet = v  # Access the first (and only) element of the list
    	print("Timestamp : %10d, SRC_IP : %10d, DST_IP : %10d, PROTOCOL : %d" % (k.value, packet.src_ip, packet.dst_ip, packet.protocol))

BPF.remove_xdp(interface, 0) #11

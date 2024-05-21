#!/usr/bin/env python
# @lint-avoid-python-3-compatibility-imports
#
# tcplife   Trace the lifespan of TCP sessions and summarize.
#           For Linux, uses BCC, BPF. Embedded C.
#
# USAGE: tcplife [-h] [-C] [-S] [-p PID] [-4 | -6] [interval [count]]
#
# This uses the sock:inet_sock_set_state tracepoint if it exists (added to
# Linux 4.16, and replacing the earlier tcp:tcp_set_state), else it uses
# kernel dynamic tracing of tcp_set_state().
#
# While throughput counters are emitted, they are fetched in a low-overhead
# manner: reading members of the tcp_info struct on TCP close. ie, we do not
# trace send/receive.
#
# Copyright 2016 Netflix, Inc.
# Licensed under the Apache License, Version 2.0 (the "License")
#
# IDEA: Julia Evans
#
# 18-Oct-2016   Brendan Gregg   Created this.
# 29-Dec-2017      "      "     Added tracepoint support.

from __future__ import print_function
from bcc import BPF
import argparse
from socket import inet_ntop, AF_INET, AF_INET6
from struct import pack
from time import strftime
#added by Girasolo
from datetime import datetime
import signal
import sys
import multiprocessing as mpù
from multiprocessing import shared_memory
import time
import socket
import os
#

# arguments
examples = """examples:
    ./tcplife           # trace all TCP connect()s
    ./tcplife -T        # include time column (HH:MM:SS)
    ./tcplife -w        # wider columns (fit IPv6)
    ./tcplife -stT      # csv output, with times & timestamps
    ./tcplife -p 181    # only trace PID 181
    ./tcplife -L 80     # only trace local port 80
    ./tcplife -L 80,81  # only trace local ports 80 and 81
    ./tcplife -D 80     # only trace remote port 80
    ./tcplife -4        # only trace IPv4 family
    ./tcplife -6        # only trace IPv6 family
"""
#added by Girasolo
timestamp = datetime.now().strftime("%y%m%d_%H:%M:%S")
#
parser = argparse.ArgumentParser(
    description="Trace the lifespan of TCP sessions and summarize",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog=examples)
parser.add_argument("-T", "--time", action="store_true",
    help="include time column on output (HH:MM:SS)")
parser.add_argument("-t", "--timestamp", action="store_true",
    help="include timestamp on output (seconds)")
parser.add_argument("-w", "--wide", action="store_true",
    help="wide column output (fits IPv6 addresses)")
parser.add_argument("-s", "--csv", action="store_true",
    help="comma separated values output")
parser.add_argument("-p", "--pid",
    help="trace this PID only")
parser.add_argument("-L", "--localport",
    help="comma-separated list of local ports to trace.")
parser.add_argument("-D", "--remoteport",
    help="comma-separated list of remote ports to trace.")
group = parser.add_mutually_exclusive_group()
group.add_argument("-4", "--ipv4", action="store_true",
    help="trace IPv4 family only")
group.add_argument("-6", "--ipv6", action="store_true",
    help="trace IPv6 family only")
parser.add_argument("--ebpf", action="store_true",
    help=argparse.SUPPRESS)
#added by Girasolo
# Option of writing the result on a file with the name of the timestamp
parser.add_argument("-f","--file", const=f"life{timestamp}.txt", nargs='?', help="print on one or a timestamp series of output files.")
# Option of communicating the result with a socketconnection by default
parser.add_argument("-sc","--socketconnection", action='store_true', help="send the print straight to the 1clock connection. Every SIGUSR1 sends a divisor message")
#
args = parser.parse_args()
debug = 0

# define BPF program
bpf_text = """
#include <uapi/linux/ptrace.h>
#include <linux/tcp.h>
#include <net/sock.h>
#include <bcc/proto.h>

BPF_HASH(birth, struct sock *, u64);

// separate data structs for ipv4 and ipv6
struct ipv4_data_t {
    u64 ts_us;
    u32 pid;
    u32 saddr;
    u32 daddr;
    u64 ports;
    u64 rx_b;
    u64 tx_b;
    u64 span_us;
    char task[TASK_COMM_LEN];
};
BPF_PERF_OUTPUT(ipv4_events);

struct ipv6_data_t {
    u64 ts_us;
    u32 pid;
    unsigned __int128 saddr;
    unsigned __int128 daddr;
    u64 ports;
    u64 rx_b;
    u64 tx_b;
    u64 span_us;
    char task[TASK_COMM_LEN];
};
BPF_PERF_OUTPUT(ipv6_events);

struct id_t {
    u32 pid;
    char task[TASK_COMM_LEN];
};
BPF_HASH(whoami, struct sock *, struct id_t);
"""

#
# XXX: The following is temporary code for older kernels, Linux 4.14 and
# older. It uses kprobes to instrument tcp_set_state(). On Linux 4.16 and
# later, the sock:inet_sock_set_state tracepoint should be used instead, as
# is done by the code that follows this. In the distant future (2021?), this
# kprobe code can be removed. This is why there is so much code
# duplication: to make removal easier.
#
bpf_text_kprobe = """
int kprobe__tcp_set_state(struct pt_regs *ctx, struct sock *sk, int state)
{
    u32 pid = bpf_get_current_pid_tgid() >> 32;

    // lport is either used in a filter here, or later
    u16 lport = sk->__sk_common.skc_num;
    FILTER_LPORT

    // dport is either used in a filter here, or later
    u16 dport = sk->__sk_common.skc_dport;
    dport = ntohs(dport);
    FILTER_DPORT

    /*
     * This tool includes PID and comm context. It's best effort, and may
     * be wrong in some situations. It currently works like this:
     * - record timestamp on any state < TCP_FIN_WAIT1
     * - cache task context on:
     *       TCP_SYN_SENT: tracing from client
     *       TCP_LAST_ACK: client-closed from server
     * - do output on TCP_CLOSE:
     *       fetch task context if cached, or use current task
     */

    // capture birth time
    if (state < TCP_FIN_WAIT1) {
        /*
         * Matching just ESTABLISHED may be sufficient, provided no code-path
         * sets ESTABLISHED without a tcp_set_state() call. Until we know
         * that for sure, match all early states to increase chances a
         * timestamp is set.
         * Note that this needs to be set before the PID filter later on,
         * since the PID isn't reliable for these early stages, so we must
         * save all timestamps and do the PID filter later when we can.
         */
        u64 ts = bpf_ktime_get_ns();
        birth.update(&sk, &ts);
    }

    // record PID & comm on SYN_SENT
    if (state == TCP_SYN_SENT || state == TCP_LAST_ACK) {
        // now we can PID filter, both here and a little later on for CLOSE
        FILTER_PID
        struct id_t me = {.pid = pid};
        bpf_get_current_comm(&me.task, sizeof(me.task));
        whoami.update(&sk, &me);
    }

    if (state != TCP_CLOSE)
        return 0;

    // calculate lifespan
    u64 *tsp, delta_us;
    tsp = birth.lookup(&sk);
    if (tsp == 0) {
        whoami.delete(&sk);     // may not exist
        return 0;               // missed create
    }
    delta_us = (bpf_ktime_get_ns() - *tsp) / 1000;
    birth.delete(&sk);

    // fetch possible cached data, and filter
    struct id_t *mep;
    mep = whoami.lookup(&sk);
    if (mep != 0)
        pid = mep->pid;
    FILTER_PID

    // get throughput stats. see tcp_get_info().
    u64 rx_b = 0, tx_b = 0;
    struct tcp_sock *tp = (struct tcp_sock *)sk;
    rx_b = tp->bytes_received;
    tx_b = tp->bytes_acked;

    u16 family = sk->__sk_common.skc_family;

    FILTER_FAMILY

    if (family == AF_INET) {
        struct ipv4_data_t data4 = {};
        data4.span_us = delta_us;
        data4.rx_b = rx_b;
        data4.tx_b = tx_b;
        data4.ts_us = bpf_ktime_get_ns() / 1000;
        data4.saddr = sk->__sk_common.skc_rcv_saddr;
        data4.daddr = sk->__sk_common.skc_daddr;
        // a workaround until data4 compiles with separate lport/dport
        data4.pid = pid;
        data4.ports = dport + ((0ULL + lport) << 32);
        if (mep == 0) {
            bpf_get_current_comm(&data4.task, sizeof(data4.task));
        } else {
            bpf_probe_read_kernel(&data4.task, sizeof(data4.task), (void *)mep->task);
        }
        ipv4_events.perf_submit(ctx, &data4, sizeof(data4));

    } else /* 6 */ {
        struct ipv6_data_t data6 = {};
        data6.span_us = delta_us;
        data6.rx_b = rx_b;
        data6.tx_b = tx_b;
        data6.ts_us = bpf_ktime_get_ns() / 1000;
        bpf_probe_read_kernel(&data6.saddr, sizeof(data6.saddr),
            sk->__sk_common.skc_v6_rcv_saddr.in6_u.u6_addr32);
        bpf_probe_read_kernel(&data6.daddr, sizeof(data6.daddr),
            sk->__sk_common.skc_v6_daddr.in6_u.u6_addr32);
        // a workaround until data6 compiles with separate lport/dport
        data6.ports = dport + ((0ULL + lport) << 32);
        data6.pid = pid;
        if (mep == 0) {
            bpf_get_current_comm(&data6.task, sizeof(data6.task));
        } else {
            bpf_probe_read_kernel(&data6.task, sizeof(data6.task), (void *)mep->task);
        }
        ipv6_events.perf_submit(ctx, &data6, sizeof(data6));
    }

    if (mep != 0)
        whoami.delete(&sk);

    return 0;
}
"""

bpf_text_tracepoint = """
TRACEPOINT_PROBE(sock, inet_sock_set_state)
{
    if (args->protocol != IPPROTO_TCP)
        return 0;

    u32 pid = bpf_get_current_pid_tgid() >> 32;
    // sk is mostly used as a UUID, and for two tcp stats:
    struct sock *sk = (struct sock *)args->skaddr;

    // lport is either used in a filter here, or later
    u16 lport = args->sport;
    FILTER_LPORT

    // dport is either used in a filter here, or later
    u16 dport = args->dport;
    FILTER_DPORT

    /*
     * This tool includes PID and comm context. It's best effort, and may
     * be wrong in some situations. It currently works like this:
     * - record timestamp on any state < TCP_FIN_WAIT1
     * - cache task context on:
     *       TCP_SYN_SENT: tracing from client
     *       TCP_LAST_ACK: client-closed from server
     * - do output on TCP_CLOSE:
     *       fetch task context if cached, or use current task
     */

    // capture birth time
    if (args->newstate < TCP_FIN_WAIT1) {
        /*
         * Matching just ESTABLISHED may be sufficient, provided no code-path
         * sets ESTABLISHED without a tcp_set_state() call. Until we know
         * that for sure, match all early states to increase chances a
         * timestamp is set.
         * Note that this needs to be set before the PID filter later on,
         * since the PID isn't reliable fore these early stages, so we must
         * save all timestamps and do the PID filter later when we can.
         */
        u64 ts = bpf_ktime_get_ns();
        birth.update(&sk, &ts);
    }

    // record PID & comm on SYN_SENT
    if (args->newstate == TCP_SYN_SENT || args->newstate == TCP_LAST_ACK) {
        // now we can PID filter, both here and a little later on for CLOSE
        FILTER_PID
        struct id_t me = {.pid = pid};
        bpf_get_current_comm(&me.task, sizeof(me.task));
        whoami.update(&sk, &me);
    }

    if (args->newstate != TCP_CLOSE)
        return 0;

    // calculate lifespan
    u64 *tsp, delta_us;
    tsp = birth.lookup(&sk);
    if (tsp == 0) {
        whoami.delete(&sk);     // may not exist
        return 0;               // missed create
    }
    delta_us = (bpf_ktime_get_ns() - *tsp) / 1000;
    birth.delete(&sk);

    // fetch possible cached data, and filter
    struct id_t *mep;
    mep = whoami.lookup(&sk);
    if (mep != 0)
        pid = mep->pid;
    FILTER_PID

    u16 family = args->family;
    FILTER_FAMILY

    // get throughput stats. see tcp_get_info().
    u64 rx_b = 0, tx_b = 0;
    struct tcp_sock *tp = (struct tcp_sock *)sk;
    rx_b = tp->bytes_received;
    tx_b = tp->bytes_acked;

    if (args->family == AF_INET) {
        struct ipv4_data_t data4 = {};
        data4.span_us = delta_us;
        data4.rx_b = rx_b;
        data4.tx_b = tx_b;
        data4.ts_us = bpf_ktime_get_ns() / 1000;
        __builtin_memcpy(&data4.saddr, args->saddr, sizeof(data4.saddr));
        __builtin_memcpy(&data4.daddr, args->daddr, sizeof(data4.daddr));
        // a workaround until data4 compiles with separate lport/dport
        data4.ports = dport + ((0ULL + lport) << 32);
        data4.pid = pid;

        if (mep == 0) {
            bpf_get_current_comm(&data4.task, sizeof(data4.task));
        } else {
            bpf_probe_read_kernel(&data4.task, sizeof(data4.task), (void *)mep->task);
        }
        ipv4_events.perf_submit(args, &data4, sizeof(data4));

    } else /* 6 */ {
        struct ipv6_data_t data6 = {};
        data6.span_us = delta_us;
        data6.rx_b = rx_b;
        data6.tx_b = tx_b;
        data6.ts_us = bpf_ktime_get_ns() / 1000;
        __builtin_memcpy(&data6.saddr, args->saddr_v6, sizeof(data6.saddr));
        __builtin_memcpy(&data6.daddr, args->daddr_v6, sizeof(data6.daddr));
        // a workaround until data6 compiles with separate lport/dport
        data6.ports = dport + ((0ULL + lport) << 32);
        data6.pid = pid;
        if (mep == 0) {
            bpf_get_current_comm(&data6.task, sizeof(data6.task));
        } else {
            bpf_probe_read_kernel(&data6.task, sizeof(data6.task), (void *)mep->task);
        }
        ipv6_events.perf_submit(args, &data6, sizeof(data6));
    }

    if (mep != 0)
        whoami.delete(&sk);

    return 0;
}
"""

if (BPF.tracepoint_exists("sock", "inet_sock_set_state")):
    bpf_text += bpf_text_tracepoint
else:
    bpf_text += bpf_text_kprobe

# code substitutions
if args.pid:
    bpf_text = bpf_text.replace('FILTER_PID',
        'if (pid != %s) { return 0; }' % args.pid)
if args.remoteport:
    dports = [int(dport) for dport in args.remoteport.split(',')]
    dports_if = ' && '.join(['dport != %d' % dport for dport in dports])
    bpf_text = bpf_text.replace('FILTER_DPORT',
        'if (%s) { birth.delete(&sk); return 0; }' % dports_if)
if args.localport:
    lports = [int(lport) for lport in args.localport.split(',')]
    lports_if = ' && '.join(['lport != %d' % lport for lport in lports])
    bpf_text = bpf_text.replace('FILTER_LPORT',
        'if (%s) { birth.delete(&sk); return 0; }' % lports_if)
if args.ipv4:
    bpf_text = bpf_text.replace('FILTER_FAMILY',
        'if (family != AF_INET) { return 0; }')
elif args.ipv6:
    bpf_text = bpf_text.replace('FILTER_FAMILY',
        'if (family != AF_INET6) { return 0; }')
#added by Girasolo
if args.file:
    f = open(args.file, 'a')                                                    # Open the first file
#


bpf_text = bpf_text.replace('FILTER_PID', '')
bpf_text = bpf_text.replace('FILTER_DPORT', '')
bpf_text = bpf_text.replace('FILTER_LPORT', '')
bpf_text = bpf_text.replace('FILTER_FAMILY', '')

if debug or args.ebpf:
    print(bpf_text)
    if args.ebpf:
        exit()

#
# Setup output formats
#
# Don't change the default output (next 2 lines): this fits in 80 chars. I
# know it doesn't have NS or UIDs etc. I know. If you really, really, really
# need to add columns, columns that solve real actual problems, I'd start by
# adding an extended mode (-x) to included those columns.
#
header_string = "%-5s %-10.10s %s%-15s %-5s %-15s %-5s %5s %5s %s"
format_string = "%-5d %-10.10s %s%-15s %-5d %-15s %-5d %5d %5d %.2f"
if args.wide:
    header_string = "%-5s %-16.16s %-2s %-39s %-5s %-39s %-5s %6s %6s %s"
    format_string = "%-5d %-16.16s %-2s %-39s %-5s %-39s %-5d %6d %6d %.2f"
if args.csv:
    header_string = "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s"
    format_string = "%d,%s,%s,%s,%s,%s,%d,%d,%d,%.2f"

#added by Girasolo
def fill_string_to_bytes(input_string, target_bytes, fill_character=' '):
    """
    Fill a string to reach a certain number of bytes (not used)
    """
    current_bytes = len(input_string.encode('utf-8'))
    if current_bytes >= target_bytes:
        return input_string
    else:
        fill_count = target_bytes - current_bytes
        filled_string = input_string + fill_character * fill_count
        return filled_string
#
   
# process event
def print_ipv4_event(cpu, data, size):
    event = b["ipv4_events"].event(data)
    global start_ts
    #added by Girasolo
    if args.file:                                                                           # Print on file
        if args.time:
            if args.csv:
                f.write("%s," % strftime("%H:%M:%S"))
            else:
                f.write("%-8s " % strftime("%H:%M:%S"))
        if args.timestamp:
            if start_ts == 0:
                start_ts = event.ts_us
            delta_s = (float(event.ts_us) - start_ts) / 1000000
            if args.csv:
                f.write("%.6f," % delta_s)
            else:
                f.write("%-9.6f " % delta_s)
        f.write(format_string % (event.pid, event.task.decode('utf-8', 'replace'),
        "4" if args.wide or args.csv else "",
        inet_ntop(AF_INET, pack("I", event.saddr)), event.ports >> 32,
        inet_ntop(AF_INET, pack("I", event.daddr)), event.ports & 0xffffffff,
        event.tx_b / 1024, event.rx_b / 1024, float(event.span_us) / 1000) + "\n")
    elif args.socketconnection:                                                             # Print on socket channel
        global client_socket
        message = ""
        if args.time:
            if args.csv:
                message = message + ("%s," % strftime("%H:%M:%S"))              
            else:
                message = message + (("%-8s " % strftime("%H:%M:%S")))
        if args.timestamp:
            if start_ts == 0:
                start_ts = event.ts_us
            delta_s = (float(event.ts_us) - start_ts) / 1000000
            if args.csv:
                message = message + ("%.6f," % delta_s)
            else:
                message = message + (("%-9.6f " % delta_s))
        message = message + ((format_string % (event.pid, event.task.decode('utf-8', 'replace'),
        "4" if args.wide or args.csv else "",
        inet_ntop(AF_INET, pack("I", event.saddr)), event.ports >> 32,
        inet_ntop(AF_INET, pack("I", event.daddr)), event.ports & 0xffffffff,
        event.tx_b / 1024, event.rx_b / 1024, float(event.span_us) / 1000) + "\n"))
        try:
            #fill the message to 15 bytes approx the longest
            #message = fill_string_to_bytes(message,15)
            client_socket.sendall(message.encode())                                         # Send the entry
        except OSError as e:
            print("Socket error:", e)

        #client_socket.sendall(message.encode())    
    else:
        #
        if args.time:
            if args.csv:
                print("%s," % strftime("%H:%M:%S"), end="")
            else:
                print("%-8s " % strftime("%H:%M:%S"), end="")
        if args.timestamp:
            if start_ts == 0:
                start_ts = event.ts_us
            delta_s = (float(event.ts_us) - start_ts) / 1000000
            if args.csv:
                print("%.6f," % delta_s, end="")
            else:
                print("%-9.6f " % delta_s, end="")
        print(format_string % (event.pid, event.task.decode('utf-8', 'replace'),
            "4" if args.wide or args.csv else "",
            inet_ntop(AF_INET, pack("I", event.saddr)), event.ports >> 32,
            inet_ntop(AF_INET, pack("I", event.daddr)), event.ports & 0xffffffff,
            event.tx_b / 1024, event.rx_b / 1024, float(event.span_us) / 1000))

def print_ipv6_event(cpu, data, size):
    event = b["ipv6_events"].event(data)
    global start_ts
    if args.time:
        if args.csv:
            print("%s," % strftime("%H:%M:%S"), end="")
        else:
            print("%-8s " % strftime("%H:%M:%S"), end="")
    if args.timestamp:
        if start_ts == 0:
            start_ts = event.ts_us
        delta_s = (float(event.ts_us) - start_ts) / 1000000
        if args.csv:
            print("%.6f," % delta_s, end="")
        else:
            print("%-9.6f " % delta_s, end="")
    print(format_string % (event.pid, event.task.decode('utf-8', 'replace'),
        "6" if args.wide or args.csv else "",
        inet_ntop(AF_INET6, event.saddr), event.ports >> 32,
        inet_ntop(AF_INET6, event.daddr), event.ports & 0xffffffff,
        event.tx_b / 1024, event.rx_b / 1024, float(event.span_us) / 1000))

#added by Girasolo
def send_interrupt(time):
    """
    Close the program after time secs
    """
    #open a new file each 25 secs. If the file fails to open continue to write on the previous one
    def handler(signum, frame):
        print("Timeout reached. Sending KeyboardInterrupt.")
        raise KeyboardInterrupt

    
    signal.signal(signal.SIGALRM, handler)                                              # Set up the signal handler for SIGALRM
    signal.alarm(time)
#

#added by Girasolo
def handlerFile(signum, frame):
    """
    Signal handler for the file option.
    SIGTERM terminates
    SIGUSR1 close the previous and creates a new file with a new timestamp
    """
    global f
    if signum == signal.SIGTERM:
        f.close()
        print("life terminates here")
    elif signum == signal.SIGUSR1:
        print("New file")
        f.close()
        timestamp = datetime.now().strftime("%y%m%d_%H:%M:%S")
        f = open(f"life{timestamp}.txt", 'a')
        if args.time:
            if args.csv:
                f.write("%s," % ("TIME"))
            else:
                f.write("%-8s " % ("TIME"))
        if args.timestamp:
            if args.csv:
                f.write("%s," % ("TIME(s)"))
            else:
                f.write("%-9s " % ("TIME(s)"))
        f.write(header_string % ("PID", "COMM",
            "IP" if args.wide or args.csv else "", "LADDR",
            "LPORT", "RADDR", "RPORT", "TX_KB", "RX_KB", "MS") + "\n")
    else: 
        print("sig not handled")
#

#added by Girasolo
def handlerSocket(signum, frame):
    """
    Signal handler for the socket option.
    SIGTERM terminates
    SIGUSR1 send a string SIGNAL HERE to communicate that the SIGUSR1 has been received (it is sent by 1clock every 25 secs)
    """
    global client_socket
    if signum == signal.SIGTERM:
        client_socket.close()
        print("life terminates here")
    if signum == signal.SIGUSR1:
        print("LIFE (pid: ", os.getpid(), ")RECEIVED THE SIGNAL SIGUSR1")
        separation = "SIGNAL HERE ---\n"
        #separation = fill_string_to_bytes(separation, 15)
        client_socket.send(separation.encode())   
    else: 
        print("sig not handled: ", signum)
#

#added by Girasolo
if args.socketconnection:  
    HOST = '127.0.0.1'                                                      # Define host and port (the same as 1clock)
    PORT = 65432
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       # Create and connect socket to the server (1clock)
    client_socket.connect((HOST, PORT))   
#

# initialize BPF
b = BPF(text=bpf_text)

# header
#added by Girasolo
if args.file:
    if args.time:
        if args.csv:
            f.write("%s," % ("TIME"))
        else:
            f.write("%-8s " % ("TIME"))
    if args.timestamp:
        if args.csv:
            f.write("%s," % ("TIME(s)"))
        else:
            f.write("%-9s " % ("TIME(s)"))
    f.write(header_string % ("PID", "COMM",
        "IP" if args.wide or args.csv else "", "LADDR",
        "LPORT", "RADDR", "RPORT", "TX_KB", "RX_KB", "MS") + "\n")
elif args.socketconnection:
    print("useless headers")
else:
    #
    if args.time:
        if args.csv:
            print("%s," % ("TIME"), end="")
        else:
            print("%-8s " % ("TIME"), end="")
    if args.timestamp:
        if args.csv:
            print("%s," % ("TIME(s)"), end="")
        else:
            print("%-9s " % ("TIME(s)"), end="")
    print(header_string % ("PID", "COMM",
        "IP" if args.wide or args.csv else "", "LADDR",
        "LPORT", "RADDR", "RPORT", "TX_KB", "RX_KB", "MS"))

start_ts = 0

# read events
b["ipv4_events"].open_perf_buffer(print_ipv4_event, page_cnt=64)
b["ipv6_events"].open_perf_buffer(print_ipv6_event, page_cnt=64)
#added by Girasolo
if args.file:                                                                  # Signal handler for file
    print("life starts here")
    signal.signal(signal.SIGUSR1, handlerFile)
    signal.signal(signal.SIGTERM, handlerFile)
#    send_interrupt(25)
#

#added by Girasolo

if args.socketconnection:                                                      # Signal handler for socket
    print("handler here")
    signal.signal(signal.SIGUSR1, handlerSocket)
    signal.signal(signal.SIGTERM, handlerSocket)
#
while 1:
    try:
        b.perf_buffer_poll()
    except KeyboardInterrupt:
        #added by Girasolo
        if args.file:
            f.close()
        #
        exit()
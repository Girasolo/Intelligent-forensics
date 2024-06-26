#!/usr/bin/env python
#
# tcpv4tracer   Trace TCP connections.
#               For Linux, uses BCC, eBPF. Embedded C.
#
# USAGE: tcpv4tracer [-h] [-v] [-p PID] [-N NETNS] [-4 | -6]
#
# You should generally try to avoid writing long scripts that measure multiple
# functions and walk multiple kernel structures, as they will be a burden to
# maintain as the kernel changes.
# The following code should be replaced, and simplified, when static TCP probes
# exist.
#
# Copyright 2017-2020 Kinvolk GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License")
from __future__ import print_function
from bcc import BPF
from bcc.containers import filter_by_containers

import argparse as ap
from socket import inet_ntop, AF_INET, AF_INET6
from struct import pack
#added by Girasolo
from datetime import datetime
import signal
import sys
import socket
import os
#

#added by Girasolo
timestamp = datetime.now().strftime("%y%m%d_%H:%M:%S")                      # Save the time at the beginning of the program
#
parser = ap.ArgumentParser(description="Trace TCP connections",
                           formatter_class=ap.RawDescriptionHelpFormatter)
parser.add_argument("-t", "--timestamp", action="store_true",
                    help="include timestamp on output")
parser.add_argument("-p", "--pid", default=0, type=int,
                    help="trace this PID only")
parser.add_argument("-N", "--netns", default=0, type=int,
                    help="trace this Network Namespace only")
parser.add_argument("--cgroupmap",
                    help="trace cgroups in this BPF map only")
parser.add_argument("--mntnsmap",
                    help="trace mount namespaces in this BPF map only")
group = parser.add_mutually_exclusive_group()
group.add_argument("-4", "--ipv4", action="store_true",
                    help="trace IPv4 family only")
group.add_argument("-6", "--ipv6", action="store_true",
                   help="trace IPv6 family only")
parser.add_argument("-v", "--verbose", action="store_true",
                    help="include Network Namespace in the output")
parser.add_argument("--ebpf", action="store_true",
                    help=ap.SUPPRESS)

#added by Girasolo
# Option of writing the result on a file with the name of the timestamp
parser.add_argument("-f","--file", const=f"trace{timestamp}.txt", nargs='?', help="print on one or a timestamp series of output files.")
# Option of communicating the result with a socketconnection by default
parser.add_argument("-sc","--socketconnection", action='store_true', help="send the print straight to the 1clock connection. Every SIGUSR1 sends a divisor message")
#
args = parser.parse_args()

bpf_text = """
#include <uapi/linux/ptrace.h>
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wtautological-compare"
#include <net/sock.h>
#pragma clang diagnostic pop
#include <net/inet_sock.h>
#include <net/net_namespace.h>
#include <bcc/proto.h>

#define TCP_EVENT_TYPE_CONNECT 1
#define TCP_EVENT_TYPE_ACCEPT  2
#define TCP_EVENT_TYPE_CLOSE   3

struct tcp_ipv4_event_t {
    u64 ts_ns;
    u32 type;
    u32 pid;
    char comm[TASK_COMM_LEN];
    u8 ip;
    u32 saddr;
    u32 daddr;
    u16 sport;
    u16 dport;
    u32 netns;
};
BPF_PERF_OUTPUT(tcp_ipv4_event);

struct tcp_ipv6_event_t {
    u64 ts_ns;
    u32 type;
    u32 pid;
    char comm[TASK_COMM_LEN];
    unsigned __int128 saddr;
    unsigned __int128 daddr;
    u16 sport;
    u16 dport;
    u32 netns;
    u8 ip;
};
BPF_PERF_OUTPUT(tcp_ipv6_event);

// tcp_set_state doesn't run in the context of the process that initiated the
// connection so we need to store a map TUPLE -> PID to send the right PID on
// the event
struct ipv4_tuple_t {
    u32 saddr;
    u32 daddr;
    u16 sport;
    u16 dport;
    u32 netns;
};

struct ipv6_tuple_t {
    unsigned __int128 saddr;
    unsigned __int128 daddr;
    u16 sport;
    u16 dport;
    u32 netns;
};

struct pid_comm_t {
    u64 pid;
    char comm[TASK_COMM_LEN];
};

BPF_HASH(tuplepid_ipv4, struct ipv4_tuple_t, struct pid_comm_t);
BPF_HASH(tuplepid_ipv6, struct ipv6_tuple_t, struct pid_comm_t);

BPF_HASH(connectsock, u64, struct sock *);

static int read_ipv4_tuple(struct ipv4_tuple_t *tuple, struct sock *skp)
{
  u32 net_ns_inum = 0;
  u32 saddr = skp->__sk_common.skc_rcv_saddr;
  u32 daddr = skp->__sk_common.skc_daddr;
  struct inet_sock *sockp = (struct inet_sock *)skp;
  u16 sport = sockp->inet_sport;
  u16 dport = skp->__sk_common.skc_dport;
#ifdef CONFIG_NET_NS
  net_ns_inum = skp->__sk_common.skc_net.net->ns.inum;
#endif

  ##FILTER_NETNS##

  tuple->saddr = saddr;
  tuple->daddr = daddr;
  tuple->sport = sport;
  tuple->dport = dport;
  tuple->netns = net_ns_inum;

  // if addresses or ports are 0, ignore
  if (saddr == 0 || daddr == 0 || sport == 0 || dport == 0) {
      return 0;
  }

  return 1;
}

static int read_ipv6_tuple(struct ipv6_tuple_t *tuple, struct sock *skp)
{
  u32 net_ns_inum = 0;
  unsigned __int128 saddr = 0, daddr = 0;
  struct inet_sock *sockp = (struct inet_sock *)skp;
  u16 sport = sockp->inet_sport;
  u16 dport = skp->__sk_common.skc_dport;
#ifdef CONFIG_NET_NS
  net_ns_inum = skp->__sk_common.skc_net.net->ns.inum;
#endif
  bpf_probe_read_kernel(&saddr, sizeof(saddr),
                 skp->__sk_common.skc_v6_rcv_saddr.in6_u.u6_addr32);
  bpf_probe_read_kernel(&daddr, sizeof(daddr),
                 skp->__sk_common.skc_v6_daddr.in6_u.u6_addr32);

  ##FILTER_NETNS##

  tuple->saddr = saddr;
  tuple->daddr = daddr;
  tuple->sport = sport;
  tuple->dport = dport;
  tuple->netns = net_ns_inum;

  // if addresses or ports are 0, ignore
  if (saddr == 0 || daddr == 0 || sport == 0 || dport == 0) {
      return 0;
  }

  return 1;
}

static bool check_family(struct sock *sk, u16 expected_family) {
  u64 zero = 0;
  u16 family = sk->__sk_common.skc_family;
  return family == expected_family;
}

int trace_connect_v4_entry(struct pt_regs *ctx, struct sock *sk)
{
  if (container_should_be_filtered()) {
    return 0;
  }

  u64 pid = bpf_get_current_pid_tgid();

  ##FILTER_PID##
  
  u16 family = sk->__sk_common.skc_family;
  ##FILTER_FAMILY##


  // stash the sock ptr for lookup on return
  connectsock.update(&pid, &sk);

  return 0;
}

int trace_connect_v4_return(struct pt_regs *ctx)
{
  int ret = PT_REGS_RC(ctx);
  u64 pid = bpf_get_current_pid_tgid();

  struct sock **skpp;
  skpp = connectsock.lookup(&pid);
  if (skpp == 0) {
      return 0;       // missed entry
  }

  connectsock.delete(&pid);

  if (ret != 0) {
      // failed to send SYNC packet, may not have populated
      // socket __sk_common.{skc_rcv_saddr, ...}
      return 0;
  }

  // pull in details
  struct sock *skp = *skpp;
  struct ipv4_tuple_t t = { };
  if (!read_ipv4_tuple(&t, skp)) {
      return 0;
  }

  struct pid_comm_t p = { };
  p.pid = pid;
  bpf_get_current_comm(&p.comm, sizeof(p.comm));

  tuplepid_ipv4.update(&t, &p);

  return 0;
}

int trace_connect_v6_entry(struct pt_regs *ctx, struct sock *sk)
{
  if (container_should_be_filtered()) {
    return 0;
  }
  u64 pid = bpf_get_current_pid_tgid();

  ##FILTER_PID##
  u16 family = sk->__sk_common.skc_family;
  ##FILTER_FAMILY##

  // stash the sock ptr for lookup on return
  connectsock.update(&pid, &sk);

  return 0;
}

int trace_connect_v6_return(struct pt_regs *ctx)
{
  int ret = PT_REGS_RC(ctx);
  u64 pid = bpf_get_current_pid_tgid();

  struct sock **skpp;
  skpp = connectsock.lookup(&pid);
  if (skpp == 0) {
      return 0;       // missed entry
  }

  connectsock.delete(&pid);

  if (ret != 0) {
      // failed to send SYNC packet, may not have populated
      // socket __sk_common.{skc_rcv_saddr, ...}
      return 0;
  }

  // pull in details
  struct sock *skp = *skpp;
  struct ipv6_tuple_t t = { };
  if (!read_ipv6_tuple(&t, skp)) {
      return 0;
  }

  struct pid_comm_t p = { };
  p.pid = pid;
  bpf_get_current_comm(&p.comm, sizeof(p.comm));

  tuplepid_ipv6.update(&t, &p);

  return 0;
}

int trace_tcp_set_state_entry(struct pt_regs *ctx, struct sock *skp, int state)
{
  if (state != TCP_ESTABLISHED && state != TCP_CLOSE) {
      return 0;
  }

  u16 family = skp->__sk_common.skc_family;
  ##FILTER_FAMILY##
  
  u8 ipver = 0;
  if (check_family(skp, AF_INET)) {
      ipver = 4;
      struct ipv4_tuple_t t = { };
      if (!read_ipv4_tuple(&t, skp)) {
          return 0;
      }

      if (state == TCP_CLOSE) {
          tuplepid_ipv4.delete(&t);
          return 0;
      }

      struct pid_comm_t *p;
      p = tuplepid_ipv4.lookup(&t);
      if (p == 0) {
          return 0;       // missed entry
      }

      struct tcp_ipv4_event_t evt4 = { };
      evt4.ts_ns = bpf_ktime_get_ns();
      evt4.type = TCP_EVENT_TYPE_CONNECT;
      evt4.pid = p->pid >> 32;
      evt4.ip = ipver;
      evt4.saddr = t.saddr;
      evt4.daddr = t.daddr;
      evt4.sport = ntohs(t.sport);
      evt4.dport = ntohs(t.dport);
      evt4.netns = t.netns;

      int i;
      for (i = 0; i < TASK_COMM_LEN; i++) {
          evt4.comm[i] = p->comm[i];
      }

      tcp_ipv4_event.perf_submit(ctx, &evt4, sizeof(evt4));
      tuplepid_ipv4.delete(&t);
  } else if (check_family(skp, AF_INET6)) {
      ipver = 6;
      struct ipv6_tuple_t t = { };
      if (!read_ipv6_tuple(&t, skp)) {
          return 0;
      }

      if (state == TCP_CLOSE) {
          tuplepid_ipv6.delete(&t);
          return 0;
      }

      struct pid_comm_t *p;
      p = tuplepid_ipv6.lookup(&t);
      if (p == 0) {
          return 0;       // missed entry
      }

      struct tcp_ipv6_event_t evt6 = { };
      evt6.ts_ns = bpf_ktime_get_ns();
      evt6.type = TCP_EVENT_TYPE_CONNECT;
      evt6.pid = p->pid >> 32;
      evt6.ip = ipver;
      evt6.saddr = t.saddr;
      evt6.daddr = t.daddr;
      evt6.sport = ntohs(t.sport);
      evt6.dport = ntohs(t.dport);
      evt6.netns = t.netns;

      int i;
      for (i = 0; i < TASK_COMM_LEN; i++) {
          evt6.comm[i] = p->comm[i];
      }

      tcp_ipv6_event.perf_submit(ctx, &evt6, sizeof(evt6));
      tuplepid_ipv6.delete(&t);
  }
  // else drop

  return 0;
}

int trace_close_entry(struct pt_regs *ctx, struct sock *skp)
{
  if (container_should_be_filtered()) {
    return 0;
  }

  u64 pid = bpf_get_current_pid_tgid();

  ##FILTER_PID##
  
  u16 family = skp->__sk_common.skc_family;
  ##FILTER_FAMILY##

  u8 oldstate = skp->sk_state;
  // Don't generate close events for connections that were never
  // established in the first place.
  if (oldstate == TCP_SYN_SENT ||
      oldstate == TCP_SYN_RECV ||
      oldstate == TCP_NEW_SYN_RECV)
      return 0;

  u8 ipver = 0;
  if (check_family(skp, AF_INET)) {
      ipver = 4;
      struct ipv4_tuple_t t = { };
      if (!read_ipv4_tuple(&t, skp)) {
          return 0;
      }

      struct tcp_ipv4_event_t evt4 = { };
      evt4.ts_ns = bpf_ktime_get_ns();
      evt4.type = TCP_EVENT_TYPE_CLOSE;
      evt4.pid = pid >> 32;
      evt4.ip = ipver;
      evt4.saddr = t.saddr;
      evt4.daddr = t.daddr;
      evt4.sport = ntohs(t.sport);
      evt4.dport = ntohs(t.dport);
      evt4.netns = t.netns;
      bpf_get_current_comm(&evt4.comm, sizeof(evt4.comm));

      tcp_ipv4_event.perf_submit(ctx, &evt4, sizeof(evt4));
  } else if (check_family(skp, AF_INET6)) {
      ipver = 6;
      struct ipv6_tuple_t t = { };
      if (!read_ipv6_tuple(&t, skp)) {
          return 0;
      }

      struct tcp_ipv6_event_t evt6 = { };
      evt6.ts_ns = bpf_ktime_get_ns();
      evt6.type = TCP_EVENT_TYPE_CLOSE;
      evt6.pid = pid >> 32;
      evt6.ip = ipver;
      evt6.saddr = t.saddr;
      evt6.daddr = t.daddr;
      evt6.sport = ntohs(t.sport);
      evt6.dport = ntohs(t.dport);
      evt6.netns = t.netns;
      bpf_get_current_comm(&evt6.comm, sizeof(evt6.comm));

      tcp_ipv6_event.perf_submit(ctx, &evt6, sizeof(evt6));
  }
  // else drop

  return 0;
};

int trace_accept_return(struct pt_regs *ctx)
{
  if (container_should_be_filtered()) {
    return 0;
  }

  struct sock *newsk = (struct sock *)PT_REGS_RC(ctx);
  u64 pid = bpf_get_current_pid_tgid();

  ##FILTER_PID##

  if (newsk == NULL) {
      return 0;
  }

  // pull in details
  u16 lport = 0, dport = 0;
  u32 net_ns_inum = 0;
  u8 ipver = 0;

  dport = newsk->__sk_common.skc_dport;
  lport = newsk->__sk_common.skc_num;

  // Get network namespace id, if kernel supports it
#ifdef CONFIG_NET_NS
  net_ns_inum = newsk->__sk_common.skc_net.net->ns.inum;
#endif

  ##FILTER_NETNS##
  
  u16 family = newsk->__sk_common.skc_family;
  ##FILTER_FAMILY##

  if (check_family(newsk, AF_INET)) {
      ipver = 4;

      struct tcp_ipv4_event_t evt4 = { 0 };

      evt4.ts_ns = bpf_ktime_get_ns();
      evt4.type = TCP_EVENT_TYPE_ACCEPT;
      evt4.netns = net_ns_inum;
      evt4.pid = pid >> 32;
      evt4.ip = ipver;

      evt4.saddr = newsk->__sk_common.skc_rcv_saddr;
      evt4.daddr = newsk->__sk_common.skc_daddr;

      evt4.sport = lport;
      evt4.dport = ntohs(dport);
      bpf_get_current_comm(&evt4.comm, sizeof(evt4.comm));

      // do not send event if IP address is 0.0.0.0 or port is 0
      if (evt4.saddr != 0 && evt4.daddr != 0 &&
          evt4.sport != 0 && evt4.dport != 0) {
          tcp_ipv4_event.perf_submit(ctx, &evt4, sizeof(evt4));
      }
  } else if (check_family(newsk, AF_INET6)) {
      ipver = 6;

      struct tcp_ipv6_event_t evt6 = { 0 };

      evt6.ts_ns = bpf_ktime_get_ns();
      evt6.type = TCP_EVENT_TYPE_ACCEPT;
      evt6.netns = net_ns_inum;
      evt6.pid = pid >> 32;
      evt6.ip = ipver;

      bpf_probe_read_kernel(&evt6.saddr, sizeof(evt6.saddr),
                     newsk->__sk_common.skc_v6_rcv_saddr.in6_u.u6_addr32);
      bpf_probe_read_kernel(&evt6.daddr, sizeof(evt6.daddr),
                     newsk->__sk_common.skc_v6_daddr.in6_u.u6_addr32);

      evt6.sport = lport;
      evt6.dport = ntohs(dport);
      bpf_get_current_comm(&evt6.comm, sizeof(evt6.comm));

      // do not send event if IP address is 0.0.0.0 or port is 0
      if (evt6.saddr != 0 && evt6.daddr != 0 &&
          evt6.sport != 0 && evt6.dport != 0) {
          tcp_ipv6_event.perf_submit(ctx, &evt6, sizeof(evt6));
      }
  }
  // else drop

  return 0;
}
"""

verbose_types = {"C": "connect", "A": "accept",
                 "X": "close", "U": "unknown"}

#added by Girasolo
def fill_string_to_bytes(input_string, target_bytes, fill_character=' '):
    """
    Fill a string to reach a certain number of bytes (not used)
    """
    current_bytes = len(input_string.encode())
    if current_bytes >= target_bytes:
        return input_string
    else:
        fill_count = target_bytes - current_bytes
        filled_string = input_string + fill_character * fill_count
        return filled_string
#

def print_ipv4_event(cpu, data, size):
    event = b["tcp_ipv4_event"].event(data)
    global start_ts

    #added by Girasolo
    global tdif1                                                            # Used to calculate the difference of time between a open/accept/close event and the next
    global tbef1
    if args.file:                                                           # Print on file
        if args.timestamp:
            if start_ts == 0:
                start_ts = event.ts_ns
                #added by Girasolo
                tdif1 = 0
                tbef1 = (event.ts_ns - start_ts) / 1000000000.0
            else:
                tdif1 = ((event.ts_ns - start_ts) / 1000000000.0 ) - tbef1
                tbef1 = ((event.ts_ns - start_ts) / 1000000000.0 )
            if args.verbose:
                #f.write("%-14d" % (event.ts_ns - start_ts))
                f.write("%-14d" % (tdif1*1000000000.0))
            else:
                #f.write("%-9.3f" % ((event.ts_ns - start_ts) / 1000000000.0))
                f.write("%-9.3f" % (tdif1))
                #
        if event.type == 1:
            type_str = "C"
        elif event.type == 2:
            type_str = "A"
        elif event.type == 3:
            type_str = "X"
        else:
            type_str = "U"

        if args.verbose:
            f.write("%-12s " % (verbose_types[type_str]))
        else:
            f.write("%-2s " % (type_str))

        f.write("%-6d %-16s %-2d %-16s %-16s %-6d %-6d" %
            (event.pid, event.comm.decode('utf-8', 'replace'),
            event.ip,
            inet_ntop(AF_INET, pack("I", event.saddr)),
            inet_ntop(AF_INET, pack("I", event.daddr)),
            event.sport,
            event.dport))
        if args.verbose and not args.netns:
            f.write(" %-8d" % event.netns)
        else:
            f.write("\n")
    elif args.socketconnection:                                              # Print on socket channel
        global client_socket
        message = ""
        if args.timestamp:
            if start_ts == 0:
                start_ts = event.ts_ns
                #added by Girasolo
                tdif1 = 0
                tbef1 = (event.ts_ns - start_ts) / 1000000000.0
            else:
                tdif1 = ((event.ts_ns - start_ts) / 1000000000.0 ) - tbef1
                tbef1 = ((event.ts_ns - start_ts) / 1000000000.0 )
            if args.verbose:
                #f.write("%-14d" % (event.ts_ns - start_ts))
                message = message + ("%-14d" % (tdif1*1000000000.0))
            else:
                #f.write("%-9.3f" % ((event.ts_ns - start_ts) / 1000000000.0))
                message = message + ("%-9.3f" % (tdif1))
                #
        if event.type == 1:
            type_str = "C"
        elif event.type == 2:
            type_str = "A"
        elif event.type == 3:
            type_str = "X"
        else:
            type_str = "U"

        if args.verbose:
            message = message + ("%-12s " % (verbose_types[type_str]))
        else:
            message = message + ("%-2s " % (type_str))

        message = message + ("%-6d %-16s %-2d %-16s %-16s %-6d %-6d" %
            (event.pid, event.comm.decode('utf-8', 'replace'),
            event.ip,
            inet_ntop(AF_INET, pack("I", event.saddr)),
            inet_ntop(AF_INET, pack("I", event.daddr)),
            event.sport,
            event.dport))
        if args.verbose and not args.netns:
            message = message + (" %-8d" % event.netns)
        else:
            message = message + ("\n")
        try:
            #message = fill_string_to_bytes(message, 15)
            client_socket.sendall(message.encode())                         # Send the entry
        except OSError as e:
            print("Socket error:", e)
        # Handle the error gracefully, possibly by closing the socket and/or retrying

    else:
        if args.timestamp:
            if start_ts == 0:
                start_ts = event.ts_ns
                #added by Girasolo
                tdif1 = 0
                tbef1 = (event.ts_ns - start_ts) / 1000000000.0
            else:
                tdif1 = ((event.ts_ns - start_ts) / 1000000000.0 ) - tbef1
                tbef1 = ((event.ts_ns - start_ts) / 1000000000.0 )
            if args.verbose:
                #print("%-14d" % (event.ts_ns - start_ts), end="")
                print("%-14d" % (tdif1*1000000000.0), end="")
            else:
                #print("%-9.3f" % ((event.ts_ns - start_ts) / 1000000000.0), end="")
                print("%-9.3f" % (tdif1), end="")
        if event.type == 1:
            type_str = "C"
        elif event.type == 2:
            type_str = "A"
        elif event.type == 3:
            type_str = "X"
        else:
            type_str = "U"

        if args.verbose:
            print("%-12s " % (verbose_types[type_str]), end="")
        else:
            print("%-2s " % (type_str), end="")

        print("%-6d %-16s %-2d %-16s %-16s %-6d %-6d" %
            (event.pid, event.comm.decode('utf-8', 'replace'),
            event.ip,
            inet_ntop(AF_INET, pack("I", event.saddr)),
            inet_ntop(AF_INET, pack("I", event.daddr)),
            event.sport,
            event.dport), end="")
        if args.verbose and not args.netns:
            print(" %-8d" % event.netns)
        else:
            print()


def print_ipv6_event(cpu, data, size):
    event = b["tcp_ipv6_event"].event(data)
    global start_ts
    if args.timestamp:
        if start_ts == 0:
            start_ts = event.ts_ns
        if args.verbose:
            print("%-14d" % (event.ts_ns - start_ts), end="")
        else:
            print("%-9.3f" % ((event.ts_ns - start_ts) / 1000000000.0), end="")
    if event.type == 1:
        type_str = "C"
    elif event.type == 2:
        type_str = "A"
    elif event.type == 3:
        type_str = "X"
    else:
        type_str = "U"

    if args.verbose:
        print("%-12s " % (verbose_types[type_str]), end="")
    else:
        print("%-2s " % (type_str), end="")

    print("%-6d %-16s %-2d %-16s %-16s %-6d %-6d" %
          (event.pid, event.comm.decode('utf-8', 'replace'),
           event.ip,
           "[" + inet_ntop(AF_INET6, event.saddr) + "]",
           "[" + inet_ntop(AF_INET6, event.daddr) + "]",
           event.sport,
           event.dport), end="")
    if args.verbose and not args.netns:
        print(" %-8d" % event.netns)
    else:
        print()

#added by Girasolo
def send_interrupt(time):
    """
    Close the program after time secs
    """
    def handler(signum, frame):
        print("Timeout reached. Sending KeyboardInterrupt.")
        raise KeyboardInterrupt
  
    signal.signal(signal.SIGALRM, handler)                                      # Set up the signal handler for SIGALRM   
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
    global start_ts
    if signum == signal.SIGTERM:
        f.close()
        print("trace terminates here")
    elif signum == signal.SIGUSR1:
        print("New file")
        f.close()
        timestamp = datetime.now().strftime("%y%m%d_%H:%M:%S")
        f = open(f"trace{timestamp}.txt", 'a')
        if args.verbose:
            if args.timestamp:
                f.write("%-14s" % ("TIME(ns)"), end="")
            f.write("%-12s %-6s %-16s %-2s %-16s %-16s %-6s %-7s" % ("TYPE",
                "PID", "COMM", "IP", "SADDR", "DADDR", "SPORT", "DPORT"))
            if not args.netns:
                f.write("%-8s" % "NETNS")
            f.write("\n")
        else:
            if args.timestamp:
                f.write("%-9s" % ("TIME(s)"))
            f.write("%-2s %-6s %-16s %-2s %-16s %-16s %-6s %-6s" %
                ("T", "PID", "COMM", "IP", "SADDR", "DADDR", "SPORT", "DPORT"))
            f.write("\n")

        start_ts = 0
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
    global start_ts
    if signum == signal.SIGTERM:
        client_socket.close()
        print("life terminates here")
    if signum == signal.SIGUSR1:
        print("TRACER (pid: ", os.getpid(), ")RECEIVED THE SIGNAL SIGUSR1")
        separation = "SIGNAL HERE ---\n"
        start_ts = 0 #??? should it be reset or not? better continuity?             # Every 25 seconds the starting time of the open/accept/close event is reset, so the first event is always at time 0
        #separation = fill_string_to_bytes(separation, 15)
        client_socket.send(separation.encode())   
    else: 
        print("sig not handled")
#

pid_filter = ""
netns_filter = ""

if args.pid:
    pid_filter = 'if (pid >> 32 != %d) { return 0; }' % args.pid
if args.netns:
    netns_filter = 'if (net_ns_inum != %d) { return 0; }' % args.netns
if args.ipv4:
    bpf_text = bpf_text.replace('##FILTER_FAMILY##',
        'if (family != AF_INET) { return 0; }')
elif args.ipv6:
    bpf_text = bpf_text.replace('##FILTER_FAMILY##',
        'if (family != AF_INET6) { return 0; }')
bpf_text = bpf_text.replace('##FILTER_FAMILY##', '')
bpf_text = bpf_text.replace('##FILTER_PID##', pid_filter)
bpf_text = bpf_text.replace('##FILTER_NETNS##', netns_filter)
bpf_text = filter_by_containers(args) + bpf_text

#added by Girasolo
if args.file: 
    f = open(args.file, 'a')                                                # Open the first file
#

if args.ebpf:
    print(bpf_text)
    exit()
#added by Girasolo
if args.socketconnection:  
    
    HOST = '127.0.0.1'                                                      # Define host and port (the same as 1clock)
    PORT = 65433
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       # Create and connect socket to the server (1clock)
    client_socket.connect((HOST, PORT))   
#

# initialize BPF
b = BPF(text=bpf_text)
if args.ipv4:
    b.attach_kprobe(event="tcp_v4_connect", fn_name="trace_connect_v4_entry")
    b.attach_kretprobe(event="tcp_v4_connect", fn_name="trace_connect_v4_return")
elif args.ipv6:
    b.attach_kprobe(event="tcp_v6_connect", fn_name="trace_connect_v6_entry")
    b.attach_kretprobe(event="tcp_v6_connect", fn_name="trace_connect_v6_return")
else:
    b.attach_kprobe(event="tcp_v4_connect", fn_name="trace_connect_v4_entry")
    b.attach_kretprobe(event="tcp_v4_connect", fn_name="trace_connect_v4_return")
    b.attach_kprobe(event="tcp_v6_connect", fn_name="trace_connect_v6_entry")
    b.attach_kretprobe(event="tcp_v6_connect", fn_name="trace_connect_v6_return")
b.attach_kprobe(event="tcp_set_state", fn_name="trace_tcp_set_state_entry")
b.attach_kprobe(event="tcp_close", fn_name="trace_close_entry")
b.attach_kretprobe(event="inet_csk_accept", fn_name="trace_accept_return")

#added by Girasolo
if args.file: 
    f.write("Tracing TCP established connections. Ctrl-C to end.\n")
else:
    print("Tracing TCP established connections. Ctrl-C to end.")

# header
#added by GIrasolo
if args.file:
    if args.verbose:
        if args.timestamp:
            f.write("%-14s" % ("TIME(ns)"), end="")
        f.write("%-12s %-6s %-16s %-2s %-16s %-16s %-6s %-7s" % ("TYPE",
            "PID", "COMM", "IP", "SADDR", "DADDR", "SPORT", "DPORT"))
        if not args.netns:
            f.write("%-8s" % "NETNS")
        f.write("\n")
    else:
        if args.timestamp:
            f.write("%-9s" % ("TIME(s)"))
        f.write("%-2s %-6s %-16s %-2s %-16s %-16s %-6s %-6s" %
            ("T", "PID", "COMM", "IP", "SADDR", "DADDR", "SPORT", "DPORT"))
        f.write("\n")

    start_ts = 0
elif args.socketconnection:
    print("useless headers")
    start_ts = 0
else:
    #
    if args.verbose:
        if args.timestamp:
            print("%-14s" % ("TIME(ns)"), end="")
        print("%-12s %-6s %-16s %-2s %-16s %-16s %-6s %-7s" % ("TYPE",
            "PID", "COMM", "IP", "SADDR", "DADDR", "SPORT", "DPORT"), end="")
        if not args.netns:
            print("%-8s" % "NETNS", end="")
        print()
    else:
        if args.timestamp:
            print("%-9s" % ("TIME(s)"), end="")
        print("%-2s %-6s %-16s %-2s %-16s %-16s %-6s %-6s" %
            ("T", "PID", "COMM", "IP", "SADDR", "DADDR", "SPORT", "DPORT"))

    start_ts = 0



b["tcp_ipv4_event"].open_perf_buffer(print_ipv4_event)
b["tcp_ipv6_event"].open_perf_buffer(print_ipv6_event)

#added by Girasolo
if args.file:                                                               # Signal handler for file
    print("tracer starts here")
    signal.signal(signal.SIGUSR1, handlerFile)
    signal.signal(signal.SIGTERM, handlerFile)
#    send_interrupt(25)
#


#added by Girasolo
if args.socketconnection:                                                   # Signal handler for socket
    print("handler here")
    signal.signal(signal.SIGUSR1, handlerSocket)
    signal.signal(signal.SIGTERM, handlerSocket)
#
while True:
    try:
        b.perf_buffer_poll()
    except KeyboardInterrupt:
        #added by Girasolo
        if args.file:
            f.close()
        #
        exit()

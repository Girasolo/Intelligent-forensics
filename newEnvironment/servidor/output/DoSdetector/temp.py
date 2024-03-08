from bcc import BPF

# Specify the eBPF program as a string
ebpf_code = """
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/in.h>
#include <linux/pkt_cls.h>
#include <linux/list.h>
#include <linux/rbtree.h>
#include <linux/refcount.h>
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/ipv6.h>
#include <linux/tcp.h>
#include <linux/in.h>
#include <linux/pkt_cls.h>


SEC("tc")
int flat(struct __sk_buff* skb) {
    bpf_printk("Got a Packet!\\n");

    return 0;
}

char _license[] SEC("license") = "GPL";
"""

# Create the BPF object and load the eBPF program
b = BPF(text=ebpf_code)

# Attach the eBPF program to a tracepoint (example)
b.attach_tracepoint(tp="sched:sched_switch", fn_name="flat")

# Keep the script running to capture events (Ctrl+C to exit)
try:
    b.trace_print()
except KeyboardInterrupt:
    pass
finally:
    # Detach the eBPF program when done (optional)
    b.detach_tracepoint(tp="sched:sched_switch")


#include "network.h"
#include <bcc/proto.h>
#include <linux/pkt_cls.h>
#include <linux/in.h>
#include <linux/udp.h>

BPF_HISTOGRAM(counter, u64);

int udp_counter(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    struct ethhdr *eth = data;

    
    if ((void *)eth + sizeof(*eth) <= data_end)
    {

        struct iphdr *ip = data + sizeof(*eth);
        if ((void *)ip + sizeof(*ip) <= data_end)
        {

            if (ip->protocol == IPPROTO_UDP)
            {

                struct udphdr *udp = (void *)ip + sizeof(*ip);
                if ((void *)udp + sizeof(*udp) <= data_end)
                {
                    bpf_trace_printk("Got udp packet");	
                    u64 value = htons(udp->dest);
                    counter.increment(value);
                }
            }
        }
    }
    return XDP_PASS;
}

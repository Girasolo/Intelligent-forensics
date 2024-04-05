#include "network.h"
#include <bcc/proto.h>
#include <linux/pkt_cls.h>
#include <linux/in.h>
#include <linux/udp.h>


struct _packet{
    __u32 src_ip;
    __u32 dst_ip;
    __u8 protocol;
    __u64 timestamp;
    // Add other fields as needed
};

BPF_HASH(packet_info_map, u64, struct _packet);

int udp_counter(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    struct ethhdr *eth = data;

    
    if ((void *)eth + sizeof(*eth) <= data_end)
    {

        struct iphdr *iph = data + sizeof(*eth);
        if ((void *)iph + sizeof(*iph) <= data_end)
        {
		
		struct _packet packet;
		// Get source and destination IP addresses
    		packet.src_ip = iph->saddr;
    		packet.dst_ip = iph->daddr;

    		// Get the transport protocol
    		packet.protocol = iph->protocol;

    		// Get timestamp
    		packet.timestamp = bpf_ktime_get_ns();
    		//bpf_trace_printk("Packet: src_ip=%u, dst_ip=%u, ", packet.src_ip, packet.dst_ip);
    		//bpf_trace_printk("protocol=%u, timestamp=%llu\n", packet.protocol, packet.timestamp);
    	
    		packet_info_map.update(&packet.timestamp, &packet);
	
        }
    }
    return XDP_PASS;
}






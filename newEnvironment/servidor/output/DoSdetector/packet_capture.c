// Include necessary header files for eBPF, XDP, and networking
#include "network.h"
#include <bcc/proto.h>
#include <linux/pkt_cls.h>
#include <linux/in.h>
#include <linux/udp.h>




struct packet{
    __u32 src_ip;
    __u32 dst_ip;
    __u8 protocol;
    __u64 timestamp;
    // Add other fields as needed
};

BPF_HASH(packet_info_map, u64, struct packet);



int packet_capture(struct xdp_md *ctx) {
    
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    
    struct ethhdr *eth = data;
    
    if (data + sizeof(struct ethhdr) > data_end)
    	return XDP_ABORTED;
    	
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
	return XDP_PASS;


    struct iphdr *iph = data + sizeof(struct ethhdr);
    if (data + sizeof(struct ethhdr) + sizeof(struct iphdr) > data_end)
    	return XDP_ABORTED;
    	
    	
    
    struct packet packet;
    // Get source and destination IP addresses
    packet.src_ip = iph->saddr;
    packet.dst_ip = iph->daddr;

    // Get the transport protocol
    packet.protocol = iph->protocol;

    // Get timestamp
    packet.timestamp = bpf_ktime_get_ns();

    // TODO: Extract other information like TCP/UDP ports, payload, etc.

    // Send data to user space
    //packet_info_map.update(&packet.timestamp, &packet);
    //bpf_perf_event_output(ctx, &packet_info_map, BPF_F_CURRENT_CPU, &packet, sizeof(struct packet));


    return 0;
}


#include <linux/bpf.h>
#include <linux/types.h>
#include <linux/ptrace.h>

#define SEC(NAME) __attribute__((section(NAME), used))

SEC("tracepoint/syscalls/sys_enter_execve")
int hello_ebpf(void *ctx) {
    bpf_trace_printk("Hello, eBPF!\n");
    return 0;
}

char _license[] SEC("license") = "GPL";

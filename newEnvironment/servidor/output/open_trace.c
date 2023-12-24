#include <linux/bpf.h>
#include <linux/version.h>
#include <linux/types.h>
#include <bpf/bpf_helpers.h>
struct bpf_map_def SEC("maps") syscall_count = {
    .type = BPF_MAP_TYPE_ARRAY,
    .key_size = sizeof(__u32),
    .value_size = sizeof(__u64),
    .max_entries = 1024, /* Adjust this value based on your needs */
};
SEC("tracepoint/syscalls/sys_enter_execve")
int trace_sys_enter_execve(struct pt_regs *ctx) {
    __u32 key = 0;
    __u64 *count;
    count = bpf_map_lookup_elem(&syscall_count, &key);
    if (count) {
        (*count)++;
    }
    return 0;
}
char _license[] SEC("license") = "GPL";
__u32 _version SEC("version") = LINUX_VERSION_CODE;

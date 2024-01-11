#!/bin/bash

apt-get install -y linux-headers-$(uname -r)

mount -t debugfs none /sys/kernel/debug

/bin/sleep infinity

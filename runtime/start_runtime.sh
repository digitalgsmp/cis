

#!/bin/bash

source /mnt/projects/cis/runtime/config/runtime.env

echo "Starting CIS Runtime..."

ollama serve > $CIS_LOG_PATH/ollama.log 2>&1 &

echo $! > $CIS_LOG_PATH/ollama.pid

echo "CIS Runtime started"

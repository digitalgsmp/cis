

#!/bin/bash

if ps -p $(cat /mnt/projects/cis/logs/ollama.pid) > /dev/null
then
    echo "CIS Runtime is RUNNING"
else
    echo "CIS Runtime is STOPPED"
fi

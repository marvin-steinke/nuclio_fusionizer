#!/bin/bash

# Set up environment variable ARGS
ARGS=""

# Check if each environment variable is set and add to ARGS
if [[ -n $ADDRESS ]]; then
  ARGS+=" -a $ADDRESS"
fi
if [[ -n $PLATFORM ]]; then
  ARGS+=" -p $PLATFORM"
fi
if [[ -n $REGISTRY ]]; then
  ARGS+=" -r $REGISTRY"
fi
if [[ -n $NAMESPACE ]]; then
  ARGS+=" -n $NAMESPACE"
fi
if [[ -n $KUBECONFIG ]]; then
  ARGS+=" -k $KUBECONFIG"
fi
if [[ -n $CONFIG ]]; then
  ARGS+=" -c $CONFIG"
fi
if [[ -n $WORKERS ]]; then
  ARGS+=" -w $WORKERS"
fi

# Wait a bit for the config file
sleep 1

# Run command to start app when container launches with params
# Also use exec so ctrl+c works
exec python ./nuclio_fusionizer/main.py $ARGS

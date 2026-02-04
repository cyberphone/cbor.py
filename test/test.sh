#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <python-file.py>"
    exit 1
fi
pushd $(dirname "${BASH_SOURCE[0]}")
export PYTHONPATH=../src
python3 $1
popd

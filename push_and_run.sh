#!/bin/sh

HOST=cube@10.0.0.11
DIR=robomower2

rsync -a --delete . $HOST:$DIR
ssh -XY $HOST "cd $DIR/src_python ; ./main.py"

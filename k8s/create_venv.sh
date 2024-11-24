#!/usr/bin/env sh

VENVDIR=.venv
KUBESPRAYDIR=kubespray
python3 -m venv $VENVDIR
. $VENVDIR/bin/activate
pip install -U -r $KUBESPRAYDIR/requirements.txt

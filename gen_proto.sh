#!/usr/bin/env sh
PROTO_PATH='proto/'
PYTHON_OUT='dicty/proto'

protos="$(find "$PROTO_PATH" -type f -name '*.proto')"

python -m grpc_tools.protoc \
	--proto_path="$PROTO_PATH" \
	--python_out="$PYTHON_OUT" \
	--pyi_out="$PYTHON_OUT" \
	--grpc_python_out="$PYTHON_OUT" $protos  &&
	mv "$PYTHON_OUT/dicty"/* "$PYTHON_OUT" &&
	rmdir "$PYTHON_OUT/dicty/"

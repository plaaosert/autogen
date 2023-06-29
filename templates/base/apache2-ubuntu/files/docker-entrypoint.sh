#!/bin/bash
set -eo pipefail
shopt -s nullglob

# REPLACE ME TO EDIT DOCKER STARTUP

_main() {
  exec "$@"
}

if ! _is_sourced; then
	_main "$@"
fi

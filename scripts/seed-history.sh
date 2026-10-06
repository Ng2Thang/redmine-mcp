#!/usr/bin/env bash
# Compatibility command. The common runner owns all seed modes and safety checks.
exec bash "$(dirname -- "$0")/seed.sh" history "$@"

#!/usr/bin/env bash
# Quick launch wrapper for Udyog Sathi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/build.sh" "$@"

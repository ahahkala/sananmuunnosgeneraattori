#!/bin/sh
cd "$(dirname "$0")/web" && exec python -m http.server 8000

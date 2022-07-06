#!/bin/bash

COMMAND=${1:-webserver}

if [[ "$COMMAND" == ingestion ]]; then
    exec python3 src/ingestion.py
else
    exec uvicorn main:app --app-dir src --reload-exclude pgdata --reload --host 0.0.0.0
fi;

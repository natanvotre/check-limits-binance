#!/bin/bash

COMMAND=${1:-webserver}

if [[ "$COMMAND" == ingestion ]]; then
    exec python src/ingestion.py
if [[ "$COMMAND" == tests ]]; then
    exec pytest src/tests/*
else
    exec uvicorn main:app --app-dir src --reload-exclude pgdata --reload
fi;

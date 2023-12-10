#!/bin/bash

set -e

cmd="$@"

if [ "${IS_DJANGO_SERVICE}" == "True" ]; then
  echo "Waiting for the database to become available..."
  until python3 manage.py migrate; do
    echo "Database is unavailable, sleeping for 5 seconds..."
  done
else
  sleep 30
fi

exec $cmd

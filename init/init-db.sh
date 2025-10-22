#!/bin/bash
set -e
createdb -U "$POSTGRES_USER" dvdrental
pg_restore -U "$POSTGRES_USER" -d dvdrental /docker-entrypoint-initdb.d/dvdrental.tar
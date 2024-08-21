#! /bin/bash

echo "Initialising the database"

# Ensure we are within the docker container
if [ ! -f /.dockerenv ]; then
    echo "This script should be run within the docker container"
    exit 1
fi

# Run the create-db.sh script to create the database and tables.
psql -U $POSTGRES_USER -d $POSTGRES_DB -a -f /sql/init.sql

echo "Database initialised successfully"
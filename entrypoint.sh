#!/bin/sh

if [ "$DATABASE" = "database" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done
    
    #python manage.py create_db
    #python manage.py seed_db
    echo "PostgreSQL started"
fi

exec "$@"
createuser:
	psql -c "CREATE USER glommer WITH PASSWORD 'glommer';" postgres postgres

createdb:
	psql -c "CREATE DATABASE glommer_dev WITH OWNER glommer TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8';" postgres postgres
	psql -c "CREATE DATABASE glommer_test WITH OWNER glommer TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8';" postgres postgres

dropdb:
	psql -c "DROP DATABASE IF EXISTS glommer_dev;" postgres postgres
	psql -c "DROP DATABASE IF EXISTS glommer_test;" postgres postgres


requirements:
	pip-compile --output-file requirements.txt requirements.in

serve:
	python manage.py runserver $(C9_IP):$(C9_PORT)

pgweb:
	pgweb --bind=$(C9_IP) --url $(DATABASE_URL) --skip-open

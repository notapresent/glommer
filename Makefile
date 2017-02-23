createdb:
	psql -c "CREATE DATABASE glommer_dev WITH OWNER glommer TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8';" postgres
	psql -c "CREATE DATABASE glommer_test WITH OWNER glommer TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8';" postgres

dropdb:
	psql -c "DROP DATABASE IF EXISTS glommer_dev;" postgres
	psql -c "DROP DATABASE IF EXISTS glommer_test;" postgres


requirements:
	pip-compile --output-file requirements.txt requirements.in

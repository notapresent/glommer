IP ?= 127.0.0.1
PORT ?= 8080

createuser:
	psql -c "CREATE USER glommer WITH PASSWORD 'glommer';" postgres glommer

createdb:
	psql -c "CREATE DATABASE glommer WITH OWNER glommer TEMPLATE template0 ENCODING 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8';" postgres glommer

dropdb:
	psql -c "DROP DATABASE IF EXISTS glommer;" postgres glommer

requirements:
	pip-compile --output-file requirements.txt requirements.in

serve:
	python manage.py runserver $(IP):$(PORT)

pgweb:
	pgweb --bind=$(C9_IP) --url $(DATABASE_URL) --skip-open

scrape:
	python -u manage.py scrape

test:
	python manage.py test --keepdb --settings glommer.test_settings

autotest:
	find . -name '*.py' -not -path '*/\.*' | entr -d -c  python manage.py test --keepdb --settings glommer.test_settings

coverage:
	coverage run manage.py test --keepdb --settings glommer.test_settings
	coverage report --skip-covered


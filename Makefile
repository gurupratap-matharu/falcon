APP_LIST ?= blog main pages users 
.PHONY: collectstatic run test ci install install-dev migrations staticfiles

help:
	@echo "Available commands"
	@echo " - ci               : lints, migrations, tests, coverage"
	@echo " - install          : installs production requirements"
	@echo " - install-dev      : installs development requirements"
	@echo " - isort            : sorts all imports of the project"
	@echo " - lint             : lints the codebase"
	@echo " - run              : runs the development server"
	@echo " - setup-test-data  : erases the db and loads mock data"
	@echo " - shellplus        : runs the development shell"

collectstatic:
	python manage.py collectstatic --noinput

clean:
	rm -rf __pycache__ .pytest_cache

check:
	python manage.py check

check-deploy:
	python manage.py check --deploy

install:
	poetry install

update:
	poetry update
	
setup_test_data:
	python manage.py setup_test_data
	
shellplus:
	python manage.py shell_plus

shell:
	python manage.py shell

showmigrations:
	python manage.py showmigrations

makemigrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

migrations-check:
	python manage.py makemigrations --check --dry-run

isort:
	isort $(APP_LIST)

lint: isort
	flake8 $(APP_LIST)

test: migrations-check
	python -Wa manage.py test -v 2

ci: lint test
	coverage run --source='.' manage.py test
	coverage html

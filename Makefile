.PHONY: setup update fmt check

PM=python manage.py

setup:
	poetry install --no-root

update:
	poetry update

fmt:
	isort .
	ruff format .
	djlint --reformat templates/

check:
	isort --check .
	ruff check .

runserver:
	$(PM) runserver 0.0.0.0:8000

migrate:
	$(PM) migrate

migrations:
	$(PM) makemigrations

shell:
	$(PM) shell

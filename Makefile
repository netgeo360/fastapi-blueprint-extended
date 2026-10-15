.PHONY: test

OUTPUT ?= ./my_project

test:
	cd src/app && python -m pytest --cov=. --cov-report=term-missing

ruff:
	cd src/app && ruff check . --fix; ruff format .

pre_commit:
	cd src/app && pre-commit run --all-files

generate_force:
	PYTHONPATH=src python src/app/run.py --spec src/app/sample_project.yaml --output $(OUTPUT) --force

generate:
	PYTHONPATH=src python src/app/run.py --spec src/app/sample_project.yaml --output $(OUTPUT)
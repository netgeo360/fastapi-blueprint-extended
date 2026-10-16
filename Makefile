.PHONY: test

OUTPUT ?= ./my_project

test:
	cd src/app && python -m pytest --cov=. --cov-report=term-missing

lint:
	ruff check . --fix; ruff format .

pre_commit:
	pre-commit run --all-files

generate_force:
	python -m pip install -e . && fastapi-blueprint-extended --spec src/app/input_yaml/sample_project.yaml --output $(OUTPUT) --force
generate:
	python -m pip install -e . && fastapi-blueprint-extended --spec src/app/input_yaml/sample_project.yaml --output $(OUTPUT)

	
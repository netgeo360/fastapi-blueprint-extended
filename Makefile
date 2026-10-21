.PHONY: test

OUTPUT ?= ./my_project

unit_test_codebase:
	python -m pip install -e . && cd src/app && python -m pytest --cov=. --cov-report=term-missing

unit_test_generated_project:
	python -m pip install -e . && \
	fastapi-blueprint-extended --spec src/app/input_yaml/sample_project.yaml --output "$(OUTPUT)" --force && \
	cd "$(OUTPUT)" && \
	python -m pip install -r app/requirements.txt && \
	python -m pytest --cov=app --cov-report=term-missing


lint:
	ruff check . --fix; ruff format .

pre_commit:
	pre-commit run --all-files

generate_force:
	python -m pip install -e . && fastapi-blueprint-extended --spec src/app/input_yaml/sample_project.yaml --output $(OUTPUT) --force
generate:
	python -m pip install -e . && fastapi-blueprint-extended --spec src/app/input_yaml/sample_project.yaml --output $(OUTPUT)

# fastapi-blueprint-extended
Define your API blueprint in YAML. fastapi-blueprint generates the full project structure, Docker setup, and tests. This extended version of https://github.com/netgeo360/fastapi-blueprint

# Instructions 

`python src/app/run.py --spec /src/app/sample_project.yaml --output ./my_project`

`python src/app/run.py --spec src/app/sample_project.yaml --output ./my_project --force`

# Formatting

`autoflake --in-place --remove-all-unused-imports --expand-star-imports . && isort . && black .`

Or shorter

`ruff check . --fix; ruff format .`

# Pre-commit check

Run and activate the hook

`pre-commit install`

and for check locally run

`pre-commit run --all-files`
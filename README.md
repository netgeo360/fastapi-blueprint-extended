# fastapi-blueprint-extended

Define your API specification in YAML, and `fastapi-blueprint-extended` will generate the project structure, Docker configuration, and tests. This project extends [fastapi-blueprint](https://github.com/netgeo360/fastapi-blueprint).

## Local development setup

We recommend creating a Python virtual environment before working with the project. You can use [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/stable/install.html) or Python’s built-in [`venv`](https://docs.python.org/3/library/venv.html) module.

After creating and activating the environment, install the project dependencies from the repository root:

```bash
pip install -r requirements.txt
```

## Usage

Create a YAML file containing your desired API specification. See [`sample_project.yaml`](src/app/sample_project.yaml) for an example.

The CLI provides two generation modes: **simple mode** and **force mode**.

### Simple mode

Use simple mode to generate a project for the first time:

```bash
python -m pip install -e . && fastapi-blueprint-extended --spec src/app/input_yaml/sample_project.yaml --output ./my_project
```

### Force mode

Use force mode to overwrite an existing generated project:

```bash
python -m pip install -e . && fastapi-blueprint-extended --spec src/app/input_yaml/sample_project.yaml --output ./my_project --force
```

Alternatively, use the corresponding targets defined in the [`Makefile`](.Makefile):

```bash
make generate
make generate_force
```

To use these targets, install `make` for your operating system:

- [Linux](https://www.gnu.org/software/make/)
- [Windows](https://gnuwin32.sourceforge.net/packages/make.htm)
- [macOS](https://formulae.brew.sh/formula/make)

## Development and contributions

Contributions are welcome. Please open a pull request with your changes. Before submitting, format and lint the codebase using [Ruff](https://docs.astral.sh/ruff/):

```bash
ruff check . --fix
ruff format .
```

Alternatively, run the corresponding Makefile target:

```bash
make lint
```

## Pre-commit checks

We recommend installing the [pre-commit](https://pre-commit.com/) hook before contributing:

```bash
pre-commit install
```

To run the checks locally against all files:

```bash
pre-commit run --all-files
```

Alternatively, use the Makefile target:

```bash
make pre_commit
```
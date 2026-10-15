fastapi-blueprint/
│
├── pyproject.toml                  # Build config + pytest + coverage settings
├── requirements.txt                # Dev dependencies
├── README.md                       # (θα γίνει αργότερα)
├── sample_project.yaml             # Sample input spec
├── LICENSE                         # MIT
│
├── fastapi_blueprint/              # Main package
│   ├── __init__.py
│   ├── cli.py                      # typer CLI entrypoint
│   │                               # Commands: generate, validate, version
│   │
│   ├── models/                     # Pydantic models — validate the YAML spec
│   │   ├── __init__.py
│   │   ├── spec.py                 # ProjectSpec, RouterSpec, EndpointSpec
│   │   └── schema.py               # SchemaSpec, FieldSpec
│   │
│   ├── parser/                     # YAML → Pydantic models
│   │   ├── __init__.py
│   │   └── yaml_parser.py          # load_spec(path) → ProjectSpec
│   │
│   ├── generator/                  # ProjectSpec → files on disk
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract BaseGenerator
│   │   ├── router_generator.py     # Generates routers/*.py
│   │   ├── schema_generator.py     # Generates schemas/*.py
│   │   ├── test_generator.py       # Generates tests/*.py  ← το κλειδί
│   │   ├── docker_generator.py     # Generates Dockerfile + docker-compose
│   │   └── project_generator.py   # Orchestrates all generators
│   │
│   └── templates/                  # Jinja2 templates
│       ├── router.py.j2
│       ├── schema.py.j2
│       ├── test_router.py.j2       # ← generates AAA tests
│       ├── test_schema.py.j2
│       ├── dockerfile.j2
│       └── docker_compose.j2
│
└── tests/                          # Tests για το ίδιο το tool
    ├── __init__.py
    ├── conftest.py
    ├── test_cli.py
    ├── test_yaml_parser.py
    ├── test_router_generator.py
    ├── test_schema_generator.py
    ├── test_test_generator.py
    └── test_docker_generator.py

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from pydantic import ValidationError

from app.generator import Generator
from app.utils.error_handlers import GeneratorError, SpecFormatError, SpecNotFoundError

# ==========================================
# FIXTURES & MOCKS
# ==========================================


@pytest.fixture
def generator():
    """Initializes a Generator instance with a mock spec path."""
    return Generator("dummy_spec.yaml")


@pytest.fixture
def mock_project_spec():
    """Creates a complex, structural mock mimicking ProjectSpec configuration flags."""
    spec = MagicMock()
    spec.name = "Test App-Blueprint"
    spec.database = "postgresql"
    spec.schemas = ["UserSchema", "ItemSchema"]

    # Mock single API router
    router = MagicMock()
    router.name = "Auth Router"
    router.tag = "auth"
    router.endpoints = ["login", "register"]
    spec.routers = [router]

    # Enable all conditional orchestration flags
    spec.generate_tests = True
    spec.generate_entrypoint = True
    spec.generate_requirements = True
    spec.generate_docker = True
    spec.generate_makefile = True

    # Docker configurations
    spec.docker_web.base_image = "python:3.11-slim"
    spec.docker_web.web_external_port = 8000
    spec.docker_web.web_internal_port = 8000
    spec.docker_web.workers = 4
    spec.docker_web.timezone = "UTC"
    spec.docker_web.python_version.value = "3.11"
    spec.docker_web.include_compose = True

    # Nginx configurations
    spec.docker_nginx.base_image = "nginx:alpine"
    spec.docker_nginx.nginx_external_port = 443
    spec.docker_nginx.nginx_internal_port = 443
    spec.docker_nginx.o_value = "TestOrg"
    spec.docker_nginx.cn_value = "localhost"
    spec.docker_nginx.ou_value = "Dev"
    spec.docker_nginx.timezone = "UTC"

    # Request config
    spec.req_cnf.sans_ips = ["127.0.0.1"]
    spec.req_cnf.sans_dns = ["localhost"]

    # Nginx configuration details
    spec.nginx_conf.upstream_host = "web"
    spec.nginx_conf.conf_external_port = 443
    spec.nginx_conf.conf_internal_port = 443
    spec.nginx_conf.upstream_internal_port = 8000
    spec.nginx_conf.proxy_connect_timeout = 60
    spec.nginx_conf.proxy_send_timeout = 60
    spec.nginx_conf.proxy_read_timeout = 60
    spec.nginx_conf.send_timeout = 60
    spec.nginx_conf.client_max_body_size = "10m"
    spec.nginx_conf.ssl_certificate = "/etc/ssl/cert.crt"
    spec.nginx_conf.ssl_certificate_key = "/etc/ssl/cert.key"
    spec.nginx_conf.cn_value = "localhost"

    # Entrypoint and Automation
    spec.entrypoint_shell.git_repo_url = "https://github.com"
    spec.entrypoint_shell.app_port = 8000
    spec.entrypoint_shell.gunicorn_workers = 4
    spec.entrypoint_shell.app_module = "app.app:app"
    spec.entrypoint_shell.worker_class = "uvicorn.workers.UvicornWorker"
    spec.entrypoint_shell.gunicorn_timeout = 60
    spec.entrypoint_shell.log_level = "info"

    spec.makefile.docker_network_name = "custom_net"
    spec.makefile.docker_subnet = "172.28.0.0/16"
    spec.makefile.model_dump.return_value = {
        "docker_network_name": "custom_net",
        "app_name_web_ip": "172.28.0.2",
        "app_name_nginx_ip": "172.28.0.3",
    }

    return spec


# ==========================================
# CORE METHOD UNIT TESTS
# ==========================================


@pytest.mark.parametrize(
    "input_str, expected",
    [
        ("MyAwesomeService", "myawesomeservice"),
        ("kebab-case-string", "kebab_case_string"),
        ("Space Separated Name", "space_separated_name"),
        ("", ""),
    ],
)
def test_to_snake_case(input_str, expected):
    assert Generator.to_snake_case(input_str) == expected


def test_write_saves_content_and_tracks_path(generator, tmp_path):
    target_file = tmp_path / "app.py"
    test_content = "print('Hello World')"

    generator.write(target_file, test_content)

    assert target_file.read_text(encoding="utf-8") == test_content
    assert target_file in generator.created


# ==========================================
# SPEC LOADING EXTRACTIONS
# ==========================================


@patch.object(Path, "exists", return_value=False)
def test_load_spec_raises_not_found(mock_exists, generator):
    with pytest.raises(SpecNotFoundError):
        generator.load_spec()


@patch.object(Path, "exists", return_value=True)
def test_load_spec_invalid_yaml_root(mock_exists, generator):
    invalid_yaml_root = "[item1, item2, item3]"  # Parses as a list, not a dict

    with patch.object(Path, "open", mock_open(read_data=invalid_yaml_root)):
        with pytest.raises(GeneratorError, match="YAML root must be a dictionary"):
            generator.load_spec()


@patch.object(Path, "exists", return_value=True)
def test_load_spec_syntax_error(mock_exists, generator):
    bad_yaml_syntax = "{ broken unclosed dict"

    with patch.object(Path, "open", mock_open(read_data=bad_yaml_syntax)):
        with pytest.raises(SpecFormatError, match="Invalid YAML syntax"):
            generator.load_spec()


@patch("app.generator.ProjectSpec.model_validate")
@patch.object(Path, "exists", return_value=True)
def test_load_spec_validation_failure(mock_exists, mock_validate, generator):
    yaml_structure = "project: { name: 'FastAPI App' }"

    mock_validate.side_effect = ValidationError.from_exception_data(
        title="ProjectSpec", line_errors=[]
    )

    with patch.object(Path, "open", mock_open(read_data=yaml_structure)):
        with pytest.raises(SpecFormatError, match="Blueprint layout validation failed"):
            generator.load_spec()


@patch("app.generator.ProjectSpec.model_validate")
@patch.object(Path, "exists", return_value=True)
def test_load_spec_success_path(mock_exists, mock_validate, generator):
    yaml_structure = "project: { name: 'Valid Project' }\ndatabase: sqlite"
    mock_validate.return_value = "SuccessfullyValidatedSpec"

    with patch.object(Path, "open", mock_open(read_data=yaml_structure)):
        result = generator.load_spec()

    assert result == "SuccessfullyValidatedSpec"
    mock_validate.assert_called_once()


# ==========================================
# JINJA TEMPLATE RENDERING CONTEXT TESTS
# ==========================================


def test_individual_render_methods(generator):
    mock_template = MagicMock()
    mock_template.render.return_value = "Rendered String"

    with patch.object(generator.env, "get_template", return_value=mock_template):
        dummy_spec = MagicMock()
        assert generator.render_app(dummy_spec) == "Rendered String"
        generator.env.get_template.assert_called_with("app.py.jinja2")

        req_spec = MagicMock()
        req_spec.database.value = "sqlite"
        req_spec.model_dump.return_value = {"fastapi": "0.100.0"}
        assert generator.render_requirements(req_spec) == "Rendered String"
        generator.env.get_template.assert_called_with("requirements.txt.jinja2")


# ==========================================
# ORCHESTRATION PIPELINE TESTS
# ==========================================


@patch("app.generator.RequirementsSpec")
@patch("app.generator.SchemaCollectionSpec")
def test_generate_pipeline_creates_all_files(
    mock_schema_coll, mock_req_spec, generator, mock_project_spec, tmp_path
):
    mock_template = MagicMock()
    mock_template.render.return_value = "stub content"

    with patch.object(generator.env, "get_template", return_value=mock_template):
        created_files = generator.generate(mock_project_spec, tmp_path)

        assert (tmp_path / "app" / "__init__.py").exists()
        assert (tmp_path / "app" / "app.py").exists()
        assert (tmp_path / "app" / "schemas.py").exists()
        assert (tmp_path / "app" / "routers" / "auth_router.py").exists()

        assert (tmp_path / "tests" / "test_auth_router.py").exists()
        assert (tmp_path / "app" / "entrypoint.sh").exists()
        assert (tmp_path / "app" / "requirements.txt").exists()
        assert (tmp_path / "app" / "Dockerfile.local").exists()
        assert (tmp_path / "nginx" / "local" / "nginx.conf").exists()
        assert (tmp_path / "docker-compose-local.yml").exists()
        assert (tmp_path / "Makefile").exists()

        assert len(created_files) == len(generator.created)


@patch("app.generator.RequirementsSpec")
@patch("app.generator.SchemaCollectionSpec")
def test_generate_pipeline_respects_false_flags(
    mock_schema_coll, mock_req_spec, generator, mock_project_spec, tmp_path
):
    mock_project_spec.generate_tests = False
    mock_project_spec.generate_entrypoint = False
    mock_project_spec.generate_requirements = False
    mock_project_spec.generate_docker = False
    mock_project_spec.generate_makefile = False

    mock_template = MagicMock()
    mock_template.render.return_value = "stub content"

    with patch.object(generator.env, "get_template", return_value=mock_template):
        generator.generate(mock_project_spec, tmp_path)

        assert not (tmp_path / "tests" / "test_auth_router.py").exists()
        assert not (tmp_path / "app" / "entrypoint.sh").exists()
        assert not (tmp_path / "app" / "requirements.txt").exists()
        assert not (tmp_path / "app" / "Dockerfile.local").exists()
        assert not (tmp_path / "Makefile").exists()

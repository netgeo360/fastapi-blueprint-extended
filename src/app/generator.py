"""
generate.py — standalone script, no pydantic required.
Usage: python generate.py --spec sample_project.yaml --output ./output
"""

from __future__ import annotations

from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader
from loguru import logger
from pydantic import ValidationError

from app.config.spec import (
    ProjectSpec,
    RequirementsSpec,
    RouterSpec,
    SchemaCollectionSpec,
)
from app.utils.error_handlers import GeneratorError, SpecFormatError, SpecNotFoundError


class Generator:
    """
    Handles the loading and transformation of project specifications

    Attributes:
        spec_path (Path): The filesystem path to the YAML specification.
    """

    custom_logger = logger.bind(name="fastapi-blueprint-generator")

    def __init__(self, path: str | Path) -> None:
        self.spec_path = Path(path)

        self.template_dir = Path(__file__).parent / "templates"

        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            extensions=["jinja2.ext.do"],
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.created: list[Path] = []
        self.env.filters["snake"] = Generator.to_snake_case

        self.env.filters["repr"] = repr

    @staticmethod
    def to_snake_case(name: str) -> str:
        """
        Converts a string to to_snake_case_case.
        Note: Static because it doesn't depend on instance state.
        """
        if not name:
            return ""
        return name.lower().replace("-", "_").replace(" ", "_")

    def load_spec(self) -> ProjectSpec:
        """
        Loads the project specification from a YAML file.

        Raises:
            SpecNotFoundError: If the YAML file does not exist.
            SpecFormatError: If the YAML file is invalid or not a dictionary.
            GeneratorError: If an unexpected error occurs while loading the spec.
        Returns:
            ProjectSpec: The validated project specification.
        """
        if not self.spec_path.exists():
            raise SpecNotFoundError(
                f"Specification file not found at: {self.spec_path}"
            )

        try:
            with self.spec_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                raise SpecFormatError("YAML root must be a dictionary/mapping.")

            project_data = data.pop("project", {})
            if not isinstance(project_data, dict):
                Generator.custom_logger.warning(
                    "'project' key found but is not a dictionary. Ignoring."
                )
                project_data = {}

            merged = {**data, **project_data}
            return ProjectSpec.model_validate(merged)
        except yaml.YAMLError as exc:
            Generator.custom_logger.error(f"Failed to parse YAML: {exc}")
            raise SpecFormatError(f"Invalid YAML syntax: {exc}") from exc
        except ValidationError as exc:
            Generator.custom_logger.error(f"Specification validation failed:\n{exc}")
            raise SpecFormatError(f"Blueprint layout validation failed: {exc}") from exc
        except Exception as exc:
            Generator.custom_logger.critical(f"Unexpected error loading spec: {exc}")
            raise GeneratorError(f"An unexpected error occurred: {exc}") from exc

    def render_app(self, project_spec: ProjectSpec) -> str:
        template = self.env.get_template("app.py.jinja2")
        return template.render(project_spec)

    def render_requirements(self, reqs_spec: RequirementsSpec) -> str:
        """
        Renders requirements.txt.jinja2 using only the RequirementsSpec.
        """
        template = self.env.get_template("requirements.txt.jinja2")

        return template.render(
            database=reqs_spec.database.value, versions=reqs_spec.model_dump()
        )

    def render_schemas(self, schemas_spec: SchemaCollectionSpec) -> str:
        """
        Renders schemas.py.jinja2 using the SchemaCollectionSpec wrapper.
        """
        template = self.env.get_template("schemas.py.jinja2")

        return template.render(schemas=schemas_spec.schemas)

    def render_router(
        self, router_spec: RouterSpec, schemas_spec: SchemaCollectionSpec
    ) -> str:
        """
        Renders schemas.py.jinja2 using the SchemaCollectionSpec wrapper.
        """
        template = self.env.get_template("router.py.jinja2")

        return template.render(
            router=router_spec,
            schemas=schemas_spec.schemas,
            endpoints=router_spec.endpoints,
        )

    def boilerplate(self, spec: ProjectSpec, output_path: Path):
        routers_dir = output_path / "app" / "routers"
        routers_dir.mkdir(parents=True, exist_ok=True)

        template = self.env.get_template("router.py.jinja2")

        for router_spec in spec.routers:
            content = template.render(
                router=router_spec, endpoints=router_spec.endpoints
            )

            file_name = f"{self.to_snake_case(router_spec.name)}.py"
            target_path = routers_dir / file_name
            target_path.write_text(content, encoding="utf-8")

    def render_tests(self, router_spec: RouterSpec) -> str:
        template = self.env.get_template("test_endpoints.py.jinja2")
        return template.render(endpoints=router_spec.endpoints, tag=router_spec.tag)

    def render_dockerfile(self, spec: ProjectSpec) -> str:
        web = spec.docker_web
        context = {
            "base_image": web.base_image,
            "web_external_port": web.web_external_port,
            "web_internal_port": web.web_internal_port,
            "workers": web.workers,
            "timezone": web.timezone,
            "python_version": "python" + web.python_version.value,
        }

        template = self.env.get_template("Dockerfile.local.jinja2")
        return template.render(**context)

    def render_nginx_dockerfile(self, spec: ProjectSpec) -> str:
        nginx = spec.docker_nginx
        context = {
            "base_image": nginx.base_image,
            "nginx_external_port": nginx.nginx_external_port,
            "nginx_internal_port": nginx.nginx_internal_port,
            "o_value": nginx.o_value,
            "cn_value": nginx.cn_value,
            "ou_value": nginx.ou_value,
            "timezone": nginx.timezone,
        }

        template = self.env.get_template("Dockerfile_nginx.jinja2")
        return template.render(**context)

    def render_req_cnf(self, spec: ProjectSpec) -> str:
        req_cnf = spec.req_cnf
        context = {
            "sans_ips": req_cnf.sans_ips,
            "sans_dns": req_cnf.sans_dns,
        }

        template = self.env.get_template("req.cnf.jinja2")
        return template.render(**context)

    def render_nginx_conf_file(self, spec: ProjectSpec) -> str:
        nginx_conf = spec.nginx_conf
        context = {
            "upstream_host": nginx_conf.upstream_host,
            "conf_external_port": nginx_conf.conf_external_port,
            "conf_internal_port": nginx_conf.conf_internal_port,
            "upstream_internal_port": nginx_conf.upstream_internal_port,
            "proxy_connect_timeout": nginx_conf.proxy_connect_timeout,
            "proxy_send_timeout": nginx_conf.proxy_send_timeout,
            "proxy_read_timeout": nginx_conf.proxy_read_timeout,
            "send_timeout": nginx_conf.send_timeout,
            "client_max_body_size": nginx_conf.client_max_body_size,
            "ssl_certificate": nginx_conf.ssl_certificate,
            "ssl_certificate_key": nginx_conf.ssl_certificate_key,
            "cn_value": nginx_conf.cn_value,
        }

        template = self.env.get_template("nginx.conf.jinja2")
        return template.render(**context)

    def render_compose(self, spec: ProjectSpec) -> str:
        app_name = Generator.to_snake_case(spec.name)
        web = spec.docker_web
        nginx = spec.docker_nginx
        net_spec = spec.makefile

        sub_net = net_spec.model_dump()

        context = {
            "app_name": app_name,
            "port_web_external": web.web_external_port,
            "port_web_internal": web.web_internal_port,
            "port_nginx_external": nginx.nginx_external_port,
            "port_nginx_internal": nginx.nginx_internal_port,
            "docker_network_name": sub_net.get("docker_network_name"),
            "app_name_web_ip": sub_net.get("app_name_web_ip"),
            "app_name_nginx_ip": sub_net.get("app_name_nginx_ip"),
        }

        template = self.env.get_template("docker-compose-local.yml.jinja2")
        return template.render(**context)

    def render_entrypoint(self, spec: ProjectSpec):
        entrypoint = spec.entrypoint_shell
        context = {
            "git_repo_url": entrypoint.git_repo_url,
            "app_port": entrypoint.app_port,
            "gunicorn_workers": entrypoint.gunicorn_workers,
            "app_module": entrypoint.app_module,
            "worker_class": entrypoint.worker_class,
            "gunicorn_timeout": entrypoint.gunicorn_timeout,
            "log_level": entrypoint.log_level,
        }

        template = self.env.get_template("entrypoint.sh.jinja2")
        return template.render(**context)

    def render_makefile(self, spec: ProjectSpec) -> str:
        """Renders the project automation Makefile."""
        template = self.env.get_template("Makefile.jinja2")
        return template.render(
            docker_network_name=spec.makefile.docker_network_name,
            docker_subnet=spec.makefile.docker_subnet,
        )

    def write(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")
        self.created.append(path)

    def generate(self, spec: ProjectSpec, output: Path) -> list[Path]:
        reqs_spec = RequirementsSpec(database=spec.database)
        schemas_spec = SchemaCollectionSpec(schemas=spec.schemas)

        app_dir = output / "app"
        config_dir = output / "config"
        nginx_dir = output / "nginx/local"
        routers_dir = app_dir / "routers"
        tests_dir = output / "tests"
        for d in [app_dir, routers_dir, tests_dir, config_dir, nginx_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.write(app_dir / "__init__.py", "")
        self.write(config_dir / ".gitignore", "")
        self.write(routers_dir / "__init__.py", "")
        self.write(tests_dir / "__init__.py", "")
        self.write(output / "conftest.py", "import pytest\n")

        self.write(app_dir / "app.py", self.render_app(spec))
        self.write(app_dir / "schemas.py", self.render_schemas(schemas_spec))

        for router_spec in spec.routers:
            self.write(
                routers_dir / f"{Generator.to_snake_case(router_spec.name)}.py",
                self.render_router(router_spec, schemas_spec),
            )

            if spec.generate_tests:
                self.write(
                    tests_dir / f"test_{Generator.to_snake_case(router_spec.name)}.py",
                    self.render_tests(router_spec),
                )

        if spec.generate_entrypoint:
            self.write(app_dir / "entrypoint.sh", self.render_entrypoint(spec))

        if spec.generate_requirements:
            self.write(
                app_dir / "requirements.txt", self.render_requirements(reqs_spec)
            )

        if spec.generate_docker:
            self.write(app_dir / "Dockerfile.local", self.render_dockerfile(spec))
            self.write(nginx_dir / "Dockerfile", self.render_nginx_dockerfile(spec))
            self.write(nginx_dir / "req.cnf", self.render_req_cnf(spec))
            self.write(nginx_dir / "nginx.conf", self.render_nginx_conf_file(spec))
            docker = spec.docker_web
            if docker.include_compose:
                self.write(
                    output / "docker-compose-local.yml", self.render_compose(spec)
                )

        if spec.generate_makefile:
            self.write(output / "Makefile", self.render_makefile(spec))

        return self.created

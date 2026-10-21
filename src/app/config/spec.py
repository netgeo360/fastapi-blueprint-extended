"""
fastapi_blueprint/models/spec.py

Pydantic v2 models that represent and validate the input YAML spec.
If the YAML is invalid — we fail early with a clear error message,
before any file generation happens.
"""

from __future__ import annotations

from enum import Enum
from functools import cached_property
from ipaddress import IPv4Address, IPv4Network, IPv6Address
from typing import Annotated, Any, Literal
from zoneinfo import available_timezones

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    PrivateAttr,
    computed_field,
    model_validator,
)

VALID_TIMEZONES = available_timezones()
LOWERCASE_TZ_MAP = {tz.lower(): tz for tz in VALID_TIMEZONES}


def validate_timezone(tz: str) -> str:
    """Strictly validates IANA timezones and enforces 'Region/City' format."""
    cleaned_tz = tz.strip()

    parts = cleaned_tz.split("/")
    if len(parts) != 2:
        raise ValueError(
            f"'{tz}' does not match the required 'Region/City' format. "
            "Single abbreviations (like 'UTC') are not allowed. "
            "Please use the full format (e.g., 'Europe/Athens' or 'Etc/UTC')."
        )

    lowercase_tz = cleaned_tz.lower()

    if lowercase_tz in LOWERCASE_TZ_MAP:
        return LOWERCASE_TZ_MAP[lowercase_tz]

    city_target = parts[1].replace("_", " ").lower()
    suggestions = []
    for real_tz in VALID_TIMEZONES:
        real_parts = real_tz.split("/")
        if len(real_parts) == 2:
            real_city = real_parts[1].replace("_", " ").lower()
            if city_target == real_city:
                suggestions.append(real_tz)

    if not suggestions:
        suggestions = [
            real_tz
            for real_tz in VALID_TIMEZONES
            if len(real_tz.split("/")) == 2 and city_target in real_tz.lower()
        ]

    hint = (
        f" Did you mean one of these? {', '.join(suggestions[:3])}"
        if suggestions
        else ""
    )

    raise ValueError(
        f"'{tz}' is not a valid IANA timezone.{hint} "
        "Please refer to the TZ database names listed under "
        "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
    )


TimeZoneStr = Annotated[
    str,
    AfterValidator(validate_timezone),
    Field(
        description="Valid IANA TZ database zone name, e.g., 'Europe/Athens' or 'UTC'"
    ),
]

# ── Enums ────────────────────────────────────────────────────────────────────


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class DatabaseBackend(str, Enum):
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    NONE = "none"


class PythonVersion(str, Enum):
    PY_312 = "3.12"
    PY_311 = "3.11"
    PY_310 = "3.10"


# ── Path / Query params ───────────────────────────────────────────────────────


class PathParam(BaseModel):
    name: str
    type: Literal["int", "str", "float", "uuid"] = "int"
    gt: int | None = None
    ge: int | None = None


class QueryParam(BaseModel):
    name: str
    type: Literal["int", "str", "float", "bool"] = "str"
    default: int | str | float | bool | None = None
    required: bool = False


# ── Endpoint ──────────────────────────────────────────────────────────────────


class EndpointSpec(BaseModel):
    name: str = Field(min_length=1)
    method: HttpMethod
    path: str = Field(min_length=1)
    summary: str = ""
    request_schema: str | None = None
    response_schema: str | None = None
    status_code: int = 200
    auth: bool = True
    path_params: list[PathParam] = []
    query_params: list[QueryParam] = []

    @model_validator(mode="after")
    def post_requires_request_schema(self) -> EndpointSpec:
        """POST and PUT endpoints should have a request_schema."""
        if self.method in (HttpMethod.POST, HttpMethod.PUT):
            if not self.request_schema:
                raise ValueError(
                    f"Endpoint '{self.name}': "
                    f"{self.method} endpoints should define a request_schema."
                )
        return self


# ── Router ────────────────────────────────────────────────────────────────────


class RouterSpec(BaseModel):
    name: str = Field(min_length=1)
    prefix: str = Field(min_length=1)
    tag: str
    endpoints: list[EndpointSpec] = Field(min_length=1)


# ── Schema field ──────────────────────────────────────────────────────────────


class SchemaFieldSpec(BaseModel):
    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    required: bool = True
    default: Any = None
    min_length: int | None = None
    max_length: int | None = None
    ge: int | float | None = None
    le: int | float | None = None
    gt: int | float | None = None
    lt: int | float | None = None

    @property
    def constraints(self) -> dict[str, Any]:
        """Returns only the active validation constraints."""
        relevant = ["min_length", "max_length", "ge", "le", "gt", "lt"]
        return {
            k: v
            for k, v in self.model_dump().items()
            if k in relevant and v is not None
        }


class SchemaSpec(BaseModel):
    """Represents a single schema definition (e.g., TaskCreate)."""

    name: str = Field(min_length=1)
    fields: list[SchemaFieldSpec] = Field(min_length=1)  # Correct nesting
    from_attributes: bool = False


class SchemaCollectionSpec(BaseModel):
    """Wrapper to maintain consistency in the generator."""

    schemas: list[SchemaSpec]


# ── requirements.txt ──────────────────────────────────────────────────────────────────


class RequirementsSpec(BaseModel):
    """
    Dedicated model for generating requirements.txt content.
    """

    database: DatabaseBackend = DatabaseBackend.NONE
    # Version Pins
    fastapi: str = "0.111.0"
    uvicorn: str = "0.30.0"
    pydantic: str = "2.7.1"
    httpx: str = "0.27.0"
    gunicorn: str = "23.0.0"

    # DB & Tools
    sqlalchemy: str = "2.0.30"
    asyncpg: str = "0.29.0"
    alembic: str = "1.13.1"
    aiosqlite: str = "0.20.0"

    # Testing
    pytest: str = "8.2.0"
    pytest_asyncio: str = "0.23.6"
    pytest_cov: str = "5.0.0"

    def get_context(self) -> dict:
        """
        Wraps the fields into a 'versions' key to match the Jinja2 template.
        """
        return {"database": self.database.value, "versions": self.model_dump()}


# ── Entrypoint.sh ────────────────────────────────────────────────────────────────────
class EntrypointShellSpec(BaseModel):
    git_repo_url: str | None = Field(
        default=None,
        description="The remote Git repository URL (supports HTTPS token-based "
        "or SSH paths).",
    )
    app_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="The port Gunicorn/Uvicorn will listen on.",
    )
    gunicorn_workers: int = Field(
        default=5, ge=1, description="Number of worker processes for handling requests."
    )
    app_module: str = Field(
        default="app:app",
        description="The entry point of your FastAPI application (module:instance).",
    )
    worker_class: str = Field(
        default="uvicorn.workers.UvicornH11Worker",
        description="The Uvicorn ASGI worker class for Gunicorn.",
    )
    gunicorn_timeout: int = Field(
        default=1200,
        ge=0,
        description="Workers silent for more than this many seconds are killed.",
    )
    log_level: Literal["debug", "info", "warning", "error", "critical"] = Field(
        default="info", description="The granularity of Gunicorn log outputs."
    )


class MakefileSpec(BaseModel):
    """Configuration for generating the project Makefile\
    with dynamic network infrastructure."""

    docker_network_name: str = Field(default="company_secure_sandbox")
    docker_subnet: str = Field(default="172.27.0.0/26")
    docker_gateway_ip: IPv4Address = Field(default=IPv4Address("172.27.0.1"))
    generate_ips_count: int = Field(
        default=2,
        ge=1,
        description="Number of container IPs to generate, excluding the gateway.",
    )

    _network: IPv4Network = PrivateAttr()

    @model_validator(mode="after")
    def validate_and_parse_network(self) -> MakefileSpec:
        try:
            network = IPv4Network(self.docker_subnet, strict=True)
        except ValueError as e:
            raise ValueError(
                f"Invalid CIDR configuration for docker_subnet: {e}"
            ) from e

        if self.docker_gateway_ip not in network:
            raise ValueError(
                f"Gateway {self.docker_gateway_ip} is outside subnet {network}."
            )

        object.__setattr__(self, "_network", network)

        available_hosts = sum(
            1 for ip in network.hosts() if ip != self.docker_gateway_ip
        )

        if available_hosts < self.generate_ips_count:
            raise ValueError(
                f"Subnet {network} provides only {available_hosts} container IPs "
                f"after excluding gateway {self.docker_gateway_ip}, "
                f"but {self.generate_ips_count} were requested."
            )

        return self

    @cached_property
    def generated_ips(self) -> list[IPv4Address]:
        """Generate container IPs,\
        excluding the configured gateway."""
        return [ip for ip in self._network.hosts() if ip != self.docker_gateway_ip][
            : self.generate_ips_count
        ]

    @property
    def app_name_web_ip(self) -> IPv4Address:
        return self.generated_ips[0]

    @property
    def app_name_nginx_ip(self) -> IPv4Address:
        return self.generated_ips[1]

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        data = super().model_dump(**kwargs)
        data["generated_ips"] = [str(ip) for ip in self.generated_ips]
        data["app_name_web_ip"] = str(self.app_name_web_ip)
        data["app_name_nginx_ip"] = str(self.app_name_nginx_ip)
        return data

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        protected_namespaces=(),
    )


# ── Docker ────────────────────────────────────────────────────────────────────


class DockerWebSpec(BaseModel):
    base_image: str = "python:3.12-slim-bookworm"
    python_version: PythonVersion = PythonVersion.PY_312
    web_external_port: int = 8001
    web_internal_port: int = 8000
    workers: int = Field(default=4, ge=1, le=32)
    include_compose: bool = True
    services: list[Literal["postgresql", "redis"]] = []
    timezone: TimeZoneStr = "Asia/Athens"

    @computed_field
    @property
    def python_version_annotated(self) -> int | None:
        """
        Extracts and converts the created_at datetime into a YYYYMMDDHMS integer format.
        """
        if not self.created_at:
            return None
        return int(self.created_at.strftime("%Y%m%d%H%M%S"))


class DockerNginxSpec(BaseModel):
    base_image: str = "nginx:1.25.2"
    nginx_external_port: int = Field(8000, ge=1, le=65535)
    nginx_internal_port: int = Field(8000, ge=1, le=65535)
    include_compose: bool = True
    o_value: str = "Company Name"
    cn_value: str
    ou_value: str = "Company Team"
    timezone: TimeZoneStr


class NginxConfSpec(BaseModel):
    upstream_host: str
    cn_value: str = "task.manager.localhost"
    conf_external_port: int = Field(443, ge=1, le=65535)
    conf_internal_port: int = Field(443, ge=1, le=65535)
    upstream_internal_port: int = Field(8000, ge=1, le=65535)
    proxy_connect_timeout: int = 1200
    proxy_send_timeout: int = 1200
    proxy_read_timeout: int = 1200
    send_timeout: int = 10
    client_max_body_size: str = "250M"
    ssl_certificate: str = "/etc/nginx/server.crt"
    ssl_certificate_key: str = "/etc/nginx/server.key"


class ReqCnfSpec(BaseModel):
    sans_ips: list[IPv4Address | IPv6Address] = Field(default_factory=list)

    sans_dns: list[str] = Field(default_factory=list)


# ── Project (root) ────────────────────────────────────────────────────────────


class ProjectSpec(BaseModel):
    """Root model — represents the entire input YAML spec."""

    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    version: str = "0.0.0"
    url: HttpUrl
    email: EmailStr
    python_version: PythonVersion = PythonVersion.PY_312
    database: DatabaseBackend = DatabaseBackend.POSTGRESQL
    generate_requirements: bool = True
    generate_tests: bool = True
    generate_docker: bool = True
    generate_alembic: bool = True
    generate_makefile: bool = True
    generate_entrypoint: bool = True

    routers: list[RouterSpec] = Field(min_length=1)
    schemas: list[SchemaSpec] = Field(min_length=1)
    docker_web: DockerWebSpec = Field(default_factory=DockerWebSpec)
    docker_nginx: DockerNginxSpec = Field(default_factory=DockerNginxSpec)
    req_cnf: ReqCnfSpec = Field(default_factory=ReqCnfSpec)
    nginx_conf: NginxConfSpec = Field(default_factory=NginxConfSpec)
    entrypoint_shell: EntrypointShellSpec = Field(
        alias="entrypoint", default_factory=EntrypointShellSpec
    )

    makefile: MakefileSpec = Field(default_factory=MakefileSpec)

    @model_validator(mode="after")
    def all_response_schemas_exist(self) -> ProjectSpec:
        """
        Every response_schema / request_schema referenced in an endpoint
        must be defined in the schemas section.
        """
        defined = {s.name for s in self.schemas}
        for router in self.routers:
            for ep in router.endpoints:
                for schema_ref in filter(None, [ep.request_schema, ep.response_schema]):
                    base = schema_ref.replace("List[", "").replace("]", "")
                    if base not in defined:
                        raise ValueError(
                            f"Router '{router.name}' → endpoint '{ep.name}': "
                            f"schema '{base}' is not defined in schemas section."
                        )
        return self

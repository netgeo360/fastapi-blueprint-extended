# tests/conftest.py
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_project_spec():
    """Shared global fixture available automatically to all test files."""
    spec = MagicMock()
    spec.name = "Architected Project Layout"
    return spec

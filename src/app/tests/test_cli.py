import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import app.cli as cli


def test_main_exits_when_spec_file_missing():
    test_args = ["cli.py", "--spec", "non_existent_spec.yaml", "--output", "./out"]

    with patch.object(sys, "argv", test_args):
        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(SystemExit) as exit_wrapper:
                cli.main()

            assert exit_wrapper.value.code == 1


def test_main_exits_when_output_dir_exists_without_force(tmp_path):
    spec_path = tmp_path / "spec.yaml"
    spec_path.touch()

    output_dir = tmp_path / "existing_output_dir"
    output_dir.mkdir()

    test_args = ["cli.py", "--spec", str(spec_path), "--output", str(output_dir)]

    with patch.object(sys, "argv", test_args):
        with pytest.raises(SystemExit) as exit_wrapper:
            cli.main()

        assert exit_wrapper.value.code == 1


@patch("app.run.Generator")
def test_main_success_flow_with_force_override(mock_generator_class, tmp_path):
    spec_path = tmp_path / "spec.yaml"
    spec_path.touch()

    output_dir = tmp_path / "existing_output_dir"
    output_dir.mkdir()

    test_args = [
        "cli.py",
        "--spec",
        str(spec_path),
        "--output",
        str(output_dir),
        "--force",
    ]

    mock_instance = MagicMock()
    mock_spec = MagicMock()
    mock_spec.name = "Mocked Test Plan Layout"
    mock_instance.load_spec.return_value = mock_spec
    mock_instance.generate.return_value = [output_dir / "app" / "app.py"]
    mock_generator_class.return_value = mock_instance

    with patch.object(sys, "argv", test_args):
        cli.main()

    mock_generator_class.assert_called_once_with(Path(spec_path))
    mock_instance.load_spec.assert_called_once()
    mock_instance.generate.assert_called_once_with(mock_spec, Path(output_dir))

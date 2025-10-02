import tempfile
from pathlib import Path

import pytest

from oppm.commands import BINARY_ARCHIVE_TYPES, UNARY_ARCHIVE_TYPES, _extract_app_name_from_path
from oppm.exceptions import InvalidInputError


def test_unary_archive_app_name():
    file_name = "abc"
    with tempfile.TemporaryDirectory() as temp_dir:
        for archive_type in UNARY_ARCHIVE_TYPES:
            file_path = Path(temp_dir) / f"{file_name}{archive_type}"
            file_path.touch()
            assert file_name == _extract_app_name_from_path(file_path)


def test_binary_archive_app_name():
    file_name = "abc"
    with tempfile.TemporaryDirectory() as temp_dir:
        for archive_type in BINARY_ARCHIVE_TYPES:
            file_path = Path(temp_dir) / f"{file_name}{archive_type}"
            file_path.touch()
            assert file_name == _extract_app_name_from_path(file_path)


def test_unsupported_archive_type():
    unsupported_archive_type_set = {".a", ".c", ".dll", ".iso"}
    file_name = "abc"
    with tempfile.TemporaryDirectory() as temp_dir:
        for archive_type in unsupported_archive_type_set:
            file_path = Path(temp_dir) / f"{file_name}{archive_type}"
            file_path.touch()
            with pytest.raises(InvalidInputError):
                _extract_app_name_from_path(file_path)

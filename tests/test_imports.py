# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

# System imports
import contextlib
import importlib
import os
from collections.abc import Container, Iterator
from pathlib import Path

# Third-party imports
import pytest

# Local imports


def list_packages_in_folder(
    root_package_folder: Path,
    ignores: Container[str] | None = None,
) -> Iterator[str]:
    if ignores is None:
        ignores = []

    basefolder = str(root_package_folder.parent) + '/'

    def convert_folder_to_package(foldername: str) -> str:
        return foldername.replace(basefolder, '').replace('/', '.')

    for dirpath, dirnames, filenames in os.walk(root_package_folder):
        if '__init__.py' not in filenames:
            dirnames.clear()
            continue

        package_name = convert_folder_to_package(dirpath)

        if package_name in ignores:
            dirnames.clear()
            continue

        yield package_name

        for filename in filenames:
            if not filename.endswith('.py'):
                continue
            if filename == '__init__.py':
                continue

            module_name = '.'.join([convert_folder_to_package(dirpath), filename[:-3]])

            if module_name not in ignores:
                yield module_name

        with contextlib.suppress(ValueError):
            dirnames.remove('__pycache__')


def relative_path(base_filepath: str, *subpaths: str) -> Path:
    return Path(base_filepath).parent.joinpath(*subpaths).absolute()


@pytest.mark.parametrize(
    'module_name',
    list_packages_in_folder(
        relative_path(__file__, '..', 'lookups'),
        ignores=[],
    ),
)
def test_imports(module_name: str) -> None:
    assert importlib.import_module(module_name)

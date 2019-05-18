# -*- coding: utf-8 -*-
# Copyright (c) 2019 Contributors as noted in the AUTHORS file
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# System imports
import codecs
import json
import os
import setuptools

# Third-party imports

# Local imports


ROOT_PATH = os.path.abspath(os.path.dirname(__file__))


def read_text(*paths):
    '''Returns text content of a file.'''
    with codecs.open(os.path.join(ROOT_PATH, *paths), 'r', 'utf-8') as f:
        return f.read()


def read_py(*paths):
    '''Executes a Python file and returns its globals namespace.'''
    into = {}
    exec(read_text(*paths), into)
    return into


def pipfile_requirements(section, with_version=False):
    '''Extract requirements from Pipfile.lock'''
    pipfile = json.loads(read_text('Pipfile.lock'))

    if with_version:
        return [
            package + detail.get('version', '')
            for package, detail in pipfile[section].items()
        ]
    else:
        return [
            package
            for package, detail in pipfile[section].items()
        ]


about = read_py('lookups', '__about__.py')
setup_args = dict(
    # Meta info
    name=about['__title__'],
    version=about['__version__'],
    author=about['__author__'],
    author_email=about['__email__'],
    license=about['__license__'],
    description=about['__summary__'],
    long_description='\n\n'.join([
        read_text('README.md'),
        read_text('AUTHORS.md'),
        read_text('CHANGELOG.md'),
    ]),
    long_description_content_type='text/markdown',
    url=about['__uri__'],

    # Code and dependencies
    packages=setuptools.find_packages(exclude=['tests']),
    install_requires=pipfile_requirements('default'),  # , with_version=True),
    tests_require=pipfile_requirements('develop'),
    python_requires='~=3.7',

    # Classifiers and Keywords
    classifiers=(  # https://pypi.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Object Brokering',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Typing :: Typed',
    ),
    keywords='lookup lookups dci',
)

if __name__ == '__main__':
    setuptools.setup(**setup_args)

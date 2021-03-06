#!/usr/bin/env python3

from setuptools import setup, find_packages, Extension
import os
from setuptools.command.develop import develop
from setuptools.command.install import install
from subprocess import check_call

import io
import re

def read(*names, **kwargs):
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ) as fp:
        return fp.read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        print('Running post-installation for apsw')
        check_call('''\
	pip install --user https://github.com/rogerbinns/apsw/releases/download/3.19.3-r1/apsw-3.19.3-r1.zip \
	--global-option=fetch --global-option=--version --global-option=3.19.3 --global-option=--all \
	--global-option=build --global-option=--enable-all-extensions'''.split())
        develop.run(self)

class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        check_call('''\
	pip install --user https://github.com/rogerbinns/apsw/releases/download/3.19.3-r1/apsw-3.19.3-r1.zip \
	--global-option=fetch --global-option=--version --global-option=3.19.3 --global-option=--all \
	--global-option=build --global-option=--enable-all-extensions'''.split())
        install.run(self)

setup(
    name = 'minus80',
    version = find_version('minus80','__init__.py'),
    packages = find_packages(),
    scripts = [
    ],
    ext_modules = [],
    cmdclass = {
        #'build_ext': build_ext
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },

    package_data = {
        '':['*.cyx']    
    },
    install_requires = [		
        'pandas>=0.18',		
        'bcolz',
        'blaze',
        'termcolor',
        'pyyaml'
    ],
    include_package_data=True,

    author = 'Rob Schaefer',
    author_email = 'rob@linkage.io',
    description = 'An abstract library for freezing and unfreezing data.',
    license = "Copyright Linkage Analytics 2016. Available under the MIT License",
    url = 'linkage.io'
)

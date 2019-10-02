#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages
from setuptools.command.develop import develop
from setuptools.command.install import install

requirements = [
    "requests==2.22.0",
    "spacy==2.1.8",
    "scikit-learn==0.21.3",
    "wordcloud==1.5.0",
    "matplotlib==3.1.1",
    "diskcache==4.0.0",
]

setup_requirements = ["pytest-runner"]

test_requirements = ["pytest"]


def init_bible():
    from ipybible.bible import Bible
    print(f"Populating bible (it may take a while)...")
    Bible(version='kjv', language='EN')
    # Bible(version='basicenglish', language='EN')
    # Bible(version='statenvertaling', language='NL')
    print(f"Finished...")


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self):
        init_bible()
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        init_bible()
        install.run(self)


setup(
    author="Ricky Lim",
    author_email="rlim.email@gmail.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="Administrative tasks for kilana",
    entry_points={"console_scripts": ["ipybible=ipybible.cli:main"]},
    install_requires=requirements,
    long_description="Interactive Bible with python",
    include_package_data=True,
    keywords="ipybible",
    name="ipybible",
    packages=find_packages(include=["ipybible"]),
    package_data={'ipybible': [
        'data/bible/',
        'data/bible/**/**/**',
        'data/img/*.png'
    ]},
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/ricky-lim/ipybible",
    version="0.1.0",
    zip_safe=False,
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
)

#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from setuptools import setup
import os
import GAML


def read(*names):
    values = {}
    extensions = ['.txt', '.rst','.md']
    for name in names:
        v = ''
        for ext in extensions:
            filename = name + ext
            if os.path.isfile(filename):
                with open(filename) as f:
                    v = f.read()
        values[name] = v
    return values


long_description = """%(README)s""" % read('README')


setup(
    name='GAML',
    version=GAML.__version__,
    description='Computation Chemistry Genetic Algorithm Machine Learning',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    author='Orlando Acevedo',
    author_email='orlando.acevedo@miami.edu',
    keywords='Computational Chemistry Genetic Algorithm Machine Learning',
    maintainer='Xiang Zhong',
    maintainer_email='xxz385@miami.edu',
    url='https://github.com/orlandoacevedo/GAML',
    license='MIT',
    packages=['GAML'],
    package_data={'GAML':['shell/GAML-BASH-Interface.sh'],},
    entry_points={
        'console_scripts': [
            'gaml = GAML.main:cmd_line_runner',
        ]
    },
    install_requires=['matplotlib'],
)




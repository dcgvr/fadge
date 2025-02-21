#!/usr/bin/env python3
#
# Copyright (C) 2020 Chi-kwan Chan
# Copyright (C) 2020 Steward Observatory
#
# This file is part of fadge.
#
# Fadge is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Fadge is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details.
#
# You should have received a copy of the GNU General Public License
# along with fadge.  If not, see <http://www.gnu.org/licenses/>.


from setuptools import setup, find_packages


setup(
    name='fadge',
    version='0.1.6',
    url='https://github.com/adxsrc/fadge',
    author='Chi-kwan Chan',
    author_email='chanc@arizona.edu',
    description='Fast Automatic Differential GEometry',
    packages=find_packages('mod'),
    package_dir={'': 'mod'},
    entry_points={
        'console_scripts': [
            'fadge = fadge.__main__:fadge',
        ],
    },
    python_requires='>=3.7',
    install_requires=[
        'click>=7.1.2',
        'h5py',
        'xaj>=0.1.6,<0.2',
    ],
)

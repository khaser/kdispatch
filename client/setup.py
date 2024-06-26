#!/usr/bin/env python3
from setuptools import setup

setup(
        name='kdispatch-client',
        version='0.1.0',
        packages=['.'],
        license='MIT',
        author='Andrey Khorokhorin',
        author_email='a-horohorin@mail.com',
        install_requires=['requests', 'paramiko', 'daemon'],
        entry_points={
            'console_scripts': [
                'kdispatch-client=client:main'
            ],
        }
)

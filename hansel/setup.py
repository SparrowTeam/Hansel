from setuptools import find_packages
from setuptools.command.sdist import sdist


__version__ = '0.0.1'

setup(
    name='hansel',
    version=__version__,
    include_package_data=True,
    zip_safe=False,
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]
    ),
    entry_points={
        'console_scripts': [
            'hansel_run= hansel.app',
        ]
    },
    install_requires=[
        'flask',
        'peewee',
        'pyyaml'
    ],
    tests_require=[
        'nose',
        'coverage',
    ]
)

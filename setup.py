from setuptools import setup, find_packages

setup(
    name='netsnap',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'pyats',
        'genie',
        'unicon',
        'click',
        'pandas',
        'openpyxl',
        'PyYAML',
        'deepdiff',
        'jinja2',
        'tabulate',
    ],
    entry_points={
        'console_scripts': [
            'netsnap=netsnap.cli:cli',
        ],
    },
)

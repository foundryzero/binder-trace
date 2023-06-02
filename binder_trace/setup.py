from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='binder_trace',
    install_requires=required,
    packages=find_packages(),
)
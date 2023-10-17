import os

from setuptools import find_packages, setup

dir_path = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(dir_path, "..", "README.md"), "r", encoding="utf-8") as f:
    long_description = f.read()

with open(os.path.join(dir_path, "requirements.txt"), "r", encoding="utf-8") as f:
    required = f.read().splitlines()


setup(
    name="binder_trace",
    install_requires=required,
    packages=find_packages(),
    package_data={'binder_trace': ['structs/**/*.struct', 'js/interceptbinder.js']},
    version="1.1.2",
    author='Foundry Zero',
    author_email='info@foundryzero.co.uk',
    url='https://github.com/foundryzero/binder-trace',
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.9",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "binder-trace = binder_trace.__main__:main",
        ],
    },
)

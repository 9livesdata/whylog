import os.path
import platform

from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()
    if platform.system().lower().startswith('java'):
        required.remove('regex')

with open('requirements-test.txt') as f:
    required_test = f.read().splitlines()


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="whylog",
    version="0.1",
    author="ZPP team",
    author_email="",
    description="whylog v0.1",
    license="BSD 3-clause",
    tests_require=required_test,
    install_requires=required,
    url="https://github.com/9livesdata/whylog",
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 0 - Alpha",
    ],
    packages=['whylog'],
)

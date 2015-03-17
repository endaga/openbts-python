"""setup
openbts-python package definition
"""
from setuptools import setup

# pull all the requirements from the pip-freezed file
with open('requirements.txt') as f:
  required_libs = f.readlines()

# load the readme
with open('readme.md') as f:
  readme = f.read()

version = '0.0.8'

setup(
    name='openbts',
    version=version,
    description='OpenBTS NodeManager client',
    long_description=readme,
    url='http://github.com/endaga/openbts-python',
    download_url=('https://github.com/endaga/openbts-python/tarball/%s' %
                  version),
    author='Matt Ball',
    author_email='matt.ball.2@gmail.com',
    license='MIT',
    packages=['openbts'],
    install_requires=required_libs,
    zip_safe=False
)

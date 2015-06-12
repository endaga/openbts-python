"""setup
openbts-python package definition
"""
from setuptools import setup


with open('readme.md') as f:
  readme = f.read()


version = '0.0.18'


setup(
    name='openbts',
    version=version,
    description='OpenBTS NodeManager client',
    long_description=readme,
    url='http://github.com/endaga/openbts-python',
    download_url=('https://github.com/endaga/openbts-python/tarball/%s' %
                  version),
    author='Matt Ball',
    author_email='matt@endaga.com',
    license='MIT',
    packages=['openbts'],
    install_requires=[
        "enum34==1.0.4",
        "envoy==0.0.3",
        "pyzmq==14.5.0",
    ],
    zip_safe=False
)

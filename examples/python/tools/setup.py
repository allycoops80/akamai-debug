from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages
setup(
    name='akamaikickstart', 
    version='1.0.0', 
    description='Debug tooling for Akamai {OPEN} APIs',
    author='Alan Cooper',
    author_email='alan.cooper@skyscanner.net',
    url='https://github.com/allycoops80/akamai-debug',
    packages=find_packages(),
    install_requires = [
        'edgegrid-python>=1.0.10',
	'GitPython>=0.3.6',
    ],
    license='MIT'
)

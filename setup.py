'''
#       Install Project Requirements 
'''
from setuptools import setup, find_packages

setup(name='VotingProtocol',
    version='1.0',
    install_requires=['cryptography'],
    packages=find_packages()
)
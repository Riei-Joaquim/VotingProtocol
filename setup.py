'''
#       Install Project Requirements 
'''
from setuptools import setup, find_packages

setup(name='VotingProtocol',
    version='1.0',
    install_requires=['pycryptodome>=3.10.1','cryptography>=3.1.1', 'dataclasses>=0.6'],
    packages=['VotingProtocol']
)
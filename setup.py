'''
#       Install Project Requirements 
'''
from setuptools import setup, find_packages

setup(name='VotingProtocol',
    version='1.0',
    install_requires=['pycryptodome','cryptography'],
    packages=['VotingProtocol']
)
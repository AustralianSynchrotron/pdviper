import os
from setuptools import setup, find_packages

setup(
    name='PDViPeR',
    version='1.0',
    author = "Kieran Spear, Gary Ruben, Lenneke Jong",
    author_email='pdviper@synchrotron.org.au',
    description = "PDViPeR",
    packages=find_packages(),
    url='http://www.synchrotron.org.au/pdviper',
    license='LICENSE',
    install_requires=[
        "docutils",
	"numpy",
        "chaco",
        "scipy",
	"enable",
	"traits ",
	"traitsui",
	"matplotlib ",
	"wxPython",
    ],
)

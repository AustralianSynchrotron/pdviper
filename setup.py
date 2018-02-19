from setuptools import setup
import re


with open('src/pdviper/__init__.py') as file:
    version = re.search(r"__version__ = '(.*)'", file.read()).group(1)


setup(
    name='PDViPeR',
    version='3.0.0',
    author='Australian Synchrotron',
    author_email='pdviper@synchrotron.org.au',
    description='PDViPeR',
    package_dir={'': 'src'},
    packages=[
        'pdviper',
        'pdviper.gui',
        'pdviper.gui.xy_plot',
        'pdviper.gui.heatmap',
    ],
    url='http://www.synchrotron.org.au/pdviper',
    license='LICENSE',
    install_requires=[
        'PyQt5',
        'pandas',
        'plotly',
        'PyQtChart',
        'matplotlib>=2.2.0rc1',
    ],
    entry_points={
        'console_scripts': [
            'pdviper=pdviper.main:main',
        ],
    },
)

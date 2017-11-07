from setuptools import setup

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
    ],
    url='http://www.synchrotron.org.au/pdviper',
    license='LICENSE',
    install_requires=[
        'PyQt5',
        'pandas',
        'plotly',
        'PyQtChart',
    ],
    entry_points={
        'console_scripts': [
            'pdviper=pdviper:main',
        ],
    },
)

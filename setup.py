from setuptools import setup

setup(
    name='PDViPeR',
    version='3.0.0',
    author='Australian Synchrotron',
    author_email='pdviper@synchrotron.org.au',
    description='PDViPeR',
    packages=[
        'pdviper',
        'pdviper.gui',
    ],
    url='http://www.synchrotron.org.au/pdviper',
    license='LICENSE',
    install_requires=[
        'pyqt5',
    ],
    entry_points={
        'console_scripts': [
            'pdviper=pdviper:main',
        ],
    },
)

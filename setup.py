from setuptools import setup, find_packages

setup(
    name='rodork',
    version='1.0.0',
    description='Robotics Threat Intelligence CLI using Shodan',
    author='Your Name',
    packages=find_packages(),
    install_requires=[
        'shodan',
        'colorama',
        'tabulate',
        'python-dotenv',
    ],
    entry_points={
        'console_scripts': [
            'rodork=rodork:main',
        ],
    },
)

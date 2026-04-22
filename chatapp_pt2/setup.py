from setuptools import setup

def parse_requirements():
    with open('requirements.txt') as f:
        return f.read().splitlines()

setup(
    name='chatapp',
    version='1.0',
    author='Mohamed Ahzarioui en Daan van den Brom',
    description='A Flask chatting application',
    packages=['app'],
    install_requires=parse_requirements(),
    include_package_data=True,
)

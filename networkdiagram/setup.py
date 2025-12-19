from setuptools import setup, find_packages

with open('README.md','r')as f:
    description = f.read()

setup(
    name='networkdiagram',
    version='1.9.1',
    description='A Python library for creating, calculating, and visualizing CPM/PERT Network Diagrams.',
    long_description=description,
    long_description_content_type='text/markdown',
    author='Kathan Majithia',
    author_email='kathanmajithia@gmail.com',
    packages=find_packages(),
    license='MIT',
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "networkx",
        "matplotlib"
        ],
)
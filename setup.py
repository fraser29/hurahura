from setuptools import setup, find_packages

setup(
    name='miresearch',
    version='0.0.1',
    description='Organisation and automation tools for medical imaging research',
    author='Fraser Callaghan',
    author_email='callaghan.fm@gmail.com',
    packages=find_packages(),
    install_requires=[
        'pandas'
    ],
)
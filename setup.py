from setuptools import setup, find_packages

setup(
    name='cybersailor',
    version='0.1.3',
    packages=find_packages(),
    description='Cybersailor Python SDK',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Carthooks',
    author_email='developer@carthooks.com',
    license='MIT',
    install_requires=[
        'requests>=2.23.0',
        'carthooks>=0.1.2'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
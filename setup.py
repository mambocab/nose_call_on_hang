from setuptools import find_packages, setup

setup(
    name='nose-call-on-hang',
    version='0.1',
    packages=find_packages(),
    author='Jim Witschey',
    author_email='jim.witschey@gmail.com',
    url='https://github.com/mambocab/nose_call_on_hang',
    license='MIT',
    install_requires=['nose'],
    test_suite='test',
)

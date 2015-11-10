from setuptools import setup, find_packages

setup(
    name='nose_call_on_hang',
    version='0.1',
    packages=find_packages(),
    author='Jim Witschey',
    author_email='jim.witschey@gmail.com',
    url='https://github.com/mambocab/nose_call_on_hang',
    license='MIT',
    entry_points={
        'nose.plugins': ['nose_call_on_hang = nose_call_on_hang.nose_call_on_hang.CallOnHang']
    },
    install_requires=['nose'],
)
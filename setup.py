from setuptools import setup, find_packages

setup(
    name='cadizm-fling',
    version='0.1.0',
    author='Michael Cadiz',
    author_email='michael.cadiz@gmail.com',
    packages=find_packages(),
    scripts=[
    ],
    url='http://0xfa.de',
    license='LICENSE.txt',
    description='Fling (for iOS) Solver',
    long_description=open('README.md').read(),
    install_requires=[
    ],
    include_package_data=True,
    data_files=[
#        ('', ['', ]),
    ],
    zip_safe=False,
)

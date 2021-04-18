from setuptools import find_packages, setup
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, './README.md'), encoding='utf-8') as f:
    long_description = f.read()

"""
Build Info:
python3 -m build
twine upload dist/*
"""

setup(
    name='Blankly',  # How you named your package folder (MyLib)
    packages=find_packages(),
    # packages=['Blankly'],  # Chose the same as "name"
    version='v0.1.9-alpha',
    license='lgpl-3.0',  # Chose a license from here: https://help.github.com/articles/licensing-a-repository
    description='Cryptocurrency bot development platform',  # Give a short description about your library
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Emerson Dove',  # Type in your name
    # author_email = 'your.email@domain.com',      # Type in your E-Mail
    url='https://github.com/Blankly-Finance/Blankly',  # Provide either the link to your github or to your website
    # download_url='https://github.com/EmersonDove/Blankly/archive/v0.1.1-alpha.tar.gz',
    keywords=['Crypto', 'Exchanges', 'Bot'],  # Keywords that define your package best
    install_requires=[
        'numpy',
        'sklearn',
        'scikit-learn',
        'zerorpc',
        'requests',
        'websocket-client',
        'pandas',
        'python-binance'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
        'Intended Audience :: Developers',  # Define that your audience are developers
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',  # Again, pick a license
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
)

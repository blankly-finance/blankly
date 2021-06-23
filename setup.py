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
    # packages=['Blankly'],  # Potentially should be the same thing as name
    version='v0.1.12-alpha',
    license='lgpl-3.0',  # Licenses: https://help.github.com/articles/licensing-a-repository
    description='Cryptocurrency bot development platform',  # Give a short description about your library
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Emerson Dove',
    author_email='contact@blankly.finance',
    url='https://github.com/Blankly-Finance/Blankly',  # Could be github or website
    # download_url='https://github.com/EmersonDove/Blankly/archive/v0.1.1-alpha.tar.gz',
    keywords=['Crypto', 'Exchanges', 'Bot'],  # Keywords
    install_requires=[
        'numpy',
        'scikit-learn',
        'zerorpc',
        'requests',
        'websocket-client',
        'pandas',
        'python-binance',
        'newtulipy',
        'alpaca-trade-api',
        'pytest',
        'bokeh',
        'pytest-mock'
    ],
    classifiers=[
        # Possible: "3 - Alpha", "4 - Beta" or "5 - Production/Stable"
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10'
    ],
)

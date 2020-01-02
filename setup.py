import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


with open("version", "r") as fp:
    version = fp.read()

setup(
    name="jconfigpy",
    version=version,
    author="fritzprix",
    author_email="innocentevil0914@gmail.com",
    description="configuration utility which easily integrated into project using gnu make as build system",
    license="BSD",
    keywords="configuration utility make",
    url="http://github.com/fritzprix/jconfigpy",
    download_url="http://github.com/fritzprix/jconfigpy/archive/{}.tar.gz".format(
        version),
    packages=['jconfigpy', './'],
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)

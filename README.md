# jconfigpy
> build configuration utility compatible to GNU Make

## About
> managing C(and C++) projects that have large & complex source tree in scalable way is
> very challenging task to many developers. I have investigated a few configuration utilities
> but no configuration utility fulfills my taste so far for reasons below.

1. there are many C (or C++) projects that still use preprocessor macro (header file) as its configuration tools.  this method makes project less scalable. change to the project is painful because headers for configuration are added in directory whenever extension is added.

2. Some projects use dedicated configuration utility for its own purpose (ex. Kconfig in Linux). KConfig is kind of scripting language for linux kernel configuration that has
small set of syntax for ease of use. it also provides scalabilty to project combined with GNU Makefile. however, it makes makefile too verbose unnecessarily and doesn't support dynamic visibility update of configuration parameter on-the-go.


## Getting Started
you can see how it works by input following in command line
> $ python -c -i example/config.json

## Feature
1. JSON based configuration script (ease of use)
2. Keep Makefile simple (good readability)
3. Adding new module is simple and isolated from other source tree (doesn't affect other modules build)


## Required
1. python 2.7
2. GNU Make utility




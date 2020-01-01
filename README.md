# jconfigpy  

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/76685c589399464cafbec7e1df23f708)](https://www.codacy.com/app/innocentevil0914/jconfigpy?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=fritzprix/jconfigpy&amp;utm_campaign=Badge_Grade) ![Travis Badge](https://travis-ci.org/fritzprix/jconfigpy.svg?branch=master)

> configuration utility compatible to GNU Make

## Motivation

> many C / C++ projects configured heavily based on macro variables and they make project readability worse. If project scale is getting larger, macro variables are added much more and macro branch points also become too complicated to manage project properly. and I really didn't like this kind of messy hell and started new project inspired from kconfig used in linux kernel build system.

## About

> jconfigpy is an implementation effort of a few points that are considered to be able to resolve many issues mentioned preceeding section.

+ configuration should be less intrusive as possible to source code
+ configuration description (or meta data) should be distributed into directory where each configuration is related to
+ configuration should be isolated from each other (the change in one source directory doesn't affect to the other)
+ no additional script or language just for configuration.
+ configuration utility should be able to resolve dependencies by itself.

> jconfigpy is inspired from kconfig in linux in many parts. actually, I tried it first, however, it was less portable and require another set of script language. it's quite simple though, we have a lots of familiar scripts or markup language suitable for representing configuration description model. (and I choose JSON) so I decided to
rewrite old stuff using new tools

## Getting Started

you can see how it works by input following in command line

```shell
$python jconfigpy -c -i ../example/config.json
```

or you can load configuration to generate header file and resolve dependencies

```shell
$python jconfigpy.py -s -i ../configs/config -t ../example/config.json
```

## Feature

1. JSON based configuration script (ease of use)
2. Keep source code (even Makefile) simple (good readability)
3. dependencies resolution (git)
4. Adding new module or dependency is simple and isolated from other source tree (improve project scalability)

## Required

> 1. python 2.7
> 2. GNU Make utility

## Licnese

> BSD-2
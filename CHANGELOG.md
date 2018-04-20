# Changelog

## 0.9.10

- Fix issue #73: missing versions are ignored (thanks @jedie)

## 0.9.9

- Added support for `--delay` option (thanks @clement-escolano)

## 0.9.8

- Removed support for the (defunct) piprot.io service
- Merged #68 to add support for ignoring out of date packages with `# norot`

## 0.9.7

- Merged #62 to add support for `requests[security]` style extras (thanks @zeebonk)

## 0.9.6

- Merged #53 / #54 which adds support for a simpler Github repo syntax
- Allows `-rrequirements.txt` syntax for importing other requirements files. Fixes #57.

## 0.9.5

- Merged #51 to avoid a KeyError when stable_version is unavailable (thanks @federicobond)

## 0.9.4

- Fixed #48 where pytz would break everything

## 0.9.3

- Brings back proper support for versions with different lengths

## 0.9.2

- Fixed #42 which affected version numbers with more than three groups


## 0.9.1

### Fixed

- vendored the version checking code to fix issue with pkg_resources not being
  available


## 0.9.0

### Added

- support for looking up requirements from Github
- support for looking up requirements from a given URL
- Exit status is set to `1` if requirements are out of data (thanks @skoczen!)


### Fixed

- previously if two releases were released on the same day this wasn't
  reported as being out of date.

- updated version checking to ensure that prerelease versions are not included


## 0.8.2 / 0.8.1 - 2014-09-19

### Fixed

- Boo boo during the release because of missing HISTORY.rst file


## 0.8 - 2014-09-19

### Added

-  requests-futures support, making everything a whole heap faster
-  Added documentation for the --latest feature that's been there from
   the beginning
-  Added --notify-post-commit argument to output a post-commit hook to
   automatically notify
-  Improved documentation for --notify feature


### Fixed

-  Fixed a bunch of PyLint errors and suggestions


## 0.7.2 - 2014-08-16

### Added

-  Nothing

### Deprecated

-  Nothing.

### Removed

-  Nothing.

### Fixed

-  Use rst for PyPI long description field


## 0.7.1 - 2014-08-16

### Added

-  Updated setup.py to include README in long\_description for PyPI
-  Added Notifications section to README with piprot.io details
-  Added new tests for recursive requirements files

### Deprecated

-  Nothing.

### Removed

-  Nothing.

### Fixed

-  Nothing.


## 0.7.0 - 2014-08-11

### Added

-  This CHANGELOG file, hopefully encouraging me to tell the world more
   about changes to this project
-  Support for piprot.io notifications

### Deprecated

-  Nothing.

### Removed

-  Nothing.

### Fixed

-  Nothing.

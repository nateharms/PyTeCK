# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased]
### Added
- Added handling of zero peaks detected

### Fixed
- Fixed handling of uppercase/lowercase species target

### Changed
- Using warnings module for messages

## [0.2.4] - 2018-05-31
### Fixed
- Fixed ability to handle ChemKED files with uncertainty for various properties.
- Updated handling of RCM volume history and compression time to PyKED v0.4.1
- Fixed searching through composition dict for Ar and He
- Fixed file-author -> file-authors in test files

### Changed
- Removed interpolation from end of integration (was never really necessary).


## [0.2.3] - 2018-02-07
### Fixed
- Standard deviation calculator now averages any duplicates to avoid an error.

## [0.2.2] - 2017-09-02
### Added
- Adds DOI badge to README and CITATION
- Adds AppVeyor build status badge to README
- Adds restart option to skip existing results files.
- Updates PyKED version requirement and adds optional validation skipping

### Fixed
- Fixes ignition delay detection for 1/2 max type (only one value possible, rather than list)
- Fixes test for detecting peaks with min distance
- Ensure time has units when 1/2 max target
- Fixed handling of models with variants

### Changed
- Simulation input parameters now change units in place
- Simulation input composition uses ChemKED Cantera functions

## [0.2.1] - 2017-04-14
### Added
- Adds AppVeyor build for Windows conda packages
- Adds CONTRIBUTING guide

## [0.2.0] - 2017-04-13
### Added
- Adds initial web documentation using Sphinx/Doctr
- Deploys conda and PyPI packages with tagged releases

### Changed
- Major changes for compatibility with PyKED package and newer ChemKED format

## [0.1.0] - 2016-07-12
### Added
- First published version of PyTeCK.
- Supports validation using both shock tube and RCM experimental data in ChemKED format, but RCM not fully functional.

 [Unreleased]: https://github.com/kyleniemeyer/PyTeCK/compare/v0.2.4...HEAD
 [0.2.4]: https://github.com/kyleniemeyer/PyTeCK/compare/v0.2.3...0.2.4
 [0.2.3]: https://github.com/kyleniemeyer/PyTeCK/compare/v0.2.2...0.2.3
 [0.2.2]: https://github.com/kyleniemeyer/PyTeCK/compare/v0.2.1...0.2.2
 [0.2.1]: https://github.com/kyleniemeyer/PyTeCK/compare/v0.2.0...0.2.1
 [0.2.0]: https://github.com/kyleniemeyer/PyTeCK/compare/v0.1...0.2.0
 [0.1.0]: https://github.com/kyleniemeyer/PyTeCK/compare/e99f757b7ea644065a0ee65ce86dbfb8f404be60...v0.1

# Changelog

All notable changes to this project are documented here.
This project adheres to [Semantic Versioning](https://semver.org).

## [Unreleased]
### Added
- Minor tweaks to `README.md`.
- Minor tweaks to `pyproject.toml`.

## [1.0.0] - 2026-07-19
### Added
- Initial public release.
- Dialogue model (`Graph`, `Vertex`, `Edge`) with yaml load/save.
- Runtime `GraphNavigator` with `Turn`, `Option` API, predicate filtering,
    effect processing, placeholder text evaluation, and a pluggable
    `StateAccessor` seam for engine game state.
- `GraphValidator` with runtime validity checks (structural and
    well-formedness) and a `dialogue-validate` command line tool.
- `GraphEditor` mutation and persistence API.
- Dash + Cytoscape browser editor `dialogue-editor`.
- Graphviz static svg renderer `dialogue-render`.
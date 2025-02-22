Prometheus to Icinga2 Checks
============================

<p align="center">
  <a href="https://github.com/dinotools/monitoring-prom2icinga2/issues">
    <img alt="GitHub issues" src="https://img.shields.io/github/issues/dinotools/monitoring-prom2icinga2">
  </a>
  <a href="https://github.com/dinotools/monitoring-prom2icinga2/network">
    <img alt="GitHub forks" src="https://img.shields.io/github/forks/dinotools/monitoring-prom2icinga2">
  </a>
  <a href="https://github.com/dinotools/monitoring-prom2icinga2/stargazers">
    <img alt="GitHub stars" src="https://img.shields.io/github/stars/dinotools/monitoring-prom2icinga2">
  </a>
  <a href="https://github.com/DinoTools/monitoring-prom2icinga2/blob/main/LICENSE.md">
    <img alt="GitHub license" src="https://img.shields.io/github/license/dinotools/monitoring-prom2icinga2">
  </a>
  <a href="https://dinotools.github.io/monitoring-prom2icinga2">
    <img alt="Documentation" src="https://github.com/DinoTools/monitoring-prom2icinga2/actions/workflows/docs.yml/badge.svg">
  </a>
  <a href="https://pypi.org/project/prom2icinga2/">
    <img alt="PyPI - Downloads" src="https://img.shields.io/pypi/dm/prom2icinga2">
  </a>
  <a href="https://pypi.org/project/prom2icinga2/">
    <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/prom2icinga2">
  </a>
  <a href="https://pypi.org/project/prom2icinga2/">
    <img alt="PyPI - Format" src="https://img.shields.io/pypi/format/prom2icinga2">
  </a>
  <a href="https://pypi.org/project/prom2icinga2/">
    <img alt="PyPI - Status" src="https://img.shields.io/pypi/status/prom2icinga2">
  </a>
</p>

> [!WARNING]
> **Proof of Concept**
>
> This project is in an very early stage of development. Don't use it in production.

The Exporter connects to [MikroTik](https://mikrotik.com/) RouterOS devices via API and connects to the log stream to export the logs in realtime.

Requirements
------------

- [Python](https://www.python.org/) >= 3.8 (It might still run with older versions of Python 3)
- Python Packages
    - dynaconf
    - fastapi
    - httpx
    - jinja2
    - [pyyaml](https://pypi.org/project/PyYAML/)
    - uvicorn

Installation
------------

### Docker

```
docker pull ghcr.io/dinotools/monitoring-prom2icinga2:main
docker run --rm -v ./config.yaml:/etc/prom2icinga2/config.yaml:ro ghcr.io/dinotools/monitoring-prom2icinga2:main
```

### PIP

If you want to use pip we recommend to use as virtualenv to install the dependencies.

```shell
pip install -r requirements.txt
```

### Debian/Ubuntu

Install the required packages

```shell
sudo apt-get install python3 ?? ToDo ??
```

### From PyPI

Install the package from PyPI.

```shell
pip install prom2icinga2
```

Usage
-----

```
python3 -m prom2icinga2.server:app --config config.yaml -vv
```

Resources
---------

- Git-Repository: https://github.com/DinoTools/monitoring-prom2icinga2
- Issues: https://github.com/DinoTools/monitoring-prom2icinga2/issues
- Documentation: https://dinotools.github.io/monitoring-prom2icinga2

License
-------

GPLv3+

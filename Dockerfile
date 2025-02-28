# SPDX-FileCopyrightText: none
# SPDX-License-Identifier: CC0-1.0

FROM python:3.12-alpine AS build

COPY . /build

RUN set -ex; \
    apk update; \
    apk add git; \
    cd /build; \
    python -m pip install build --user; \
    python -m build --wheel --outdir dist/ . ; \
    ls -l dist/

FROM python:3.12-alpine

COPY --from=build /build/dist/*.whl /dist/

RUN set -ex; \
    python -m pip install /dist/*.whl; \
    python -m pip install toml; \
    rm -rf /dist

ENV PROM2ICINGA2_CHECK_CONFIG=/etc/prom2icinga2/checks.yaml \
    PROM2ICINGA2_CONFIG=/etc/prom2icinga2/config.toml

ENTRYPOINT ["uvicorn", "prom2icinga2.server:app", "--host", "0.0.0.0"]

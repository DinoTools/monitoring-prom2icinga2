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
    rm -rf /dist

ENTRYPOINT ["/usr/local/bin/prom2icinga2"]
CMD ["--config", "/etc/prom2icinga2/config.yaml", "-vv"]

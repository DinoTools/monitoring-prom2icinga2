# SPDX-FileCopyrightText: PhiBo DinoTools (2025-)
# SPDX-License-Identifier: GPL-3.0-or-later

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Response, Request
import httpx
import jinja2.nativetypes

from .config import load_config, settings
from .icinga2 import get_icinga2_host


@asynccontextmanager
async def lifespan(app: FastAPI):
    icinga2_auth = None
    if settings.icinga2.username and settings.icinga2.password:
        icinga2_auth = httpx.BasicAuth(
            username=settings.icinga2.username,
            password=settings.icinga2.password,
        )
    app.icinga2_client = httpx.AsyncClient(
        base_url=settings.icinga2.url,
        auth=icinga2_auth,
        verify=False  # <- !!! Change it !!!
    )
    app.prometheus_client = httpx.AsyncClient(
        base_url=settings.prometheus.url,
    )

    load_config("checks.yaml")
    yield
    await app.icinga2_client.aclose()
    await app.prometheus_client.aclose()

app = FastAPI(lifespan=lifespan)
jinja2_env = jinja2.nativetypes.NativeEnvironment()


@app.get("/check/{host_name}")
async def check_request(host_name: str, request: Request):
    start_time = datetime.now()


    icinga2_client: httpx.AsyncClient = request.app.icinga2_client
    print("start")
    icinga2_host = await get_icinga2_host(host_name, icinga2_client)
    # check_config = request.app.check_config.get(check_name)
    # if not check_config:
    #     return Response(status_code=404, content="Check not found")
    print("running")
    await icinga2_host.process(request.app.prometheus_client)


    print(f"Fetch: {datetime.now() - start_time}")

    return Response(content="ok")

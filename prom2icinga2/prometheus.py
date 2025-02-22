# SPDX-FileCopyrightText: PhiBo DinoTools (2025-)
# SPDX-License-Identifier: GPL-3.0-or-later

import httpx


async def query_prometheus(client: httpx.AsyncClient, query: str):
    response = await client.get(
        url="/api/v1/query",
        params={
            "query": query
        }
    )
    results = response.json()
    #from pprint import pprint
    #pprint(results)
    return results

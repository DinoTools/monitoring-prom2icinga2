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

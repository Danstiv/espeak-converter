#!/usr/bin/env python3
import httpx
import quart

from constants import PROXY

app = quart.Quart(__name__)


@app.route('/', methods=['POST'])
async def download():
    data =await quart.request.json
    client = httpx.AsyncClient(proxies=PROXY, timeout=300)
    try:
        response = await client.get(data['url'], headers=data['headers'])
        await client.aclose()
    except Exception:
        response = None
    if not response:
        return quart.Response('error', status=500)
    return quart.Response(response.content, status=response.status_code, headers=dict(response.headers))


app.run(host='0.0.0.0', port=10011)

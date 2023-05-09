import asyncio
import typing as t

import aiohttp

from settings import BASE_HEADERS


class Spider:
    def __init__(self):
        self.base_headers: t.Dict[str, str] = BASE_HEADERS
        self.semaphore = asyncio.Semaphore(50)

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.base_headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def get(self, _url: str, _params: t.Optional[dict] = None) -> t.Union[dict, bytes]:
        async with self.semaphore:
            async with self.session.get(
                    url=_url,
                    params=_params
            ) as resp:
                if resp.status == 200:
                    if 'json' in resp.content_type:
                        resp_data: t.Union[dict, bytes] = await resp.json()
                    else:
                        resp_data: t.Union[dict, bytes] = await resp.content.read()

        return resp_data

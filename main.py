import time
import uuid
import asyncio
import typing as t
from copy import deepcopy
from pathlib import Path

import requests
import aiofiles

from spider import Spider
from settings import KEY_WORD, SAVE_PATH

task_queue = asyncio.Queue()
params = {
    'tn': 'resultjson_com',
    'fp': 'detail',
    'word': KEY_WORD,
    # 'hd': '1',
    'pn': '0',
    'rn': '60',
}

Path(SAVE_PATH).mkdir(parents=True, exist_ok=True)


def get_image_num() -> int:
    """
    获取图片总数
    """
    resp: requests.Response = requests.get('https://image.baidu.com/search/acjson', params=params)
    resp_json: dict = resp.json()
    return resp_json['listNum']


def get_params() -> t.Generator:
    """
    获取请求参数
    """
    image_num = get_image_num()
    print(f'检索到{image_num}张图片')
    for _ in range((image_num // 60) + 1):
        _params = deepcopy(params)
        _params.update({
            'pn': str(_ * 60)
        })
        yield _params


async def producer(_url, _params, spider) -> None:
    """
    生成图片任务
    """
    resp_json: dict = await spider.get(
        _url=_url,
        _params=_params
    )
    for _ in resp_json['data']:
        if _:
            await task_queue.put(_['thumbURL'])


async def consumer(_url, spider) -> None:
    """
    消费图片任务
    """
    resp_data = await spider.get(_url)
    async with aiofiles.open(Path(SAVE_PATH).joinpath(f'{uuid.uuid1()}.png'), 'wb') as f:
        await f.write(resp_data)


async def main():
    async with Spider() as spider:
        print('获取所有图片链接。。。')
        async with asyncio.TaskGroup() as tg:
            for _params in get_params():
                tg.create_task(producer(
                    _url='https://image.baidu.com/search/acjson',
                    _params=_params,
                    spider=spider
                ))
        print('获取所有图片链接成功！\n开始下载图片。。。')
        async with asyncio.TaskGroup() as tg:
            while not task_queue.empty():
                task = await task_queue.get()
                tg.create_task(consumer(
                    task,
                    spider
                ))
        print('图片下载完成！')

if __name__ == '__main__':
    start_time = time.time()
    asyncio.run(main())
    print(f'总耗时：{time.time() - start_time:.2f}s')

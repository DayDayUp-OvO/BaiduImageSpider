import uuid
import asyncio
import typing as t
from copy import deepcopy
from pathlib import Path

import requests
import aiofiles

from image_spider.client import Client

task_queue = asyncio.Queue()


def get_image_num(_params: dict) -> int:
    """
    获取图片总数
    """
    resp: requests.Response = requests.get('https://image.baidu.com/search/acjson', params=_params)
    resp_json: dict = resp.json()
    return resp_json['listNum']


def get_params(key_words: list, only_hd: bool) -> t.Generator:
    """
    获取请求参数
    """
    base_params = {
        'tn': 'resultjson_com',
        'fp': 'detail',
        'pn': '0',
        'rn': '60',
    }
    if only_hd:
        base_params.update({'hd': '1'})
    for key_word in key_words:
        key_word_params = deepcopy(base_params)
        key_word_params.update({'word': key_word})
        image_num = get_image_num(key_word_params)
        print(f'关键词: {key_word} 检索到{image_num}张图片')
        for _ in range((image_num // 60) + 1):
            yield_params = deepcopy(key_word_params)
            yield_params.update({
                'pn': str(_ * 60)
            })
            yield yield_params, key_word


async def producer(_url: str, _params: dict, client: Client, key_word: str) -> None:
    """
    生成图片任务
    """
    resp_json: dict = await client.get(
        _url=_url,
        _params=_params
    )
    for _ in resp_json['data']:
        if _:
            await task_queue.put((_['thumbURL'], key_word))


async def consumer(_url: str, client: Client, key_word: str, save_path: str) -> None:
    """
    消费图片任务
    """
    resp_data = await client.get(_url)
    async with aiofiles.open(Path(save_path).joinpath(key_word).joinpath(f'{uuid.uuid1()}.png'), 'wb') as f:
        await f.write(resp_data)


async def run_task(*args, **kwargs):
    async with Client(kwargs['semaphore']) as client:
        print('获取所有图片链接。。。')
        async with asyncio.TaskGroup() as tg:
            for task_params, key_word in get_params(kwargs['key_words'], kwargs['only_hd']):
                tg.create_task(producer(
                    _url='https://image.baidu.com/search/acjson',
                    _params=task_params,
                    client=client,
                    key_word=key_word
                ))
        print('获取所有图片链接成功！\n开始下载图片。。。')
        async with asyncio.TaskGroup() as tg:
            while not task_queue.empty():
                task, key_word = await task_queue.get()
                tg.create_task(consumer(
                    task,
                    client,
                    key_word,
                    kwargs['save_path']
                ))
        print('图片下载完成！')

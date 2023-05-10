import time
import asyncio
import argparse
from pathlib import Path

from settings import DEFAULT_SAVE_PATH, DEFAULT_SEMAPHORE, DEFAULT_ONLY_HD
from image_spider.baidu_spider import run_task

parser = argparse.ArgumentParser(usage='\n\tpython main.py -k 张婧仪 赵今麦 周也')

parser.add_argument('-k', '--key', nargs='+', type=str, dest='key', required=True, help='检索词')
parser.add_argument('-hd', '--hd', dest='hd', type=int, default=DEFAULT_ONLY_HD, help='是否只下载高清, 0: 否, 1: 是')
parser.add_argument('-o', '--output', dest='output', type=str, default=DEFAULT_SAVE_PATH, help='输出文件夹路径')
parser.add_argument('-s', '--semaphore', dest='semaphore', type=int, default=DEFAULT_SEMAPHORE, help='最大并发请求数')

args = parser.parse_args()

key_words = args.key
only_hd = args.hd
semaphore = args.semaphore
save_path = args.output

assert only_hd in [0, 1], '-hd参数只可以输入0/1'
print(f'检索词：{", ".join(key_words)}\n图片保存路径：{save_path}')
[Path(save_path).joinpath(key_word).mkdir(parents=True, exist_ok=True) for key_word in key_words]

if __name__ == '__main__':
    start_time = time.time()
    asyncio.run(run_task(**{
        'key_words': key_words,
        'only_hd': [False, True][only_hd],
        'semaphore': semaphore,
        'save_path': save_path
    }))
    print(f'任务总耗时：{time.time() - start_time:.2f}s')

import calendar

from concurrent.futures import ThreadPoolExecutor
import time

from bocfx.bocfx_util import get_bocfx_data_by_time, get_headers, output_csv
import pandas as pd
from pandas import DataFrame

year = 2024
month = 12

# 定义任务执行的函数
def task(n):
    date = f"{year}-{month}-{n+1}"
    return get_bocfx_data_by_time(date, date)


def get_days_in_month(year, month):
    # 获取指定年份和月份的天数
    _, num_days = calendar.monthrange(year, month)
    return num_days


if __name__ == '__main__':
    num_tasks = get_days_in_month(year, month)
    num_threads = 10  # 同时运行10个线程

    # 使用ThreadPoolExecutor来管理线程池
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # 提交任务，返回一个结果对象列表
        results = list(executor.map(task, range(num_tasks)))

    headers = get_headers()
    data = [item for sublist in results for item in sublist]

    df = pd.DataFrame(data, columns=headers)

    output_csv(df)





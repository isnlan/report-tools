from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pandas as pd

from bocfx.bocfx_util import get_bocfx_data_by_time, get_headers, output_csv


# 定义任务执行的函数
def task(n, start_date: str, end_date: str):
    print(f"start task {n} {start_date} ～ {end_date}\n")
    table = get_bocfx_data_by_time(start_date, end_date)

    print(f"task {start_date} ～ {end_date}, count: {len(table)}\n")

    return table


# 分割日期区间的函数
def split_date_range(start_date: str, end_date: str, step: int):
    # 将字符串日期转换为 datetime 对象
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    # 使用生成器分割日期区间
    current_date = start
    while current_date <= end:
        # 计算下一步的结束日期
        next_date = current_date + timedelta(days=step - 1)
        if next_date > end:
            next_date = end

        # 将日期转换回字符串格式
        yield current_date.strftime("%Y-%m-%d"), next_date.strftime("%Y-%m-%d")

        # 更新当前日期
        current_date = next_date + timedelta(days=1)


# 主函数，使用 ThreadPoolExecutor 并行执行任务
def main(start_date: str, end_date: str, step: int, num_threads: int):
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        # 为每个日期区间提交任务
        futures = []
        n = 1  # 任务编号
        for start, end in split_date_range(start_date, end_date, step):
            futures.append(executor.submit(task, n, start, end))
            n += 1

        # 获取所有任务的结果，并将它们展开成一个大的列表
        all_results = []
        for future in futures:
            all_results.extend(future.result())  # 将每个任务的返回值列表展开合并

    return all_results


if __name__ == '__main__':
    start_data = "2025-02-1"
    end_data = "2025-02-28"

    headers = get_headers()
    data = main(start_data, end_data, 1, 2)

    df = pd.DataFrame(data, columns=headers)

    output_csv(df)

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import chinese_calendar
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

    # 使用生成器分割日期区间，只处理工作日
    current_date = start
    while current_date <= end:
        # 如果当前日期是工作日，才进行处理
        if chinese_calendar.is_workday(current_date):
            # 计算下一步的结束日期
            next_date = current_date
            days_counted = 0
            
            # 向后查找指定天数的工作日
            while days_counted < step and next_date <= end:
                if not chinese_calendar.is_workday(next_date + timedelta(days=1)):
                    break

                next_date += timedelta(days=1)

                if next_date <= end:
                    days_counted += 1
            
            if next_date > end:
                next_date = end

            # 将日期转换回字符串格式
            yield current_date.strftime("%Y-%m-%d"), next_date.strftime("%Y-%m-%d")
            
            # 更新当前日期到下一个日期
            current_date = next_date + timedelta(days=1)
        else:
            # 如果不是工作日，直接移到下一天
            current_date += timedelta(days=1)


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
    start_data = "2025-03-01"
    end_data = "2025-03-31"

    headers = get_headers()
    data = main(start_data, end_data, 1, 2)

    df = pd.DataFrame(data, columns=headers)

    file_name = f'boc-{start_data}_{end_data}.xlsx'

    output_csv(file_name, df)

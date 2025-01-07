import base64
import calendar
import re
from datetime import datetime

import ddddocr
import pandas as pd
from pandas import DataFrame
from playwright.sync_api import sync_playwright, Page, Playwright, TimeoutError

from bocfx.html_util import get_data


def ocr_image(data: bytes) -> str:
    ocr = ddddocr.DdddOcr(show_ad=False)
    code = ocr.classification(data)

    return code


def get_code(page: Page) -> str:
    page.wait_for_selector('#captcha_img')

    # 获取 src 属性
    img_src = page.get_attribute('#captcha_img', 'src')

    if img_src.startswith('data:image'):
        # 分割 Data URL
        header, base64_data = img_src.split(',', 1)
        # 解码 Base64
        img_bytes = base64.b64decode(base64_data)
        # 保存图片

        return ocr_image(img_bytes)


def get_month_first_last_day(year, month):
    # 获取该月的第一天
    first_day = datetime(year, month, 1)

    # 获取该月的最后一天
    last_day = datetime(year, month, calendar.monthrange(year, month)[1])

    return first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')


def goto_main_page(page: Page):
    page.goto("https://srh.bankofchina.com/search/whpj/search_cn.jsp", wait_until="networkidle")


def run_task(page: Page, start_time: str, end_time: str):
    goto_main_page(page)

    page.locator("input[name=\"erectDate\"]").fill(start_time)
    page.locator("input[name=\"nothing\"]").fill(end_time)
    page.locator("#pjname").select_option("美元")

    while True:
        # 获取验证码
        code = get_code(page)

        page.locator("input[name=\"captcha\"]").fill(code)
        page.get_by_role("button", name="查询").click()

        error_element = page.query_selector("text=验证码错误！")
        if not error_element:
            break

    data = get_table(page, start_time)

    return data


def output_csv(df: DataFrame):
    # 将timestamp列转换为datetime类型
    df['发布时间'] = pd.to_datetime(df['发布时间'], format='%Y.%m.%d %H:%M:%S')
    df["时间"] = df['发布时间'].dt.strftime('%H:%M:%S')

    # 提取日期和时间部分
    df['date'] = df['发布时间'].dt.date
    df['hour'] = df['发布时间'].dt.hour

    # 筛选出10点区间内的数据
    df_10am = df[(df['hour'] == 10)]

    # 找到每一天10点的最早时间记录
    df_earliest = df_10am.loc[df_10am.groupby('date')['发布时间'].idxmin()]

    # 输出到新的表格
    df_earliest = df_earliest[['date', '时间', '现钞卖出价']]

    # 显示结果
    print(df_earliest)

    # 保存到新的Excel文件
    df_earliest.to_excel('earliest_10am_sell_price.xlsx', index=False)


def extract_total_pages(text):
    """
    从给定的文本中提取总页数。
    例如，从 "共3页" 中提取 3。
    """
    match = re.search(r'共(\d+)页', text)
    if match:
        return int(match.group(1))
    return None


def get_page_count(page: Page):
    # 定位到分页导航元素
    pagination_selector = 'div.turn_page#list_navigator ol li'

    try:
        # 等待分页导航元素加载
        page.wait_for_selector(pagination_selector, timeout=3000)
    except TimeoutError:
        return 1

    # 获取所有 <li> 元素
    pagination_items = page.query_selector_all(pagination_selector)

    total_pages = 1

    # 遍历所有 <li> 元素，查找包含 "共X页" 的元素
    for item in pagination_items:
        text = item.inner_text().strip()
        pages = extract_total_pages(text)
        if pages:
            total_pages = pages
            break  # 找到后退出循环

    return total_pages


def get_table(page: Page, start_time: str):
    # 定位到表格元素
    table_selector = 'div.BOC_main.publish table'
    page.wait_for_selector(table_selector)

    count = get_page_count(page)

    # 提取表格数据
    data = []

    for index in range(count):
        page_number = index + 1
        jump_target_page_umber(page, page_number, start_time)

        data.extend(get_data(page.content(), table_selector))

    return data


def jump_target_page_umber(page: Page, page_number: int, start_time: str):
    if page_number == 1:
        return

    while True:
        if "对不起，你一分钟内访问次数超过10次！" in page.content():
            print(f"{start_time} 检测到访问限制，刷新页面...")
            page.reload(wait_until="networkidle")
            page.wait_for_timeout(2000)
            continue

        link = page.get_by_role("link", name=f"{page_number}", exact=True)
        if link.evaluate("element => element.classList.contains('current')"):
            # 已经是当前页面了
            return

        # 点击跳转
        link.click()
        page.wait_for_load_state("networkidle")


def run(playwright: Playwright, start_time: str, end_time: str):
    browser = playwright.chromium.launch(headless=True, args=["--start-maximized"], slow_mo=500)

    kwargs = {
        "java_script_enabled": True,
        "viewport": {"width": 1920, "height": 1080},
        "no_viewport": True,
    }

    browser.new_page()
    context = browser.new_context(**kwargs)
    page = context.new_page()

    data = run_task(page, start_time, end_time)

    page.close()
    browser.close()

    return data


def get_headers():
    headers = ['货币名称', '现汇买入价', '现钞买入价', '现汇卖出价', '现钞卖出价', '中行折算价', '发布时间']
    return headers


def get_bocfx_data_by_time(start_time: str, end_time: str):
    with sync_playwright() as playwright:
        return run(playwright, start_time, end_time)

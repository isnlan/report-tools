import base64
import re
from datetime import datetime

import ddddocr
import pandas as pd
from playwright.sync_api import sync_playwright, Page, Playwright


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


def run_task(page: Page):
    page.goto("https://srh.bankofchina.com/search/whpj/search_cn.jsp")

    now = datetime.now()
    # 格式化日期为 YYYY-MM-DD
    date = now.strftime('%Y-%m-%d')

    page.locator("input[name=\"erectDate\"]").fill(date)
    page.locator("input[name=\"nothing\"]").fill(date)

    page.locator("#pjname").select_option("美元")

    while True:
        # 获取验证码
        code = get_code(page)

        page.locator("input[name=\"captcha\"]").fill(code)
        page.get_by_role("button", name="查询").click()

        error_element = page.query_selector("text=验证码错误！")
        if not error_element:
            break

    df = get_table(page)

    df['发布时间'] = pd.to_datetime(df['发布时间'], format='%Y.%m.%d %H:%M:%S')

    df_am_10_oclock = df[df['发布时间'].dt.hour == 10]
    if not df_am_10_oclock.empty:
        # 找到 '发布时间' 最早的记录
        earliest_record = df_am_10_oclock.loc[df_am_10_oclock['发布时间'].idxmin()]

        # 提取 '现钞买入价'
        balance = earliest_record['现钞卖出价']

        print(f"发布时间在10点间，时间最小的现钞卖出价为: {balance}")
    else:
        print("没有找到发布时间在10点间的记录。")


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

    # 等待分页导航元素加载
    page.wait_for_selector(pagination_selector)

    # 获取所有 <li> 元素
    pagination_items = page.query_selector_all(pagination_selector)

    total_pages = None

    # 遍历所有 <li> 元素，查找包含 "共X页" 的元素
    for item in pagination_items:
        text = item.inner_text().strip()
        pages = extract_total_pages(text)
        if pages:
            total_pages = pages
            break  # 找到后退出循环

    return total_pages


def get_table(page: Page):
    # 定位到表格元素
    table_selector = 'div.BOC_main.publish table'
    page.wait_for_selector(table_selector)

    count = get_page_count(page)

    # 提取表头
    headers = []

    # 尝试从 tbody 的第一行获取表头
    first_row = page.query_selector(f'{table_selector} tbody tr')
    if first_row:
        header_elements = first_row.query_selector_all('th')
        if not header_elements:
            # 如果 th 不存在，尝试使用 td 作为表头
            header_elements = first_row.query_selector_all('td')
        headers = [th.inner_text().strip() for th in header_elements]

    # 如果仍未获取到表头，提示并退出
    if not headers:
        print("未能提取到表头。请检查选择器或页面结构。")
        return

    # 提取表格数据
    data = []

    for current_page in range(count):
        # 获取所有数据行（跳过表头行）
        rows = page.query_selector_all(f'{table_selector} tbody tr')
        for index, row in enumerate(rows):
            # 如果 thead 不存在且这是第一行，则跳过（表头行）
            if index == 0:
                continue
            cells = row.query_selector_all('td')
            if not cells:
                # 如果没有 td，跳过该行
                continue

            row_data = [cell.inner_text().strip() for cell in cells]
            # 检查所有单元格是否为空字符串
            if not all((cell == '' or cell is None) for cell in row_data):
                data.append(row_data)
            else:
                print(f"第 {current_page} 页的第 {index + 1} 行为空，已跳过。")

        # 点击下一页
        page.get_by_role("link", name="下一页").click()

    # 检查是否提取到了数据
    if not data:
        print("未能提取到表格数据。请检查选择器或页面结构。")
        return

    # 创建 DataFrame 并导出 CSV
    df = pd.DataFrame(data, columns=headers)

    # df.to_csv('output.csv', index=False, encoding='utf-8-sig')
    # print('数据已成功写入 output.csv')
    return df


def run(playwright: Playwright, f) -> None:
    browser = playwright.chromium.launch(headless=True, args=["--start-maximized"], slow_mo=500)

    kwargs = {
        "java_script_enabled": True,
        "viewport": {"width": 1920, "height": 1080},
        "no_viewport": True,
    }
    contex = browser.new_context(**kwargs)
    page = contex.new_page()

    f(page)

    page.close()
    browser.close()


if __name__ == '__main__':
    with sync_playwright() as playwright:
        run(playwright, run_task)

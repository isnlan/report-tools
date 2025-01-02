import base64
from datetime import datetime
import pandas as pd

import ddddocr
import csv

from playwright.sync_api import sync_playwright, Page, Browser, Playwright


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

    # 获取验证码
    code = get_code(page)
    page.locator("input[name=\"captcha\"]").fill(code)
    page.get_by_role("button", name="查询").click()


    get_table(page)


def get_table(page: Page):
    # 定位到表格元素
    table_selector = 'div.BOC_main.publish table'
    page.wait_for_selector(table_selector)

    # 提取表头
    headers = []
    # 尝试从 thead 获取表头
    thead = page.query_selector(f'{table_selector} thead')
    if thead:
        header_elements = thead.query_selector_all('tr th')
        headers = [th.inner_text().strip() for th in header_elements]
    else:
        # 如果没有 thead，尝试从 tbody 的第一行获取表头
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
    # 获取所有数据行（跳过表头行）
    rows = page.query_selector_all(f'{table_selector} tbody tr')
    for index, row in enumerate(rows):
        # 如果 thead 不存在且这是第一行，则跳过（表头行）
        if not thead and index == 0:
            continue
        cells = row.query_selector_all('td')
        if not cells:
            # 如果没有 td，跳过该行
            continue
        row_data = [cell.inner_text().strip() for cell in cells]
        data.append(row_data)


    # 检查是否提取到了数据
    if not data:
        print("未能提取到表格数据。请检查选择器或页面结构。")
        return

    # 创建 DataFrame 并导出 CSV
    df = pd.DataFrame(data, columns=headers)
    df.to_csv('output.csv', index=False, encoding='utf-8-sig')
    print('数据已成功写入 output.csv')


def run(playwright: Playwright, f) -> None:
    browser = playwright.chromium.launch(headless=False, args=["--start-maximized"], slow_mo=500)

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

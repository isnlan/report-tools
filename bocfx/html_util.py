from bs4 import BeautifulSoup


def get_table(page_content: str, selector: str):
    # 提取表格数据
    data = []

    soup = BeautifulSoup(page_content, 'html.parser')

    # 定位表格
    table = soup.select_one(selector)
    if not table:
        return data

    # 获取所有数据行（跳过表头行）
    rows = table.select('tbody tr')
    for index, row in enumerate(rows):
        # 如果这是第一行，则跳过（表头行）
        if index == 0:
            continue

        # 获取单元格数据
        cells = row.select('td')
        if not cells:
            continue

        row_data = [cell.get_text(strip=True) for cell in cells]
        # 检查所有单元格是否为空字符串
        if not all((cell == '' or cell is None) for cell in row_data):
            data.append(row_data)

    return data

# 这是使用python写的一个报表工具

### 1、安装虚拟环境

```shell
python -m venv venv
```

#### 激活虚拟环境
##### 1、windows：
```shell
venv\Scripts\activate
```

##### 2、linux or mac
```shell
source venv/bin/activate
```

### 3、安装依赖
```shell
pip install numpy
pip install openpyxl
pip install pandas
pip install XlsxWriter
pip install requests
pip install playwright
pip install ddddocr
pip install bs4
pip install chinese_calendar
playwright install
```

### 2、安装依赖
```shell
pip install -r requirements.txt
```

### 3、保存依赖
```shell
pip freeze > requirements.txt
```

```shell
python -m playwright codegen --save-storage=auth.json --target python -o examples/test.py -b chromium https://srh.bankofchina.com/search/whpj/search_cn.jsp
python -m playwright codegen --load-storage=auth.json --target python -o examples/test.py -b chromium https://srh.bankofchina.com/search/whpj/search_cn.jsp
```
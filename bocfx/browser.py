import threading

from playwright.sync_api import sync_playwright


class BrowserSingleton:
    browser = None

    @classmethod
    def get_browser(cls):
        if cls.browser is None:
            print("Launching a new browser instance...")
            pw = sync_playwright().start()
            cls.browser = pw.chromium.launch(headless=False, args=["--start-maximized"], slow_mo=500)

        return cls.browser


# 创建线程本地存储
thread_local = threading.local()


def get_page():
    # 在每个线程中创建独立的浏览器实例
    if not hasattr(thread_local, 'page'):
        print("Launching a new browser instance...")
        pw = sync_playwright().start()
        thread_local.browser = pw.chromium.launch(headless=True, args=["--start-maximized"], slow_mo=500)
        thread_local.context = thread_local.browser.new_context()  # 创建一个新的上下文
        thread_local.page = thread_local.context.new_page()  # 创建一个新的页面


    return thread_local.page

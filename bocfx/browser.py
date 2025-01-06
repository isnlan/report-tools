from playwright.sync_api import sync_playwright


class BrowserSingleton:
    _browser_instance = None

    @classmethod
    def get_browser(cls):
        if cls._browser_instance is None:
            print("Launching a new browser instance...")
            with sync_playwright() as p:
                cls._browser_instance = p.chromium.launch(headless=False, args=["--start-maximized"], slow_mo=500)  # 这里可以选择 Chromium, Firefox, WebKit
        return cls._browser_instance
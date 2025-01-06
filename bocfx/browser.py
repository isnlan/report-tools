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

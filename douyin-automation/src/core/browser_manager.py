"""浏览器实例管理模块"""

from pathlib import Path
from typing import Optional, Literal
from DrissionPage import ChromiumPage, ChromiumOptions

from .account_manager import AccountManager


PlatformType = Literal['baiying', 'douyin', 'douyin_creator']


class BrowserManager:
    """浏览器实例管理器

    每个账户的每个平台拥有独立的浏览器配置目录，
    实现Cookie和会话的持久化。
    """

    # 平台对应的起始URL
    PLATFORM_URLS = {
        'baiying': 'https://buyin.jinritemai.com/',
        'douyin': 'https://www.douyin.com/',
        'douyin_creator': 'https://creator.douyin.com/',
    }

    def __init__(self, account_manager: AccountManager):
        """初始化浏览器管理器

        Args:
            account_manager: 账户管理器实例
        """
        self.account_manager = account_manager
        self._browsers: dict[str, ChromiumPage] = {}  # key: account_id:platform

    def _get_browser_key(self, account_id: str, platform: PlatformType) -> str:
        """生成浏览器实例的唯一键"""
        return f"{account_id}:{platform}"

    def get_browser(
        self,
        account_id: str,
        platform: PlatformType,
        headless: bool = False,
        reuse: bool = True
    ) -> ChromiumPage:
        """获取指定账户和平台的浏览器实例

        Args:
            account_id: 账户ID
            platform: 平台类型
            headless: 是否无头模式
            reuse: 是否复用已有实例

        Returns:
            ChromiumPage实例
        """
        key = self._get_browser_key(account_id, platform)

        # 检查是否有可复用的实例
        if reuse and key in self._browsers:
            browser = self._browsers[key]
            try:
                # 检查浏览器是否还活着
                _ = browser.url
                return browser
            except Exception:
                # 浏览器已关闭，移除引用
                del self._browsers[key]

        # 获取浏览器配置目录
        profile_path = self.account_manager.get_browser_profile_path(account_id, platform)
        if profile_path is None:
            raise ValueError(f"账户 {account_id} 不存在")

        # 创建浏览器选项
        co = ChromiumOptions()
        co.set_user_data_path(str(profile_path))

        if headless:
            co.headless()

        # 反检测设置
        co.set_argument('--disable-blink-features=AutomationControlled')
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')

        # 创建浏览器实例
        browser = ChromiumPage(co)
        self._browsers[key] = browser

        # 标记账户为最近使用
        self.account_manager.mark_account_used(account_id)

        return browser

    def navigate_to_platform(
        self,
        account_id: str,
        platform: PlatformType,
        headless: bool = False
    ) -> ChromiumPage:
        """打开浏览器并导航到指定平台

        Args:
            account_id: 账户ID
            platform: 平台类型
            headless: 是否无头模式

        Returns:
            已导航到平台的ChromiumPage实例
        """
        browser = self.get_browser(account_id, platform, headless)
        url = self.PLATFORM_URLS.get(platform)
        if url:
            browser.get(url)
        return browser

    def close_browser(self, account_id: str, platform: PlatformType) -> None:
        """关闭指定浏览器实例

        Args:
            account_id: 账户ID
            platform: 平台类型
        """
        key = self._get_browser_key(account_id, platform)
        if key in self._browsers:
            try:
                self._browsers[key].quit()
            except Exception:
                pass
            del self._browsers[key]

    def close_all_browsers(self, account_id: Optional[str] = None) -> None:
        """关闭所有浏览器实例

        Args:
            account_id: 如果指定，只关闭该账户的浏览器
        """
        keys_to_remove = []
        for key, browser in self._browsers.items():
            if account_id is None or key.startswith(f"{account_id}:"):
                try:
                    browser.quit()
                except Exception:
                    pass
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self._browsers[key]

    def is_logged_in(self, account_id: str, platform: PlatformType) -> bool:
        """检查是否已登录

        Args:
            account_id: 账户ID
            platform: 平台类型

        Returns:
            是否已登录
        """
        try:
            browser = self.get_browser(account_id, platform, reuse=True)
            current_url = browser.url

            # 根据平台检查登录状态
            if platform == 'baiying':
                # 检查是否在登录页
                return 'login' not in current_url.lower()
            elif platform == 'douyin':
                # 检查是否有登录按钮
                login_btn = browser.ele('xpath://button[contains(text(), "登录")]', timeout=1)
                return login_btn is None
            elif platform == 'douyin_creator':
                # 检查是否在登录页
                return 'login' not in current_url.lower()

            return False
        except Exception:
            return False

    def wait_for_login(
        self,
        account_id: str,
        platform: PlatformType,
        timeout: float = 300
    ) -> bool:
        """等待用户手动登录

        Args:
            account_id: 账户ID
            platform: 平台类型
            timeout: 超时时间(秒)

        Returns:
            是否登录成功
        """
        import time
        browser = self.navigate_to_platform(account_id, platform)

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_logged_in(account_id, platform):
                return True
            time.sleep(2)

        return False

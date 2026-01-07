"""浏览器实例管理模块"""

import shutil
import zipfile
import json
from pathlib import Path
from typing import Optional, Literal, List
from datetime import datetime
from DrissionPage import ChromiumPage, ChromiumOptions

from .account_manager import AccountManager
from .builtin_browser import get_browser_executable


PlatformType = Literal['baiying', 'douyin', 'douyin_creator']


class BrowserManager:
    """浏览器实例管理器

    每个账户的每个平台拥有独立的浏览器配置目录，
    实现Cookie和会话的持久化。
    """

    # 平台对应的起始URL
    PLATFORM_URLS = {
        'baiying': 'https://buyin.jinritemai.com/mpa/account/login?log_out=1&type=24',
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

        # 确保目录存在
        profile_path.mkdir(parents=True, exist_ok=True)

        # 创建浏览器选项
        co = ChromiumOptions()

        # 使用内置浏览器
        browser_path = get_browser_executable()
        co.set_browser_path(browser_path)

        # 设置用户数据目录 - 这是保存登录状态的关键
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

    # ========== Profile 导入/导出功能 ==========

    def export_profile(
        self,
        account_id: str,
        platform: PlatformType,
        output_path: Path,
        include_cache: bool = False
    ) -> Path:
        """导出浏览器 profile (Cookie、登录状态等)

        Args:
            account_id: 账户ID
            platform: 平台类型
            output_path: 导出文件路径 (不含扩展名)
            include_cache: 是否包含缓存文件 (会增大文件体积)

        Returns:
            导出的 zip 文件路径
        """
        # 先关闭该平台的浏览器，确保数据已保存
        self.close_browser(account_id, platform)

        profile_path = self.account_manager.get_browser_profile_path(account_id, platform)
        if profile_path is None or not profile_path.exists():
            raise ValueError(f"账户 {account_id} 的 {platform} profile 不存在")

        # 确保输出目录存在
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 生成 zip 文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"{output_path.stem}_{account_id}_{platform}_{timestamp}.zip"
        zip_path = output_path.parent / zip_filename

        # 需要排除的目录/文件 (减小文件体积)
        exclude_patterns = [
            'Cache',
            'Code Cache',
            'GPUCache',
            'ShaderCache',
            'Service Worker',
            'blob_storage',
            'IndexedDB',
            '*.log',
            '*.tmp',
        ]

        if not include_cache:
            exclude_patterns.extend([
                'Media Cache',
                'GrShaderCache',
            ])

        # 创建 metadata
        metadata = {
            'version': '1.0',
            'account_id': account_id,
            'platform': platform,
            'exported_at': datetime.now().isoformat(),
            'include_cache': include_cache,
        }

        # 创建 zip 文件
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 写入 metadata
            zf.writestr('_metadata.json', json.dumps(metadata, ensure_ascii=False, indent=2))

            # 遍历 profile 目录
            for file_path in profile_path.rglob('*'):
                if file_path.is_file():
                    # 检查是否需要排除
                    relative_path = file_path.relative_to(profile_path)
                    should_exclude = False

                    for pattern in exclude_patterns:
                        if pattern.startswith('*'):
                            if file_path.suffix == pattern[1:]:
                                should_exclude = True
                                break
                        elif pattern in str(relative_path):
                            should_exclude = True
                            break

                    if not should_exclude:
                        try:
                            zf.write(file_path, f'profile/{relative_path}')
                        except (PermissionError, OSError):
                            # 跳过被锁定的文件
                            pass

        return zip_path

    def import_profile(
        self,
        account_id: str,
        platform: PlatformType,
        zip_path: Path,
        overwrite: bool = True
    ) -> bool:
        """导入浏览器 profile

        Args:
            account_id: 账户ID
            platform: 平台类型
            zip_path: 要导入的 zip 文件路径
            overwrite: 是否覆盖现有 profile

        Returns:
            是否导入成功
        """
        zip_path = Path(zip_path)
        if not zip_path.exists():
            raise FileNotFoundError(f"文件不存在: {zip_path}")

        # 先关闭该平台的浏览器
        self.close_browser(account_id, platform)

        profile_path = self.account_manager.get_browser_profile_path(account_id, platform)
        if profile_path is None:
            raise ValueError(f"账户 {account_id} 不存在")

        # 读取并验证 metadata
        with zipfile.ZipFile(zip_path, 'r') as zf:
            try:
                metadata_content = zf.read('_metadata.json').decode('utf-8')
                metadata = json.loads(metadata_content)
            except (KeyError, json.JSONDecodeError):
                raise ValueError("无效的 profile 文件: 缺少或损坏的 metadata")

            # 验证版本
            if metadata.get('version') != '1.0':
                raise ValueError(f"不支持的 profile 版本: {metadata.get('version')}")

            # 如果覆盖，先清空目录
            if overwrite and profile_path.exists():
                shutil.rmtree(profile_path)

            profile_path.mkdir(parents=True, exist_ok=True)

            # 解压 profile 文件
            for member in zf.namelist():
                if member.startswith('profile/') and not member.endswith('/'):
                    # 获取相对路径
                    relative_path = member[len('profile/'):]
                    target_path = profile_path / relative_path

                    # 创建目录
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    # 解压文件
                    with zf.open(member) as src, open(target_path, 'wb') as dst:
                        dst.write(src.read())

        return True

    def export_all_profiles(
        self,
        account_id: str,
        output_dir: Path,
        include_cache: bool = False
    ) -> List[Path]:
        """导出账户的所有平台 profile

        Args:
            account_id: 账户ID
            output_dir: 导出目录
            include_cache: 是否包含缓存

        Returns:
            导出的 zip 文件路径列表
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exported_files = []
        for platform in ['baiying', 'douyin', 'douyin_creator']:
            profile_path = self.account_manager.get_browser_profile_path(account_id, platform)
            if profile_path and profile_path.exists():
                try:
                    zip_path = self.export_profile(
                        account_id,
                        platform,
                        output_dir / 'profile',
                        include_cache
                    )
                    exported_files.append(zip_path)
                except Exception:
                    pass  # 跳过失败的平台

        return exported_files

    def get_profile_info(self, account_id: str, platform: PlatformType) -> Optional[dict]:
        """获取 profile 信息

        Args:
            account_id: 账户ID
            platform: 平台类型

        Returns:
            profile 信息字典，不存在返回 None
        """
        profile_path = self.account_manager.get_browser_profile_path(account_id, platform)
        if profile_path is None or not profile_path.exists():
            return None

        # 计算目录大小
        total_size = 0
        file_count = 0
        for f in profile_path.rglob('*'):
            if f.is_file():
                total_size += f.stat().st_size
                file_count += 1

        # 检查关键文件
        has_cookies = (profile_path / 'Default' / 'Cookies').exists() or \
                      (profile_path / 'Cookies').exists()
        has_local_storage = (profile_path / 'Default' / 'Local Storage').exists() or \
                           (profile_path / 'Local Storage').exists()

        return {
            'path': str(profile_path),
            'size_bytes': total_size,
            'size_mb': round(total_size / 1024 / 1024, 2),
            'file_count': file_count,
            'has_cookies': has_cookies,
            'has_local_storage': has_local_storage,
        }

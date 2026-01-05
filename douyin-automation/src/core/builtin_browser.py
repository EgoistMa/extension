"""内置浏览器管理模块

自动下载和管理独立的 Chromium 浏览器，不依赖系统安装的浏览器。
"""

import os
import sys
import zipfile
import stat
import shutil
from pathlib import Path
from typing import Optional
import urllib.request
import json


class BuiltinBrowser:
    """内置浏览器管理器

    负责下载、安装和管理项目自带的 Chromium 浏览器。
    """

    # Chromium 下载源 (使用 playwright 的 CDN)
    CHROMIUM_REVISION = "1148"  # Chromium 版本号

    # 不同平台的下载配置
    PLATFORM_CONFIG = {
        "win32": {
            "url": "https://playwright.azureedge.net/builds/chromium/{revision}/chromium-win64.zip",
            "executable": "chrome-win/chrome.exe",
            "zip_root": "chrome-win",
        },
        "win64": {
            "url": "https://playwright.azureedge.net/builds/chromium/{revision}/chromium-win64.zip",
            "executable": "chrome-win/chrome.exe",
            "zip_root": "chrome-win",
        },
        "darwin": {
            "url": "https://playwright.azureedge.net/builds/chromium/{revision}/chromium-mac.zip",
            "executable": "chrome-mac/Chromium.app/Contents/MacOS/Chromium",
            "zip_root": "chrome-mac",
        },
        "linux": {
            "url": "https://playwright.azureedge.net/builds/chromium/{revision}/chromium-linux.zip",
            "executable": "chrome-linux/chrome",
            "zip_root": "chrome-linux",
        },
    }

    def __init__(self, base_dir: Optional[Path] = None):
        """初始化

        Args:
            base_dir: 浏览器安装目录，默认为项目下的 browser 目录
        """
        if base_dir is None:
            # 默认安装在项目根目录下的 browser 文件夹
            base_dir = Path(__file__).parent.parent.parent / "browser"

        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # 确定当前平台
        self.platform = self._get_platform()
        self.config = self.PLATFORM_CONFIG.get(self.platform)

        if not self.config:
            raise RuntimeError(f"不支持的平台: {self.platform}")

    def _get_platform(self) -> str:
        """获取当前平台标识"""
        if sys.platform == "win32":
            return "win64" if sys.maxsize > 2**32 else "win32"
        elif sys.platform == "darwin":
            return "darwin"
        elif sys.platform.startswith("linux"):
            return "linux"
        return sys.platform

    @property
    def browser_dir(self) -> Path:
        """浏览器安装目录"""
        return self.base_dir / f"chromium-{self.CHROMIUM_REVISION}"

    @property
    def executable_path(self) -> Path:
        """浏览器可执行文件路径"""
        return self.browser_dir / self.config["executable"]

    def is_installed(self) -> bool:
        """检查浏览器是否已安装"""
        return self.executable_path.exists()

    def get_executable(self) -> str:
        """获取浏览器可执行文件路径

        如果未安装，会自动下载安装。

        Returns:
            浏览器可执行文件的绝对路径
        """
        if not self.is_installed():
            self.download_and_install()
        return str(self.executable_path.absolute())

    def download_and_install(self, progress_callback=None) -> None:
        """下载并安装浏览器

        Args:
            progress_callback: 进度回调函数 (downloaded, total) -> None
        """
        url = self.config["url"].format(revision=self.CHROMIUM_REVISION)
        zip_path = self.base_dir / f"chromium-{self.CHROMIUM_REVISION}.zip"

        print(f"正在下载内置浏览器...")
        print(f"URL: {url}")

        try:
            # 下载文件
            self._download_file(url, zip_path, progress_callback)

            print(f"正在解压...")

            # 解压
            self._extract_zip(zip_path, self.browser_dir)

            # 设置可执行权限 (Linux/Mac)
            if self.platform in ("darwin", "linux"):
                self._set_executable_permission(self.executable_path)

            # 清理 zip 文件
            zip_path.unlink()

            print(f"内置浏览器安装完成: {self.executable_path}")

        except Exception as e:
            # 清理失败的安装
            if zip_path.exists():
                zip_path.unlink()
            if self.browser_dir.exists():
                shutil.rmtree(self.browser_dir)
            raise RuntimeError(f"浏览器安装失败: {e}")

    def _download_file(self, url: str, dest: Path, progress_callback=None) -> None:
        """下载文件"""

        def reporthook(block_num, block_size, total_size):
            if progress_callback and total_size > 0:
                downloaded = block_num * block_size
                progress_callback(downloaded, total_size)

        urllib.request.urlretrieve(url, dest, reporthook=reporthook if progress_callback else None)

    def _extract_zip(self, zip_path: Path, dest_dir: Path) -> None:
        """解压 zip 文件"""
        dest_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(dest_dir)

    def _set_executable_permission(self, path: Path) -> None:
        """设置可执行权限"""
        current = os.stat(path)
        os.chmod(path, current.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def uninstall(self) -> None:
        """卸载浏览器"""
        if self.browser_dir.exists():
            shutil.rmtree(self.browser_dir)
            print(f"已卸载内置浏览器")

    def get_version_info(self) -> dict:
        """获取浏览器版本信息"""
        return {
            "revision": self.CHROMIUM_REVISION,
            "platform": self.platform,
            "installed": self.is_installed(),
            "path": str(self.executable_path) if self.is_installed() else None,
        }


# 全局单例
_builtin_browser: Optional[BuiltinBrowser] = None


def get_builtin_browser() -> BuiltinBrowser:
    """获取内置浏览器管理器单例"""
    global _builtin_browser
    if _builtin_browser is None:
        _builtin_browser = BuiltinBrowser()
    return _builtin_browser


def get_browser_executable() -> str:
    """获取内置浏览器可执行文件路径

    这是最常用的接口，会自动下载安装浏览器（如果未安装）。

    Returns:
        浏览器可执行文件的绝对路径
    """
    return get_builtin_browser().get_executable()

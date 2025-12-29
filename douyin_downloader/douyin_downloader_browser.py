#!/usr/bin/env python3
"""
抖音视频下载器 - 浏览器版本
使用 DrissionPage 自动化浏览器，绕过反爬验证
"""

import re
import json
import time
import argparse
from pathlib import Path
from urllib.parse import unquote

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
except ImportError:
    print("请先安装 DrissionPage: pip install DrissionPage")
    exit(1)


class DouyinBrowserDownloader:
    """使用浏览器自动化的抖音视频下载器"""

    def __init__(self, headless: bool = True, debug: bool = False):
        """
        初始化下载器

        Args:
            headless: 是否使用无头模式
            debug: 是否启用调试模式
        """
        self.debug = debug
        self.headless = headless
        self.page = None

    def _find_chrome_path(self) -> str:
        """查找 Chrome 浏览器路径"""
        import os
        import platform

        possible_paths = []

        if platform.system() == 'Windows':
            possible_paths = [
                os.path.expandvars(r'%ProgramFiles%\Google\Chrome\Application\chrome.exe'),
                os.path.expandvars(r'%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe'),
                os.path.expandvars(r'%LocalAppData%\Google\Chrome\Application\chrome.exe'),
                r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                # Edge 作为备选
                os.path.expandvars(r'%ProgramFiles%\Microsoft\Edge\Application\msedge.exe'),
                os.path.expandvars(r'%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe'),
            ]
        elif platform.system() == 'Darwin':  # macOS
            possible_paths = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '/Applications/Chromium.app/Contents/MacOS/Chromium',
            ]
        else:  # Linux
            possible_paths = [
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable',
                '/usr/bin/chromium',
                '/usr/bin/chromium-browser',
            ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def _init_browser(self):
        """初始化浏览器"""
        if self.page:
            return

        co = ChromiumOptions()

        # 查找并设置浏览器路径
        chrome_path = self._find_chrome_path()
        if chrome_path:
            if self.debug:
                print(f"[DEBUG] 找到浏览器: {chrome_path}")
            co.set_browser_path(chrome_path)
        else:
            print("警告: 未找到 Chrome/Edge 浏览器，请确保已安装")

        if self.headless:
            # 使用新版无头模式 (Chrome 109+)，更难被检测
            co.set_argument('--headless=new')

        # 反无头检测参数
        co.set_argument('--disable-blink-features=AutomationControlled')
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-gpu')
        co.set_argument('--disable-infobars')
        co.set_argument('--disable-extensions')
        co.set_argument('--disable-popup-blocking')

        # 设置窗口大小（无头模式下也需要）
        co.set_argument('--window-size=1920,1080')

        # 设置真实的 User-Agent
        co.set_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # 忽略证书错误
        co.set_argument('--ignore-certificate-errors')

        self.page = ChromiumPage(co)

        # 注入 JavaScript 隐藏 webdriver 特征
        try:
            self.page.run_js('''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
                window.chrome = {runtime: {}};
            ''')
        except Exception:
            pass

        if self.debug:
            print(f"[DEBUG] 浏览器已初始化, headless={self.headless}")

    def extract_aweme_id(self, url: str) -> str:
        """从 URL 中提取视频 ID"""
        patterns = [
            r'/video/(\d+)',
            r'/note/(\d+)',
            r'modal_id=(\d+)',
            r'/(\d{19})(?:\?|$|/)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        if url.isdigit() and len(url) >= 18:
            return url

        raise ValueError(f"无法从 URL 中提取视频 ID: {url}")

    def get_video_info(self, aweme_id: str) -> dict:
        """获取视频信息"""
        self._init_browser()

        video_url = f"https://www.douyin.com/video/{aweme_id}"

        if self.debug:
            print(f"[DEBUG] 正在访问: {video_url}")

        self.page.get(video_url)

        # 等待页面加载
        time.sleep(3)

        if self.debug:
            print(f"[DEBUG] 页面标题: {self.page.title}")
            print(f"[DEBUG] 页面 URL: {self.page.url}")
            html_len = len(self.page.html) if self.page.html else 0
            print(f"[DEBUG] 页面长度: {html_len}")

        # 等待视频加载（最多等待 20 秒）
        for i in range(20):
            if self.debug and i % 5 == 0:
                print(f"[DEBUG] 尝试提取... ({i+1}/20)")

            # 尝试从 RENDER_DATA 提取
            try:
                render_script = self.page.ele('#RENDER_DATA', timeout=1)
                if render_script:
                    render_text = render_script.text
                    if render_text and len(render_text) > 100:
                        if self.debug:
                            print(f"[DEBUG] RENDER_DATA 长度: {len(render_text)}")
                        data = json.loads(unquote(render_text))
                        detail = self._find_aweme_detail(data)
                        if detail:
                            if self.debug:
                                print(f"[DEBUG] 从 RENDER_DATA 提取成功")
                            return detail
            except Exception as e:
                if self.debug and i == 0:
                    print(f"[DEBUG] RENDER_DATA 提取失败: {e}")

            # 尝试直接获取视频元素的 src
            try:
                video_ele = self.page.ele('tag:video', timeout=1)
                if video_ele:
                    video_src = video_ele.attr('src')
                    if self.debug and i == 0:
                        print(f"[DEBUG] video src: {video_src[:100] if video_src else 'None'}...")
                    if video_src and ('douyin' in video_src or 'douyinvod' in video_src or video_src.startswith('http')):
                        if self.debug:
                            print(f"[DEBUG] 从 video 元素提取成功")
                        return {
                            'aweme_id': aweme_id,
                            'video': {'play_addr': {'url_list': [video_src]}},
                            'desc': self._get_title() or aweme_id,
                            'author': {'nickname': 'unknown'}
                        }
            except Exception:
                pass

            # 尝试从 source 元素获取
            try:
                source_ele = self.page.ele('tag:source', timeout=1)
                if source_ele:
                    source_src = source_ele.attr('src')
                    if source_src and source_src.startswith('http'):
                        if self.debug:
                            print(f"[DEBUG] 从 source 元素提取成功: {source_src[:80]}...")
                        return {
                            'aweme_id': aweme_id,
                            'video': {'play_addr': {'url_list': [source_src]}},
                            'desc': self._get_title() or aweme_id,
                            'author': {'nickname': 'unknown'}
                        }
            except Exception:
                pass

            time.sleep(1)

        # 最后尝试：打印页面内容帮助调试
        if self.debug:
            print(f"[DEBUG] 最终页面 HTML 前 2000 字符:")
            print(self.page.html[:2000] if self.page.html else "无内容")

        raise Exception("无法获取视频信息，请检查视频 ID 是否正确，或尝试 --no-headless 模式")

    def _get_title(self) -> str:
        """尝试获取视频标题"""
        try:
            title_ele = self.page.ele('tag:title')
            if title_ele:
                return title_ele.text.split(' - ')[0]
        except Exception:
            pass
        return None

    def _find_aweme_detail(self, data, depth=0) -> dict:
        """递归查找视频详情"""
        if depth > 10:
            return None

        if isinstance(data, dict):
            if 'aweme_id' in data and 'video' in data:
                return data

            for key in ['aweme_detail', 'awemeDetail', 'detail', 'aweme']:
                if key in data:
                    val = data[key]
                    if isinstance(val, dict):
                        if 'aweme_id' in val or 'video' in val:
                            return val
                        if 'detail' in val:
                            return val.get('detail')

            for value in data.values():
                result = self._find_aweme_detail(value, depth + 1)
                if result:
                    return result

        elif isinstance(data, list):
            for item in data:
                result = self._find_aweme_detail(item, depth + 1)
                if result:
                    return result

        return None

    def get_video_url(self, video_info: dict) -> str:
        """提取视频 URL"""
        # 优先从 bit_rate 获取最高画质
        try:
            bit_rates = video_info.get('video', {}).get('bit_rate', [])
            if bit_rates:
                sorted_rates = sorted(
                    bit_rates,
                    key=lambda x: x.get('play_addr', {}).get('width', 0),
                    reverse=True
                )
                if sorted_rates:
                    url_list = sorted_rates[0].get('play_addr', {}).get('url_list', [])
                    if url_list:
                        for url in url_list:
                            if 'douyin.com' in url:
                                return url
                        return url_list[0]
        except Exception:
            pass

        # 回退到 play_addr
        try:
            url_list = video_info.get('video', {}).get('play_addr', {}).get('url_list', [])
            if url_list:
                if len(url_list) > 2:
                    return url_list[2]
                return url_list[0]
        except Exception:
            pass

        raise Exception("无法提取视频 URL")

    def download_video(self, video_url: str, output_path: str = None, aweme_id: str = None) -> str:
        """下载视频"""
        import requests

        video_url = video_url.replace('http:', 'https:')

        if not output_path:
            filename = f"douyin_{aweme_id or int(time.time())}.mp4"
            output_path = str(Path.cwd() / filename)

        print(f"开始下载: {video_url[:80]}...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Referer': 'https://www.douyin.com/',
        }

        resp = requests.get(video_url, headers=headers, stream=True, timeout=60)
        resp.raise_for_status()

        total_size = int(resp.headers.get('content-length', 0))
        downloaded = 0

        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        print(f"\r下载进度: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')

        print(f"\n下载完成: {output_path}")
        return output_path

    def download(self, url: str, output_path: str = None) -> str:
        """主下载入口"""
        print(f"正在解析: {url}")

        aweme_id = self.extract_aweme_id(url)
        print(f"视频 ID: {aweme_id}")

        print("正在获取视频详情（使用浏览器）...")
        video_info = self.get_video_info(aweme_id)

        title = video_info.get('desc', '无标题')[:50]
        author = video_info.get('author', {}).get('nickname', '未知')
        print(f"标题: {title}")
        print(f"作者: {author}")

        video_url = self.get_video_url(video_info)
        print(f"视频 URL: {video_url[:80]}...")

        return self.download_video(video_url, output_path, aweme_id)

    def close(self):
        """关闭浏览器"""
        if self.page:
            try:
                self.page.quit()
            except Exception:
                pass
            self.page = None


def main():
    parser = argparse.ArgumentParser(
        description='抖音视频下载器 (浏览器版本)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python douyin_downloader_browser.py https://www.douyin.com/video/7123456789012345678
  python douyin_downloader_browser.py <url> -o my_video.mp4
  python douyin_downloader_browser.py <url> --no-headless  # 显示浏览器窗口
        '''
    )
    parser.add_argument('url', help='抖音视频 URL 或视频 ID')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('--no-headless', action='store_true', help='显示浏览器窗口（调试用）')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')

    args = parser.parse_args()

    downloader = None
    try:
        downloader = DouyinBrowserDownloader(
            headless=not args.no_headless,
            debug=args.debug
        )
        output_file = downloader.download(args.url, args.output)
        print(f"\n成功! 文件已保存到: {output_file}")
    except Exception as e:
        print(f"\n错误: {e}")
        return 1
    finally:
        if downloader:
            downloader.close()

    return 0


if __name__ == '__main__':
    exit(main())

#!/usr/bin/env python3
"""
抖音搜索视频下载器
从搜索页面筛选并下载符合条件的视频
"""

import re
import json
import time
import argparse
from pathlib import Path
from urllib.parse import unquote, quote
from dataclasses import dataclass
from typing import List, Optional

try:
    from DrissionPage import ChromiumPage, ChromiumOptions
except ImportError:
    print("请先安装 DrissionPage: pip install DrissionPage")
    exit(1)

import requests


@dataclass
class VideoInfo:
    """视频信息"""
    aweme_id: str
    title: str
    author: str
    duration: float  # 秒
    digg_count: int  # 点赞数
    play_count: int  # 播放数
    video_url: str = ""
    cover_url: str = ""
    create_time: int = 0  # 发布时间戳


class DouyinSearchDownloader:
    """抖音搜索下载器"""

    def __init__(self, headless: bool = False, debug: bool = False):
        self.headless = headless
        self.debug = debug
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
                os.path.expandvars(r'%ProgramFiles%\Microsoft\Edge\Application\msedge.exe'),
                os.path.expandvars(r'%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe'),
            ]
        elif platform.system() == 'Darwin':
            possible_paths = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            ]
        else:
            possible_paths = [
                '/usr/bin/google-chrome',
                '/usr/bin/google-chrome-stable',
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

        chrome_path = self._find_chrome_path()
        if chrome_path:
            if self.debug:
                print(f"[DEBUG] 找到浏览器: {chrome_path}")
            co.set_browser_path(chrome_path)

        if self.headless:
            co.set_argument('--headless=new')

        # 反检测参数
        co.set_argument('--disable-blink-features=AutomationControlled')
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-gpu')
        co.set_argument('--window-size=1920,1080')
        co.set_argument('--start-maximized')
        co.set_argument('--disable-infobars')
        co.set_argument('--disable-extensions')
        co.set_argument('--ignore-certificate-errors')
        co.set_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # 设置偏好
        co.set_pref('credentials_enable_service', False)
        co.set_pref('profile.password_manager_enabled', False)

        self.page = ChromiumPage(co)

        # 注入反检测脚本
        try:
            self.page.run_js('''
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
                window.chrome = {runtime: {}};
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                    Promise.resolve({state: Notification.permission}) :
                    originalQuery(parameters)
                );
            ''')
        except Exception:
            pass

        if self.debug:
            print(f"[DEBUG] 浏览器已初始化, headless={self.headless}")

    def search_videos(self, search_url: str, scroll_times: int = 3) -> List[VideoInfo]:
        """
        从搜索页面获取视频列表

        Args:
            search_url: 搜索页面 URL
            scroll_times: 滚动次数，用于加载更多内容

        Returns:
            视频信息列表
        """
        self._init_browser()

        if self.debug:
            print(f"[DEBUG] 访问搜索页面: {search_url}")

        self.page.get(search_url)
        time.sleep(3)

        videos = []

        # 滚动页面加载更多内容
        for i in range(scroll_times):
            if self.debug:
                print(f"[DEBUG] 滚动页面 ({i + 1}/{scroll_times})...")

            self.page.scroll.to_bottom()
            time.sleep(2)

            # 尝试从 RENDER_DATA 提取
            videos = self._extract_videos_from_page()
            if videos:
                if self.debug:
                    print(f"[DEBUG] 已找到 {len(videos)} 个视频")

        return videos

    def _extract_videos_from_page(self) -> List[VideoInfo]:
        """从页面提取视频信息"""
        videos = []

        if self.debug:
            print(f"[DEBUG] 页面标题: {self.page.title}")
            print(f"[DEBUG] 页面 URL: {self.page.url}")
            html_len = len(self.page.html) if self.page.html else 0
            print(f"[DEBUG] 页面长度: {html_len}")

        # 方法1: 从 RENDER_DATA 提取
        try:
            render_script = self.page.ele('#RENDER_DATA', timeout=2)
            if render_script:
                render_text = render_script.text
                if render_text:
                    if self.debug:
                        print(f"[DEBUG] RENDER_DATA 长度: {len(render_text)}")
                    data = json.loads(unquote(render_text))
                    videos = self._parse_search_data(data)
                    if self.debug:
                        print(f"[DEBUG] 从 RENDER_DATA 解析到 {len(videos)} 个视频")
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] RENDER_DATA 解析失败: {e}")

        # 方法2: 从页面 HTML 中搜索视频数据
        if not videos:
            try:
                html = self.page.html
                # 搜索 aweme_id 模式
                aweme_ids = re.findall(r'"aweme_id"\s*:\s*"(\d+)"', html)
                if self.debug:
                    print(f"[DEBUG] 从 HTML 找到 {len(set(aweme_ids))} 个 aweme_id")

                # 尝试找到完整的 JSON 数据块
                json_matches = re.findall(r'\{"aweme_id"[^}]+?"statistics"[^}]+?\}', html)
                if self.debug:
                    print(f"[DEBUG] 找到 {len(json_matches)} 个 JSON 块")
            except Exception as e:
                if self.debug:
                    print(f"[DEBUG] HTML 搜索失败: {e}")

        # 方法3: 从视频卡片元素提取
        if not videos:
            videos = self._extract_from_cards()

        return videos

    def _extract_from_cards(self) -> List[VideoInfo]:
        """从页面视频卡片元素提取"""
        videos = []
        try:
            # 尝试找视频卡片链接
            video_links = self.page.eles('tag:a@href^=/video/', timeout=2)
            if self.debug:
                print(f"[DEBUG] 找到 {len(video_links)} 个视频链接")

            seen_ids = set()
            for link in video_links:
                href = link.attr('href')
                if href:
                    match = re.search(r'/video/(\d+)', href)
                    if match:
                        aweme_id = match.group(1)
                        if aweme_id not in seen_ids:
                            seen_ids.add(aweme_id)
                            videos.append(VideoInfo(
                                aweme_id=aweme_id,
                                title=link.attr('title') or '',
                                author='unknown',
                                duration=0,
                                digg_count=0,
                                play_count=0
                            ))

            if self.debug and videos:
                print(f"[DEBUG] 从卡片提取到 {len(videos)} 个视频")
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] 卡片提取失败: {e}")

        return videos

    def _parse_search_data(self, data: dict, depth: int = 0) -> List[VideoInfo]:
        """递归解析搜索数据"""
        videos = []

        if depth > 15:
            return videos

        if isinstance(data, dict):
            # 检查是否是视频列表
            if 'data' in data and isinstance(data['data'], list):
                for item in data['data']:
                    video = self._parse_video_item(item)
                    if video:
                        videos.append(video)

            # 检查 aweme_list
            if 'aweme_list' in data and isinstance(data['aweme_list'], list):
                for item in data['aweme_list']:
                    video = self._parse_video_item(item)
                    if video:
                        videos.append(video)

            # 递归搜索
            for value in data.values():
                videos.extend(self._parse_search_data(value, depth + 1))

        elif isinstance(data, list):
            for item in data:
                videos.extend(self._parse_search_data(item, depth + 1))

        # 去重
        seen = set()
        unique_videos = []
        for v in videos:
            if v.aweme_id not in seen:
                seen.add(v.aweme_id)
                unique_videos.append(v)

        return unique_videos

    def _parse_video_item(self, item: dict) -> Optional[VideoInfo]:
        """解析单个视频项"""
        try:
            # 可能在 aweme_info 里
            aweme = item.get('aweme_info') or item

            aweme_id = aweme.get('aweme_id')
            if not aweme_id:
                return None

            # 获取时长 (毫秒转秒)
            duration_ms = aweme.get('video', {}).get('duration', 0)
            if not duration_ms:
                duration_ms = aweme.get('duration', 0)
            duration = duration_ms / 1000 if duration_ms > 1000 else duration_ms

            # 获取统计数据
            statistics = aweme.get('statistics', {})
            digg_count = statistics.get('digg_count', 0)
            play_count = statistics.get('play_count', 0)

            # 获取发布时间
            create_time = aweme.get('create_time', 0)

            # 标题和作者
            title = aweme.get('desc', '')[:100]
            author = aweme.get('author', {}).get('nickname', 'unknown')

            # 视频 URL
            video_url = ""
            video_data = aweme.get('video', {})
            play_addr = video_data.get('play_addr', {})
            url_list = play_addr.get('url_list', [])
            if url_list:
                video_url = url_list[2] if len(url_list) > 2 else url_list[0]

            # 封面
            cover_url = ""
            cover_data = video_data.get('cover', {}) or video_data.get('origin_cover', {})
            cover_list = cover_data.get('url_list', [])
            if cover_list:
                cover_url = cover_list[0]

            return VideoInfo(
                aweme_id=aweme_id,
                title=title,
                author=author,
                duration=duration,
                digg_count=digg_count,
                play_count=play_count,
                video_url=video_url,
                cover_url=cover_url,
                create_time=create_time
            )
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] 解析视频项失败: {e}")
            return None

    def _extract_from_network(self) -> List[VideoInfo]:
        """从网络请求中提取（备用方案）"""
        # TODO: 可以通过监听网络请求获取
        return []

    def filter_videos(
        self,
        videos: List[VideoInfo],
        min_duration: float = 0,
        max_duration: float = 9999,
        top_n: int = 1,
        sort_by: str = "digg"  # digg, time, or digg_time
    ) -> List[VideoInfo]:
        """
        筛选视频

        Args:
            videos: 视频列表
            min_duration: 最小时长（秒）
            max_duration: 最大时长（秒）
            top_n: 返回前 N 个
            sort_by: 排序方式 - digg(点赞), time(最新), digg_time(点赞+最新)

        Returns:
            筛选后的视频列表
        """
        # 按时长筛选
        if min_duration > 0 or max_duration < 9999:
            filtered = [v for v in videos if min_duration <= v.duration <= max_duration]
            if self.debug:
                print(f"[DEBUG] 时长 {min_duration}-{max_duration}s 筛选后: {len(filtered)} 个视频")
        else:
            filtered = videos.copy()

        # 排序
        if sort_by == "time":
            # 按发布时间排序（最新的在前）
            filtered.sort(key=lambda x: x.create_time, reverse=True)
        elif sort_by == "digg_time":
            # 先按时间筛选最新的，再按点赞排序
            filtered.sort(key=lambda x: x.create_time, reverse=True)
            # 取最新的一批（比如前50%或至少top_n*3个）
            recent_count = max(len(filtered) // 2, top_n * 3, 10)
            recent = filtered[:recent_count]
            # 再按点赞排序
            recent.sort(key=lambda x: x.digg_count, reverse=True)
            filtered = recent
        else:  # digg
            # 按点赞量排序
            filtered.sort(key=lambda x: x.digg_count, reverse=True)

        return filtered[:top_n]

    def get_video_url(self, aweme_id: str) -> str:
        """获取视频的下载 URL"""
        video_page_url = f"https://www.douyin.com/video/{aweme_id}"

        if self.debug:
            print(f"[DEBUG] 获取视频详情: {video_page_url}")

        self.page.get(video_page_url)
        time.sleep(3)

        # 尝试从 source 元素获取
        for _ in range(10):
            try:
                source_ele = self.page.ele('tag:source', timeout=1)
                if source_ele:
                    src = source_ele.attr('src')
                    if src and src.startswith('http'):
                        return src
            except Exception:
                pass
            time.sleep(1)

        return ""

    def download_video(self, video_url: str, output_path: str) -> bool:
        """下载视频"""
        video_url = video_url.replace('http:', 'https:')

        print(f"开始下载: {video_url[:80]}...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.douyin.com/',
        }

        try:
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
                            print(f"\r下载进度: {percent:.1f}%", end='')

            print(f"\n下载完成: {output_path}")
            return True
        except Exception as e:
            print(f"下载失败: {e}")
            return False

    def search_and_download(
        self,
        search_url: str,
        min_duration: float = 0,
        max_duration: float = 9999,
        top_n: int = 1,
        output_dir: str = ".",
        scroll_times: int = 5,
        sort_by: str = "digg"
    ):
        """
        搜索并下载视频

        Args:
            search_url: 搜索页面 URL
            min_duration: 最小时长（秒）
            max_duration: 最大时长（秒）
            top_n: 下载前 N 个
            output_dir: 输出目录
            scroll_times: 滚动次数
            sort_by: 排序方式
        """
        from datetime import datetime

        print(f"正在搜索视频...")
        sort_desc = {"digg": "点赞最高", "time": "最新发布", "digg_time": "最新+点赞最高"}
        print(f"筛选条件: {sort_desc.get(sort_by, sort_by)}, 下载 {top_n} 个")
        if min_duration > 0 or max_duration < 9999:
            print(f"时长限制: {min_duration}-{max_duration} 秒")
        print()

        # 1. 获取搜索结果
        videos = self.search_videos(search_url, scroll_times)

        if not videos:
            print("未找到任何视频")
            return

        print(f"找到 {len(videos)} 个视频")
        print()

        # 显示所有视频信息
        def format_time(ts):
            if ts:
                try:
                    return datetime.fromtimestamp(ts).strftime('%m-%d %H:%M')
                except:
                    pass
            return "未知"

        print("=" * 100)
        print(f"{'ID':<20} {'时长':>8} {'点赞':>12} {'发布时间':<12} {'标题':<30}")
        print("=" * 100)
        for v in sorted(videos, key=lambda x: x.digg_count, reverse=True)[:20]:
            title_short = v.title[:26] + '..' if len(v.title) > 28 else v.title
            pub_time = format_time(v.create_time)
            print(f"{v.aweme_id:<20} {v.duration:>6.1f}s {v.digg_count:>12,} {pub_time:<12} {title_short}")
        print("=" * 100)
        print()

        # 2. 筛选视频
        selected = self.filter_videos(videos, min_duration, max_duration, top_n, sort_by)

        if not selected:
            print(f"没有找到符合条件的视频")
            durations = [v.duration for v in videos]
            if durations:
                print(f"提示: 当前视频时长范围 {min(durations):.1f}s - {max(durations):.1f}s")
            return

        print(f"筛选出 {len(selected)} 个符合条件的视频:")
        for i, v in enumerate(selected, 1):
            pub_time = format_time(v.create_time)
            print(f"  {i}. [{v.aweme_id}] 时长:{v.duration:.1f}s 点赞:{v.digg_count:,} 发布:{pub_time}")
            print(f"     标题: {v.title[:60]}...")
        print()

        # 3. 下载视频
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for i, video in enumerate(selected, 1):
            print(f"\n[{i}/{len(selected)}] 正在下载视频 {video.aweme_id}...")

            # 获取视频 URL
            video_url = video.video_url
            if not video_url or 'douyin' not in video_url:
                video_url = self.get_video_url(video.aweme_id)

            if not video_url:
                print(f"无法获取视频 URL，跳过")
                continue

            # 下载
            filename = f"douyin_{video.aweme_id}_{video.duration:.0f}s_{video.digg_count}.mp4"
            filepath = output_path / filename
            self.download_video(video_url, str(filepath))

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
        description='抖音搜索视频下载器 - 自动筛选并下载符合条件的视频',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 下载点赞最高的 5 个视频
  python douyin_search_downloader.py <url> --top 5

  # 下载最新且点赞最高的 5 个视频
  python douyin_search_downloader.py <url> --top 5 --sort digg_time

  # 下载时长 30-40 秒、点赞最高的前 3 个
  python douyin_search_downloader.py <url> --min-duration 30 --max-duration 40 --top 3

  # 更多滚动以加载更多视频
  python douyin_search_downloader.py <url> --scroll 10

排序方式:
  digg      - 按点赞量排序（默认）
  time      - 按发布时间排序（最新的在前）
  digg_time - 从最新视频中选点赞最高的
        '''
    )
    parser.add_argument('url', help='抖音搜索页面 URL')
    parser.add_argument('--min-duration', type=float, default=0, help='最小时长（秒），默认不限')
    parser.add_argument('--max-duration', type=float, default=9999, help='最大时长（秒），默认不限')
    parser.add_argument('--top', type=int, default=1, help='下载前 N 个，默认 1')
    parser.add_argument('--sort', choices=['digg', 'time', 'digg_time'], default='digg_time',
                        help='排序方式: digg(点赞), time(最新), digg_time(最新+点赞)')
    parser.add_argument('--output', '-o', default='.', help='输出目录')
    parser.add_argument('--scroll', type=int, default=5, help='滚动次数（加载更多），默认 5')
    parser.add_argument('--headless', action='store_true', help='无头模式（不显示浏览器）')
    parser.add_argument('--debug', action='store_true', help='调试模式')

    args = parser.parse_args()

    downloader = None
    try:
        downloader = DouyinSearchDownloader(
            headless=args.headless,
            debug=args.debug
        )
        downloader.search_and_download(
            search_url=args.url,
            min_duration=args.min_duration,
            max_duration=args.max_duration,
            top_n=args.top,
            output_dir=args.output,
            scroll_times=args.scroll,
            sort_by=args.sort
        )
    except KeyboardInterrupt:
        print("\n用户取消")
    except Exception as e:
        print(f"\n错误: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        if downloader:
            downloader.close()

    return 0


if __name__ == '__main__':
    exit(main())

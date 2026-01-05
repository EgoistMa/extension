"""抖音视频搜索器

基于 douyin_search_downloader.py 重构，适配新架构
"""

import re
import json
import time
import random
from typing import List, Optional, Callable
from urllib.parse import unquote
from DrissionPage import ChromiumPage

from core.browser_manager import BrowserManager
from core.config import Config
from models.video import Video


class DouyinSearcher:
    """抖音视频搜索器"""

    def __init__(
        self,
        browser_manager: BrowserManager,
        account_id: str,
        config: Optional[Config] = None
    ):
        """初始化搜索器

        Args:
            browser_manager: 浏览器管理器
            account_id: 账户ID
            config: 配置对象
        """
        self.browser_manager = browser_manager
        self.account_id = account_id
        self.config = config or Config()
        self.page: Optional[ChromiumPage] = None
        self.debug = self.config.get('browser.debug', False)

    def start(self, headless: bool = False) -> None:
        """启动浏览器"""
        self.page = self.browser_manager.navigate_to_platform(
            self.account_id, 'douyin', headless
        )
        # 注入反检测脚本
        self._inject_stealth_scripts()

    def close(self) -> None:
        """关闭浏览器"""
        self.browser_manager.close_browser(self.account_id, 'douyin')
        self.page = None

    def search_videos(
        self,
        keyword: str,
        scroll_times: int = 5,
        on_log: Optional[Callable[[str], None]] = None
    ) -> List[Video]:
        """搜索视频

        Args:
            keyword: 搜索关键词
            scroll_times: 滚动次数
            on_log: 日志回调

        Returns:
            视频列表
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            if self.debug:
                print(msg)

        if not self.page:
            self.start()

        # 构建搜索URL
        search_url = f"https://www.douyin.com/search/{keyword}?type=video"
        log(f"搜索: {search_url}")

        self.page.get(search_url)
        time.sleep(2)

        # 重新注入反检测脚本
        self._inject_stealth_scripts()

        # 模拟真实用户行为
        time.sleep(1 + random.random() * 2)

        # 检查验证码
        if not self._check_and_wait_captcha(on_log=on_log):
            log("验证码超时")
            return []

        # 等待页面加载
        if not self._wait_for_page_load(on_log=on_log):
            log("页面加载超时，尝试继续...")

        videos = []

        # 提取视频
        videos = self._extract_videos()
        if videos:
            log(f"初始加载找到 {len(videos)} 个视频")

        # 滚动加载更多
        for i in range(scroll_times):
            if not self._check_and_wait_captcha(max_wait=30, on_log=on_log):
                break

            self.page.scroll.to_bottom()
            time.sleep(3)

            new_videos = self._extract_videos()
            if len(new_videos) > len(videos):
                log(f"滚动 {i+1}: 找到 {len(new_videos)} 个视频 (+{len(new_videos) - len(videos)})")
                videos = new_videos

        log(f"搜索完成: 共找到 {len(videos)} 个视频")
        return videos

    def search_by_url(
        self,
        search_url: str,
        scroll_times: int = 5,
        on_log: Optional[Callable[[str], None]] = None
    ) -> List[Video]:
        """通过URL搜索视频

        Args:
            search_url: 搜索页面URL
            scroll_times: 滚动次数
            on_log: 日志回调

        Returns:
            视频列表
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            if self.debug:
                print(msg)

        if not self.page:
            self.start()

        log(f"访问: {search_url}")
        self.page.get(search_url)
        time.sleep(2)

        self._inject_stealth_scripts()
        time.sleep(1 + random.random() * 2)

        if not self._check_and_wait_captcha(on_log=on_log):
            return []

        if not self._wait_for_page_load(on_log=on_log):
            log("页面加载超时，尝试继续...")

        videos = self._extract_videos()
        if videos:
            log(f"初始加载找到 {len(videos)} 个视频")

        for i in range(scroll_times):
            if not self._check_and_wait_captcha(max_wait=30, on_log=on_log):
                break

            self.page.scroll.to_bottom()
            time.sleep(3)

            new_videos = self._extract_videos()
            if len(new_videos) > len(videos):
                log(f"滚动 {i+1}: 找到 {len(new_videos)} 个视频")
                videos = new_videos

        log(f"搜索完成: 共找到 {len(videos)} 个视频")
        return videos

    def filter_videos(
        self,
        videos: List[Video],
        min_duration: float = 0,
        max_duration: float = float('inf'),
        min_likes: int = 0,
        top_n: int = 5,
        sort_by: str = "digg_time"
    ) -> List[Video]:
        """筛选视频

        Args:
            videos: 视频列表
            min_duration: 最短时长(秒)
            max_duration: 最长时长(秒)
            min_likes: 最低点赞数
            top_n: 返回数量
            sort_by: 排序方式 (digg/time/digg_time)

        Returns:
            筛选后的视频列表
        """
        # 按条件筛选
        filtered = []
        for v in videos:
            if v.meets_criteria(min_duration, max_duration, min_likes):
                filtered.append(v)

        # 排序
        if sort_by == "time":
            filtered.sort(key=lambda x: x.publish_time, reverse=True)
        elif sort_by == "digg_time":
            # 先按时间筛选最新的，再按点赞排序
            filtered.sort(key=lambda x: x.publish_time, reverse=True)
            recent_count = max(len(filtered) // 2, top_n * 3, 10)
            recent = filtered[:recent_count]
            recent.sort(key=lambda x: x.likes, reverse=True)
            filtered = recent
        else:  # digg
            filtered.sort(key=lambda x: x.likes, reverse=True)

        return filtered[:top_n]

    def get_video_download_url(self, video: Video) -> str:
        """获取视频下载URL

        Args:
            video: 视频对象

        Returns:
            下载URL
        """
        if video.download_url:
            return video.download_url

        video_page_url = f"https://www.douyin.com/video/{video.video_id}"
        self.page.get(video_page_url)
        time.sleep(3)

        # 尝试从source元素获取
        for _ in range(10):
            try:
                source_ele = self.page.ele('tag:source', timeout=1)
                if source_ele:
                    src = source_ele.attr('src')
                    if src and src.startswith('http'):
                        video.download_url = src
                        return src
            except Exception:
                pass
            time.sleep(1)

        return ""

    def _extract_videos(self) -> List[Video]:
        """从页面提取视频信息"""
        videos = []

        # 方法1: 从 RENDER_DATA 提取
        try:
            render_script = self.page.ele('#RENDER_DATA', timeout=2)
            if render_script and render_script.text:
                data = json.loads(unquote(render_script.text))
                videos = self._parse_render_data(data)
        except Exception:
            pass

        # 方法2: 从DOM提取
        if not videos:
            videos = self._extract_from_dom()

        return videos

    def _parse_render_data(self, data: dict, depth: int = 0) -> List[Video]:
        """递归解析RENDER_DATA"""
        videos = []

        if depth > 15:
            return videos

        if isinstance(data, dict):
            if 'data' in data and isinstance(data['data'], list):
                for item in data['data']:
                    video = self._parse_video_item(item)
                    if video:
                        videos.append(video)

            if 'aweme_list' in data and isinstance(data['aweme_list'], list):
                for item in data['aweme_list']:
                    video = self._parse_video_item(item)
                    if video:
                        videos.append(video)

            for value in data.values():
                videos.extend(self._parse_render_data(value, depth + 1))

        elif isinstance(data, list):
            for item in data:
                videos.extend(self._parse_render_data(item, depth + 1))

        # 去重
        seen = set()
        unique = []
        for v in videos:
            if v.video_id not in seen:
                seen.add(v.video_id)
                unique.append(v)

        return unique

    def _parse_video_item(self, item: dict) -> Optional[Video]:
        """解析单个视频项"""
        try:
            aweme = item.get('aweme_info') or item
            aweme_id = aweme.get('aweme_id')
            if not aweme_id:
                return None

            # 时长
            duration_ms = aweme.get('video', {}).get('duration', 0)
            if not duration_ms:
                duration_ms = aweme.get('duration', 0)
            duration = duration_ms / 1000 if duration_ms > 1000 else duration_ms

            # 统计数据
            statistics = aweme.get('statistics', {})
            likes = statistics.get('digg_count', 0)
            comments = statistics.get('comment_count', 0)
            shares = statistics.get('share_count', 0)
            plays = statistics.get('play_count', 0)

            # 作者信息
            author = aweme.get('author', {})
            author_id = author.get('uid', '')
            author_name = author.get('nickname', 'unknown')

            # 标题
            title = aweme.get('desc', '')[:150]

            # 视频URL
            video_url = ""
            video_data = aweme.get('video', {})
            play_addr = video_data.get('play_addr', {})
            url_list = play_addr.get('url_list', [])
            if url_list:
                video_url = url_list[2] if len(url_list) > 2 else url_list[0]

            # 发布时间
            create_time = aweme.get('create_time', 0)
            publish_time = ""
            if create_time:
                from datetime import datetime
                try:
                    publish_time = datetime.fromtimestamp(create_time).isoformat()
                except Exception:
                    pass

            return Video(
                video_id=aweme_id,
                title=title,
                url=f"https://www.douyin.com/video/{aweme_id}",
                author_id=author_id,
                author_name=author_name,
                duration=duration,
                likes=likes,
                comments=comments,
                shares=shares,
                plays=plays,
                download_url=video_url,
                publish_time=publish_time
            )
        except Exception:
            return None

    def _extract_from_dom(self) -> List[Video]:
        """从DOM元素提取视频信息"""
        videos = []

        try:
            video_data = self.page.run_js('''
                const videos = [];
                const seenIds = new Set();

                const videoLinks = document.querySelectorAll('a[href*="douyin.com/video/"], a[href*="/video/"]');

                videoLinks.forEach(link => {
                    const href = link.getAttribute('href') || '';
                    const match = href.match(/\\/video\\/(\\d+)/);
                    if (!match) return;

                    const videoId = match[1];
                    if (seenIds.has(videoId)) return;
                    seenIds.add(videoId);

                    let card = link.closest('.search-result-card') ||
                               link.closest('[class*="search-result"]') ||
                               link.parentElement?.parentElement?.parentElement?.parentElement;

                    let title = '';
                    let author = '';
                    let duration = '';
                    let likes = '';

                    if (card) {
                        // 提取点赞数
                        const svgElements = card.querySelectorAll('svg');
                        for (const svg of svgElements) {
                            const nextSpan = svg.nextElementSibling;
                            if (nextSpan && nextSpan.tagName === 'SPAN') {
                                const text = nextSpan.textContent?.trim() || '';
                                if (text.match(/^[\\d.]+[万wk]?$/i)) {
                                    likes = text;
                                    break;
                                }
                            }
                        }

                        // 提取时长
                        const allDivs = card.querySelectorAll('div');
                        for (const div of allDivs) {
                            const text = div.textContent?.trim() || '';
                            if (text.match(/^\\d{1,2}:\\d{2}(:\\d{2})?$/) && div.children.length === 0) {
                                duration = text;
                                break;
                            }
                        }

                        // 提取作者
                        const atSpans = card.querySelectorAll('span');
                        for (let i = 0; i < atSpans.length; i++) {
                            if (atSpans[i].textContent?.trim() === '@' && atSpans[i + 1]) {
                                author = atSpans[i + 1].textContent?.trim() || '';
                                break;
                            }
                        }

                        // 提取标题
                        for (const div of allDivs) {
                            if (div.children.length === 0) {
                                const text = div.textContent?.trim() || '';
                                if (text.length > 15 &&
                                    !text.match(/^[\\d:]+$/) &&
                                    !text.match(/^[\\d.]+[万wk]?$/i) &&
                                    !text.startsWith('@')) {
                                    if (!title || text.length > title.length) {
                                        title = text.substring(0, 150);
                                    }
                                }
                            }
                        }
                    }

                    videos.push({
                        id: videoId,
                        title: title,
                        author: author,
                        duration: duration,
                        likes: likes
                    });
                });

                return JSON.stringify(videos);
            ''')

            if video_data:
                parsed = json.loads(video_data)
                for item in parsed:
                    # 解析时长
                    duration = 0
                    if item.get('duration'):
                        parts = item['duration'].split(':')
                        try:
                            if len(parts) == 2:
                                duration = int(parts[0]) * 60 + int(parts[1])
                            elif len(parts) == 3:
                                duration = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                        except Exception:
                            pass

                    # 解析点赞数
                    likes = self._parse_count(item.get('likes', ''))

                    videos.append(Video(
                        video_id=item['id'],
                        title=item.get('title', ''),
                        url=f"https://www.douyin.com/video/{item['id']}",
                        author_name=item.get('author', 'unknown'),
                        duration=duration,
                        likes=likes
                    ))

        except Exception:
            pass

        return videos

    def _parse_count(self, text: str) -> int:
        """解析数量文本"""
        if not text:
            return 0

        text = text.strip().lower().replace(',', '')

        try:
            if '万' in text or 'w' in text:
                num = float(re.sub(r'[^\d.]', '', text))
                return int(num * 10000)
            elif 'k' in text:
                num = float(re.sub(r'[^\d.]', '', text))
                return int(num * 1000)
            else:
                return int(re.sub(r'[^\d]', '', text) or 0)
        except Exception:
            return 0

    def _inject_stealth_scripts(self) -> None:
        """注入反检测脚本"""
        if not self.page:
            return

        try:
            self.page.run_js('''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: true
                });
                delete navigator.__proto__.webdriver;

                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en-US', 'en'],
                    configurable: true
                });

                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32',
                    configurable: true
                });

                window.chrome = {
                    runtime: {},
                    loadTimes: function() { return {}; },
                    csi: function() { return {}; }
                };
            ''')
        except Exception:
            pass

    def _check_and_wait_captcha(
        self,
        max_wait: int = 120,
        on_log: Optional[Callable[[str], None]] = None
    ) -> bool:
        """检查并等待验证码"""
        captcha_selectors = [
            'div[class*="captcha"]',
            'div[class*="verify"]',
            'div[class*="slider"]',
            'div[class*="secsdk"]',
        ]

        start_time = time.time()
        captcha_detected = False

        while time.time() - start_time < max_wait:
            has_captcha = False
            for selector in captcha_selectors:
                try:
                    ele = self.page.ele(selector, timeout=0.5)
                    if ele:
                        has_captcha = True
                        break
                except Exception:
                    pass

            if has_captcha:
                if not captcha_detected:
                    captcha_detected = True
                    if on_log:
                        on_log("检测到验证码，请在浏览器中完成验证...")
                time.sleep(2)
            else:
                if captcha_detected and on_log:
                    on_log("验证码已完成")
                return True

        return not captcha_detected

    def _wait_for_page_load(
        self,
        max_wait: int = 60,
        on_log: Optional[Callable[[str], None]] = None
    ) -> bool:
        """等待页面加载"""
        start_time = time.time()

        while time.time() - start_time < max_wait:
            if not self._check_and_wait_captcha(max_wait=5, on_log=on_log):
                time.sleep(2)
                continue

            try:
                video_count = self.page.run_js('''
                    return document.querySelectorAll('a[href*="douyin.com/video/"], a[href*="/video/"]').length;
                ''')
                if video_count and video_count > 0:
                    return True

                render_script = self.page.ele('#RENDER_DATA', timeout=1)
                if render_script and render_script.text and len(render_script.text) > 1000:
                    return True
            except Exception:
                pass

            time.sleep(2)

        return False

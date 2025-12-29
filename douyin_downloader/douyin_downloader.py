#!/usr/bin/env python3
"""
抖音视频下载器
基于浏览器插件逻辑实现的 Python 版本
"""

import re
import json
import requests
import argparse
import time
import random
from urllib.parse import urlencode, urlparse, unquote
from pathlib import Path


class DouyinDownloader:
    """抖音视频下载器"""

    # 抖音 API 端点
    DETAIL_API = "https://www.douyin.com/aweme/v1/web/aweme/detail/"

    def __init__(self, cookie: str = None, debug: bool = False):
        """
        初始化下载器

        Args:
            cookie: 抖音网站的 Cookie（可选，但建议提供以获取更好的效果）
            debug: 是否启用调试模式
        """
        self.cookie = cookie
        self.debug = debug
        self.session = requests.Session()
        self._setup_headers()
        self._init_session()

    def _setup_headers(self):
        """设置请求头"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Referer': 'https://www.douyin.com/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.douyin.com',
            'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        if self.cookie:
            self.headers['Cookie'] = self.cookie

    def _init_session(self):
        """初始化会话，获取必要的 Cookie"""
        try:
            # 先访问抖音主页，获取基础 cookie
            resp = self.session.get(
                'https://www.douyin.com/',
                headers=self.headers,
                timeout=10
            )
            if self.debug:
                print(f"[DEBUG] 初始化 session, status: {resp.status_code}")
                print(f"[DEBUG] Cookies: {dict(self.session.cookies)}")
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] 初始化 session 失败: {e}")

    def _get_detail_params(self, aweme_id: str) -> dict:
        """
        构建视频详情请求参数（参考插件逻辑）

        Args:
            aweme_id: 视频 ID

        Returns:
            请求参数字典
        """
        return {
            'device_platform': 'webapp',
            'aid': 6383,  # 0x18ef
            'channel': 'channel_pc_web',
            'aweme_id': aweme_id,
            'update_version_code': '170400',
            'pc_client_type': 1,
            'version_code': '190500',
            'version_name': '19.5.0',
            'cookie_enabled': 'true',
            'screen_width': 1835,  # 0x72b
            'screen_height': 1032,  # 0x408
            'browser_language': 'zh-CN',
            'browser_platform': 'Win32',
            'browser_name': 'Chrome',
            'browser_version': '124.0.0.0',
            'browser_online': 'true',
            'engine_name': 'Blink',
            'engine_version': '124.0.0.0',
            'os_name': 'Windows',
            'os_version': '10',
            'cpu_core_num': 16,  # 0x10
            'device_memory': 8,
            'platform': 'PC',
            'downlink': 10,
            'effective_type': '4g',
            'round_trip_time': 100,  # 0x64
            'webid': str(random.randint(7000000000000000000, 7999999999999999999)),
        }

    def extract_aweme_id(self, url: str) -> str:
        """
        从抖音 URL 中提取视频 ID

        Args:
            url: 抖音视频 URL

        Returns:
            视频 ID
        """
        # 处理短链接（需要先获取重定向后的真实 URL）
        if 'v.douyin.com' in url or 'douyin.com/discover' in url:
            try:
                resp = self.session.get(url, headers=self.headers, allow_redirects=True, timeout=10)
                url = resp.url
            except Exception as e:
                print(f"解析短链接失败: {e}")

        # 从 URL 中提取 aweme_id
        # 格式1: https://www.douyin.com/video/7123456789012345678
        # 格式2: https://www.douyin.com/note/7123456789012345678
        # 格式3: URL 参数中包含 modal_id

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

        # 尝试直接作为 ID
        if url.isdigit() and len(url) >= 18:
            return url

        raise ValueError(f"无法从 URL 中提取视频 ID: {url}")

    def get_video_detail(self, aweme_id: str) -> dict:
        """
        获取视频详情

        Args:
            aweme_id: 视频 ID

        Returns:
            视频详情数据
        """
        # 方法1: 尝试从视频页面 HTML 中提取数据（更可靠）
        try:
            detail = self._get_detail_from_page(aweme_id)
            if detail:
                return detail
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] 从页面提取失败: {e}")

        # 方法2: 尝试 API 请求
        try:
            detail = self._get_detail_from_api(aweme_id)
            if detail:
                return detail
        except Exception as e:
            if self.debug:
                print(f"[DEBUG] API 请求失败: {e}")

        raise Exception("无法获取视频详情，请尝试提供 Cookie")

    def _get_detail_from_page(self, aweme_id: str) -> dict:
        """从视频页面 HTML 中提取视频数据"""
        page_url = f"https://www.douyin.com/video/{aweme_id}"

        if self.debug:
            print(f"[DEBUG] 正在访问页面: {page_url}")

        resp = self.session.get(page_url, headers=self.headers, timeout=15)
        resp.raise_for_status()
        html = resp.text

        if self.debug:
            print(f"[DEBUG] 页面长度: {len(html)}")

        # 尝试从 RENDER_DATA 中提取
        render_match = re.search(r'<script id="RENDER_DATA" type="application/json">([^<]+)</script>', html)
        if render_match:
            try:
                render_data = json.loads(unquote(render_match.group(1)))
                if self.debug:
                    print(f"[DEBUG] 找到 RENDER_DATA")

                # 遍历查找 aweme_detail
                for key, value in render_data.items():
                    if isinstance(value, dict):
                        if 'aweme' in value and 'detail' in value['aweme']:
                            return value['aweme']['detail']
                        if 'awemeDetail' in value:
                            return value['awemeDetail']
                        # 递归查找
                        detail = self._find_aweme_detail(value)
                        if detail:
                            return detail
            except json.JSONDecodeError as e:
                if self.debug:
                    print(f"[DEBUG] RENDER_DATA 解析失败: {e}")

        # 尝试从 SSR_HYDRATED_DATA 中提取
        ssr_match = re.search(r'window\._SSR_HYDRATED_DATA_\s*=\s*(\{.+?\})\s*</script>', html, re.DOTALL)
        if ssr_match:
            try:
                # 处理可能的 undefined 值
                json_str = ssr_match.group(1).replace(':undefined', ':null')
                ssr_data = json.loads(json_str)
                if self.debug:
                    print(f"[DEBUG] 找到 SSR_HYDRATED_DATA")
                detail = self._find_aweme_detail(ssr_data)
                if detail:
                    return detail
            except json.JSONDecodeError as e:
                if self.debug:
                    print(f"[DEBUG] SSR_HYDRATED_DATA 解析失败: {e}")

        return None

    def _find_aweme_detail(self, data, depth=0) -> dict:
        """递归查找 aweme_detail 数据"""
        if depth > 10:
            return None

        if isinstance(data, dict):
            # 检查是否是视频详情对象
            if 'aweme_id' in data and 'video' in data:
                return data

            # 检查特定键名
            for key in ['aweme_detail', 'awemeDetail', 'detail']:
                if key in data and isinstance(data[key], dict):
                    if 'aweme_id' in data[key] or 'video' in data[key]:
                        return data[key]

            # 递归搜索
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

    def _get_detail_from_api(self, aweme_id: str) -> dict:
        """通过 API 获取视频详情"""
        params = self._get_detail_params(aweme_id)
        url = f"{self.DETAIL_API}?{urlencode(params)}"

        if self.debug:
            print(f"[DEBUG] API URL: {url[:100]}...")

        resp = self.session.get(url, headers=self.headers, timeout=15)

        if self.debug:
            print(f"[DEBUG] API 响应状态: {resp.status_code}")
            print(f"[DEBUG] API 响应前200字符: {resp.text[:200]}")

        resp.raise_for_status()

        try:
            data = resp.json()
        except json.JSONDecodeError:
            raise Exception(f"API 返回非 JSON 响应 (可能触发了反爬)")

        if data.get('status_code') == 0 and data.get('aweme_detail'):
            return data['aweme_detail']
        else:
            raise Exception(f"API 返回错误: {data.get('status_msg', '未知错误')}")

    def get_video_url(self, aweme_detail: dict) -> str:
        """
        从视频详情中提取最高质量的视频 URL

        Args:
            aweme_detail: 视频详情数据

        Returns:
            视频下载 URL
        """
        # 优先尝试获取最高质量的视频（参考插件的 getHighestQualityVideoUrl）
        try:
            bit_rates = aweme_detail.get('video', {}).get('bit_rate', [])
            if bit_rates:
                # 按宽度排序，获取最高质量
                sorted_rates = sorted(
                    bit_rates,
                    key=lambda x: x.get('play_addr', {}).get('width', 0),
                    reverse=True
                )
                if sorted_rates:
                    url_list = sorted_rates[0].get('play_addr', {}).get('url_list', [])
                    if url_list:
                        # 优先使用 douyin.com 域名的 URL
                        for url in url_list:
                            if 'douyin.com' in url:
                                return url
                        return url_list[0]
        except Exception:
            pass

        # 回退到普通的 play_addr
        try:
            url_list = aweme_detail.get('video', {}).get('play_addr', {}).get('url_list', [])
            if url_list:
                # 优先使用第三个 URL（索引2），参考插件逻辑
                if len(url_list) > 2:
                    return url_list[2]
                return url_list[0]
        except Exception:
            pass

        raise Exception("无法提取视频 URL")

    def download_video(self, video_url: str, output_path: str = None, aweme_id: str = None) -> str:
        """
        下载视频

        Args:
            video_url: 视频 URL
            output_path: 输出文件路径（可选）
            aweme_id: 视频 ID（用于生成默认文件名）

        Returns:
            下载的文件路径
        """
        # 确保使用 HTTPS
        video_url = video_url.replace('http:', 'https:')

        # 生成输出文件名
        if not output_path:
            filename = f"douyin_{aweme_id or int(time.time())}.mp4"
            output_path = str(Path.cwd() / filename)

        print(f"开始下载: {video_url[:80]}...")

        try:
            # 下载视频
            download_headers = self.headers.copy()
            download_headers['Range'] = 'bytes=0-'

            resp = self.session.get(video_url, headers=download_headers, stream=True, timeout=60)
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

        except requests.exceptions.RequestException as e:
            raise Exception(f"下载失败: {e}")

    def download(self, url: str, output_path: str = None) -> str:
        """
        从抖音 URL 下载视频（主入口方法）

        Args:
            url: 抖音视频 URL 或视频 ID
            output_path: 输出文件路径（可选）

        Returns:
            下载的文件路径
        """
        print(f"正在解析: {url}")

        # 1. 提取视频 ID
        aweme_id = self.extract_aweme_id(url)
        print(f"视频 ID: {aweme_id}")

        # 2. 获取视频详情
        print("正在获取视频详情...")
        detail = self.get_video_detail(aweme_id)

        # 打印视频信息
        title = detail.get('desc', '无标题')[:50]
        author = detail.get('author', {}).get('nickname', '未知')
        print(f"标题: {title}")
        print(f"作者: {author}")

        # 3. 提取视频 URL
        video_url = self.get_video_url(detail)
        print(f"视频 URL: {video_url[:80]}...")

        # 4. 下载视频
        return self.download_video(video_url, output_path, aweme_id)


def main():
    parser = argparse.ArgumentParser(
        description='抖音视频下载器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python douyin_downloader.py https://www.douyin.com/video/7123456789012345678
  python douyin_downloader.py https://v.douyin.com/xxxxx
  python douyin_downloader.py 7123456789012345678 -o my_video.mp4
  python douyin_downloader.py <url> --cookie "your_cookie_here"
        '''
    )
    parser.add_argument('url', help='抖音视频 URL 或视频 ID')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('--cookie', help='抖音网站 Cookie（可提高成功率）')
    parser.add_argument('--cookie-file', help='从文件读取 Cookie')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')

    args = parser.parse_args()

    # 读取 Cookie
    cookie = args.cookie
    if args.cookie_file:
        try:
            with open(args.cookie_file, 'r', encoding='utf-8') as f:
                cookie = f.read().strip()
        except Exception as e:
            print(f"警告: 无法读取 Cookie 文件: {e}")

    # 创建下载器并下载
    try:
        downloader = DouyinDownloader(cookie=cookie, debug=args.debug)
        output_file = downloader.download(args.url, args.output)
        print(f"\n成功! 文件已保存到: {output_file}")
    except Exception as e:
        print(f"\n错误: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())

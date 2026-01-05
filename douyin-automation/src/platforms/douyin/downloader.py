"""抖音视频下载器"""

import os
import re
import requests
from pathlib import Path
from typing import List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.video import Video


class VideoDownloader:
    """抖音视频下载器"""

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.douyin.com/',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    def __init__(
        self,
        output_dir: Path,
        max_workers: int = 3,
        timeout: int = 60
    ):
        """初始化下载器

        Args:
            output_dir: 输出目录
            max_workers: 最大并发下载数
            timeout: 请求超时时间(秒)
        """
        self.output_dir = Path(output_dir)
        self.max_workers = max_workers
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def download_videos(
        self,
        videos: List[Video],
        on_progress: Optional[Callable[[str, int, int], None]] = None,
        on_log: Optional[Callable[[str], None]] = None
    ) -> List[Video]:
        """批量下载视频

        Args:
            videos: 视频列表
            on_progress: 进度回调 (message, current, total)
            on_log: 日志回调

        Returns:
            下载成功的视频列表
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(msg)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        downloaded = []
        total = len(videos)

        log(f"开始下载 {total} 个视频...")

        for i, video in enumerate(videos):
            if on_progress:
                on_progress(f"下载视频 {i+1}/{total}", i+1, total)

            log(f"[{i+1}/{total}] 下载: {video.video_id}")

            if not video.download_url:
                log(f"  跳过: 无下载URL")
                continue

            # 生成文件名
            filename = self._generate_filename(video)
            output_path = self.output_dir / filename

            # 下载
            success = self._download_file(
                video.download_url,
                output_path,
                on_progress=lambda msg: log(f"  {msg}")
            )

            if success:
                video.local_path = str(output_path)
                video.is_downloaded = True
                downloaded.append(video)
                log(f"  完成: {filename}")
            else:
                log(f"  失败")

        log(f"下载完成: {len(downloaded)}/{total}")
        return downloaded

    def download_single(
        self,
        video: Video,
        on_progress: Optional[Callable[[str], None]] = None
    ) -> bool:
        """下载单个视频

        Args:
            video: 视频对象
            on_progress: 进度回调

        Returns:
            是否成功
        """
        if not video.download_url:
            return False

        self.output_dir.mkdir(parents=True, exist_ok=True)

        filename = self._generate_filename(video)
        output_path = self.output_dir / filename

        success = self._download_file(
            video.download_url,
            output_path,
            on_progress=on_progress
        )

        if success:
            video.local_path = str(output_path)
            video.is_downloaded = True

        return success

    def _download_file(
        self,
        url: str,
        output_path: Path,
        on_progress: Optional[Callable[[str], None]] = None
    ) -> bool:
        """下载单个文件

        Args:
            url: 下载URL
            output_path: 输出路径
            on_progress: 进度回调

        Returns:
            是否成功
        """
        try:
            # 确保URL是https
            url = url.replace('http:', 'https:')

            response = self.session.get(
                url,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        if total_size and on_progress:
                            percent = (downloaded / total_size) * 100
                            on_progress(f"下载进度: {percent:.1f}%")

            return True

        except Exception as e:
            if on_progress:
                on_progress(f"下载失败: {e}")
            return False

    def _generate_filename(self, video: Video) -> str:
        """生成文件名

        Args:
            video: 视频对象

        Returns:
            文件名
        """
        # 基础格式: douyin_{video_id}_{duration}s_{likes}.mp4
        parts = [
            "douyin",
            video.video_id,
            f"{int(video.duration)}s" if video.duration else "0s",
            str(video.likes) if video.likes else "0"
        ]

        filename = "_".join(parts) + ".mp4"

        # 清理非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)

        return filename

    def download_with_retry(
        self,
        video: Video,
        max_retries: int = 3,
        on_log: Optional[Callable[[str], None]] = None
    ) -> bool:
        """带重试的下载

        Args:
            video: 视频对象
            max_retries: 最大重试次数
            on_log: 日志回调

        Returns:
            是否成功
        """
        def log(msg: str):
            if on_log:
                on_log(msg)

        for attempt in range(max_retries):
            if attempt > 0:
                log(f"重试 {attempt}/{max_retries}...")

            success = self.download_single(video, on_progress=log)
            if success:
                return True

            import time
            time.sleep(2)

        return False

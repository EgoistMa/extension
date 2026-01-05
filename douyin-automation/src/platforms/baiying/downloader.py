"""百应素材下载器

参考 baiying.js 中的 downImage() 和 downMainVideo() 实现
"""

import os
import re
import time
import requests
from pathlib import Path
from typing import List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.product import Product


class MaterialDownloader:
    """素材下载器"""

    # 请求头
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://buyin.jinritemai.com/',
    }

    def __init__(
        self,
        output_dir: Path,
        max_workers: int = 5,
        timeout: int = 30
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

    def download_materials(
        self,
        product: Product,
        on_progress: Optional[Callable[[str, int, int], None]] = None
    ) -> Product:
        """下载产品的所有素材

        Args:
            product: 产品信息
            on_progress: 进度回调 (message, current, total)

        Returns:
            更新后的Product对象
        """
        # 创建产品目录
        product_dir = self.output_dir / self._sanitize_filename(product.title[:30])
        product_dir.mkdir(parents=True, exist_ok=True)

        # 下载图片
        local_images = self._download_images(
            product.images,
            product_dir / "images",
            on_progress
        )
        product.local_images = local_images

        # 下载视频
        if product.video_url:
            video_path = self._download_video(
                product.video_url,
                product_dir / "video",
                on_progress
            )
            if video_path:
                product.local_video = video_path

        return product

    def _download_images(
        self,
        urls: List[str],
        output_dir: Path,
        on_progress: Optional[Callable[[str, int, int], None]] = None
    ) -> List[str]:
        """批量下载图片

        Args:
            urls: 图片URL列表
            output_dir: 输出目录
            on_progress: 进度回调

        Returns:
            已下载的本地路径列表
        """
        if not urls:
            return []

        output_dir.mkdir(parents=True, exist_ok=True)
        local_paths = []
        total = len(urls)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {}
            for i, url in enumerate(urls):
                filename = f"image_{i+1:03d}{self._get_extension(url, '.jpg')}"
                output_path = output_dir / filename
                future = executor.submit(self._download_file, url, output_path)
                futures[future] = (i, output_path)

            for future in as_completed(futures):
                i, output_path = futures[future]
                try:
                    success = future.result()
                    if success:
                        local_paths.append(str(output_path))
                    if on_progress:
                        on_progress(f"下载图片 {i+1}/{total}", i+1, total)
                except Exception as e:
                    print(f"下载图片失败: {e}")

        return local_paths

    def _download_video(
        self,
        url: str,
        output_dir: Path,
        on_progress: Optional[Callable[[str, int, int], None]] = None
    ) -> str:
        """下载视频

        Args:
            url: 视频URL
            output_dir: 输出目录
            on_progress: 进度回调

        Returns:
            本地视频路径
        """
        if not url:
            return ""

        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"main_video{self._get_extension(url, '.mp4')}"
        output_path = output_dir / filename

        if on_progress:
            on_progress("下载视频...", 0, 1)

        success = self._download_file(url, output_path, is_video=True)

        if on_progress:
            on_progress("视频下载完成" if success else "视频下载失败", 1, 1)

        return str(output_path) if success else ""

    def _download_file(
        self,
        url: str,
        output_path: Path,
        is_video: bool = False
    ) -> bool:
        """下载单个文件

        Args:
            url: 文件URL
            output_path: 输出路径
            is_video: 是否是视频文件

        Returns:
            是否下载成功
        """
        try:
            # 确保URL有协议
            if url.startswith('//'):
                url = 'https:' + url

            # 发送请求
            response = self.session.get(
                url,
                timeout=self.timeout if not is_video else self.timeout * 3,
                stream=is_video
            )
            response.raise_for_status()

            # 写入文件
            if is_video:
                # 流式写入大文件
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            else:
                with open(output_path, 'wb') as f:
                    f.write(response.content)

            return True

        except Exception as e:
            print(f"下载失败 {url}: {e}")
            return False

    def _get_extension(self, url: str, default: str = "") -> str:
        """从URL获取文件扩展名"""
        # 移除查询参数
        url_path = url.split('?')[0]
        # 获取扩展名
        ext = os.path.splitext(url_path)[1].lower()
        # 验证扩展名
        valid_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.webm', '.mov']
        return ext if ext in valid_exts else default

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除Windows不允许的字符
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 移除控制字符
        filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
        # 移除前后空格
        filename = filename.strip()
        # 如果为空，使用默认名
        return filename if filename else "product"

    def download_single_image(self, url: str, output_path: Path) -> bool:
        """下载单个图片

        Args:
            url: 图片URL
            output_path: 输出路径

        Returns:
            是否成功
        """
        return self._download_file(url, output_path)

    def download_single_video(self, url: str, output_path: Path) -> bool:
        """下载单个视频

        Args:
            url: 视频URL
            output_path: 输出路径

        Returns:
            是否成功
        """
        return self._download_file(url, output_path, is_video=True)

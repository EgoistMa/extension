"""百应素材下载器

参考 baiying.js 中的 downImage(), downMainVideo(), downloadResource() 实现

baiying.js 文件命名格式:
- 图片: {userId}_{excuteTime}_{product_id}_image_{index}.jpg
- 视频: {userId}_{excuteTime}_{product_id}_video_{index}.mp4

本模块简化命名为:
- 图片: {product_id}_image_{index}.jpg
- 视频: {product_id}_video.mp4
- 产品信息: product_info.json
"""

import os
import re
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from models.product import Product


class MaterialDownloader:
    """素材下载器

    参考 baiying.js 的 downloadResource() 实现
    支持分块下载大文件和进度显示
    """

    # 请求头 (模拟浏览器)
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://buyin.jinritemai.com/',
    }

    # 视频请求头
    VIDEO_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'video/webm,video/mp4,video/*;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://buyin.jinritemai.com/',
    }

    def __init__(
        self,
        output_dir: Path,
        max_workers: int = 5,
        timeout: int = 30,
        user_id: str = "auto"
    ):
        """初始化下载器

        Args:
            output_dir: 输出目录
            max_workers: 最大并发下载数
            timeout: 请求超时时间(秒)
            user_id: 用户ID (用于文件命名)
        """
        self.output_dir = Path(output_dir)
        self.max_workers = max_workers
        self.timeout = timeout
        self.user_id = user_id
        self.execute_time = self._get_midnight_timestamp()
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def _get_midnight_timestamp(self) -> str:
        """获取当天午夜时间戳 (对应 baiying.js 的 getMidnightTimestamp)"""
        now = datetime.now()
        midnight = datetime(now.year, now.month, now.day)
        return str(int(midnight.timestamp() * 1000))

    def download_materials(
        self,
        product: Product,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
        on_log: Optional[Callable[[str], None]] = None
    ) -> Product:
        """下载产品的所有素材

        对应 baiying.js 中的 downImage() + downMainVideo()

        Args:
            product: 产品信息
            on_progress: 进度回调 (message, current, total)
            on_log: 日志回调

        Returns:
            更新后的Product对象
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(f"[MaterialDownloader] {msg}")

        # 创建产品目录 (使用产品ID作为目录名更可靠)
        dir_name = f"{product.product_id}_{self._sanitize_filename(product.title[:20])}"
        product_dir = self.output_dir / dir_name
        product_dir.mkdir(parents=True, exist_ok=True)

        log(f"开始下载素材到: {product_dir}")

        # 下载图片 (对应 baiying.js 的 downImage)
        if product.images:
            log(f"开始下载 {len(product.images)} 张图片...")
            local_images = self._download_images(
                product.images,
                product.product_id,
                product_dir,
                on_progress,
                on_log
            )
            product.local_images = local_images
            log(f"图片下载完成: {len(local_images)}/{len(product.images)}")
        else:
            log("未找到产品图片")

        # 下载视频 (对应 baiying.js 的 downMainVideo)
        if product.video_url:
            log("开始下载产品视频...")
            video_path = self._download_video(
                product.video_url,
                product.product_id,
                product_dir,
                on_progress,
                on_log
            )
            if video_path:
                product.local_video = video_path
                log(f"视频下载完成: {video_path}")
            else:
                log("视频下载失败")

        # 保存产品信息 JSON 文件
        self._save_product_info(product, product_dir, on_log)

        return product

    def _save_product_info(
        self,
        product: Product,
        output_dir: Path,
        on_log: Optional[Callable[[str], None]] = None
    ) -> bool:
        """保存产品信息到 JSON 文件

        Args:
            product: 产品信息
            output_dir: 输出目录
            on_log: 日志回调

        Returns:
            是否保存成功
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(f"[MaterialDownloader] {msg}")

        try:
            # 构建产品信息字典
            product_info = {
                # 基础信息
                "product_id": product.product_id,
                "title": product.title,
                "url": product.url,

                # 价格和佣金
                "price": product.price,
                "commission": product.commission,
                "commission_rate": product.commission_rate,

                # 销量信息
                "monthly_sales": product.monthly_sales,
                "total_sales": product.total_sales,

                # 评价信息
                "rating": product.rating,
                "rating_percentage": product.rating_percentage,

                # 店铺信息
                "shop_name": product.shop_name,
                "shop_score": product.shop_score,

                # 素材信息
                "main_image": product.main_image,
                "images": product.images,
                "video_url": product.video_url,
                "cart_link": product.cart_link,

                # 本地文件路径
                "local_images": product.local_images,
                "local_video": product.local_video,

                # 元数据
                "download_time": datetime.now().isoformat(),
                "source": "baiying",
            }

            # 保存 JSON 文件
            json_path = output_dir / "product_info.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(product_info, f, ensure_ascii=False, indent=2)

            log(f"产品信息已保存: {json_path}")
            return True

        except Exception as e:
            log(f"保存产品信息失败: {e}")
            return False

    def _download_images(
        self,
        urls: List[str],
        product_id: str,
        output_dir: Path,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
        on_log: Optional[Callable[[str], None]] = None
    ) -> List[str]:
        """批量下载图片

        对应 baiying.js 的 downImage():
        文件名格式: {userId}_{excuteTime}_{product_id}_image_{index}.jpg

        简化格式: {product_id}_image_{index}.jpg

        Args:
            urls: 图片URL列表
            product_id: 产品ID
            output_dir: 输出目录
            on_progress: 进度回调
            on_log: 日志回调

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
                # 文件名格式参考 baiying.js
                filename = f"{product_id}_image_{i+1}.jpg"
                output_path = output_dir / filename
                future = executor.submit(self._download_file, url, output_path)
                futures[future] = (i, output_path, url)

            for future in as_completed(futures):
                i, output_path, url = futures[future]
                try:
                    success = future.result()
                    if success:
                        local_paths.append(str(output_path))
                        if on_log:
                            on_log(f"  图片 {i+1}/{total} 下载成功")
                    else:
                        if on_log:
                            on_log(f"  图片 {i+1}/{total} 下载失败")
                    if on_progress:
                        on_progress(f"下载图片 {i+1}/{total}", i+1, total)
                except Exception as e:
                    print(f"下载图片失败: {e}")
                    if on_log:
                        on_log(f"  图片 {i+1}/{total} 下载失败: {e}")

        return local_paths

    def _download_video(
        self,
        url: str,
        product_id: str,
        output_dir: Path,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
        on_log: Optional[Callable[[str], None]] = None
    ) -> str:
        """下载视频

        对应 baiying.js 的 downMainVideo():
        文件名格式: {userId}_{excuteTime}_{product_id}_video_1.mp4

        简化格式: {product_id}_video.mp4

        Args:
            url: 视频URL
            product_id: 产品ID
            output_dir: 输出目录
            on_progress: 进度回调
            on_log: 日志回调

        Returns:
            本地视频路径
        """
        if not url:
            return ""

        output_dir.mkdir(parents=True, exist_ok=True)

        # 文件名格式参考 baiying.js
        filename = f"{product_id}_video.mp4"
        output_path = output_dir / filename

        if on_progress:
            on_progress("下载视频...", 0, 1)

        if on_log:
            on_log(f"  视频URL: {url[:50]}...")

        success = self._download_file(url, output_path, is_video=True, on_log=on_log)

        if on_progress:
            on_progress("视频下载完成" if success else "视频下载失败", 1, 1)

        return str(output_path) if success else ""

    def _download_file(
        self,
        url: str,
        output_path: Path,
        is_video: bool = False,
        on_log: Optional[Callable[[str], None]] = None
    ) -> bool:
        """下载单个文件

        对应 baiying.js 的 downloadResource()
        支持分块下载大文件和进度显示

        Args:
            url: 文件URL
            output_path: 输出路径
            is_video: 是否是视频文件
            on_log: 日志回调

        Returns:
            是否下载成功
        """
        try:
            # 确保URL有协议 (对应 baiying.js 检查)
            if not url or not url.startswith('http'):
                if url and url.startswith('//'):
                    url = 'https:' + url
                else:
                    raise ValueError(f"无效的URL: {url}")

            # 使用不同的请求头
            headers = self.VIDEO_HEADERS if is_video else self.HEADERS

            # 发送请求
            response = self.session.get(
                url,
                headers=headers,
                timeout=self.timeout if not is_video else self.timeout * 3,
                stream=True  # 始终使用流式下载
            )
            response.raise_for_status()

            # 获取文件信息 (对应 baiying.js 的 Content-Type 和 Content-Length 检查)
            content_type = response.headers.get('Content-Type', '')
            content_length = response.headers.get('Content-Length')

            if on_log and is_video:
                size_info = f"{int(content_length) / 1024 / 1024:.2f}MB" if content_length else "未知"
                on_log(f"  响应信息: 类型={content_type}, 大小={size_info}")

            # 写入文件 (对应 baiying.js 的分块读取)
            bytes_written = 0
            chunk_size = 8192  # 8KB chunks
            last_reported_percent = -20  # 上次报告的百分比

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        bytes_written += len(chunk)

                        # 进度日志 - 每20%输出一次
                        if is_video and content_length and on_log:
                            total_size = int(content_length)
                            progress = bytes_written / total_size * 100
                            if progress >= last_reported_percent + 20:
                                last_reported_percent = int(progress // 20) * 20
                                on_log(f"  下载进度: {last_reported_percent}% ({total_size / 1024 / 1024:.1f}MB)")

            # 验证完整性 (对应 baiying.js 的数据完整性检查)
            if content_length and bytes_written != int(content_length):
                raise ValueError(f"数据不完整: 实际读取 {bytes_written} 字节, 预期 {content_length} 字节")

            return True

        except Exception as e:
            print(f"下载失败 {url}: {e}")
            if on_log:
                on_log(f"  下载失败: {e}")
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

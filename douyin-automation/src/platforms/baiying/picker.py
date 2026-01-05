"""百应选品模块

整合解析器和下载器，提供完整的选品流程
"""

import time
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from DrissionPage import ChromiumPage

from core.browser_manager import BrowserManager
from core.config import Config
from models.product import Product
from .parser import ProductParser
from .downloader import MaterialDownloader


class BaiyingPicker:
    """百应选品器

    实现从百应平台选品、筛选、下载素材的完整流程
    """

    def __init__(
        self,
        browser_manager: BrowserManager,
        account_id: str,
        config: Optional[Config] = None
    ):
        """初始化选品器

        Args:
            browser_manager: 浏览器管理器
            account_id: 账户ID
            config: 配置对象
        """
        self.browser_manager = browser_manager
        self.account_id = account_id
        self.config = config or Config()
        self.page: Optional[ChromiumPage] = None
        self.parser: Optional[ProductParser] = None

    def start(self, headless: bool = False) -> None:
        """启动浏览器并导航到百应

        Args:
            headless: 是否无头模式
        """
        self.page = self.browser_manager.navigate_to_platform(
            self.account_id, 'baiying', headless
        )
        self.parser = ProductParser(self.page)

    def close(self) -> None:
        """关闭浏览器"""
        self.browser_manager.close_browser(self.account_id, 'baiying')
        self.page = None
        self.parser = None

    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self.browser_manager.is_logged_in(self.account_id, 'baiying')

    def wait_for_login(self, timeout: float = 300) -> bool:
        """等待用户登录

        Args:
            timeout: 超时时间(秒)

        Returns:
            是否登录成功
        """
        return self.browser_manager.wait_for_login(self.account_id, 'baiying', timeout)

    def navigate_to_product(self, url: str) -> bool:
        """导航到产品页面

        Args:
            url: 产品URL

        Returns:
            是否成功
        """
        if not self.page:
            return False

        try:
            self.page.get(url)
            time.sleep(2)  # 等待页面加载
            return True
        except Exception as e:
            print(f"导航到产品页面失败: {e}")
            return False

    def parse_current_product(self) -> Optional[Product]:
        """解析当前页面的产品信息

        Returns:
            Product对象
        """
        if not self.parser:
            return None
        return self.parser.parse_product_info()

    def filter_product(self, product: Product) -> bool:
        """检查产品是否满足筛选条件

        Args:
            product: 产品信息

        Returns:
            是否满足条件
        """
        filter_config = self.config.get('filter', {})
        return product.meets_criteria(
            min_rating=filter_config.get('min_rating', 0),
            commission_min=filter_config.get('commission_min', 0),
            commission_max=filter_config.get('commission_max', float('inf')),
            price_min=filter_config.get('price_min', 0),
            price_max=filter_config.get('price_max', float('inf')),
            monthly_sales_min=filter_config.get('monthly_sales_min', 0),
            commission_type=filter_config.get('commission_type', 'amount')
        )

    def download_materials(
        self,
        product: Product,
        output_dir: Path,
        on_progress: Optional[Callable[[str, int, int], None]] = None
    ) -> Product:
        """下载产品素材

        Args:
            product: 产品信息
            output_dir: 输出目录
            on_progress: 进度回调

        Returns:
            更新后的Product
        """
        downloader = MaterialDownloader(output_dir)
        return downloader.download_materials(product, on_progress)

    def process_product_url(
        self,
        url: str,
        output_dir: Path,
        on_log: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None
    ) -> Optional[Product]:
        """处理单个产品URL

        完整流程: 导航 → 解析 → 筛选 → 下载素材

        Args:
            url: 产品URL
            output_dir: 输出目录
            on_log: 日志回调
            on_progress: 进度回调

        Returns:
            处理后的Product，失败返回None
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(msg)

        # 导航到产品页面
        log(f"正在访问产品页面: {url}")
        if not self.navigate_to_product(url):
            log("访问产品页面失败")
            return None

        # 解析产品信息
        log("正在解析产品信息...")
        product = self.parse_current_product()
        if not product:
            log("解析产品信息失败")
            return None

        log(f"产品: {product.title}")
        log(f"价格: ¥{product.price}, 佣金: ¥{product.commission}")
        log(f"月销: {product.monthly_sales}, 好评率: {product.rating_percentage}%")

        # 筛选
        if not self.filter_product(product):
            log("产品不满足筛选条件")
            return None

        log("产品满足筛选条件")
        log(f"找到 {len(product.images)} 张图片, 视频: {'有' if product.video_url else '无'}")

        # 下载素材
        log("开始下载素材...")
        product = self.download_materials(product, output_dir, on_progress)

        log(f"下载完成: {len(product.local_images)} 张图片")
        if product.local_video:
            log(f"视频已下载: {product.local_video}")

        return product

    def process_multiple_urls(
        self,
        urls: List[str],
        output_dir: Path,
        on_log: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
        on_product: Optional[Callable[[Product], None]] = None
    ) -> List[Product]:
        """批量处理产品URL

        Args:
            urls: 产品URL列表
            output_dir: 输出目录
            on_log: 日志回调
            on_progress: 进度回调
            on_product: 单个产品处理完成回调

        Returns:
            成功处理的Product列表
        """
        def log(msg: str):
            if on_log:
                on_log(msg)

        products = []
        total = len(urls)

        log(f"开始处理 {total} 个产品...")

        for i, url in enumerate(urls):
            log(f"\n[{i+1}/{total}] 处理产品...")

            if on_progress:
                on_progress(f"处理产品 {i+1}/{total}", i+1, total)

            product = self.process_product_url(url, output_dir, on_log)
            if product:
                products.append(product)
                if on_product:
                    on_product(product)

            # 避免请求过快
            if i < total - 1:
                time.sleep(2)

        log(f"\n处理完成: 共 {total} 个产品, 成功 {len(products)} 个")
        return products

    def get_statistics(self, products: List[Product]) -> Dict[str, Any]:
        """获取处理统计

        Args:
            products: 产品列表

        Returns:
            统计信息
        """
        total_images = sum(len(p.images) for p in products)
        downloaded_images = sum(len(p.local_images) for p in products)
        videos_count = sum(1 for p in products if p.video_url)
        downloaded_videos = sum(1 for p in products if p.local_video)

        return {
            'total_products': len(products),
            'total_images': total_images,
            'downloaded_images': downloaded_images,
            'total_videos': videos_count,
            'downloaded_videos': downloaded_videos,
            'avg_price': sum(p.price for p in products) / len(products) if products else 0,
            'avg_commission': sum(p.commission for p in products) / len(products) if products else 0,
        }

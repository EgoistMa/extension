"""百应选品模块

整合解析器和下载器，提供完整的选品流程
"""

import re
import time
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from DrissionPage import ChromiumPage

from core.browser_manager import BrowserManager
from core.config import Config
from models.product import Product
from .parser import ProductParser
from .downloader import MaterialDownloader


# ========== 数据解析辅助函数 ==========

def parse_price(text: str) -> float:
    """解析价格文本

    '到手价 ¥8.1' -> 8.1
    """
    if not text:
        return 0.0
    match = re.search(r'¥([\d.]+)', text)
    return float(match.group(1)) if match else 0.0


def parse_sales(text: str) -> int:
    """解析月销量文本

    '月销 1,433' -> 1433
    '月销 1.25万' -> 12500
    '月销 7.78万' -> 77800
    """
    if not text:
        return 0
    text = text.replace('月销', '').strip().replace(',', '')
    if '万' in text:
        return int(float(text.replace('万', '')) * 10000)
    try:
        return int(text)
    except ValueError:
        return 0


def parse_commission(text: str) -> float:
    """解析佣金文本

    '赚¥3.2' -> 3.2
    """
    if not text:
        return 0.0
    match = re.search(r'¥([\d.]+)', text)
    return float(match.group(1)) if match else 0.0


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

    def _parse_product_from_tab(self, tab) -> Optional[Product]:
        """从指定标签页解析产品信息

        Args:
            tab: ChromiumTab 对象

        Returns:
            Product对象
        """
        try:
            parser = ProductParser(tab)
            return parser.parse_product_info()
        except Exception as e:
            print(f"[BaiyingPicker] 解析产品失败: {e}")
            return None

    def _get_cart_link_from_tab(
        self,
        tab,
        on_log: Optional[Callable[[str], None]] = None
    ) -> str:
        """从产品详情页获取小黄车链接

        点击「复制链接」按钮，从剪贴板读取链接

        Args:
            tab: ChromiumTab 对象
            on_log: 日志回调

        Returns:
            小黄车链接，获取失败返回空字符串
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(f"[BaiyingPicker] {msg}")

        try:
            # 查找「复制链接」按钮 - 使用文本内容定位更稳定
            copy_link_selectors = [
                'xpath://div[contains(text(), "复制链接")]/..',
                'xpath://div[text()="复制链接"]/..',
                'xpath://*[contains(@class, "copyLink")]',
                'xpath://div[contains(@class, "rightPart")]//*[contains(text(), "复制链接")]/..',
            ]

            copy_btn = None
            for sel in copy_link_selectors:
                try:
                    copy_btn = tab.ele(sel, timeout=2)
                    if copy_btn:
                        log(f"  找到「复制链接」按钮")
                        break
                except Exception:
                    continue

            if not copy_btn:
                log("  未找到「复制链接」按钮")
                return ""

            # 点击按钮复制链接到剪贴板
            copy_btn.click()
            time.sleep(0.5)

            # 从剪贴板读取链接 - 使用 JavaScript
            try:
                # 方法1: 使用 navigator.clipboard API (需要页面焦点)
                cart_link = tab.run_js('''
                    return navigator.clipboard.readText().then(text => text).catch(() => '');
                ''')
            except Exception:
                cart_link = ""

            # 如果 JavaScript 方法失败，尝试使用 pyperclip
            if not cart_link:
                try:
                    import pyperclip
                    cart_link = pyperclip.paste()
                except Exception:
                    pass

            # 验证是否是有效链接
            if cart_link and ('douyin' in cart_link or 'http' in cart_link):
                log(f"  获取到小黄车链接: {cart_link[:50]}...")
                return cart_link
            else:
                log(f"  剪贴板内容不是有效链接: {cart_link[:30] if cart_link else '空'}...")
                return ""

        except Exception as e:
            log(f"  获取小黄车链接失败: {e}")
            return ""

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
        on_progress: Optional[Callable[[str, int, int], None]] = None,
        on_log: Optional[Callable[[str], None]] = None
    ) -> Product:
        """下载产品素材

        Args:
            product: 产品信息
            output_dir: 输出目录
            on_progress: 进度回调
            on_log: 日志回调

        Returns:
            更新后的Product
        """
        downloader = MaterialDownloader(output_dir)
        return downloader.download_materials(product, on_progress, on_log)

    def process_product_url(
        self,
        url: str,
        output_dir: Path,
        on_log: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
        skip_filter: bool = False
    ) -> Optional[Product]:
        """处理单个产品URL

        完整流程: 导航 → 解析 → 筛选 → 下载素材
        对应 baiying.js 的整体流程

        Args:
            url: 产品URL
            output_dir: 输出目录
            on_log: 日志回调
            on_progress: 进度回调
            skip_filter: 是否跳过筛选

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

        # 解析产品信息 (对应 baiying.js 的 getProductInfo)
        log("正在解析产品信息...")
        product = self.parse_current_product()
        if not product:
            log("解析产品信息失败")
            return None

        log(f"产品: {product.title}")
        log(f"产品ID: {product.product_id}")
        log(f"价格: ¥{product.price}, 佣金: ¥{product.commission} ({product.commission_rate}%)")
        log(f"已售: {product.total_sales}, 好评率: {product.rating_percentage}%")

        # 筛选 (违规词检测放到选品模块)
        if not skip_filter:
            if not self.filter_product(product):
                log("产品不满足筛选条件")
                return None
            log("产品满足筛选条件")

        log(f"找到 {len(product.images)} 张图片, 视频: {'有' if product.video_url else '无'}")

        # 下载素材 (对应 baiying.js 的 downImage + downMainVideo)
        log("开始下载素材...")
        product = self.download_materials(product, output_dir, on_progress, on_log)

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
        on_product: Optional[Callable[[Product], None]] = None,
        skip_filter: bool = False
    ) -> List[Product]:
        """批量处理产品URL

        当从选品列表选出 N 个产品后，使用此方法下载所有产品的素材

        Args:
            urls: 产品URL列表
            output_dir: 输出目录
            on_log: 日志回调
            on_progress: 进度回调
            on_product: 单个产品处理完成回调
            skip_filter: 是否跳过筛选 (已在选品阶段完成)

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

            product = self.process_product_url(
                url, output_dir, on_log, on_progress, skip_filter
            )
            if product:
                products.append(product)
                if on_product:
                    on_product(product)

            # 避免请求过快
            if i < total - 1:
                time.sleep(2)

        log(f"\n处理完成: 共 {total} 个产品, 成功 {len(products)} 个")
        return products

    def download_materials_for_products(
        self,
        products: List[Product],
        output_dir: Path,
        on_log: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
        on_product: Optional[Callable[[Product], None]] = None
    ) -> List[Product]:
        """为已选定的 N 个产品下载素材

        当选品模块已经选出 N 个产品后，使用此方法批量下载素材
        这是选品流程中"下载素材"步骤的入口

        Args:
            products: 已选定的产品列表 (包含图片URL等信息)
            output_dir: 输出目录
            on_log: 日志回调
            on_progress: 进度回调
            on_product: 单个产品处理完成回调

        Returns:
            更新后的Product列表 (包含本地文件路径)
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(msg)

        total = len(products)
        log(f"开始为 {total} 个产品下载素材...")

        downloaded_products = []
        downloader = MaterialDownloader(output_dir)

        for i, product in enumerate(products):
            log(f"\n[{i+1}/{total}] 下载产品素材: {product.title[:30]}...")

            if on_progress:
                on_progress(f"下载素材 {i+1}/{total}", i+1, total)

            try:
                # 下载素材
                updated_product = downloader.download_materials(
                    product,
                    on_progress=on_progress,
                    on_log=on_log
                )

                downloaded_products.append(updated_product)

                log(f"  完成: {len(updated_product.local_images)} 张图片" +
                    (f", 1 个视频" if updated_product.local_video else ""))

                if on_product:
                    on_product(updated_product)

            except Exception as e:
                log(f"  下载失败: {e}")
                # 即使下载失败也保留产品信息
                downloaded_products.append(product)

            # 避免请求过快
            if i < total - 1:
                time.sleep(1)

        success_count = sum(1 for p in downloaded_products if p.local_images)
        log(f"\n下载完成: 共 {total} 个产品, 成功 {success_count} 个")

        return downloaded_products

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

    # ========== 登录后自动选品流程 ==========

    def is_on_dashboard(self) -> bool:
        """检查是否在登录后的 dashboard 页面"""
        if not self.page:
            return False
        return 'dashboard' in self.page.url.lower()

    def _close_dropdown_menu(self) -> None:
        """关闭导航栏下拉菜单

        将鼠标移动到页面中间区域，触发下拉菜单关闭
        """
        if not self.page:
            return

        try:
            # 将鼠标移动到页面中间偏下的位置（避开顶部导航栏）
            # 获取视口大小，移动到中间位置
            self.page.actions.move(500, 400)  # 移动到页面中间区域
            time.sleep(0.5)
        except Exception:
            # 忽略失败
            pass

    def click_picking_header(self, on_log: Optional[Callable[[str], None]] = None) -> bool:
        """点击顶部「选品」导航进入选品页面

        Args:
            on_log: 日志回调

        Returns:
            是否成功
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(f"[BaiyingPicker] {msg}")

        if not self.page:
            log("错误: 浏览器未启动")
            return False

        try:
            log(f"当前页面URL: {self.page.url}")
            log("尝试点击「选品」导航...")

            # 多种选择器尝试
            selectors = [
                'css:div[data-guide="xuanpin"]',
                'xpath://div[@data-guide="xuanpin"]',
                'xpath://div[contains(@class, "headerNav-item")]//div[text()="选品"]/..',
                'xpath://div[contains(@class, "headerNav")]//div[contains(text(), "选品")]',
                'xpath://*[contains(@class, "headerNav")]//*[text()="选品"]',
            ]

            picking_btn = None
            for selector in selectors:
                log(f"  尝试选择器: {selector}")
                try:
                    picking_btn = self.page.ele(selector, timeout=2)
                    if picking_btn:
                        log(f"  找到元素: {picking_btn.tag}, text={picking_btn.text[:20] if picking_btn.text else 'N/A'}")
                        break
                except Exception as e:
                    log(f"  选择器失败: {e}")
                    continue

            if not picking_btn:
                log("未找到「选品」按钮，所有选择器均失败")
                return False

            log("点击选品按钮...")
            picking_btn.click()
            time.sleep(1)

            # 检查是否出现下拉菜单，如果有则点击「选品广场」或「精选联盟」
            dropdown_items = [
                'xpath://div[contains(@class, "dropdown") or contains(@class, "menu") or contains(@class, "popup")]//*[contains(text(), "选品广场")]',
                'xpath://div[contains(@class, "dropdown") or contains(@class, "menu") or contains(@class, "popup")]//*[contains(text(), "精选联盟")]',
                'xpath://a[contains(text(), "选品广场")]',
                'xpath://a[contains(text(), "精选联盟")]',
                'xpath://*[contains(text(), "选品广场")]',
            ]

            for item_sel in dropdown_items:
                try:
                    menu_item = self.page.ele(item_sel, timeout=1)
                    if menu_item:
                        log(f"发现下拉菜单项: {menu_item.text[:20] if menu_item.text else 'N/A'}")
                        menu_item.click()
                        time.sleep(2)
                        break
                except Exception:
                    continue
            else:
                # 没有下拉菜单，可能已经直接跳转了
                time.sleep(1)

            # 验证是否进入选品页面
            current_url = self.page.url.lower()
            log(f"点击后URL: {self.page.url}")

            if 'pick' in current_url or 'merch' in current_url or 'select' in current_url:
                log("成功进入选品页面")

            # 确保关闭导航栏下拉菜单 - 多种方式尝试
            log("关闭导航下拉菜单...")
            self._close_dropdown_menu()

            return True

        except Exception as e:
            log(f"点击选品导航失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def apply_monthly_sales_filter(
        self,
        monthly_sales_min: int,
        on_log: Optional[Callable[[str], None]] = None
    ) -> bool:
        """应用月销筛选器

        Args:
            monthly_sales_min: 最低月销量
            on_log: 日志回调

        Returns:
            是否成功
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(f"[BaiyingPicker] {msg}")

        if not self.page:
            return False

        # 月销选项映射 (注意：DOM 中使用 ≥ 符号，不是 >=)
        sales_options = {
            0: '不限',
            1: '500以下',  # 特殊选项
            500: '≥500',
            1000: '≥1000',
            5000: '≥5000',
            10000: '≥1w',
            50000: '≥5w',
            100000: '≥10w',
            500000: '≥50w',
            1000000: '≥100w',
        }

        # 找到最接近的选项（向下取整）
        target_option = '不限'
        for threshold in sorted(sales_options.keys(), reverse=True):
            if monthly_sales_min >= threshold:
                target_option = sales_options[threshold]
                break

        log(f"月销筛选: {monthly_sales_min} -> 选择「{target_option}」")

        try:
            # 点击「月销」筛选器 - 多种选择器尝试
            sales_selectors = [
                'xpath://div[contains(@class, "combine-select-content")]//span[text()="月销"]/..',
                'xpath://div[contains(@class, "boxCombineSelect")]//span[text()="月销"]/..',
                'xpath://*[contains(@class, "select")]//span[text()="月销"]/..',
                'xpath://span[text()="月销"]/..',
            ]

            sales_btn = None
            for sel in sales_selectors:
                sales_btn = self.page.ele(sel, timeout=1)
                if sales_btn:
                    log(f"  找到月销筛选器")
                    break

            if not sales_btn:
                log("未找到月销筛选器")
                return False

            sales_btn.click()
            time.sleep(0.8)

            # 选择对应选项 - 使用 auxo-select 组件的实际 DOM 结构
            option_selectors = [
                # auxo-select 组件的实际结构
                f'xpath://div[contains(@class, "auxo-select-dropdown")]//div[contains(@class, "auxo-select-item-option-content") and text()="{target_option}"]',
                f'xpath://div[contains(@class, "auxo-select-dropdown")]//div[text()="{target_option}"]',
                f'xpath://div[contains(@class, "auxo-select-item-option-content") and text()="{target_option}"]',
                # 备用选择器
                f'xpath://div[contains(@class, "dropdown") or contains(@class, "popup") or contains(@class, "overlay")]//*[text()="{target_option}"]',
                f'xpath://div[contains(@class, "select-dropdown")]//*[text()="{target_option}"]',
                f'xpath://*[contains(@class, "option-content") and text()="{target_option}"]',
                f'xpath://div[text()="{target_option}"]',
            ]

            option_ele = None
            for sel in option_selectors:
                try:
                    option_ele = self.page.ele(sel, timeout=1)
                    if option_ele:
                        log(f"  找到选项元素: {sel[:50]}...")
                        break
                except Exception:
                    continue

            if option_ele:
                option_ele.click()
                log(f"已选择月销: {target_option}")
                time.sleep(0.5)
                return True
            else:
                log(f"未找到月销选项: {target_option}")
                # 点击空白处关闭下拉
                try:
                    self.page.ele('tag:body').click()
                except Exception:
                    pass
                time.sleep(0.3)
                return False

        except Exception as e:
            log(f"应用月销筛选失败: {e}")
            return False

    def apply_rating_filter(
        self,
        min_rating: float,
        on_log: Optional[Callable[[str], None]] = None
    ) -> bool:
        """应用好评率筛选器

        Args:
            min_rating: 最低好评率 (如 90 表示 90%)
            on_log: 日志回调

        Returns:
            是否成功
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(f"[BaiyingPicker] {msg}")

        if not self.page:
            return False

        # 好评率选项映射 (注意：DOM 中使用 ≥ 符号，不是 >=)
        rating_options = {
            0: '不限',
            80: '≥80%',
            85: '≥85%',
            90: '≥90%',
            95: '≥95%',
        }

        # 找到最接近的选项（向下取整）
        target_option = '不限'
        for threshold in sorted(rating_options.keys(), reverse=True):
            if min_rating >= threshold:
                target_option = rating_options[threshold]
                break

        log(f"好评率筛选: {min_rating}% -> 选择「{target_option}」")

        try:
            # 点击「好评率」筛选器 - 多种选择器尝试
            rating_selectors = [
                'xpath://div[contains(@class, "combine-select-content")]//span[text()="好评率"]/..',
                'xpath://div[contains(@class, "boxCombineSelect")]//span[text()="好评率"]/..',
                'xpath://*[contains(@class, "select")]//span[text()="好评率"]/..',
                'xpath://span[text()="好评率"]/..',
            ]

            rating_btn = None
            for sel in rating_selectors:
                rating_btn = self.page.ele(sel, timeout=1)
                if rating_btn:
                    log(f"  找到好评率筛选器")
                    break

            if not rating_btn:
                log("未找到好评率筛选器")
                return False

            rating_btn.click()
            time.sleep(0.8)

            # 选择对应选项 - 使用 auxo-select 组件的实际 DOM 结构
            option_selectors = [
                # auxo-select 组件的实际结构
                f'xpath://div[contains(@class, "auxo-select-dropdown")]//div[contains(@class, "auxo-select-item-option-content") and text()="{target_option}"]',
                f'xpath://div[contains(@class, "auxo-select-dropdown")]//div[text()="{target_option}"]',
                f'xpath://div[contains(@class, "auxo-select-item-option-content") and text()="{target_option}"]',
                # 备用选择器
                f'xpath://div[contains(@class, "dropdown") or contains(@class, "popup") or contains(@class, "overlay")]//*[text()="{target_option}"]',
                f'xpath://div[contains(@class, "select-dropdown")]//*[text()="{target_option}"]',
                f'xpath://*[contains(@class, "option-content") and text()="{target_option}"]',
                f'xpath://div[text()="{target_option}"]',
            ]

            option_ele = None
            for sel in option_selectors:
                try:
                    option_ele = self.page.ele(sel, timeout=1)
                    if option_ele:
                        log(f"  找到选项元素: {sel[:50]}...")
                        break
                except Exception:
                    continue

            if option_ele:
                option_ele.click()
                log(f"已选择好评率: {target_option}")
                time.sleep(0.5)
                return True
            else:
                log(f"未找到好评率选项: {target_option}")
                # 点击空白处关闭下拉
                try:
                    self.page.ele('tag:body').click()
                except Exception:
                    pass
                time.sleep(0.3)
                return False

        except Exception as e:
            log(f"应用好评率筛选失败: {e}")
            return False

    def apply_filters_from_config(
        self,
        on_log: Optional[Callable[[str], None]] = None
    ) -> bool:
        """根据 config 配置应用筛选条件

        Args:
            on_log: 日志回调

        Returns:
            是否成功应用了筛选
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(f"[BaiyingPicker] {msg}")

        filter_config = self.config.get('filter', {})
        log(f"筛选配置: {filter_config}")

        applied = 0

        # 应用月销筛选
        monthly_sales_min = filter_config.get('monthly_sales_min', 0)
        if monthly_sales_min > 0:
            if self.apply_monthly_sales_filter(monthly_sales_min, on_log):
                applied += 1

        # 应用好评率筛选
        min_rating = filter_config.get('min_rating', 0)
        if min_rating > 0:
            if self.apply_rating_filter(min_rating, on_log):
                applied += 1

        log(f"共应用 {applied} 个筛选条件")
        return applied > 0

    def wait_for_login_and_navigate(
        self,
        timeout: float = 300,
        on_log: Optional[Callable[[str], None]] = None
    ) -> bool:
        """等待登录成功后自动进入选品页面并应用筛选

        Args:
            timeout: 登录超时时间(秒)
            on_log: 日志回调

        Returns:
            是否成功
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(f"[BaiyingPicker] {msg}")

        if not self.page:
            log("错误: 浏览器未启动")
            return False

        log("等待登录...")
        log(f"当前URL: {self.page.url}")

        # 等待登录成功 (URL 包含 dashboard)
        start_time = time.time()
        check_count = 0
        while time.time() - start_time < timeout:
            current_url = self.page.url
            check_count += 1
            if check_count % 5 == 0:  # 每10秒输出一次
                log(f"检测中... URL: {current_url}")

            if self.is_on_dashboard():
                log(f"检测到登录成功! URL: {current_url}")
                break
            time.sleep(2)
        else:
            log(f"登录超时，最终URL: {self.page.url}")
            return False

        # 等待页面完全加载
        log("等待页面加载...")
        time.sleep(3)

        # 点击「选品」header
        if not self.click_picking_header(on_log):
            log("进入选品页面失败")
            return False

        # 等待选品页面加载
        time.sleep(2)

        # 再次确保下拉菜单已关闭（防止遮挡筛选器）
        self._close_dropdown_menu()
        time.sleep(0.5)

        # 应用筛选条件
        log("应用筛选条件...")
        self.apply_filters_from_config(on_log)

        log("选品页面已准备就绪")
        return True

    # ========== 智能选品流程 ==========

    def get_product_list(
        self,
        on_log: Optional[Callable[[str], None]] = None
    ) -> List[Dict[str, Any]]:
        """从选品广场页面获取产品卡片列表

        使用 JavaScript 批量提取数据，大幅提升速度。

        Args:
            on_log: 日志回调

        Returns:
            产品信息列表 [{index, title, price, sales, commission_ratio, commission, card_element}, ...]
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(f"[BaiyingPicker] {msg}")

        if not self.page:
            log("错误: 浏览器未启动")
            return []

        log("正在获取产品列表...")

        # 等待产品卡片加载
        time.sleep(2)

        # 查找所有产品卡片
        cards = self.page.eles('css:div.index_module__card____3337', timeout=5)
        if not cards:
            # 备用选择器
            cards = self.page.eles('css:div[class*="card____"]', timeout=3)

        log(f"找到 {len(cards)} 个产品卡片")

        if not cards:
            log("未找到任何产品卡片")
            return []

        # 逐个解析卡片数据（使用较短的超时时间）
        products = []
        batch_results = []  # 存储当前批次的解析结果

        for i, card in enumerate(cards):
            try:
                # 提取标题 - 优先尝试普通标题，再尝试抖音旗舰标题(luckyTitle)
                title = ""
                title_ele = card.ele('css:div[class*="title___"]:not([class*="luckyTitle"]) > span', timeout=0.3)
                if title_ele:
                    title = title_ele.text.strip()

                # 如果普通标题为空，尝试获取 luckyTitle（抖音旗舰产品）
                if not title:
                    lucky_title_ele = card.ele('css:div[class*="luckyTitle___"] > span', timeout=0.3)
                    if lucky_title_ele:
                        title = lucky_title_ele.text.strip()

                # 提取价格
                price_ele = card.ele('css:span[class*="price___"]', timeout=0.3)
                price_text = price_ele.text.strip() if price_ele else ""

                # 提取月销
                sales_ele = card.ele('css:div[class*="priceAndSales___"] > span:last-child', timeout=0.3)
                sales_text = sales_ele.text.strip() if sales_ele else ""

                # 提取佣金比例
                ratio_ele = card.ele('css:div[class*="cosratio___"]', timeout=0.3)
                ratio_text = ratio_ele.text.strip() if ratio_ele else "0"

                # 提取佣金金额
                fee_ele = card.ele('css:div[class*="cosFee___"]', timeout=0.3)
                fee_text = fee_ele.text.strip() if fee_ele else ""

                # 解析数值
                price = parse_price(price_text)
                sales = parse_sales(sales_text)
                commission_ratio = int(ratio_text) if ratio_text.isdigit() else 0
                commission = parse_commission(fee_text)

                # 记录本次解析结果
                batch_results.append({
                    'index': i,
                    'title': title[:20] + "..." if len(title) > 20 else title,
                    'price': price,
                    'price_text': price_text,
                    'sales': sales,
                    'sales_text': sales_text,
                    'ratio': commission_ratio,
                    'commission': commission,
                })

                # 只添加有效数据
                if title or price_text:
                    products.append({
                        'index': i,
                        'title': title or f"产品{i+1}",
                        'price': price,
                        'sales': sales,
                        'commission_ratio': commission_ratio,
                        'commission': commission,
                        'card_element': card,
                    })

                # 每10个打印一次进度和结果
                if (i + 1) % 10 == 0:
                    log(f"  已解析 {i+1}/{len(cards)} 个卡片...")
                    log(f"  --- 第 {i-8}-{i+1} 个卡片解析结果 ---")
                    for r in batch_results:
                        log(f"    [{r['index']:2d}] {r['title']:<23} | 价格: {r['price_text']:<15} -> ¥{r['price']:<6.1f} | 月销: {r['sales_text']:<10} -> {r['sales']:<6d} | 佣金: {r['ratio']}%/¥{r['commission']}")
                    batch_results = []  # 清空批次结果

            except Exception as e:
                log(f"  解析卡片 {i} 失败: {e}")
                batch_results.append({'index': i, 'title': f'[解析失败: {e}]', 'price': 0, 'price_text': '', 'sales': 0, 'sales_text': '', 'ratio': 0, 'commission': 0})
                continue

        # 打印剩余的结果
        if batch_results:
            log(f"  --- 剩余 {len(batch_results)} 个卡片解析结果 ---")
            for r in batch_results:
                log(f"    [{r['index']:2d}] {r['title']:<23} | 价格: {r['price_text']:<15} -> ¥{r['price']:<6.1f} | 月销: {r['sales_text']:<10} -> {r['sales']:<6d} | 佣金: {r['ratio']}%/¥{r['commission']}")

        log(f"解析完成: 成功 {len(products)} 个产品")
        return products

    def _get_product_list_slow(
        self,
        on_log: Optional[Callable[[str], None]] = None
    ) -> List[Dict[str, Any]]:
        """逐个解析产品卡片（备用方法）"""
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(f"[BaiyingPicker] {msg}")

        cards = self.page.eles('css:div[class*="card____"]', timeout=3)
        log(f"找到 {len(cards)} 个产品卡片，逐个解析...")

        products = []
        for i, card in enumerate(cards):
            if i > 0 and i % 10 == 0:
                log(f"  已解析 {i}/{len(cards)} 个卡片...")

            try:
                # 提取标题 - 优先尝试普通标题，再尝试抖音旗舰标题(luckyTitle)
                title = ""
                title_ele = card.ele('css:div[class*="title___"]:not([class*="luckyTitle"]) > span', timeout=0.2)
                if title_ele:
                    title = title_ele.text.strip()
                # 如果普通标题为空，尝试获取 luckyTitle（抖音旗舰产品）
                if not title:
                    lucky_title_ele = card.ele('css:div[class*="luckyTitle___"] > span', timeout=0.2)
                    if lucky_title_ele:
                        title = lucky_title_ele.text.strip()
                if not title:
                    title = f"产品{i+1}"

                price_ele = card.ele('css:span[class*="price___"]', timeout=0.2)
                price = parse_price(price_ele.text if price_ele else "")

                sales_ele = card.ele('css:div[class*="priceAndSales___"] > span:last-child', timeout=0.2)
                sales = parse_sales(sales_ele.text if sales_ele else "")

                ratio_ele = card.ele('css:div[class*="cosratio___"]', timeout=0.2)
                ratio_text = ratio_ele.text if ratio_ele else "0"
                commission_ratio = int(ratio_text) if ratio_text.isdigit() else 0

                fee_ele = card.ele('css:div[class*="cosFee___"]', timeout=0.2)
                commission = parse_commission(fee_ele.text if fee_ele else "")

                if title or price > 0:
                    products.append({
                        'index': i,
                        'title': title,
                        'price': price,
                        'sales': sales,
                        'commission_ratio': commission_ratio,
                        'commission': commission,
                        'card_element': card,
                    })
            except Exception as e:
                log(f"  解析卡片 {i} 失败: {e}")
                continue

        log(f"解析完成: 成功 {len(products)} 个产品")
        return products

    def filter_products_by_config(
        self,
        products: List[Dict[str, Any]],
        on_log: Optional[Callable[[str], None]] = None
    ) -> List[Dict[str, Any]]:
        """根据配置筛选产品列表

        Args:
            products: 产品列表
            on_log: 日志回调

        Returns:
            满足条件的产品列表
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(f"[BaiyingPicker] {msg}")

        filter_config = self.config.get('filter', {})

        price_min = filter_config.get('price_min', 0)
        price_max = filter_config.get('price_max', float('inf'))
        commission_min = filter_config.get('commission_min', 0)
        commission_max = filter_config.get('commission_max', float('inf'))
        commission_type = filter_config.get('commission_type', 'amount')

        log(f"筛选条件: 价格 {price_min}-{price_max}, 佣金({commission_type}) {commission_min}-{commission_max}")

        filtered = []
        for p in products:
            # 价格筛选
            if not (price_min <= p['price'] <= price_max):
                continue

            # 佣金筛选
            if commission_type == 'amount':
                if not (commission_min <= p['commission'] <= commission_max):
                    continue
            else:  # ratio
                if not (commission_min <= p['commission_ratio'] <= commission_max):
                    continue

            filtered.append(p)

        log(f"筛选后剩余 {len(filtered)} 个产品 (原 {len(products)} 个)")
        return filtered

    def auto_pick_products(
        self,
        n: int,
        output_dir: Path,
        on_log: Optional[Callable[[str], None]] = None,
        on_progress: Optional[Callable[[str, int, int], None]] = None
    ) -> List[Product]:
        """自动选择 N 个产品并下载素材

        完整流程:
        1. 获取产品列表
        2. 打印全部产品
        3. 筛选满足条件的产品
        4. 打印筛选结果
        5. 选择前 N 个
        6. 逐个进入详情页下载素材

        Args:
            n: 要选择的产品数量
            output_dir: 素材输出目录
            on_log: 日志回调
            on_progress: 进度回调

        Returns:
            下载完素材的 Product 列表
        """
        def log(msg: str):
            if on_log:
                on_log(msg)
            print(f"[BaiyingPicker] {msg}")

        if not self.page:
            log("错误: 浏览器未启动")
            return []

        # 1. 获取产品列表
        products = self.get_product_list(on_log)
        if not products:
            log("=" * 60)
            log("⚠️ 警告: 未获取到任何产品!")
            log("   可能原因:")
            log("   1. 页面尚未完全加载")
            log("   2. 筛选条件过于严格导致无结果")
            log("   3. 需要重新登录")
            log("=" * 60)
            return []

        # 2. 打印全部产品
        log("=" * 60)
        log(f"页面产品列表 (共 {len(products)} 个):")
        log("-" * 60)
        for p in products:
            title_short = p['title'][:25] + "..." if len(p['title']) > 25 else p['title']
            log(f"  [{p['index']:2d}] {title_short:<28} ¥{p['price']:<6.1f} 月销{p['sales']:<6d} 佣金{p['commission_ratio']}%/¥{p['commission']}")
        log("=" * 60)

        # 3. 根据配置筛选
        filtered = self.filter_products_by_config(products, on_log)

        if not filtered:
            filter_config = self.config.get('filter', {})
            log("=" * 60)
            log("⚠️ 警告: 筛选后没有符合条件的产品!")
            log(f"   筛选条件:")
            log(f"     - 价格: {filter_config.get('price_min', 0)} - {filter_config.get('price_max', '无上限')}")
            log(f"     - 佣金: {filter_config.get('commission_min', 0)} - {filter_config.get('commission_max', '无上限')}")
            log(f"   共 {len(products)} 个产品均不符合条件")
            log("   建议: 请调整设置中的筛选条件")
            log("=" * 60)
            return []

        # 4. 打印筛选结果
        log("=" * 60)
        log(f"筛选后产品 (共 {len(filtered)} 个):")
        log("-" * 60)
        for p in filtered:
            title_short = p['title'][:25] + "..." if len(p['title']) > 25 else p['title']
            log(f"  [{p['index']:2d}] {title_short:<28} ¥{p['price']:<6.1f} 月销{p['sales']:<6d} 佣金{p['commission_ratio']}%/¥{p['commission']}")
        log("=" * 60)

        # 5. 选择前 N 个
        selected = filtered[:n]
        log(f"选择前 {len(selected)} 个产品进行处理")

        # 6. 逐个处理：点击进入详情页(新标签) -> 解析 -> 下载素材 -> 关闭标签
        result_products = []

        # 保存原始标签页的 tab_id
        original_tab_ids = self.page.tab_ids.copy()
        log(f"原始标签页: {original_tab_ids}")

        for i, p in enumerate(selected):
            log(f"\n{'='*60}")
            log(f"[{i+1}/{len(selected)}] 处理产品: {p['title'][:40]}...")

            if on_progress:
                on_progress(f"处理产品 {i+1}/{len(selected)}", i+1, len(selected))

            try:
                # 点击卡片 - 会打开新标签页
                log("  点击进入产品详情...")
                p['card_element'].click()
                time.sleep(3)

                # 获取新的标签页列表
                current_tab_ids = self.page.tab_ids
                log(f"  当前标签页数量: {len(current_tab_ids)}")

                # 找到新打开的标签页 ID
                new_tab_ids = [t for t in current_tab_ids if t not in original_tab_ids]

                if new_tab_ids:
                    new_tab_id = new_tab_ids[-1]  # 取最新打开的
                    log(f"  新标签页ID: {new_tab_id}")

                    # 使用 get_tab() 获取新标签页对象
                    new_tab = self.page.get_tab(new_tab_id)
                    log(f"  切换到新标签页: {new_tab.url[:50] if new_tab.url else 'loading...'}...")
                    time.sleep(2)

                    # 使用新标签页对象创建 parser
                    self.parser = ProductParser(new_tab)

                    # 解析产品详情 (在新标签页上操作)
                    log("  解析产品详情...")
                    product = self._parse_product_from_tab(new_tab)

                    if product:
                        log(f"  产品ID: {product.product_id}")
                        log(f"  图片数: {len(product.images)}, 视频: {'有' if product.video_url else '无'}")

                        # 获取小黄车链接
                        log("  获取小黄车链接...")
                        cart_link = self._get_cart_link_from_tab(new_tab, on_log)
                        if cart_link:
                            product.cart_link = cart_link

                        # 下载素材
                        log("  开始下载素材...")
                        product = self.download_materials(product, output_dir, on_log=on_log)

                        log(f"  下载完成: {len(product.local_images)} 张图片")
                        result_products.append(product)
                    else:
                        log("  警告: 解析产品详情失败")

                    # 关闭新标签页
                    new_tab.close()
                    log("  已关闭产品详情页")
                    time.sleep(1)
                else:
                    log("  警告: 点击后未打开新标签页")

            except Exception as e:
                log(f"  错误: 处理产品失败 - {e}")
                import traceback
                traceback.print_exc()
                # 尝试关闭多余的标签页
                try:
                    current_tabs = self.page.tab_ids
                    for tid in current_tabs:
                        if tid not in original_tab_ids:
                            self.page.get_tab(tid).close()
                except Exception:
                    pass

            # 避免请求过快
            if i < len(selected) - 1:
                time.sleep(2)

        log(f"\n{'='*60}")
        log(f"选品完成: 共处理 {len(selected)} 个产品, 成功 {len(result_products)} 个")
        log("=" * 60)

        return result_products

"""百应产品页面解析器

参考 baiying.js 中的 getProductInfo() 和 getBaiyingImageUrls() 实现
"""

import re
from typing import List, Optional, Tuple
from DrissionPage import ChromiumPage

from models.product import Product


class ProductParser:
    """百应产品页面解析器"""

    def __init__(self, page: ChromiumPage):
        """初始化解析器

        Args:
            page: 浏览器页面实例
        """
        self.page = page

    def parse_product_info(self) -> Optional[Product]:
        """解析当前页面的产品信息

        对应 baiying.js 中的 getProductInfo()

        Returns:
            Product对象，解析失败返回None
        """
        try:
            # 获取产品ID (从URL中提取)
            product_id = self._extract_product_id()
            if not product_id:
                return None

            # 获取产品标题
            title = self._get_text_content('.product-title', '') or \
                    self._get_text_content('[class*="productTitle"]', '') or \
                    self._get_text_content('h1', '')

            # 获取产品URL
            url = self.page.url

            # 获取价格信息
            price = self._parse_price()

            # 获取佣金信息
            commission, commission_rate = self._parse_commission()

            # 获取销量信息
            monthly_sales, total_sales = self._parse_sales()

            # 获取评价信息
            rating, rating_percentage = self._parse_rating()

            # 获取店铺信息
            shop_name, shop_score = self._parse_shop_info()

            # 获取素材
            images = self.get_product_images()
            video_url = self._get_video_url()
            main_image = images[0] if images else ""

            return Product(
                product_id=product_id,
                title=title.strip(),
                url=url,
                price=price,
                commission=commission,
                commission_rate=commission_rate,
                monthly_sales=monthly_sales,
                total_sales=total_sales,
                rating=rating,
                rating_percentage=rating_percentage,
                shop_name=shop_name,
                shop_score=shop_score,
                main_image=main_image,
                images=images,
                video_url=video_url
            )
        except Exception as e:
            print(f"解析产品信息失败: {e}")
            return None

    def _extract_product_id(self) -> str:
        """从URL中提取产品ID"""
        url = self.page.url
        # 尝试多种URL格式
        patterns = [
            r'/product/(\d+)',
            r'product_id=(\d+)',
            r'/goods/(\d+)',
            r'id=(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return ""

    def _get_text_content(self, selector: str, default: str = "") -> str:
        """获取元素文本内容"""
        try:
            ele = self.page.ele(selector, timeout=1)
            if ele:
                return ele.text.strip()
        except Exception:
            pass
        return default

    def _parse_number(self, text: str) -> float:
        """从文本中解析数字"""
        if not text:
            return 0.0
        # 移除非数字字符（保留小数点和负号）
        text = re.sub(r'[^\d.\-]', '', text.replace(',', ''))
        try:
            return float(text) if text else 0.0
        except ValueError:
            return 0.0

    def _parse_price(self) -> float:
        """解析到手价"""
        # 尝试多个选择器
        selectors = [
            '[class*="salePrice"]',
            '[class*="price"]',
            '.price-value',
            '[data-testid="price"]',
        ]
        for selector in selectors:
            text = self._get_text_content(selector)
            if text:
                price = self._parse_number(text)
                if price > 0:
                    return price
        return 0.0

    def _parse_commission(self) -> Tuple[float, float]:
        """解析佣金信息

        Returns:
            (佣金金额, 佣金比例)
        """
        commission = 0.0
        commission_rate = 0.0

        # 查找佣金元素
        selectors = [
            '[class*="commission"]',
            '[class*="Commission"]',
            '[class*="yongjin"]',
        ]

        for selector in selectors:
            text = self._get_text_content(selector)
            if text:
                # 检查是否是比例
                if '%' in text:
                    rate = self._parse_number(text.replace('%', ''))
                    if rate > 0:
                        commission_rate = rate
                else:
                    # 金额
                    amount = self._parse_number(text)
                    if amount > 0:
                        commission = amount

        return commission, commission_rate

    def _parse_sales(self) -> Tuple[int, int]:
        """解析销量信息

        Returns:
            (月销量, 总销量)
        """
        monthly_sales = 0
        total_sales = 0

        # 月销
        monthly_selectors = [
            '[class*="monthSale"]',
            '[class*="month-sale"]',
            ':contains("月销")',
        ]
        for selector in monthly_selectors:
            text = self._get_text_content(selector)
            if text and '月' in text:
                # 处理 "1.2万" 这样的格式
                monthly_sales = self._parse_sales_number(text)
                if monthly_sales > 0:
                    break

        # 总销/已售
        total_selectors = [
            '[class*="totalSale"]',
            '[class*="sold"]',
            ':contains("已售")',
        ]
        for selector in total_selectors:
            text = self._get_text_content(selector)
            if text and ('售' in text or '销' in text):
                total_sales = self._parse_sales_number(text)
                if total_sales > 0:
                    break

        return monthly_sales, total_sales

    def _parse_sales_number(self, text: str) -> int:
        """解析销量数字，处理万/亿等单位"""
        if not text:
            return 0

        multiplier = 1
        if '亿' in text:
            multiplier = 100000000
            text = text.replace('亿', '')
        elif '万' in text:
            multiplier = 10000
            text = text.replace('万', '')
        elif 'w' in text.lower():
            multiplier = 10000
            text = re.sub(r'[wW]', '', text)

        num = self._parse_number(text)
        return int(num * multiplier)

    def _parse_rating(self) -> Tuple[float, float]:
        """解析评价信息

        Returns:
            (评分, 好评率)
        """
        rating = 0.0
        rating_percentage = 0.0

        # 评分 (0-5分)
        rating_selectors = [
            '[class*="score"]',
            '[class*="rating"]',
            '[class*="star"]',
        ]
        for selector in rating_selectors:
            text = self._get_text_content(selector)
            if text:
                r = self._parse_number(text)
                if 0 < r <= 5:
                    rating = r
                    break

        # 好评率
        rate_selectors = [
            '[class*="goodRate"]',
            '[class*="good-rate"]',
            '[class*="praise"]',
            ':contains("好评")',
        ]
        for selector in rate_selectors:
            text = self._get_text_content(selector)
            if text and ('好评' in text or '%' in text):
                rate = self._parse_number(text.replace('%', ''))
                if 0 < rate <= 100:
                    rating_percentage = rate
                    break

        return rating, rating_percentage

    def _parse_shop_info(self) -> Tuple[str, float]:
        """解析店铺信息

        Returns:
            (店铺名称, 店铺评分)
        """
        shop_name = ""
        shop_score = 0.0

        # 店铺名称
        name_selectors = [
            '[class*="shopName"]',
            '[class*="shop-name"]',
            '[class*="storeName"]',
        ]
        for selector in name_selectors:
            name = self._get_text_content(selector)
            if name:
                shop_name = name
                break

        # 店铺评分
        score_selectors = [
            '[class*="shopScore"]',
            '[class*="shop-score"]',
            '[class*="storeScore"]',
        ]
        for selector in score_selectors:
            text = self._get_text_content(selector)
            if text:
                score = self._parse_number(text)
                if 0 < score <= 5:
                    shop_score = score
                    break

        return shop_name, shop_score

    def get_product_images(self) -> List[str]:
        """获取产品图片列表

        对应 baiying.js 中的 getBaiyingImageUrls()
        从 slick-track 中获取图片

        Returns:
            图片URL列表
        """
        images = []

        try:
            # 优先从 slick-track 获取 (轮播图)
            slick_track = self.page.ele('.slick-track', timeout=2)
            if slick_track:
                img_elements = slick_track.eles('img')
                for img in img_elements:
                    src = img.attr('src') or img.attr('data-src')
                    if src and self._is_valid_image_url(src):
                        images.append(self._clean_image_url(src))

            # 如果 slick-track 没有图片，尝试其他选择器
            if not images:
                selectors = [
                    '.product-images img',
                    '[class*="productImage"] img',
                    '.gallery img',
                    '.swiper-slide img',
                ]
                for selector in selectors:
                    img_elements = self.page.eles(selector, timeout=1)
                    for img in img_elements:
                        src = img.attr('src') or img.attr('data-src')
                        if src and self._is_valid_image_url(src):
                            images.append(self._clean_image_url(src))
                    if images:
                        break

        except Exception as e:
            print(f"获取产品图片失败: {e}")

        # 去重
        return list(dict.fromkeys(images))

    def _is_valid_image_url(self, url: str) -> bool:
        """检查是否是有效的图片URL"""
        if not url:
            return False
        # 排除占位图和图标
        excluded = ['placeholder', 'loading', 'icon', 'logo', 'avatar', 'base64']
        url_lower = url.lower()
        return not any(ex in url_lower for ex in excluded)

    def _clean_image_url(self, url: str) -> str:
        """清理图片URL，获取高清版本"""
        # 移除尺寸参数，获取原图
        url = re.sub(r'[?&](w|h|width|height|size)=\d+', '', url)
        url = re.sub(r'@\d+[wh]_\d+[wh]', '', url)  # 移除 @100w_100h 这样的参数
        # 确保是 https
        if url.startswith('//'):
            url = 'https:' + url
        return url

    def _get_video_url(self) -> str:
        """获取产品视频URL

        对应 baiying.js 中的 downMainVideo()
        """
        try:
            # 查找视频元素
            video_selectors = [
                'video source',
                'video',
                '[class*="video"] video',
                '[class*="Video"] video',
            ]

            for selector in video_selectors:
                video = self.page.ele(selector, timeout=1)
                if video:
                    src = video.attr('src')
                    if src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        return src

            # 尝试从 data 属性获取
            video_containers = self.page.eles('[data-video-url]', timeout=1)
            for container in video_containers:
                src = container.attr('data-video-url')
                if src:
                    if src.startswith('//'):
                        src = 'https:' + src
                    return src

        except Exception as e:
            print(f"获取视频URL失败: {e}")

        return ""

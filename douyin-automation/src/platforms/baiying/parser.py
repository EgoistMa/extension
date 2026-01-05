"""百应产品页面解析器

参考 baiying.js 中的 getProductInfo() 和 getBaiyingImageUrls() 实现

百应页面关键选择器 (来自 baiying.js):
- 产品标题: .index_module__title____450e
- 数据容器: .index_module__dataCardContainer____0bd5
- 数据项: .index_module__dataItem____0bd5
- 数据标题: .index_module__dataTitle____0bd5
- 数据内容: .index_module__dataContent____0bd5
- 评分容器: .index_module__scoreContainer____1d3f
- 图片轮播: div.slick-track
- 主内容区: div.index_module__mainContent___ac928
"""

import re
from typing import List, Optional, Tuple, Dict, Any
from DrissionPage import ChromiumPage

from models.product import Product


class ProductParser:
    """百应产品页面解析器"""

    # 百应页面选择器 (从 baiying.js 提取)
    SELECTORS = {
        # 产品基础信息
        'title': '.index_module__title____450e',
        'title_container': '.index_module__titleContainer____450e',
        'copy_id': '.index_module__copyId____0e09',

        # 数据卡片
        'data_container': '.index_module__dataCardContainer____0bd5',
        'data_item': '.index_module__dataItem____0bd5',
        'data_title': '.index_module__dataTitle____0bd5',
        'data_content': '.index_module__dataContent____0bd5',

        # 评分
        'score_container': '.index_module__scoreContainer____1d3f',
        'total_score': '.index_module__totalScore____1d3f',
        'big_num': '.index_module__bigNum____1d3f',
        'detail_item': '.index_module__detailItem____1d3f',
        'small_num': '.index_module__smallNum____1d3f',
        'text_line': '.index_module__textLine____1d3f',

        # 图片和视频
        'slick_track': 'div.slick-track',
        'main_content': 'div.index_module__mainContent___ac928',

        # 带货内容
        'card_container': '.index_module__cardContainer____3c42',
        'content_card': '.index_module__contentCard____1821',
    }

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

            # 获取产品标题 (使用百应特定选择器)
            title = self._get_text_content(self.SELECTORS['title'], '')
            if not title:
                # 降级选择器
                title = self._get_text_content('.product-title', '') or \
                        self._get_text_content('[class*="productTitle"]', '') or \
                        self._get_text_content('h1', '')

            # 获取产品URL
            url = self.page.url

            # 解析数据卡片信息
            card_data = self._parse_data_card()

            # 获取价格信息
            price = card_data.get('price', 0.0)

            # 获取佣金信息
            commission = card_data.get('commission', 0.0)
            commission_rate = card_data.get('commission_rate', 0.0)

            # 获取销量信息
            monthly_sales = card_data.get('monthly_sales', 0)
            total_sales = card_data.get('total_sales', 0)

            # 获取评价信息
            rating_percentage = card_data.get('good_ratio', 0.0)

            # 解析店铺评分
            score_data = self._parse_score_container()
            rating = score_data.get('service_score', 0.0)
            shop_score = score_data.get('service_score', 0.0)

            # 获取店铺信息
            shop_name = ""  # 百应页面可能没有直接显示店铺名

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

    def _parse_data_card(self) -> Dict[str, Any]:
        """解析数据卡片信息

        对应 baiying.js 中 getProductInfo() 的数据卡片解析部分

        Returns:
            包含价格、佣金、销量等信息的字典
        """
        result = {
            'price': 0.0,
            'commission': 0.0,
            'commission_rate': 0.0,
            'good_ratio': 0.0,
            'total_sales': 0,
            'monthly_sales': 0,
            'author_num': 0,
        }

        try:
            data_container = self.page.ele(self.SELECTORS['data_container'], timeout=2)
            if not data_container:
                return result

            data_items = data_container.eles(self.SELECTORS['data_item'])

            for item in data_items:
                try:
                    # 获取标题
                    title_ele = item.ele(self.SELECTORS['data_title'], timeout=0.5)
                    if title_ele:
                        title = title_ele.text.strip()
                        content_ele = item.ele(self.SELECTORS['data_content'], timeout=0.5)
                        if not content_ele:
                            continue
                        value = content_ele.text.strip()
                    else:
                        # 备用结构
                        content_ele = item.ele(self.SELECTORS['data_content'], timeout=0.5)
                        if not content_ele:
                            continue
                        spans = content_ele.eles('tag:span')
                        if len(spans) >= 2:
                            title = spans[0].text.strip()
                            value = spans[1].text.strip()
                        else:
                            continue

                    # 解析数据
                    if title == '到手价':
                        # 提取价格 ¥xx.xx
                        match = re.search(r'¥?(\d+(?:\.\d+)?)', value)
                        if match:
                            result['price'] = float(match.group(1))

                    elif title in ['团长高佣', '专属高佣', '佣金']:
                        # 提取佣金比例和金额
                        ratio_match = re.search(r'(\d+(?:\.\d+)?)%', value)
                        fee_match = re.search(r'赚(\d+(?:\.\d+)?)', value)
                        if ratio_match:
                            result['commission_rate'] = float(ratio_match.group(1))
                        if fee_match:
                            result['commission'] = float(fee_match.group(1))

                    elif title == '好评率':
                        # 提取好评率
                        ratio_match = re.search(r'(\d+(?:\.\d+)?)', value.replace('%', ''))
                        if ratio_match:
                            result['good_ratio'] = float(ratio_match.group(1))

                    elif title == '已售':
                        # 处理销量 (可能有"万+"格式)
                        result['total_sales'] = self._parse_sales_number(value)

                    elif title == '带货人数':
                        result['author_num'] = self._parse_sales_number(value)

                except Exception as e:
                    print(f"解析数据项失败: {e}")
                    continue

        except Exception as e:
            print(f"解析数据卡片失败: {e}")

        return result

    def _parse_score_container(self) -> Dict[str, float]:
        """解析评分容器

        对应 baiying.js 中 getProductInfo() 的评分解析部分

        Returns:
            包含各项评分的字典
        """
        result = {
            'service_score': 0.0,
            'goods_score': 0.0,
            'logistics_score': 0.0,
            'exper_score': 0.0,
        }

        try:
            score_container = self.page.ele(self.SELECTORS['score_container'], timeout=2)
            if not score_container:
                return result

            # 获取总体评分
            total_score_ele = score_container.ele(self.SELECTORS['total_score'], timeout=0.5)
            if total_score_ele:
                big_num_ele = total_score_ele.ele(self.SELECTORS['big_num'], timeout=0.5)
                if big_num_ele:
                    score_text = big_num_ele.text.strip()
                    score_match = re.search(r'(\d+(?:\.\d+)?)', score_text)
                    if score_match:
                        result['service_score'] = float(score_match.group(1))

            # 获取详细评分
            detail_items = score_container.eles(self.SELECTORS['detail_item'])
            for detail_item in detail_items:
                try:
                    small_num_ele = detail_item.ele(self.SELECTORS['small_num'], timeout=0.5)
                    text_line_ele = detail_item.ele(self.SELECTORS['text_line'], timeout=0.5)

                    if small_num_ele and text_line_ele:
                        score_text = small_num_ele.text.strip()
                        label = text_line_ele.text.strip()

                        score_match = re.search(r'(\d+(?:\.\d+)?)', score_text)
                        if score_match:
                            score = float(score_match.group(1))

                            if label == '商品':
                                result['goods_score'] = score
                            elif label == '物流':
                                result['logistics_score'] = score
                            elif label == '商家':
                                result['exper_score'] = score
                except Exception:
                    continue

        except Exception as e:
            print(f"解析评分容器失败: {e}")

        return result

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

        逻辑:
        1. 从 div.slick-track 获取所有 img 元素
        2. 检查主内容区是否有视频，如果有则跳过第一张图片（因为那是视频封面）
        3. 返回所有有效的图片URL

        Returns:
            图片URL列表
        """
        images = []

        try:
            # 从 slick-track 获取 (轮播图) - 对应 baiying.js
            slick_track = self.page.ele(self.SELECTORS['slick_track'], timeout=2)
            if slick_track:
                img_elements = slick_track.eles('tag:img')
                print(f"获取到图片标签数: {len(img_elements)}")

                # 检查主内容区是否包含视频 - 对应 baiying.js 逻辑
                has_video = False
                main_content = self.page.ele(self.SELECTORS['main_content'], timeout=1)
                if main_content:
                    video_ele = main_content.ele('tag:video', timeout=0.5)
                    has_video = video_ele is not None

                has_skipped_first = False

                for i, img in enumerate(img_elements):
                    # 如果有视频，跳过第一张图片（视频封面）
                    if has_video and i == 0 and not has_skipped_first:
                        print('跳过第一个图片，因为主内容区域包含视频元素')
                        has_skipped_first = True
                        continue

                    src = img.attr('src')
                    if src:
                        # 确保URL完整
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif not src.startswith('http'):
                            # 相对路径转绝对路径
                            from urllib.parse import urljoin
                            src = urljoin(self.page.url, src)
                        images.append(src)
                    else:
                        print('未获取到img_src属性')
            else:
                print("未获取到slick-track元素")

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

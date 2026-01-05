"""产品数据模型"""

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class Product:
    """百应产品信息

    对应 baiying.js 中 getProductInfo() 获取的数据结构
    """
    # 基础信息
    product_id: str                     # 产品ID
    title: str                          # 产品标题
    url: str                            # 产品URL

    # 价格和佣金
    price: float                        # 到手价
    commission: float                   # 佣金金额
    commission_rate: float = 0.0        # 佣金比例 (%)

    # 销售数据
    monthly_sales: int = 0              # 月销量
    total_sales: int = 0                # 总销量

    # 评价数据
    rating: float = 0.0                 # 评分 (0-5)
    rating_percentage: float = 0.0      # 好评率 (%)

    # 店铺信息
    shop_name: str = ""                 # 店铺名称
    shop_score: float = 0.0             # 店铺评分

    # 素材信息
    main_image: str = ""                # 主图URL
    images: List[str] = field(default_factory=list)  # 产品图片列表
    video_url: str = ""                 # 主视频URL

    # 本地路径
    local_images: List[str] = field(default_factory=list)  # 已下载的图片路径
    local_video: str = ""               # 已下载的视频路径

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = "baiying"             # 来源平台

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Product':
        """从字典创建"""
        # 过滤掉不存在的字段
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    def save(self, path: Path) -> None:
        """保存到JSON文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: Path) -> 'Product':
        """从JSON文件加载"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def meets_criteria(
        self,
        min_rating: float = 0,
        commission_min: float = 0,
        commission_max: float = float('inf'),
        price_min: float = 0,
        price_max: float = float('inf'),
        monthly_sales_min: int = 0,
        commission_type: str = "amount"
    ) -> bool:
        """检查是否满足筛选条件

        Args:
            min_rating: 最低好评率 (%)
            commission_min: 最低佣金
            commission_max: 最高佣金
            price_min: 最低到手价
            price_max: 最高到手价
            monthly_sales_min: 最低月销量
            commission_type: 佣金类型 (amount=金额, ratio=比例)

        Returns:
            是否满足条件
        """
        # 检查好评率
        if self.rating_percentage < min_rating:
            return False

        # 检查佣金
        if commission_type == "amount":
            commission_value = self.commission
        else:
            commission_value = self.commission_rate

        if commission_value < commission_min or commission_value > commission_max:
            return False

        # 检查价格
        if self.price < price_min or self.price > price_max:
            return False

        # 检查月销量
        if self.monthly_sales < monthly_sales_min:
            return False

        return True

    @property
    def has_materials(self) -> bool:
        """是否有素材"""
        return bool(self.images) or bool(self.video_url)

    @property
    def materials_downloaded(self) -> bool:
        """素材是否已下载"""
        return bool(self.local_images) or bool(self.local_video)

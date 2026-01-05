"""豆包API封装

用于生成视频标题、描述、标签等文案
参考 baiying.js 中的 callDoubaoAPI() 实现
"""

import json
import requests
from typing import Optional, Dict, Any, List

from core.config import Config
from models.product import Product


class DoubaoAPI:
    """豆包API封装

    使用火山引擎的豆包大模型生成文案
    """

    DEFAULT_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    DEFAULT_MODEL = "doubao-1-5-pro-32k"

    def __init__(self, config: Optional[Config] = None):
        """初始化API

        Args:
            config: 配置对象
        """
        self.config = config or Config()
        self.api_key = self.config.get('doubao.api_key', '')
        self.model = self.config.get('doubao.model', self.DEFAULT_MODEL)
        self.endpoint = self.config.get('doubao.endpoint', self.DEFAULT_ENDPOINT)

    def _call_api(self, prompt: str, system_prompt: str = "") -> str:
        """调用豆包API

        Args:
            prompt: 用户提示
            system_prompt: 系统提示

        Returns:
            API响应文本
        """
        if not self.api_key:
            raise ValueError("未配置豆包API密钥")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            choices = result.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")

            return ""

        except Exception as e:
            print(f"豆包API调用失败: {e}")
            return ""

    def generate_video_title(
        self,
        product: Product,
        style: str = "吸引眼球"
    ) -> str:
        """生成视频标题

        Args:
            product: 产品信息
            style: 标题风格

        Returns:
            生成的标题
        """
        system_prompt = """你是一个专业的短视频标题创作者。
请根据产品信息生成一个吸引人的视频标题。
要求：
1. 标题长度在15-30字之间
2. 突出产品卖点和价格优势
3. 使用吸引眼球的词汇
4. 不要使用特殊符号
5. 只返回标题本身，不要加任何解释"""

        prompt = f"""请为以下产品生成一个{style}的短视频标题：

产品名称：{product.title}
价格：¥{product.price}
佣金：¥{product.commission}
月销：{product.monthly_sales}
好评率：{product.rating_percentage}%"""

        title = self._call_api(prompt, system_prompt)
        return title.strip()[:50] if title else product.title[:30]

    def generate_video_description(
        self,
        product: Product,
        include_tags: bool = True
    ) -> str:
        """生成视频描述

        Args:
            product: 产品信息
            include_tags: 是否包含标签

        Returns:
            生成的描述
        """
        system_prompt = """你是一个专业的短视频文案创作者。
请根据产品信息生成视频描述。
要求：
1. 描述简洁明了，100-200字
2. 突出产品特点和优惠信息
3. 使用口语化表达
4. 最后可以加上号召行动的话语
5. 只返回描述本身"""

        prompt = f"""请为以下产品生成短视频描述：

产品名称：{product.title}
价格：¥{product.price}
佣金：¥{product.commission}（分享可得）
月销：{product.monthly_sales}
好评率：{product.rating_percentage}%
店铺：{product.shop_name}"""

        description = self._call_api(prompt, system_prompt)

        if description:
            desc = description.strip()[:300]
        else:
            desc = f"{product.title}\n到手价¥{product.price}，超值推荐！"

        return desc

    def generate_video_tags(
        self,
        product: Product,
        count: int = 5
    ) -> List[str]:
        """生成视频标签

        Args:
            product: 产品信息
            count: 标签数量

        Returns:
            标签列表
        """
        system_prompt = f"""你是一个专业的短视频标签创作者。
请根据产品信息生成{count}个相关标签。
要求：
1. 每个标签2-6个字
2. 标签要有搜索热度
3. 包含产品类目相关词
4. 一行一个标签
5. 不要加#符号
6. 只返回标签，不要解释"""

        prompt = f"""请为以下产品生成{count}个视频标签：

产品名称：{product.title}
类目：{product.shop_name}
价格区间：¥{product.price}"""

        result = self._call_api(prompt, system_prompt)

        if result:
            tags = [tag.strip() for tag in result.split('\n') if tag.strip()]
            return tags[:count]

        # 默认标签
        return ["好物推荐", "种草", "平价好物", "必买清单", "分享"][:count]

    def generate_copywriting(
        self,
        product: Product,
        style: str = "口播"
    ) -> str:
        """生成完整文案（口播稿）

        Args:
            product: 产品信息
            style: 文案风格 (口播/种草/测评)

        Returns:
            生成的文案
        """
        system_prompt = f"""你是一个专业的短视频{style}文案创作者。
请根据产品信息生成一段{style}文案。
要求：
1. 文案适合30-60秒的短视频
2. 语言自然流畅，适合朗读
3. 突出产品卖点和优惠
4. 加入互动引导
5. 只返回文案本身"""

        prompt = f"""请为以下产品生成{style}文案：

产品名称：{product.title}
价格：¥{product.price}
佣金：¥{product.commission}
月销：{product.monthly_sales}
好评率：{product.rating_percentage}%
店铺：{product.shop_name}"""

        return self._call_api(prompt, system_prompt)

    def generate_all(self, product: Product) -> Dict[str, Any]:
        """一次生成所有文案

        Args:
            product: 产品信息

        Returns:
            包含标题、描述、标签的字典
        """
        return {
            "title": self.generate_video_title(product),
            "description": self.generate_video_description(product),
            "tags": self.generate_video_tags(product),
        }

    def is_configured(self) -> bool:
        """检查是否已配置API"""
        return bool(self.api_key)

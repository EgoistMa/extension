"""多账户管理模块"""

import json
import shutil
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class AccountConfig:
    """账户配置"""
    account_id: str
    name: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: str = ""
    is_active: bool = True
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'AccountConfig':
        return cls(**data)


class AccountManager:
    """账户管理器

    每个账户拥有独立的浏览器配置目录:
    accounts/
    ├── account_1/
    │   ├── account_config.json
    │   ├── baiying/
    │   │   └── browser_profile/
    │   ├── douyin/
    │   │   └── browser_profile/
    │   └── douyin_creator/
    │       └── browser_profile/
    """

    PLATFORMS = ['baiying', 'douyin', 'douyin_creator']

    def __init__(self, data_dir: Optional[Path] = None):
        """初始化账户管理器

        Args:
            data_dir: 数据目录路径，默认为 data/accounts
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "data" / "accounts"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._accounts: dict[str, AccountConfig] = {}
        self._load_accounts()

    def _load_accounts(self) -> None:
        """加载所有账户"""
        self._accounts.clear()
        for account_dir in self.data_dir.iterdir():
            if account_dir.is_dir():
                config_file = account_dir / "account_config.json"
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            account = AccountConfig.from_dict(data)
                            self._accounts[account.account_id] = account
                    except (json.JSONDecodeError, IOError, TypeError):
                        continue

    def _save_account(self, account: AccountConfig) -> None:
        """保存单个账户配置"""
        account_dir = self.data_dir / account.account_id
        account_dir.mkdir(parents=True, exist_ok=True)
        config_file = account_dir / "account_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(account.to_dict(), f, ensure_ascii=False, indent=2)

    def create_account(self, name: str, account_id: Optional[str] = None) -> AccountConfig:
        """创建新账户

        Args:
            name: 账户名称
            account_id: 账户ID，默认自动生成

        Returns:
            创建的账户配置
        """
        if account_id is None:
            # 生成唯一ID
            existing_ids = set(self._accounts.keys())
            counter = 1
            while f"account_{counter}" in existing_ids:
                counter += 1
            account_id = f"account_{counter}"

        if account_id in self._accounts:
            raise ValueError(f"账户 {account_id} 已存在")

        # 创建账户配置
        account = AccountConfig(account_id=account_id, name=name)

        # 创建目录结构
        account_dir = self.data_dir / account_id
        account_dir.mkdir(parents=True, exist_ok=True)

        for platform in self.PLATFORMS:
            platform_dir = account_dir / platform / "browser_profile"
            platform_dir.mkdir(parents=True, exist_ok=True)

        # 保存配置
        self._save_account(account)
        self._accounts[account_id] = account

        return account

    def get_account(self, account_id: str) -> Optional[AccountConfig]:
        """获取账户配置"""
        return self._accounts.get(account_id)

    def list_accounts(self) -> List[AccountConfig]:
        """列出所有账户"""
        return list(self._accounts.values())

    def update_account(self, account_id: str, **kwargs) -> Optional[AccountConfig]:
        """更新账户信息

        Args:
            account_id: 账户ID
            **kwargs: 要更新的字段

        Returns:
            更新后的账户配置，如果账户不存在返回None
        """
        account = self._accounts.get(account_id)
        if account is None:
            return None

        for key, value in kwargs.items():
            if hasattr(account, key):
                setattr(account, key, value)

        self._save_account(account)
        return account

    def delete_account(self, account_id: str, delete_data: bool = False) -> bool:
        """删除账户

        Args:
            account_id: 账户ID
            delete_data: 是否删除账户数据目录

        Returns:
            是否删除成功
        """
        if account_id not in self._accounts:
            return False

        del self._accounts[account_id]

        if delete_data:
            account_dir = self.data_dir / account_id
            if account_dir.exists():
                shutil.rmtree(account_dir)

        return True

    def get_browser_profile_path(self, account_id: str, platform: str) -> Optional[Path]:
        """获取账户的浏览器配置目录

        Args:
            account_id: 账户ID
            platform: 平台名称 (baiying, douyin, douyin_creator)

        Returns:
            浏览器配置目录路径
        """
        if platform not in self.PLATFORMS:
            raise ValueError(f"不支持的平台: {platform}")

        if account_id not in self._accounts:
            return None

        return self.data_dir / account_id / platform / "browser_profile"

    def mark_account_used(self, account_id: str) -> None:
        """标记账户为最近使用"""
        self.update_account(account_id, last_used=datetime.now().isoformat())

    def get_active_accounts(self) -> List[AccountConfig]:
        """获取所有活动账户"""
        return [acc for acc in self._accounts.values() if acc.is_active]

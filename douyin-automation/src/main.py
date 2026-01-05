#!/usr/bin/env python3
"""
抖音自动化营销工具 - 主入口

实现完整的工作流:
百应选品 → 素材下载 → 抖音视频搜索 → 剪映剪辑 → 导出 → 抖音上传
"""

import sys
import argparse
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.config import Config
from core.account_manager import AccountManager
from workflow.pipeline import Pipeline


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='抖音自动化营销工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 运行完整工作流
  python main.py run --account account_1 --product-url "https://..."

  # 创建新账户
  python main.py account create --name "账户1"

  # 列出所有账户
  python main.py account list

  # 恢复中断的项目
  python main.py resume --project-id "xxx"
'''
    )

    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # run 命令
    run_parser = subparsers.add_parser('run', help='运行工作流')
    run_parser.add_argument('--account', '-a', required=True, help='账户ID')
    run_parser.add_argument('--product-url', '-u', help='产品URL')
    run_parser.add_argument('--output', '-o', help='输出目录')
    run_parser.add_argument('--name', '-n', help='项目名称')

    # account 命令
    account_parser = subparsers.add_parser('account', help='账户管理')
    account_sub = account_parser.add_subparsers(dest='account_cmd')

    # account create
    create_parser = account_sub.add_parser('create', help='创建账户')
    create_parser.add_argument('--name', '-n', required=True, help='账户名称')
    create_parser.add_argument('--id', help='账户ID (可选)')

    # account list
    account_sub.add_parser('list', help='列出账户')

    # account delete
    delete_parser = account_sub.add_parser('delete', help='删除账户')
    delete_parser.add_argument('--id', required=True, help='账户ID')
    delete_parser.add_argument('--data', action='store_true', help='同时删除数据')

    # resume 命令
    resume_parser = subparsers.add_parser('resume', help='恢复项目')
    resume_parser.add_argument('--project-id', '-p', required=True, help='项目ID')

    # config 命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_parser.add_argument('--show', action='store_true', help='显示配置')
    config_parser.add_argument('--set', nargs=2, metavar=('KEY', 'VALUE'), help='设置配置项')

    # gui 命令
    subparsers.add_parser('gui', help='启动图形界面')

    args = parser.parse_args()

    if args.command == 'run':
        cmd_run(args)
    elif args.command == 'account':
        cmd_account(args)
    elif args.command == 'resume':
        cmd_resume(args)
    elif args.command == 'config':
        cmd_config(args)
    elif args.command == 'gui':
        cmd_gui()
    else:
        parser.print_help()


def cmd_run(args):
    """运行工作流"""
    config = Config()
    account_manager = AccountManager()

    # 检查账户是否存在
    account = account_manager.get_account(args.account)
    if not account:
        print(f"错误: 账户 '{args.account}' 不存在")
        print("使用 'python main.py account list' 查看所有账户")
        return 1

    pipeline = Pipeline(account_manager, config)

    # 设置回调
    pipeline.on_log = lambda msg: print(f"[LOG] {msg}")
    pipeline.on_progress = lambda step, cur, total: print(f"[进度] {step}: {cur}/{total}")

    output_dir = Path(args.output) if args.output else None

    project = pipeline.run(
        account_id=args.account,
        product_url=args.product_url,
        project_name=args.name,
        output_dir=output_dir
    )

    if project and project.status == "completed":
        print("\n项目完成!")
        return 0
    else:
        print("\n项目失败")
        return 1


def cmd_account(args):
    """账户管理"""
    account_manager = AccountManager()

    if args.account_cmd == 'create':
        try:
            account = account_manager.create_account(args.name, args.id)
            print(f"账户已创建: {account.account_id}")
            print(f"名称: {account.name}")
        except ValueError as e:
            print(f"错误: {e}")
            return 1

    elif args.account_cmd == 'list':
        accounts = account_manager.list_accounts()
        if not accounts:
            print("没有账户")
            return

        print(f"\n{'ID':<15} {'名称':<20} {'创建时间':<25} {'最后使用':<25}")
        print("-" * 85)
        for acc in accounts:
            last_used = acc.last_used[:19] if acc.last_used else "-"
            created = acc.created_at[:19] if acc.created_at else "-"
            print(f"{acc.account_id:<15} {acc.name:<20} {created:<25} {last_used:<25}")

    elif args.account_cmd == 'delete':
        success = account_manager.delete_account(args.id, delete_data=args.data)
        if success:
            print(f"账户已删除: {args.id}")
        else:
            print(f"账户不存在: {args.id}")
            return 1
    else:
        print("使用 'python main.py account -h' 查看帮助")


def cmd_resume(args):
    """恢复项目"""
    from workflow.checkpoint import Checkpoint

    checkpoint = Checkpoint()
    project = checkpoint.load(args.project_id)

    if not project:
        print(f"未找到项目: {args.project_id}")
        return 1

    print(f"项目: {project.name}")
    print(f"状态: {project.status}")
    print(f"进度: {project.progress}%")

    if project.is_finished:
        print("项目已结束，无需恢复")
        return 0

    config = Config()
    account_manager = AccountManager()
    pipeline = Pipeline(account_manager, config)

    pipeline.on_log = lambda msg: print(f"[LOG] {msg}")

    result = pipeline.resume(args.project_id)

    if result and result.status == "completed":
        print("\n项目完成!")
        return 0
    return 1


def cmd_gui():
    """启动图形界面"""
    from ui import run_app
    return run_app()


def cmd_config(args):
    """配置管理"""
    config = Config()

    if args.show:
        import json
        print(json.dumps(config.all, indent=2, ensure_ascii=False))

    elif args.set:
        key, value = args.set
        # 尝试转换值类型
        try:
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif '.' in value:
                value = float(value)
            else:
                value = int(value)
        except ValueError:
            pass  # 保持字符串

        config.set(key, value)
        config.save()
        print(f"已设置: {key} = {value}")
    else:
        print("使用 --show 显示配置或 --set KEY VALUE 设置配置")


if __name__ == '__main__':
    exit(main() or 0)

"""主窗口"""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QSplitter, QPushButton, QLabel, QLineEdit,
    QComboBox, QTextEdit, QProgressBar, QGroupBox, QFormLayout,
    QFileDialog, QMessageBox, QListWidget, QListWidgetItem,
    QStatusBar, QToolBar, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QFont

from core.config import Config
from core.account_manager import AccountManager
from workflow.pipeline import Pipeline
from models.project import ProjectStatus


class WorkerThread(QThread):
    """工作线程"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(str, int, int)
    status_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, pipeline: Pipeline, account_id: str, product_url: str, project_name: str = None):
        super().__init__()
        self.pipeline = pipeline
        self.account_id = account_id
        self.product_url = product_url
        self.project_name = project_name

    def run(self):
        try:
            # 设置回调
            self.pipeline.on_log = lambda msg: self.log_signal.emit(msg)
            self.pipeline.on_progress = lambda step, cur, total: self.progress_signal.emit(step, cur, total)
            self.pipeline.on_status_change = lambda p: self.status_signal.emit(p.status)

            project = self.pipeline.run(
                account_id=self.account_id,
                product_url=self.product_url,
                project_name=self.project_name
            )

            if project and project.status == ProjectStatus.COMPLETED.value:
                self.finished_signal.emit(True, "项目完成!")
            else:
                error = project.error_message if project else "未知错误"
                self.finished_signal.emit(False, f"项目失败: {error}")

        except Exception as e:
            self.finished_signal.emit(False, f"错误: {str(e)}")


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.account_manager = AccountManager()
        self.pipeline = Pipeline(self.account_manager, self.config)
        self.worker = None

        self.init_ui()
        self.load_accounts()
        self.load_settings()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("抖音自动化营销工具")
        self.setMinimumSize(1000, 700)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧面板 (控制区)
        left_panel = self.create_left_panel()
        left_panel.setMaximumWidth(350)

        # 右侧面板 (日志区)
        right_panel = self.create_right_panel()

        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 650])

        main_layout.addWidget(splitter)

        # 创建菜单栏
        self.create_menu_bar()

        # 创建状态栏
        self.statusBar().showMessage("就绪")

    def create_left_panel(self) -> QWidget:
        """创建左侧控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 账户选择
        account_group = QGroupBox("账户管理")
        account_layout = QVBoxLayout(account_group)

        account_row = QHBoxLayout()
        account_row.addWidget(QLabel("选择账户:"))
        self.account_combo = QComboBox()
        self.account_combo.setMinimumWidth(150)
        account_row.addWidget(self.account_combo)

        btn_add_account = QPushButton("添加")
        btn_add_account.clicked.connect(self.add_account)
        account_row.addWidget(btn_add_account)

        account_layout.addLayout(account_row)

        # 账户登录按钮
        login_row = QHBoxLayout()
        btn_login_baiying = QPushButton("登录百应")
        btn_login_baiying.clicked.connect(lambda: self.login_platform('baiying'))
        btn_login_douyin = QPushButton("登录抖音")
        btn_login_douyin.clicked.connect(lambda: self.login_platform('douyin'))
        btn_login_creator = QPushButton("登录创作者")
        btn_login_creator.clicked.connect(lambda: self.login_platform('douyin_creator'))
        login_row.addWidget(btn_login_baiying)
        login_row.addWidget(btn_login_douyin)
        login_row.addWidget(btn_login_creator)
        account_layout.addLayout(login_row)

        layout.addWidget(account_group)

        # 任务设置
        task_group = QGroupBox("任务设置")
        task_layout = QFormLayout(task_group)

        self.product_url_input = QLineEdit()
        self.product_url_input.setPlaceholderText("输入百应产品URL...")
        task_layout.addRow("产品URL:", self.product_url_input)

        self.project_name_input = QLineEdit()
        self.project_name_input.setPlaceholderText("可选，留空自动生成")
        task_layout.addRow("项目名称:", self.project_name_input)

        layout.addWidget(task_group)

        # 筛选设置
        filter_group = QGroupBox("视频筛选")
        filter_layout = QFormLayout(filter_group)

        self.min_duration_input = QLineEdit()
        self.min_duration_input.setText(str(self.config.get('douyin_video.min_duration', 45)))
        filter_layout.addRow("最短时长(秒):", self.min_duration_input)

        self.max_duration_input = QLineEdit()
        self.max_duration_input.setText(str(self.config.get('douyin_video.max_duration', 80)))
        filter_layout.addRow("最长时长(秒):", self.max_duration_input)

        self.min_likes_input = QLineEdit()
        self.min_likes_input.setText(str(self.config.get('douyin_video.min_likes', 1000)))
        filter_layout.addRow("最低点赞:", self.min_likes_input)

        self.download_count_input = QLineEdit()
        self.download_count_input.setText(str(self.config.get('douyin_video.download_count', 5)))
        filter_layout.addRow("下载数量:", self.download_count_input)

        layout.addWidget(filter_group)

        # 进度显示
        progress_group = QGroupBox("任务进度")
        progress_layout = QVBoxLayout(progress_group)

        self.status_label = QLabel("状态: 等待开始")
        progress_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.step_label = QLabel("步骤: -")
        progress_layout.addWidget(self.step_label)

        layout.addWidget(progress_group)

        # 操作按钮
        btn_layout = QHBoxLayout()

        self.btn_start = QPushButton("开始任务")
        self.btn_start.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")
        self.btn_start.clicked.connect(self.start_task)
        btn_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton("停止")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_task)
        btn_layout.addWidget(self.btn_stop)

        layout.addLayout(btn_layout)

        # 设置按钮
        btn_settings = QPushButton("设置")
        btn_settings.clicked.connect(self.open_settings)
        layout.addWidget(btn_settings)

        layout.addStretch()

        return panel

    def create_right_panel(self) -> QWidget:
        """创建右侧日志面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # 日志标签
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("运行日志"))
        btn_clear = QPushButton("清空")
        btn_clear.clicked.connect(self.clear_log)
        log_header.addWidget(btn_clear)
        log_header.addStretch()
        layout.addLayout(log_header)

        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setStyleSheet("QTextEdit { background-color: #1e1e1e; color: #d4d4d4; }")
        layout.addWidget(self.log_text)

        return panel

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        action_settings = QAction("设置", self)
        action_settings.triggered.connect(self.open_settings)
        file_menu.addAction(action_settings)

        file_menu.addSeparator()

        action_exit = QAction("退出", self)
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)

        # 账户菜单
        account_menu = menubar.addMenu("账户")

        action_add = QAction("添加账户", self)
        action_add.triggered.connect(self.add_account)
        account_menu.addAction(action_add)

        action_delete = QAction("删除账户", self)
        action_delete.triggered.connect(self.delete_account)
        account_menu.addAction(action_delete)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        action_about = QAction("关于", self)
        action_about.triggered.connect(self.show_about)
        help_menu.addAction(action_about)

    def load_accounts(self):
        """加载账户列表"""
        self.account_combo.clear()
        accounts = self.account_manager.list_accounts()
        for acc in accounts:
            self.account_combo.addItem(f"{acc.name} ({acc.account_id})", acc.account_id)

        if not accounts:
            self.account_combo.addItem("无账户 - 请先添加", None)

    def load_settings(self):
        """加载设置"""
        self.min_duration_input.setText(str(self.config.get('douyin_video.min_duration', 45)))
        self.max_duration_input.setText(str(self.config.get('douyin_video.max_duration', 80)))
        self.min_likes_input.setText(str(self.config.get('douyin_video.min_likes', 1000)))
        self.download_count_input.setText(str(self.config.get('douyin_video.download_count', 5)))

    def save_filter_settings(self):
        """保存筛选设置"""
        try:
            self.config.set('douyin_video.min_duration', float(self.min_duration_input.text()))
            self.config.set('douyin_video.max_duration', float(self.max_duration_input.text()))
            self.config.set('douyin_video.min_likes', int(self.min_likes_input.text()))
            self.config.set('douyin_video.download_count', int(self.download_count_input.text()))
            self.config.save()
        except ValueError:
            pass

    def add_account(self):
        """添加账户"""
        from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "添加账户", "请输入账户名称:")
        if ok and name:
            try:
                account = self.account_manager.create_account(name)
                self.load_accounts()
                # 选择新创建的账户
                index = self.account_combo.findData(account.account_id)
                if index >= 0:
                    self.account_combo.setCurrentIndex(index)
                self.log(f"账户已创建: {account.account_id}")
                QMessageBox.information(self, "成功", f"账户 '{name}' 创建成功!")
            except Exception as e:
                QMessageBox.warning(self, "错误", f"创建账户失败: {e}")

    def delete_account(self):
        """删除账户"""
        account_id = self.account_combo.currentData()
        if not account_id:
            QMessageBox.warning(self, "警告", "请先选择一个账户")
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除账户 '{account_id}' 吗?\n这将删除所有相关数据!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.account_manager.delete_account(account_id, delete_data=True)
            self.load_accounts()
            self.log(f"账户已删除: {account_id}")

    def login_platform(self, platform: str):
        """打开浏览器登录平台"""
        account_id = self.account_combo.currentData()
        if not account_id:
            QMessageBox.warning(self, "警告", "请先选择一个账户")
            return

        from core.browser_manager import BrowserManager
        browser_manager = BrowserManager(self.account_manager)

        platform_names = {
            'baiying': '百应',
            'douyin': '抖音',
            'douyin_creator': '抖音创作者中心'
        }

        self.log(f"正在打开 {platform_names[platform]} 登录页面...")
        self.statusBar().showMessage(f"请在浏览器中登录 {platform_names[platform]}...")

        try:
            browser_manager.navigate_to_platform(account_id, platform)
            QMessageBox.information(
                self, "提示",
                f"浏览器已打开，请在浏览器中登录 {platform_names[platform]}。\n"
                "登录完成后，Cookie 将自动保存。"
            )
        except Exception as e:
            QMessageBox.warning(self, "错误", f"打开浏览器失败: {e}")

    def start_task(self):
        """开始任务"""
        account_id = self.account_combo.currentData()
        if not account_id:
            QMessageBox.warning(self, "警告", "请先选择一个账户")
            return

        product_url = self.product_url_input.text().strip()
        if not product_url:
            QMessageBox.warning(self, "警告", "请输入产品URL")
            return

        # 保存筛选设置
        self.save_filter_settings()

        project_name = self.project_name_input.text().strip() or None

        # 禁用开始按钮
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("状态: 正在启动...")

        self.log("=" * 50)
        self.log("开始新任务")
        self.log(f"账户: {account_id}")
        self.log(f"产品URL: {product_url}")
        self.log("=" * 50)

        # 创建新的 Pipeline 实例
        self.pipeline = Pipeline(self.account_manager, self.config)

        # 创建工作线程
        self.worker = WorkerThread(self.pipeline, account_id, product_url, project_name)
        self.worker.log_signal.connect(self.log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.status_signal.connect(self.update_status)
        self.worker.finished_signal.connect(self.task_finished)
        self.worker.start()

    def stop_task(self):
        """停止任务"""
        if self.pipeline:
            self.pipeline.stop()
        self.log("正在停止任务...")
        self.statusBar().showMessage("正在停止...")

    def task_finished(self, success: bool, message: str):
        """任务完成回调"""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

        if success:
            self.progress_bar.setValue(100)
            self.status_label.setText("状态: 完成")
            self.log(f"✓ {message}")
            QMessageBox.information(self, "完成", message)
        else:
            self.status_label.setText("状态: 失败")
            self.log(f"✗ {message}")
            QMessageBox.warning(self, "失败", message)

        self.statusBar().showMessage("就绪")

    def update_progress(self, step: str, current: int, total: int):
        """更新进度"""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress_bar.setValue(percent)
        self.step_label.setText(f"步骤: {step} ({current}/{total})")

    def update_status(self, status: str):
        """更新状态"""
        status_names = {
            'pending': '等待',
            'product_searching': '搜索产品',
            'product_found': '产品已找到',
            'material_downloading': '下载素材',
            'material_downloaded': '素材已下载',
            'video_searching': '搜索视频',
            'video_filtered': '视频已筛选',
            'video_downloading': '下载视频',
            'video_downloaded': '视频已下载',
            'jianying_generating': '生成剪映项目',
            'jianying_generated': '剪映项目已生成',
            'exporting': '导出视频',
            'exported': '视频已导出',
            'uploading': '上传视频',
            'published': '已发布',
            'completed': '完成',
            'failed': '失败',
        }
        status_text = status_names.get(status, status)
        self.status_label.setText(f"状态: {status_text}")
        self.statusBar().showMessage(f"当前: {status_text}")

    def log(self, message: str):
        """添加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        # 滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_log(self):
        """清空日志"""
        self.log_text.clear()

    def open_settings(self):
        """打开设置对话框"""
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            self.load_settings()
            self.log("设置已更新")

    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self, "关于",
            "抖音自动化营销工具 v1.0\n\n"
            "功能:\n"
            "• 百应选品\n"
            "• 抖音视频搜索下载\n"
            "• 剪映自动剪辑导出\n"
            "• 抖音自动上传发布\n\n"
            "多账户支持 | 断点恢复 | AI文案生成"
        )

    def closeEvent(self, event):
        """关闭事件"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "确认退出",
                "任务正在运行中，确定要退出吗?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

            self.pipeline.stop()
            self.worker.wait(3000)

        event.accept()


def run_app():
    """运行应用"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    run_app()

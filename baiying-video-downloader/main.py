#!/usr/bin/env python3
"""
百应视频素材下载器
接收选品数据，异步下载抖音视频素材
"""

import sys
import os
import json
import asyncio
import threading
import queue
from datetime import datetime
from pathlib import Path

# GUI
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QSpinBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QTextEdit, QGroupBox, QFormLayout, QTabWidget, QFileDialog,
    QMessageBox, QSplitter, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

# HTTP Server
from flask import Flask, request, jsonify
from flask_cors import CORS

# 添加父目录到路径以导入downloader
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from douyin_downloader.douyin_search_downloader import DouyinSearchDownloader, VideoInfo
except ImportError:
    # 如果导入失败，定义一个简单的类
    class VideoInfo:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    DouyinSearchDownloader = None


class ProductData:
    """产品数据"""
    def __init__(self, data: dict):
        self.name = data.get('name', '')
        self.commission_rate = data.get('commission_rate', '')
        self.commission_amount = data.get('commission_amount', '')
        self.price = data.get('price', '')
        self.monthly_sales = data.get('monthly_sales', '')
        self.shop_score = data.get('shop_score', '')
        self.total_score = data.get('totalScore', 0)
        self.status = 'pending'  # pending, downloading, completed, failed
        self.videos_downloaded = 0


class DownloadWorker(QThread):
    """下载工作线程"""
    progress = pyqtSignal(str, str, int)  # product_name, status, video_count
    log = pyqtSignal(str)
    finished_product = pyqtSignal(str)

    def __init__(self, product: ProductData, settings: dict):
        super().__init__()
        self.product = product
        self.settings = settings
        self.is_running = True

    def run(self):
        """执行下载任务"""
        product_name = self.product.name
        self.progress.emit(product_name, 'downloading', 0)
        self.log.emit(f"[开始] 搜索产品: {product_name}")

        try:
            if DouyinSearchDownloader is None:
                self.log.emit(f"[错误] 未找到 DouyinSearchDownloader 模块")
                self.progress.emit(product_name, 'failed', 0)
                return

            # 创建下载器
            downloader = DouyinSearchDownloader(
                headless=self.settings.get('headless', True),
                debug=self.settings.get('debug', False)
            )

            # 构建搜索URL
            search_keyword = product_name[:20]  # 取前20个字符作为搜索关键词
            search_url = f"https://www.douyin.com/search/{search_keyword}?type=video"

            self.log.emit(f"[搜索] URL: {search_url}")

            # 搜索视频
            videos = downloader.search_videos(
                search_url,
                scroll_times=self.settings.get('scroll_times', 3)
            )

            self.log.emit(f"[结果] 找到 {len(videos)} 个视频")

            if not videos:
                self.progress.emit(product_name, 'failed', 0)
                self.log.emit(f"[失败] 未找到相关视频")
                downloader.close()
                return

            # 筛选视频
            min_likes = self.settings.get('min_likes', 0)
            if min_likes > 0:
                videos = [v for v in videos if v.digg_count >= min_likes]
                self.log.emit(f"[筛选] 点赞数 >= {min_likes}: {len(videos)} 个视频")

            filtered = downloader.filter_videos(
                videos,
                min_duration=self.settings.get('min_duration', 15),
                max_duration=self.settings.get('max_duration', 60),
                top_n=self.settings.get('download_count', 3),
                sort_by=self.settings.get('sort_by', 'digg_time')
            )

            self.log.emit(f"[筛选] 筛选后 {len(filtered)} 个视频")

            if not filtered:
                self.progress.emit(product_name, 'failed', 0)
                self.log.emit(f"[失败] 没有符合条件的视频")
                downloader.close()
                return

            # 创建输出目录
            output_dir = Path(self.settings.get('output_dir', './downloads'))
            product_dir = output_dir / self._safe_filename(product_name[:30])
            product_dir.mkdir(parents=True, exist_ok=True)

            # 下载视频
            downloaded = 0
            for i, video in enumerate(filtered):
                if not self.is_running:
                    break

                self.log.emit(f"[下载] ({i+1}/{len(filtered)}) 视频ID: {video.aweme_id}")

                # 获取视频URL
                video_url = video.video_url
                if not video_url or 'douyin' not in video_url:
                    video_url = downloader.get_video_url(video.aweme_id)

                if video_url:
                    filename = f"{video.aweme_id}_{video.duration:.0f}s_{video.digg_count}.mp4"
                    filepath = product_dir / filename

                    if downloader.download_video(video_url, str(filepath)):
                        downloaded += 1
                        self.progress.emit(product_name, 'downloading', downloaded)
                        self.log.emit(f"[成功] 已下载: {filename}")
                    else:
                        self.log.emit(f"[失败] 下载失败: {video.aweme_id}")
                else:
                    self.log.emit(f"[失败] 无法获取视频URL: {video.aweme_id}")

            downloader.close()

            if downloaded > 0:
                self.progress.emit(product_name, 'completed', downloaded)
                self.log.emit(f"[完成] {product_name}: 成功下载 {downloaded} 个视频")
            else:
                self.progress.emit(product_name, 'failed', 0)
                self.log.emit(f"[失败] {product_name}: 没有成功下载任何视频")

        except Exception as e:
            self.log.emit(f"[错误] {product_name}: {str(e)}")
            self.progress.emit(product_name, 'failed', 0)

        self.finished_product.emit(product_name)

    def _safe_filename(self, name: str) -> str:
        """生成安全的文件名"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()

    def stop(self):
        self.is_running = False


class ServerThread(QThread):
    """HTTP服务器线程"""
    product_received = pyqtSignal(dict)
    log = pyqtSignal(str)

    def __init__(self, port: int = 5000):
        super().__init__()
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)
        self._setup_routes()

    def _setup_routes(self):
        @self.app.route('/api/products', methods=['POST'])
        def receive_products():
            try:
                data = request.json
                self.log.emit(f"[服务器] 收到请求: {data.get('product_count', 0)} 个产品")
                self.product_received.emit(data)
                return jsonify({'success': True, 'message': '已接收产品列表'})
            except Exception as e:
                self.log.emit(f"[服务器错误] {str(e)}")
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            return jsonify({'status': 'running', 'port': self.port})

    def run(self):
        self.log.emit(f"[服务器] 启动在端口 {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, threaded=True, use_reloader=False)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("百应视频素材下载器 v1.0")
        self.setMinimumSize(1000, 700)

        self.products = {}  # name -> ProductData
        self.download_queue = queue.Queue()
        self.current_worker = None
        self.server_thread = None

        self._init_ui()
        self._start_server()

    def _init_ui(self):
        """初始化UI"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 创建标签页
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # 产品列表标签页
        products_tab = self._create_products_tab()
        tabs.addTab(products_tab, "📦 产品列表")

        # 设置标签页
        settings_tab = self._create_settings_tab()
        tabs.addTab(settings_tab, "⚙️ 下载设置")

        # 日志标签页
        log_tab = self._create_log_tab()
        tabs.addTab(log_tab, "📝 运行日志")

        # 底部状态栏
        self._create_status_bar()

    def _create_products_tab(self) -> QWidget:
        """创建产品列表标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 顶部工具栏
        toolbar = QHBoxLayout()

        self.server_status = QLabel("🔴 服务器未启动")
        toolbar.addWidget(self.server_status)

        toolbar.addStretch()

        self.start_all_btn = QPushButton("▶️ 开始全部下载")
        self.start_all_btn.clicked.connect(self._start_all_downloads)
        toolbar.addWidget(self.start_all_btn)

        self.stop_btn = QPushButton("⏹️ 停止")
        self.stop_btn.clicked.connect(self._stop_downloads)
        self.stop_btn.setEnabled(False)
        toolbar.addWidget(self.stop_btn)

        clear_btn = QPushButton("🗑️ 清空列表")
        clear_btn.clicked.connect(self._clear_products)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        # 产品表格
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(8)
        self.product_table.setHorizontalHeaderLabels([
            "产品名称", "佣金比例", "佣金赚", "价格", "月销", "评分", "综合得分", "状态"
        ])

        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 8):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.product_table)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        return widget

    def _create_settings_tab(self) -> QWidget:
        """创建设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 服务器设置
        server_group = QGroupBox("🌐 服务器设置")
        server_layout = QFormLayout(server_group)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1000, 65535)
        self.port_spin.setValue(5000)
        server_layout.addRow("监听端口:", self.port_spin)

        self.auto_download_check = QCheckBox("收到产品后自动开始下载")
        self.auto_download_check.setChecked(True)
        server_layout.addRow(self.auto_download_check)

        layout.addWidget(server_group)

        # 视频筛选设置
        filter_group = QGroupBox("🎬 视频筛选条件")
        filter_layout = QFormLayout(filter_group)

        self.min_duration_spin = QDoubleSpinBox()
        self.min_duration_spin.setRange(0, 600)
        self.min_duration_spin.setValue(15)
        self.min_duration_spin.setSuffix(" 秒")
        filter_layout.addRow("最小视频时长:", self.min_duration_spin)

        self.max_duration_spin = QDoubleSpinBox()
        self.max_duration_spin.setRange(0, 600)
        self.max_duration_spin.setValue(60)
        self.max_duration_spin.setSuffix(" 秒")
        filter_layout.addRow("最大视频时长:", self.max_duration_spin)

        self.min_likes_spin = QSpinBox()
        self.min_likes_spin.setRange(0, 10000000)
        self.min_likes_spin.setValue(1000)
        self.min_likes_spin.setSingleStep(100)
        filter_layout.addRow("最小点赞数:", self.min_likes_spin)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["点赞+最新 (digg_time)", "点赞最高 (digg)", "最新发布 (time)"])
        filter_layout.addRow("排序方式:", self.sort_combo)

        layout.addWidget(filter_group)

        # 下载设置
        download_group = QGroupBox("📥 下载设置")
        download_layout = QFormLayout(download_group)

        self.download_count_spin = QSpinBox()
        self.download_count_spin.setRange(1, 20)
        self.download_count_spin.setValue(3)
        download_layout.addRow("每产品下载视频数:", self.download_count_spin)

        self.scroll_times_spin = QSpinBox()
        self.scroll_times_spin.setRange(1, 20)
        self.scroll_times_spin.setValue(5)
        download_layout.addRow("页面滚动次数:", self.scroll_times_spin)

        output_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(str(Path.home() / "Downloads" / "baiying_videos"))
        output_layout.addWidget(self.output_dir_edit)

        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(browse_btn)

        download_layout.addRow("保存目录:", output_layout)

        self.headless_check = QCheckBox("无头模式（不显示浏览器窗口）")
        self.headless_check.setChecked(True)
        download_layout.addRow(self.headless_check)

        self.debug_check = QCheckBox("调试模式")
        download_layout.addRow(self.debug_check)

        layout.addWidget(download_group)

        # 保存按钮
        save_btn = QPushButton("💾 保存设置")
        save_btn.clicked.connect(self._save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()

        return widget

    def _create_log_tab(self) -> QWidget:
        """创建日志标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_text)

        clear_log_btn = QPushButton("清空日志")
        clear_log_btn.clicked.connect(lambda: self.log_text.clear())
        layout.addWidget(clear_log_btn)

        return widget

    def _create_status_bar(self):
        """创建状态栏"""
        self.statusBar().showMessage("就绪")

    def _start_server(self):
        """启动HTTP服务器"""
        port = self.port_spin.value()
        self.server_thread = ServerThread(port)
        self.server_thread.product_received.connect(self._on_products_received)
        self.server_thread.log.connect(self._log)
        self.server_thread.start()

        self.server_status.setText(f"🟢 服务器运行中 (端口: {port})")
        self._log(f"服务器已启动，监听端口: {port}")

    def _on_products_received(self, data: dict):
        """收到产品数据"""
        products = data.get('products', [])
        source = data.get('source', 'unknown')
        timestamp = data.get('timestamp', '')

        self._log(f"收到 {len(products)} 个产品 (来源: {source})")

        # 添加到表格
        for p_data in products:
            product = ProductData(p_data)
            if product.name not in self.products:
                self.products[product.name] = product
                self._add_product_to_table(product)

        # 自动开始下载
        if self.auto_download_check.isChecked() and products:
            self._start_all_downloads()

    def _add_product_to_table(self, product: ProductData):
        """添加产品到表格"""
        row = self.product_table.rowCount()
        self.product_table.insertRow(row)

        self.product_table.setItem(row, 0, QTableWidgetItem(product.name))
        self.product_table.setItem(row, 1, QTableWidgetItem(product.commission_rate))
        self.product_table.setItem(row, 2, QTableWidgetItem(product.commission_amount))
        self.product_table.setItem(row, 3, QTableWidgetItem(product.price))
        self.product_table.setItem(row, 4, QTableWidgetItem(product.monthly_sales))
        self.product_table.setItem(row, 5, QTableWidgetItem(product.shop_score))
        self.product_table.setItem(row, 6, QTableWidgetItem(f"{product.total_score:.1f}"))
        self.product_table.setItem(row, 7, QTableWidgetItem("⏳ 等待中"))

    def _get_settings(self) -> dict:
        """获取当前设置"""
        sort_map = {
            0: 'digg_time',
            1: 'digg',
            2: 'time'
        }
        return {
            'min_duration': self.min_duration_spin.value(),
            'max_duration': self.max_duration_spin.value(),
            'min_likes': self.min_likes_spin.value(),
            'sort_by': sort_map.get(self.sort_combo.currentIndex(), 'digg_time'),
            'download_count': self.download_count_spin.value(),
            'scroll_times': self.scroll_times_spin.value(),
            'output_dir': self.output_dir_edit.text(),
            'headless': self.headless_check.isChecked(),
            'debug': self.debug_check.isChecked()
        }

    def _start_all_downloads(self):
        """开始下载所有产品"""
        pending_products = [p for p in self.products.values() if p.status == 'pending']

        if not pending_products:
            self._log("没有待下载的产品")
            return

        self._log(f"开始下载 {len(pending_products)} 个产品的视频...")

        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(pending_products))
        self.progress_bar.setValue(0)

        self.start_all_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        # 将产品加入队列
        for product in pending_products:
            self.download_queue.put(product)

        # 开始处理队列
        self._process_next_download()

    def _process_next_download(self):
        """处理下一个下载任务"""
        if self.download_queue.empty():
            self._log("所有下载任务完成")
            self.start_all_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.progress_bar.setVisible(False)
            return

        product = self.download_queue.get()
        settings = self._get_settings()

        self.current_worker = DownloadWorker(product, settings)
        self.current_worker.progress.connect(self._on_download_progress)
        self.current_worker.log.connect(self._log)
        self.current_worker.finished_product.connect(self._on_product_finished)
        self.current_worker.start()

    def _on_download_progress(self, product_name: str, status: str, video_count: int):
        """下载进度更新"""
        # 更新表格状态
        for row in range(self.product_table.rowCount()):
            if self.product_table.item(row, 0).text() == product_name:
                status_map = {
                    'downloading': f"⬇️ 下载中 ({video_count})",
                    'completed': f"✅ 完成 ({video_count})",
                    'failed': "❌ 失败"
                }
                self.product_table.setItem(row, 7, QTableWidgetItem(status_map.get(status, status)))
                break

        # 更新产品状态
        if product_name in self.products:
            self.products[product_name].status = status
            self.products[product_name].videos_downloaded = video_count

    def _on_product_finished(self, product_name: str):
        """产品下载完成"""
        completed = sum(1 for p in self.products.values() if p.status in ['completed', 'failed'])
        self.progress_bar.setValue(completed)

        # 处理下一个
        self._process_next_download()

    def _stop_downloads(self):
        """停止下载"""
        self._log("正在停止下载...")

        # 清空队列
        while not self.download_queue.empty():
            try:
                self.download_queue.get_nowait()
            except:
                break

        # 停止当前工作线程
        if self.current_worker:
            self.current_worker.stop()

        self.start_all_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

    def _clear_products(self):
        """清空产品列表"""
        self.products.clear()
        self.product_table.setRowCount(0)
        self._log("已清空产品列表")

    def _browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if dir_path:
            self.output_dir_edit.setText(dir_path)

    def _save_settings(self):
        """保存设置"""
        settings = self._get_settings()
        self._log(f"设置已保存: {json.dumps(settings, ensure_ascii=False)}")
        QMessageBox.information(self, "提示", "设置已保存")

    def _log(self, message: str):
        """写入日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        self.statusBar().showMessage(message)

    def closeEvent(self, event):
        """关闭事件"""
        if self.current_worker:
            self.current_worker.stop()
            self.current_worker.wait()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()

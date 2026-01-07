"""设置对话框"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QFormLayout, QLineEdit, QPushButton, QLabel, QGroupBox,
    QFileDialog, QSpinBox, QDoubleSpinBox, QCheckBox,
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt

from core.config import Config


class SettingsDialog(QDialog):
    """设置对话框"""

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.config = config
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("设置")
        self.setMinimumSize(500, 450)

        layout = QVBoxLayout(self)

        # 标签页
        tab_widget = QTabWidget()

        # 筛选设置
        tab_widget.addTab(self.create_filter_tab(), "筛选条件")

        # 剪映设置
        tab_widget.addTab(self.create_jianying_tab(), "剪映设置")

        # 豆包API设置
        tab_widget.addTab(self.create_doubao_tab(), "AI设置")

        # 其他设置
        tab_widget.addTab(self.create_other_tab(), "其他")

        layout.addWidget(tab_widget)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.save_and_close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def create_filter_tab(self) -> QWidget:
        """创建筛选设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 选品设置
        picking_group = QGroupBox("选品设置")
        picking_layout = QFormLayout(picking_group)

        self.product_count = QSpinBox()
        self.product_count.setRange(1, 20)
        self.product_count.setToolTip("自动选品时要处理的产品数量")
        picking_layout.addRow("产品数量 N:", self.product_count)

        layout.addWidget(picking_group)

        # 百应筛选
        baiying_group = QGroupBox("百应产品筛选")
        baiying_layout = QFormLayout(baiying_group)

        self.min_rating = QSpinBox()
        self.min_rating.setRange(0, 100)
        self.min_rating.setSuffix(" %")
        baiying_layout.addRow("最低好评率:", self.min_rating)

        self.commission_min = QDoubleSpinBox()
        self.commission_min.setRange(0, 1000)
        self.commission_min.setPrefix("¥ ")
        baiying_layout.addRow("最低佣金:", self.commission_min)

        self.commission_max = QDoubleSpinBox()
        self.commission_max.setRange(0, 1000)
        self.commission_max.setPrefix("¥ ")
        baiying_layout.addRow("最高佣金:", self.commission_max)

        self.price_min = QDoubleSpinBox()
        self.price_min.setRange(0, 10000)
        self.price_min.setPrefix("¥ ")
        baiying_layout.addRow("最低到手价:", self.price_min)

        self.price_max = QDoubleSpinBox()
        self.price_max.setRange(0, 10000)
        self.price_max.setPrefix("¥ ")
        baiying_layout.addRow("最高到手价:", self.price_max)

        self.monthly_sales_min = QSpinBox()
        self.monthly_sales_min.setRange(0, 10000000)
        baiying_layout.addRow("最低月销:", self.monthly_sales_min)

        layout.addWidget(baiying_group)

        # 抖音视频筛选
        douyin_group = QGroupBox("抖音视频筛选")
        douyin_layout = QFormLayout(douyin_group)

        self.min_duration = QDoubleSpinBox()
        self.min_duration.setRange(0, 600)
        self.min_duration.setSuffix(" 秒")
        douyin_layout.addRow("最短时长:", self.min_duration)

        self.max_duration = QDoubleSpinBox()
        self.max_duration.setRange(0, 600)
        self.max_duration.setSuffix(" 秒")
        douyin_layout.addRow("最长时长:", self.max_duration)

        self.min_likes = QSpinBox()
        self.min_likes.setRange(0, 10000000)
        douyin_layout.addRow("最低点赞:", self.min_likes)

        self.download_count = QSpinBox()
        self.download_count.setRange(1, 50)
        douyin_layout.addRow("下载数量:", self.download_count)

        self.scroll_times = QSpinBox()
        self.scroll_times.setRange(1, 20)
        self.scroll_times.setToolTip("搜索页面滚动次数，滚动越多加载的视频越多")
        douyin_layout.addRow("滚动次数:", self.scroll_times)

        layout.addWidget(douyin_group)
        layout.addStretch()

        return widget

    def create_jianying_tab(self) -> QWidget:
        """创建剪映设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("剪映设置")
        form_layout = QFormLayout(group)

        # 剪映路径
        app_path_row = QHBoxLayout()
        self.jianying_app_path = QLineEdit()
        self.jianying_app_path.setPlaceholderText("JianyingPro.exe 路径")
        app_path_row.addWidget(self.jianying_app_path)
        btn_browse_app = QPushButton("浏览")
        btn_browse_app.clicked.connect(lambda: self.browse_file(self.jianying_app_path, "应用程序 (*.exe)"))
        app_path_row.addWidget(btn_browse_app)
        form_layout.addRow("剪映路径:", app_path_row)

        # 模板目录
        template_row = QHBoxLayout()
        self.jianying_template = QLineEdit()
        self.jianying_template.setPlaceholderText("剪映模板项目目录")
        template_row.addWidget(self.jianying_template)
        btn_browse_template = QPushButton("浏览")
        btn_browse_template.clicked.connect(lambda: self.browse_folder(self.jianying_template))
        template_row.addWidget(btn_browse_template)
        form_layout.addRow("模板目录:", template_row)

        # 草稿目录
        draft_row = QHBoxLayout()
        self.jianying_draft = QLineEdit()
        self.jianying_draft.setPlaceholderText("剪映草稿目录")
        draft_row.addWidget(self.jianying_draft)
        btn_browse_draft = QPushButton("浏览")
        btn_browse_draft.clicked.connect(lambda: self.browse_folder(self.jianying_draft))
        draft_row.addWidget(btn_browse_draft)
        form_layout.addRow("草稿目录:", draft_row)

        # 导出超时
        self.export_timeout = QSpinBox()
        self.export_timeout.setRange(60, 7200)
        self.export_timeout.setSuffix(" 秒")
        form_layout.addRow("导出超时:", self.export_timeout)

        layout.addWidget(group)
        layout.addStretch()

        return widget

    def create_doubao_tab(self) -> QWidget:
        """创建豆包API设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        group = QGroupBox("豆包API设置 (AI文案生成)")
        form_layout = QFormLayout(group)

        self.doubao_api_key = QLineEdit()
        self.doubao_api_key.setPlaceholderText("输入API密钥")
        self.doubao_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("API密钥:", self.doubao_api_key)

        self.doubao_model = QLineEdit()
        self.doubao_model.setPlaceholderText("doubao-1-5-pro-32k")
        form_layout.addRow("模型:", self.doubao_model)

        self.doubao_endpoint = QLineEdit()
        self.doubao_endpoint.setPlaceholderText("API端点URL")
        form_layout.addRow("端点:", self.doubao_endpoint)

        # 测试按钮
        btn_test = QPushButton("测试连接")
        btn_test.clicked.connect(self.test_doubao_api)
        form_layout.addRow("", btn_test)

        layout.addWidget(group)

        # 说明
        info_label = QLabel(
            "豆包API用于自动生成视频标题、描述和标签。\n"
            "如不配置，将使用默认文案。\n\n"
            "获取API密钥: https://www.volcengine.com/product/doubao"
        )
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)

        layout.addStretch()

        return widget

    def create_other_tab(self) -> QWidget:
        """创建其他设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 输出设置
        output_group = QGroupBox("输出设置")
        output_layout = QFormLayout(output_group)

        output_row = QHBoxLayout()
        self.output_dir = QLineEdit()
        self.output_dir.setPlaceholderText("项目输出目录")
        output_row.addWidget(self.output_dir)
        btn_browse_output = QPushButton("浏览")
        btn_browse_output.clicked.connect(lambda: self.browse_folder(self.output_dir))
        output_row.addWidget(btn_browse_output)
        output_layout.addRow("输出目录:", output_row)

        layout.addWidget(output_group)

        # 浏览器设置
        browser_group = QGroupBox("浏览器设置")
        browser_layout = QFormLayout(browser_group)

        self.headless_mode = QCheckBox("无头模式 (不显示浏览器窗口)")
        browser_layout.addRow("", self.headless_mode)

        self.debug_mode = QCheckBox("调试模式 (显示详细日志)")
        browser_layout.addRow("", self.debug_mode)

        layout.addWidget(browser_group)

        # 服务器设置
        server_group = QGroupBox("HTTP服务器")
        server_layout = QFormLayout(server_group)

        self.server_port = QSpinBox()
        self.server_port.setRange(1024, 65535)
        server_layout.addRow("端口:", self.server_port)

        layout.addWidget(server_group)

        layout.addStretch()

        return widget

    def browse_file(self, line_edit: QLineEdit, filter: str = ""):
        """浏览文件"""
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", filter)
        if path:
            line_edit.setText(path)

    def browse_folder(self, line_edit: QLineEdit):
        """浏览文件夹"""
        path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if path:
            line_edit.setText(path)

    def load_settings(self):
        """加载设置"""
        # 选品设置
        self.product_count.setValue(int(self.config.get('picking.product_count', 3)))

        # 筛选设置
        self.min_rating.setValue(int(self.config.get('filter.min_rating', 90)))
        self.commission_min.setValue(float(self.config.get('filter.commission_min', 3.5)))
        self.commission_max.setValue(float(self.config.get('filter.commission_max', 20.0)))
        self.price_min.setValue(float(self.config.get('filter.price_min', 20.0)))
        self.price_max.setValue(float(self.config.get('filter.price_max', 50.0)))
        self.monthly_sales_min.setValue(int(self.config.get('filter.monthly_sales_min', 10000)))

        self.min_duration.setValue(float(self.config.get('douyin_video.min_duration', 45)))
        self.max_duration.setValue(float(self.config.get('douyin_video.max_duration', 80)))
        self.min_likes.setValue(int(self.config.get('douyin_video.min_likes', 1000)))
        self.download_count.setValue(int(self.config.get('douyin_video.download_count', 5)))
        self.scroll_times.setValue(int(self.config.get('douyin_video.scroll_times', 3)))

        # 剪映设置
        self.jianying_app_path.setText(self.config.get('jianying.app_path', ''))
        self.jianying_template.setText(self.config.get('jianying.template_dir', ''))
        self.jianying_draft.setText(self.config.get('jianying.draft_dir', ''))
        self.export_timeout.setValue(int(self.config.get('jianying.export_timeout', 1200)))

        # 豆包设置
        self.doubao_api_key.setText(self.config.get('doubao.api_key', ''))
        self.doubao_model.setText(self.config.get('doubao.model', 'doubao-1-5-pro-32k'))
        self.doubao_endpoint.setText(self.config.get('doubao.endpoint', ''))

        # 其他设置
        self.output_dir.setText(self.config.get('output.base_dir', ''))
        self.headless_mode.setChecked(self.config.get('browser.headless', False))
        self.debug_mode.setChecked(self.config.get('browser.debug', True))
        self.server_port.setValue(int(self.config.get('server.port', 5000)))

    def save_settings(self):
        """保存设置"""
        # 选品设置
        self.config.set('picking.product_count', self.product_count.value())

        # 筛选设置
        self.config.set('filter.min_rating', self.min_rating.value())
        self.config.set('filter.commission_min', self.commission_min.value())
        self.config.set('filter.commission_max', self.commission_max.value())
        self.config.set('filter.price_min', self.price_min.value())
        self.config.set('filter.price_max', self.price_max.value())
        self.config.set('filter.monthly_sales_min', self.monthly_sales_min.value())

        self.config.set('douyin_video.min_duration', self.min_duration.value())
        self.config.set('douyin_video.max_duration', self.max_duration.value())
        self.config.set('douyin_video.min_likes', self.min_likes.value())
        self.config.set('douyin_video.download_count', self.download_count.value())
        self.config.set('douyin_video.scroll_times', self.scroll_times.value())

        # 剪映设置
        self.config.set('jianying.app_path', self.jianying_app_path.text())
        self.config.set('jianying.template_dir', self.jianying_template.text())
        self.config.set('jianying.draft_dir', self.jianying_draft.text())
        self.config.set('jianying.export_timeout', self.export_timeout.value())

        # 豆包设置
        self.config.set('doubao.api_key', self.doubao_api_key.text())
        self.config.set('doubao.model', self.doubao_model.text())
        self.config.set('doubao.endpoint', self.doubao_endpoint.text())

        # 其他设置
        self.config.set('output.base_dir', self.output_dir.text())
        self.config.set('browser.headless', self.headless_mode.isChecked())
        self.config.set('browser.debug', self.debug_mode.isChecked())
        self.config.set('server.port', self.server_port.value())

        self.config.save()

    def save_and_close(self):
        """保存并关闭"""
        self.save_settings()
        self.accept()

    def test_doubao_api(self):
        """测试豆包API"""
        api_key = self.doubao_api_key.text()
        if not api_key:
            QMessageBox.warning(self, "警告", "请先输入API密钥")
            return

        # 临时保存设置
        self.save_settings()

        from ai.doubao import DoubaoAPI
        api = DoubaoAPI(self.config)

        try:
            # 简单测试
            result = api._call_api("你好", "请简单回复")
            if result:
                QMessageBox.information(self, "成功", f"API连接成功!\n\n响应: {result[:100]}...")
            else:
                QMessageBox.warning(self, "失败", "API返回空响应")
        except Exception as e:
            QMessageBox.warning(self, "失败", f"API测试失败: {e}")

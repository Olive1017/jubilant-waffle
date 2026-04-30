import sys
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QMessageBox, QGroupBox, QFileDialog
)
from PySide6.QtGui import QFont
from scraping_handler import ScrapingThread


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("合同管理系统 - 自动化工具")
        self.setMinimumSize(900, 600)
        self.scraping_thread = None
        self.excel_path = None  # 添加Excel路径属性
        self.init_ui()
        self.setup_style()

    def init_ui(self):
        """初始化UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # 左侧日志显示区域
        log_panel = QWidget()
        log_layout = QVBoxLayout()
        log_panel.setLayout(log_layout)

        log_title = QLabel("运行日志")
        log_title.setFont(QFont("Arial", 14, QFont.Bold))
        log_layout.addWidget(log_title)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                color: black;
                font-size: 12px;
                font-family: Consolas, Monaco, monospace;
                border: 1px solid #ddd;
            }
        """)
        log_layout.addWidget(self.log_text)

        # 右侧控制面板
        control_panel = QWidget()
        control_panel.setFixedWidth(250)
        control_layout = QVBoxLayout()
        control_panel.setLayout(control_layout)

        # 控制面板标题
        title_label = QLabel("控制面板")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        control_layout.addWidget(title_label)

        control_layout.addSpacing(20)

        # 状态信息
        status_group = QGroupBox("系统状态")
        status_layout = QVBoxLayout()

        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #52c41a; font-weight: bold;")
        status_layout.addWidget(self.status_label)

        status_group.setLayout(status_layout)
        control_layout.addWidget(status_group)

        control_layout.addSpacing(20)

        # 抓取操作区
        scrape_group = QGroupBox("抓取操作")
        scrape_layout = QVBoxLayout()
        scrape_layout.setSpacing(10)

        self.start_btn = QPushButton("启动")
        self.start_btn.setFixedHeight(40)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #52c41a;
            }
            QPushButton:hover {
                background-color: #73d13d;
            }
            QPushButton:pressed {
                background-color: #389e0d;
            }
        """)
        self.start_btn.clicked.connect(self.start_scraping)
        scrape_layout.addWidget(self.start_btn)

        self.continue_btn = QPushButton("继续")
        self.continue_btn.setFixedHeight(40)
        self.continue_btn.setEnabled(False)
        self.continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
        """)
        self.continue_btn.clicked.connect(self.continue_scraping)
        scrape_layout.addWidget(self.continue_btn)

        scrape_group.setLayout(scrape_layout)
        control_layout.addWidget(scrape_group)

        control_layout.addSpacing(20)

        # 数据管理区
        data_group = QGroupBox("数据管理")
        data_layout = QVBoxLayout()

        self.export_btn = QPushButton("选择保存路径")
        self.export_btn.setFixedHeight(40)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
        """)
        self.export_btn.clicked.connect(self.select_excel_path)
        data_layout.addWidget(self.export_btn)

        data_group.setLayout(data_layout)
        control_layout.addWidget(data_group)

        control_layout.addSpacing(20)

        control_layout.addStretch()

        # 添加退出按钮
        exit_btn = QPushButton("退出")
        exit_btn.setFixedHeight(35)
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4f;
            }
            QPushButton:hover {
                background-color: #ff7875;
            }
            QPushButton:pressed {
                background-color: #cf1322;
            }
        """)
        exit_btn.clicked.connect(self.close)
        control_layout.addWidget(exit_btn)

        # 添加到主布局
        main_layout.addWidget(log_panel)
        main_layout.addWidget(control_panel)

    def setup_style(self):
        """设置样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d9d9d9;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
            QPushButton:disabled {
                background-color: #d9d9d9;
                color: #999;
            }
            QLabel {
                color: #333;
                font-size: 12px;
            }
        """)

    def start_scraping(self):
        """开始抓取"""
        # 检查是否已选择Excel保存路径
        if self.excel_path is None:
            QMessageBox.warning(self, "提示", "请先点击【选择保存路径】按钮创建Excel文件")
            return

        self.log_text.clear()
        self.log_text.append("=" * 60)
        self.log_text.append(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log_text.append("=" * 60)

        self.start_btn.setEnabled(False)
        self.status_label.setText("运行中")
        self.status_label.setStyleSheet("color: #1890ff; font-weight: bold;")

        # 创建并启动抓取线程
        self.scraping_thread = ScrapingThread()
        self.scraping_thread.need_continue.connect(lambda: self.continue_btn.setEnabled(True))
        self.scraping_thread.finished.connect(self.on_scraping_finished)
        self.scraping_thread.start()

    def continue_scraping(self):
        """继续抓取"""
        if self.scraping_thread:
            self.scraping_thread.should_continue = True
            self.continue_btn.setEnabled(False)
            self.showMinimized()

    def on_scraping_finished(self, success, message):
        """抓取完成回调"""
        self.start_btn.setEnabled(True)
        self.continue_btn.setEnabled(False)

        # 保存并关闭Excel文件
        try:
            from data_handler import save_and_close
            save_and_close()
            print("Excel文件已保存并关闭")
        except Exception as e:
            print(f"保存Excel文件时出错: {e}")

        # 重置保存路径按钮
        self.excel_path = None
        self.export_btn.setEnabled(True)
        self.export_btn.setText("选择保存路径")

        if success:
            self.status_label.setText("完成")
            self.status_label.setStyleSheet("color: #52c41a; font-weight: bold;")
            self.append_log("=" * 60)
            self.append_log(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.append_log("=" * 60)
        else:
            self.status_label.setText("出错")
            self.status_label.setStyleSheet("color: #ff4d4f; font-weight: bold;")
            self.append_log(f"错误: {message}")

    def append_log(self, message):
        """追加日志"""
        self.log_text.append(message)
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def closeEvent(self, event):
        """关闭事件"""
        event.accept()

    def select_excel_path(self):
        """选择Excel保存路径并初始化文件"""
        try:
            # 打开文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "选择Excel保存路径",
                "",
                "Excel文件 (*.xlsx);;所有文件 (*)"
            )

            if file_path:
                # 如果用户没有输入扩展名，自动添加.xlsx
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'

                # 初始化Excel文件
                from data_handler import init_excel_file
                init_excel_file(file_path)

                self.excel_path = file_path  # 保存路径
                self.export_btn.setEnabled(False)  # 禁用按钮
                self.export_btn.setText(f"已选择: {Path(file_path).name}")
                QMessageBox.information(self, "成功", f"Excel文件已创建，抓取时将实时写入数据到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"创建文件失败: {str(e)}")


class App(QApplication):
    """应用主类"""

    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName("合同管理系统")

        # 重定向标准输出到UI日志
        sys.stdout = self

        # 直接打开主窗口
        self.main_window = MainWindow()
        self.main_window.show()

    def write(self, text):
        """重写write方法，将输出发送到UI日志"""
        if text.strip():  # 忽略空行
            self.main_window.append_log(text.rstrip())

    def flush(self):
        """必须实现flush方法"""
        pass

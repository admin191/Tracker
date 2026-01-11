import sys
import json
import os
import time
import subprocess
import threading
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTableView, QPushButton, QLabel, QFileDialog, QHeaderView, 
    QGroupBox, QLineEdit, QComboBox, QDateEdit, QGridLayout, 
    QMessageBox, QAction, QMenuBar, QStatusBar
)
from PyQt5.QtCore import (
    Qt, QAbstractTableModel, QDateTime, QDate, QSortFilterProxyModel,
    QUrl, QTimer
)
from PyQt5.QtGui import QFont, QColor, QPalette, QDesktopServices

class LogModel(QAbstractTableModel):
    """日志数据模型"""
    def __init__(self, logs=None):
        super().__init__()
        self.logs = logs or []
        self.headers = [
            "时间", "IP地址", "设备类型", "浏览器", "操作系统", 
            "平台", "经纬度", "高德地图", "国家", "省份", "城市"
        ]
    
    def rowCount(self, parent=None):
        return len(self.logs)
    
    def columnCount(self, parent=None):
        return len(self.headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.logs):
            return None
        
        log = self.logs[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            if column == 0:  # 时间
                return log.get('timestamp', 'N/A')
            elif column == 1:  # IP地址
                return log.get('public_ip', 'N/A')
            elif column == 2:  # 设备类型
                return log.get('deviceType', 'N/A')
            elif column == 3:  # 浏览器
                browser = log.get('browser', 'N/A')
                return browser[:50] + '...' if len(browser) > 50 else browser
            elif column == 4:  # 操作系统
                return log.get('os', 'N/A')
            elif column == 5:  # 平台
                # 根据操作系统推断平台
                os_name = log.get('os', '').lower()
                platform = log.get('platform', '').lower()
                
                if 'ios' in os_name or 'iphone' in os_name or 'ipad' in os_name:
                    return 'iOS'
                elif 'android' in os_name:
                    return 'Android'
                elif 'mac' in os_name or 'macos' in os_name:
                    return 'macOS'
                elif 'win' in os_name or 'windows' in os_name:
                    return 'Windows'
                elif 'linux' in os_name:
                    return 'Linux'
                elif platform:
                    return platform.capitalize()
                else:
                    return 'Unknown'
            elif column == 6:  # 经纬度
                lat = log.get('latitude', 'N/A')
                lng = log.get('longitude', 'N/A')
                return f"{lat}, {lng}"
            elif column == 7:  # 高德地图
                return "查看地图"
            elif column == 8:  # 国家
                return log.get('country', 'N/A')
            elif column == 9:  # 省份
                return log.get('region', 'N/A')
            elif column == 10:  # 城市
                return log.get('city', 'N/A')
        
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        
        elif role == Qt.ForegroundRole:
            if column == 6:  # 高德地图链接
                return QColor(0, 0, 255)  # 蓝色
        
        elif role == Qt.FontRole:
            if column == 6:  # 高德地图链接
                font = QFont()
                font.setUnderline(True)
                return font
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None
    
    def get_log(self, index):
        """获取指定行的日志"""
        if 0 <= index < len(self.logs):
            return self.logs[index]
        return None

class LogViewer(QMainWindow):
    """日志查看器主窗口"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("设备信息日志查看器")
        self.setGeometry(100, 100, 1200, 800)
        self.log_file = "device_info.json"
        self.logs = []
        
        # 网站管理相关属性
        self.website_process = None
        self.website_port = 8001
        self.website_running = False
        
        # 科技感后台相关属性
        self.tech_website_process = None
        self.tech_website_port = 8002
        self.tech_website_running = False
        self.tech_website_password = "Pzf75513"
        
        self.init_ui()
        self.load_logs()
    
    def init_ui(self):
        """初始化UI界面"""
        # 设置主题样式
        self.setStyleSheet("""QWidget {
            font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
            font-size: 13px;
            color: #333;
        }
        
        QMainWindow {
            background-color: #f8f9fa;
        }
        
        QGroupBox {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            margin: 12px;
            padding: 15px;
            background-color: white;
            box-shadow: 0 3px 6px rgba(0,0,0,0.08);
        }
        
        QGroupBox::title {
            color: #0078d7;
            font-weight: 600;
            font-size: 14px;
            padding: 0 12px;
            top: -12px;
            background-color: white;
        }
        
        QPushButton {
            background-color: #0078d7;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: 600;
            font-size: 13px;
            transition: all 0.2s ease;
        }
        
        QPushButton:hover {
            background-color: #106ebe;
            box-shadow: 0 2px 8px rgba(0, 120, 215, 0.3);
        }
        
        QPushButton:pressed {
            background-color: #005a9e;
            transform: translateY(1px);
        }
        
        QPushButton#refresh_button {
            background-color: #5cb85c;
        }
        
        QPushButton#refresh_button:hover {
            background-color: #4cae4c;
            box-shadow: 0 2px 8px rgba(92, 184, 92, 0.3);
        }
        
        QPushButton#delete_button {
            background-color: #e74c3c;
        }
        
        QPushButton#delete_button:hover {
            background-color: #d43f3a;
            box-shadow: 0 2px 8px rgba(231, 76, 60, 0.3);
        }
        
        QTableView {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            background-color: white;
            gridline-color: #f0f0f0;
        }
        
        QHeaderView::section {
            background-color: #f8f9fa;
            color: #333;
            font-weight: 600;
            font-size: 13px;
            padding: 10px;
            border: none;
            border-bottom: 2px solid #e0e0e0;
        }
        
        QHeaderView::section:horizontal {
            border-right: 1px solid #e0e0e0;
        }
        
        QHeaderView::section:horizontal:last {
            border-right: none;
        }
        
        QTableView::item {
            padding: 12px 8px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        QTableView::item:hover {
            background-color: #e8f4fd;
        }
        
        QTableView::item:selected {
            background-color: #cce8ff;
            color: #000;
        }
        
        QLineEdit, QComboBox, QDateEdit {
            border: 1px solid #e0e0e0;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
            background-color: white;
            transition: border-color 0.2s ease;
        }
        
        QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
            border-color: #0078d7;
            outline: none;
            box-shadow: 0 0 0 2px rgba(0, 120, 215, 0.2);
        }
        
        QLabel {
            font-size: 13px;
            color: #555;
        }
        
        QStatusBar {
            background-color: white;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #666;
        }""")
        
        # 创建主部件和布局
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # 创建菜单栏
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        
        open_action = QAction("打开日志文件", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        refresh_action = QAction("刷新", self)
        refresh_action.triggered.connect(self.load_logs)
        file_menu.addAction(refresh_action)
        
        export_action = QAction("导出表格", self)
        export_action.triggered.connect(self.export_table)
        file_menu.addAction(export_action)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 创建工具栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        
        # 搜索和筛选区域
        search_group = QGroupBox("搜索和筛选")
        search_layout = QGridLayout(search_group)
        
        # IP地址搜索
        search_layout.addWidget(QLabel("IP地址:"), 0, 0)
        self.ip_search = QLineEdit()
        self.ip_search.setPlaceholderText("输入IP地址搜索")
        search_layout.addWidget(self.ip_search, 0, 1)
        
        # 设备类型筛选
        search_layout.addWidget(QLabel("设备类型:"), 0, 2)
        self.device_type = QComboBox()
        self.device_type.addItems(["全部", "Desktop", "Mobile", "Tablet", "Unknown"])
        search_layout.addWidget(self.device_type, 0, 3)
        
        # 平台筛选
        search_layout.addWidget(QLabel("平台:"), 2, 0)
        self.platform_filter = QComboBox()
        self.platform_filter.addItems(["全部", "iOS", "Android", "Windows", "macOS", "Linux", "Unknown"])
        search_layout.addWidget(self.platform_filter, 2, 1)
        
        # 日期筛选
        search_layout.addWidget(QLabel("日期:"), 1, 0)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        search_layout.addWidget(self.date_edit, 1, 1)
        
        # 时间筛选
        search_layout.addWidget(QLabel("时间段:"), 1, 2)
        self.time_edit = QComboBox()
        time_options = ["全部", "00:00-06:00", "06:00-12:00", "12:00-18:00", "18:00-24:00"]
        self.time_edit.addItems(time_options)
        search_layout.addWidget(self.time_edit, 1, 3)
        
        # 操作按钮区域
        button_layout = QHBoxLayout()
        
        # 搜索按钮
        self.search_button = QPushButton("搜索")
        self.search_button.clicked.connect(self.filter_logs)
        button_layout.addWidget(self.search_button)
        
        self.refresh_button = QPushButton("刷新日志")
        self.refresh_button.setObjectName("refresh_button")
        self.refresh_button.clicked.connect(self.load_logs)
        button_layout.addWidget(self.refresh_button)
        
        self.reset_button = QPushButton("重置")
        self.reset_button.clicked.connect(self.reset_filter)
        button_layout.addWidget(self.reset_button)
        
        self.delete_button = QPushButton("删除选中")
        self.delete_button.setObjectName("delete_button")
        self.delete_button.setStyleSheet("background-color: #e74c3c; color: white;")
        self.delete_button.clicked.connect(self.delete_selected)
        button_layout.addWidget(self.delete_button)
        
        # 添加按钮布局到搜索布局
        search_layout.addLayout(button_layout, 2, 0, 1, 4)
        
        main_layout.addWidget(search_group)
        
        # 创建网站管理区域
        website_group = QGroupBox("网站管理")
        website_layout = QGridLayout(website_group)
        
        # 端口输入
        website_layout.addWidget(QLabel("端口:"), 0, 0)
        self.port_input = QLineEdit(str(self.website_port))
        self.port_input.setPlaceholderText("输入端口号")
        self.port_input.setFixedWidth(100)
        website_layout.addWidget(self.port_input, 0, 1)
        
        # 启动/停止按钮
        self.start_stop_btn = QPushButton("启动网站")
        self.start_stop_btn.setFixedWidth(120)
        self.start_stop_btn.clicked.connect(self.toggle_website)
        website_layout.addWidget(self.start_stop_btn, 0, 2)
        
        # 状态标签
        self.website_status = QLabel("网站状态: 未运行")
        self.website_status.setStyleSheet("color: red; font-weight: bold;")
        website_layout.addWidget(self.website_status, 0, 3)
        
        main_layout.addWidget(website_group)
        
        # 创建科技感后台管理区域
        tech_website_group = QGroupBox("科技感后台管理")
        tech_website_layout = QGridLayout(tech_website_group)
        
        # 端口输入
        tech_website_layout.addWidget(QLabel("端口:"), 0, 0)
        self.tech_port_input = QLineEdit(str(self.tech_website_port))
        self.tech_port_input.setPlaceholderText("输入端口号")
        self.tech_port_input.setFixedWidth(100)
        tech_website_layout.addWidget(self.tech_port_input, 0, 1)
        
        # 密码输入
        tech_website_layout.addWidget(QLabel("密码:"), 0, 2)
        self.tech_password_input = QLineEdit(self.tech_website_password)
        self.tech_password_input.setPlaceholderText("输入密码")
        self.tech_password_input.setFixedWidth(150)
        tech_website_layout.addWidget(self.tech_password_input, 0, 3)
        
        # 启动/停止按钮
        self.tech_start_stop_btn = QPushButton("启动科技后台")
        self.tech_start_stop_btn.setFixedWidth(150)
        self.tech_start_stop_btn.clicked.connect(self.toggle_tech_website)
        tech_website_layout.addWidget(self.tech_start_stop_btn, 0, 4)
        
        # 状态标签
        self.tech_website_status = QLabel("科技后台状态: 未运行")
        self.tech_website_status.setStyleSheet("color: red; font-weight: bold;")
        tech_website_layout.addWidget(self.tech_website_status, 0, 5)
        
        main_layout.addWidget(tech_website_group)
        
        # 创建日志表格
        self.log_model = LogModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.log_model)
        self.proxy_model.setDynamicSortFilter(True)
        
        self.table_view = QTableView()
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.doubleClicked.connect(self.on_cell_double_clicked)
        # 设置为多选模式
        self.table_view.setSelectionMode(QTableView.ExtendedSelection)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        
        main_layout.addWidget(self.table_view)
        
        # 创建状态栏
        self.status_label = QLabel("就绪")
        self.statusBar.addWidget(self.status_label)
        
        self.setCentralWidget(central_widget)
        
        # 设置窗口淡入效果
        self.setWindowOpacity(0.0)
        QTimer.singleShot(100, self.fade_in_window)
    
    def fade_in_window(self):
        """窗口淡入动画"""
        opacity = 0.0
        while opacity < 1.0:
            opacity += 0.1
            self.setWindowOpacity(opacity)
            QApplication.processEvents()
            QTimer.singleShot(20, lambda: None)
        self.setWindowOpacity(1.0)
    
    def load_logs(self):
        """加载日志文件"""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.logs = json.load(f)
                
                # 按时间倒序排列
                self.logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                
                # 更新模型数据
                self.log_model.logs = self.logs
                self.log_model.layoutChanged.emit()
                
                # 更新状态栏
                self.status_label.setText(f"已加载 {len(self.logs)} 条记录")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"加载日志文件失败: {str(e)}")
        else:
            QMessageBox.information(self, "提示", "日志文件不存在")
    
    def open_file(self):
        """打开日志文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开日志文件", ".", "JSON Files (*.json)"
        )
        if file_path:
            self.log_file = file_path
            self.load_logs()
    
    def filter_logs(self):
        """筛选日志"""
        # 获取原始日志数据
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    all_logs = json.load(f)
            except:
                all_logs = []
        else:
            all_logs = []
        
        # 应用筛选条件
        filtered_logs = all_logs
        
        # IP地址筛选
        ip_filter = self.ip_search.text().strip()
        if ip_filter:
            filtered_logs = [log for log in filtered_logs if ip_filter in log.get('public_ip', '')]
        
        # 设备类型筛选
        device_type = self.device_type.currentText()
        if device_type != "全部":
            filtered_logs = [
                log for log in filtered_logs 
                if log.get('deviceType', 'Unknown') == device_type
            ]
        
        # 平台筛选
        platform = self.platform_filter.currentText()
        if platform != "全部":
            # 根据平台名称筛选日志
            filtered_logs = [
                log for log in filtered_logs
                if self.get_platform(log) == platform
            ]
        
        # 日期筛选
        selected_date = self.date_edit.date().toString("yyyy-MM-dd")
        filtered_logs = [log for log in filtered_logs if log.get('timestamp', '').startswith(selected_date)]
        
        # 时间筛选
        time_range = self.time_edit.currentText()
        if time_range != "全部":
            time_start, time_end = time_range.split("-")
            start_hour, start_min = map(int, time_start.split(":"))
            end_hour, end_min = map(int, time_end.split(":"))
            
            filtered_logs = [
                log for log in filtered_logs
                if self.is_time_in_range(log.get('timestamp', ''), start_hour, start_min, end_hour, end_min)
            ]
        
        # 按时间倒序排列
        filtered_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # 更新模型数据
        self.log_model.logs = filtered_logs
        self.log_model.layoutChanged.emit()
        
        # 更新状态栏
        self.status_label.setText(f"已筛选 {len(filtered_logs)} 条记录")
    
    def is_time_in_range(self, timestamp, start_hour, start_min, end_hour, end_min):
        """检查时间是否在指定范围内"""
        if not timestamp:
            return False
        try:
            time_part = timestamp.split(" ")[1]
            hour, minute, _ = map(int, time_part.split(":"))
            
            if start_hour < end_hour:
                return (start_hour < hour or (start_hour == hour and start_min <= minute)) and \
                       (hour < end_hour or (hour == end_hour and minute <= end_min))
            else:  # 跨午夜
                return (start_hour < hour or (start_hour == hour and start_min <= minute)) or \
                       (hour < end_hour or (hour == end_hour and minute <= end_min))
        except:
            return False
    
    def reset_filter(self):
        """重置筛选条件"""
        self.ip_search.clear()
        self.device_type.setCurrentIndex(0)
        self.platform_filter.setCurrentIndex(0)
        self.date_edit.setDate(QDate.currentDate())
        self.time_edit.setCurrentIndex(0)
        self.load_logs()
    
    def get_platform(self, log):
        """根据日志记录的操作系统信息推断平台"""
        os_name = log.get('os', '').lower()
        platform = log.get('platform', '').lower()
        
        if 'ios' in os_name or 'iphone' in os_name or 'ipad' in os_name:
            return 'iOS'
        elif 'android' in os_name:
            return 'Android'
        elif 'mac' in os_name or 'macos' in os_name:
            return 'macOS'
        elif 'win' in os_name or 'windows' in os_name:
            return 'Windows'
        elif 'linux' in os_name:
            return 'Linux'
        elif platform:
            return platform.capitalize()
        else:
            return 'Unknown'
    
    def delete_selected(self):
        """删除选中的记录"""
        try:
            # 获取选中的行
            selected_rows = self.table_view.selectionModel().selectedRows()
            if not selected_rows:
                QMessageBox.warning(self, "警告", "请先选择要删除的记录")
                return
            
            # 确认删除
            reply = QMessageBox.question(
                self, "确认删除", f"确定要删除选中的 {len(selected_rows)} 条记录吗？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            
            # 获取选中行的原始索引
            source_indices = [self.proxy_model.mapToSource(index) for index in selected_rows]
            source_rows = sorted([index.row() for index in source_indices], reverse=True)
            
            # 删除原始日志中的记录
            for row in source_rows:
                if 0 <= row < len(self.logs):
                    del self.logs[row]
            
            # 保存更新后的日志 - 使用非阻塞方式
            try:
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    json.dump(self.logs, f, ensure_ascii=False, indent=2)
            except Exception as file_error:
                QMessageBox.critical(self, "错误", f"保存日志文件失败: {str(file_error)}")
                return
            
            # 使用正确的模型更新方式
            # beginResetModel() 和 endResetModel() 会完全重置模型，解决索引问题
            self.log_model.beginResetModel()
            # 直接更新模型的日志列表，不需要使用副本
            self.log_model.logs = self.logs
            self.log_model.endResetModel()
            
            # 代理模型会自动更新，不需要手动调用invalidateFilter或layoutChanged
            
            # 更新状态栏
            self.status_label.setText(f"已删除 {len(selected_rows)} 条记录")
        except Exception as e:
            # 捕获所有异常，防止软件崩溃
            import traceback
            error_msg = f"删除记录时发生错误: {str(e)}"
            print(f"删除错误详细信息: {traceback.format_exc()}")
            QMessageBox.critical(self, "错误", error_msg)
    
    def on_cell_double_clicked(self, index):
        """处理单元格双击事件"""
        source_index = self.proxy_model.mapToSource(index)
        log = self.log_model.get_log(source_index.row())
        if not log:
            return
        
        if index.column() == 6:  # 高德地图链接
            # 打开高德地图
            lat = log.get('latitude', 'N/A')
            lng = log.get('longitude', 'N/A')
            if lat != 'N/A' and lng != 'N/A':
                try:
                    wgs_lng = float(lng)
                    wgs_lat = float(lat)
                    # 转换为GCJ-02坐标
                    gcj_lng, gcj_lat = self.wgs84_to_gcj02(wgs_lng, wgs_lat)
                    map_url = f"https://uri.amap.com/marker?position={gcj_lng:.6f},{gcj_lat:.6f}&name=当前位置&coordinate=gaode"
                except:
                    map_url = f"https://uri.amap.com/marker?position={lng},{lat}&name=当前位置&coordinate=gaode"
                
                # 打开浏览器访问高德地图
                QDesktopServices.openUrl(QUrl(map_url))
            else:
                QMessageBox.information(self, "提示", "无法获取地图信息")
        else:
            # 显示详细信息弹窗
            self.show_log_details(log)
    
    def wgs84_to_gcj02(self, lng, lat):
        """将WGS-84坐标转换为GCJ-02坐标"""
        import math
        PI = math.pi
        a = 6378137.0
        ee = 0.00669342162296594323
        
        if self.out_of_china(lng, lat):
            return lng, lat
        
        d_lat = self.transform_lat(lng - 105.0, lat - 35.0)
        d_lng = self.transform_lng(lng - 105.0, lat - 35.0)
        rad_lat = lat / 180.0 * PI
        magic = math.sin(rad_lat)
        magic = 1 - ee * magic * magic
        sqrt_magic = math.sqrt(magic)
        d_lat = (d_lat * 180.0) / ((a * (1 - ee)) / (magic * sqrt_magic) * PI)
        d_lng = (d_lng * 180.0) / (a / sqrt_magic * math.cos(rad_lat) * PI)
        
        gcj_lat = lat + d_lat
        gcj_lng = lng + d_lng
        
        return gcj_lng, gcj_lat
    
    def transform_lat(self, x, y):
        """计算纬度偏移量"""
        import math
        PI = math.pi
        ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
        ret += (20.0 * math.sin(y * PI) + 40.0 * math.sin(y / 3.0 * PI)) * 2.0 / 3.0
        ret += (160.0 * math.sin(y / 12.0 * PI) + 320 * math.sin(y * PI / 30.0)) * 2.0 / 3.0
        return ret
    
    def transform_lng(self, x, y):
        """计算经度偏移量"""
        import math
        PI = math.pi
        ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
        ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
        ret += (20.0 * math.sin(x * PI) + 40.0 * math.sin(x / 3.0 * PI)) * 2.0 / 3.0
        ret += (150.0 * math.sin(x / 12.0 * PI) + 300.0 * math.sin(x / 30.0 * PI)) * 2.0 / 3.0
        return ret
    
    def toggle_website(self):
        """切换网站运行状态"""
        if not self.website_running:
            self.start_website()
        else:
            self.stop_website()
    
    def toggle_tech_website(self):
        """切换科技感后台运行状态"""
        if not self.tech_website_running:
            self.start_tech_website()
        else:
            self.stop_tech_website()
    
    def update_dependencies(self):
        """更新依赖库文件"""
        try:
            # 检查requirements.txt文件是否存在
            if os.path.exists('requirements.txt'):
                # 更新依赖库
                self.status_label.setText("正在更新依赖库...")
                QApplication.processEvents()
                
                cmd = [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt', '--upgrade']
                
                process = subprocess.Popen(
                    cmd,
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # 等待命令执行完成
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    self.status_label.setText("依赖库更新完成")
                else:
                    self.status_label.setText(f"依赖库更新失败: {stderr[:100]}...")
        except Exception as e:
            self.status_label.setText(f"更新依赖库时出错: {str(e)}")
    
    def start_website(self):
        """启动网站"""
        try:
            # 检查app.py文件是否存在
            app_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
            if not os.path.exists(app_file):
                QMessageBox.critical(self, "错误", f"app.py文件不存在，请确保该文件在当前目录中")
                return
            
            # 获取端口号
            port = self.port_input.text()
            if not port.isdigit():
                QMessageBox.warning(self, "警告", "请输入有效的端口号")
                return
            
            self.website_port = int(port)
            
            # 检查端口是否被占用
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('127.0.0.1', self.website_port)) == 0:
                    QMessageBox.warning(self, "警告", f"端口 {self.website_port} 已被占用")
                    return
            
            # 构建启动命令
            cmd = [sys.executable, 'app.py']
            env = os.environ.copy()
            env['FLASK_RUN_PORT'] = str(self.website_port)
            env['FLASK_ENV'] = 'development'  # 设置Flask环境
            env['BACKEND_TYPE'] = 'normal'  # 标准后台
            
            # 打印调试信息
            print(f"启动命令: {' '.join(cmd)}")
            print(f"工作目录: {os.path.dirname(os.path.abspath(__file__))}")
            print(f"环境变量: {env}")
            
            # 后台运行配置，移除可能导致问题的标志
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # 启动网站进程
            self.website_process = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                # 移除可能导致问题的CREATE_NO_WINDOW标志
            )
            
            # 检查进程是否成功启动
            time.sleep(1)  # 等待1秒，让进程有时间启动
            if self.website_process.poll() is not None:
                # 进程已经退出，获取错误信息
                stdout, stderr = self.website_process.communicate()
                error_msg = f"网站进程启动失败，退出码: {self.website_process.returncode}\n"
                error_msg += f"标准输出: {stdout}\n"
                error_msg += f"错误输出: {stderr}"
                QMessageBox.critical(self, "错误", error_msg)
                self.website_process = None
                return
            
            # 更新状态
            self.website_running = True
            self.start_stop_btn.setText("停止网站")
            self.website_status.setText(f"网站状态: 运行中 (端口: {self.website_port})")
            self.website_status.setStyleSheet("color: green; font-weight: bold;")
            self.status_label.setText(f"已启动网站，端口: {self.website_port}")
            
            # 启动日志线程，使用非阻塞方式读取日志
            threading.Thread(target=self.read_website_logs, daemon=True).start()
            
            # 启动一个定时器，定期检查进程状态
            self.check_process_timer = QTimer(self)
            self.check_process_timer.timeout.connect(self.check_website_process)
            self.check_process_timer.start(5000)  # 每5秒检查一次
            
        except Exception as e:
            import traceback
            error_msg = f"启动网站失败: {str(e)}\n详细信息: {traceback.format_exc()}"
            print(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def start_tech_website(self):
        """启动科技感后台"""
        try:
            # 检查app.py文件是否存在
            app_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.py')
            if not os.path.exists(app_file):
                QMessageBox.critical(self, "错误", f"app.py文件不存在，请确保该文件在当前目录中")
                return
            
            # 获取端口号
            port = self.tech_port_input.text()
            if not port.isdigit():
                QMessageBox.warning(self, "警告", "请输入有效的端口号")
                return
            
            self.tech_website_port = int(port)
            
            # 检查端口是否被占用
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(('127.0.0.1', self.tech_website_port)) == 0:
                    QMessageBox.warning(self, "警告", f"端口 {self.tech_website_port} 已被占用")
                    return
            
            # 获取密码
            password = self.tech_password_input.text().strip()
            if not password:
                QMessageBox.warning(self, "警告", "请输入有效的密码")
                return
            self.tech_website_password = password
            
            # 构建启动命令
            cmd = [sys.executable, 'app.py']
            env = os.environ.copy()
            env['FLASK_RUN_PORT'] = str(self.tech_website_port)
            env['FLASK_ENV'] = 'development'  # 设置Flask环境
            env['BACKEND_TYPE'] = 'tech'  # 科技感后台
            env['TECH_BACKEND_PASSWORD'] = password
            
            # 打印调试信息
            print(f"启动科技感后台命令: {' '.join(cmd)}")
            print(f"工作目录: {os.path.dirname(os.path.abspath(__file__))}")
            print(f"环境变量: {env}")
            
            # 后台运行配置，移除可能导致问题的标志
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            # 启动网站进程
            self.tech_website_process = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                # 移除可能导致问题的CREATE_NO_WINDOW标志
            )
            
            # 检查进程是否成功启动
            time.sleep(1)  # 等待1秒，让进程有时间启动
            if self.tech_website_process.poll() is not None:
                # 进程已经退出，获取错误信息
                stdout, stderr = self.tech_website_process.communicate()
                error_msg = f"科技感后台进程启动失败，退出码: {self.tech_website_process.returncode}\n"
                error_msg += f"标准输出: {stdout}\n"
                error_msg += f"错误输出: {stderr}"
                QMessageBox.critical(self, "错误", error_msg)
                self.tech_website_process = None
                return
            
            # 更新状态
            self.tech_website_running = True
            self.tech_start_stop_btn.setText("停止科技后台")
            self.tech_website_status.setText(f"科技后台状态: 运行中 (端口: {self.tech_website_port})")
            self.tech_website_status.setStyleSheet("color: green; font-weight: bold;")
            self.status_label.setText(f"已启动科技感后台，端口: {self.tech_website_port}")
            
            # 启动日志线程，使用非阻塞方式读取日志
            threading.Thread(target=self.read_tech_website_logs, daemon=True).start()
            
            # 启动一个定时器，定期检查进程状态
            self.tech_check_process_timer = QTimer(self)
            self.tech_check_process_timer.timeout.connect(self.check_tech_website_process)
            self.tech_check_process_timer.start(5000)  # 每5秒检查一次
            
        except Exception as e:
            import traceback
            error_msg = f"启动科技感后台失败: {str(e)}\n详细信息: {traceback.format_exc()}"
            print(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
    
    def stop_website(self):
        """停止网站"""
        try:
            if self.website_process:
                # 终止进程
                self.website_process.terminate()
                self.website_process.wait(timeout=5)
                
                # 更新状态
                self.website_running = False
                self.start_stop_btn.setText("启动网站")
                self.website_status.setText("网站状态: 未运行")
                self.website_status.setStyleSheet("color: red; font-weight: bold;")
                self.status_label.setText("已停止网站")
                self.website_process = None
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止网站失败: {str(e)}")
    
    def stop_tech_website(self):
        """停止科技感后台"""
        try:
            if self.tech_website_process:
                # 终止进程
                self.tech_website_process.terminate()
                self.tech_website_process.wait(timeout=5)
                
                # 更新状态
                self.tech_website_running = False
                self.tech_start_stop_btn.setText("启动科技后台")
                self.tech_website_status.setText("科技后台状态: 未运行")
                self.tech_website_status.setStyleSheet("color: red; font-weight: bold;")
                self.status_label.setText("已停止科技感后台")
                self.tech_website_process = None
                
                # 停止定时器
                if hasattr(self, 'tech_check_process_timer'):
                    self.tech_check_process_timer.stop()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"停止科技感后台失败: {str(e)}")
    
    def check_website_process(self):
        """检查网站进程状态"""
        if self.website_process and self.website_running:
            if self.website_process.poll() is not None:
                # 进程已退出
                self.website_running = False
                self.start_stop_btn.setText("启动网站")
                self.website_status.setText("网站状态: 已停止")
                self.website_status.setStyleSheet("color: red; font-weight: bold;")
                self.status_label.setText("网站进程已意外停止")
                self.website_process = None
                
                # 停止定时器
                if hasattr(self, 'check_process_timer'):
                    self.check_process_timer.stop()
    
    def check_tech_website_process(self):
        """检查科技感后台进程状态"""
        if self.tech_website_process and self.tech_website_running:
            if self.tech_website_process.poll() is not None:
                # 进程已退出
                self.tech_website_running = False
                self.tech_start_stop_btn.setText("启动科技后台")
                self.tech_website_status.setText("科技后台状态: 已停止")
                self.tech_website_status.setStyleSheet("color: red; font-weight: bold;")
                self.status_label.setText("科技感后台进程已意外停止")
                self.tech_website_process = None
                
                # 停止定时器
                if hasattr(self, 'tech_check_process_timer'):
                    self.tech_check_process_timer.stop()
    
    def read_website_logs(self):
        """读取网站日志"""
        if self.website_process:
            for line in iter(self.website_process.stdout.readline, ''):
                # 这里可以处理网站日志，暂时只打印到控制台
                print(f"网站日志: {line.strip()}")
            
            for line in iter(self.website_process.stderr.readline, ''):
                print(f"网站错误: {line.strip()}")
    
    def read_tech_website_logs(self):
        """读取科技感后台日志"""
        if self.tech_website_process:
            for line in iter(self.tech_website_process.stdout.readline, ''):
                # 这里可以处理科技感后台日志，暂时只打印到控制台
                print(f"科技感后台日志: {line.strip()}")
            
            for line in iter(self.tech_website_process.stderr.readline, ''):
                print(f"科技感后台错误: {line.strip()}")
    
    def show_log_details(self, log):
        """显示日志详细信息弹窗"""
        from PyQt5.QtWidgets import QTextBrowser, QVBoxLayout, QDialog
        
        # 创建详细信息对话框
        details_dialog = QDialog(self)
        details_dialog.setWindowTitle("详细信息")
        details_dialog.setGeometry(200, 200, 600, 500)
        details_dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 8px;
            }
            QTextBrowser {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 15px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
                color: #333;
            }
        """)
        
        # 创建文本浏览器显示详细信息
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        
        # 构建详细信息HTML内容
        details_html = f"""
        <html>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; color: #333;">
            <h2 style="color: #0078d7; margin-bottom: 20px; border-bottom: 1px solid #e0e0e0; padding-bottom: 10px;">访问详情</h2>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="width: 120px; font-weight: bold; padding: 8px 0;">访问时间:</td>
                    <td style="padding: 8px 0;">{log.get('timestamp', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px 0;">IP地址:</td>
                    <td style="padding: 8px 0;">{log.get('public_ip', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px 0;">设备类型:</td>
                    <td style="padding: 8px 0;">{log.get('deviceType', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px 0;">浏览器:</td>
                    <td style="padding: 8px 0;">{log.get('browser', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px 0;">操作系统:</td>
                    <td style="padding: 8px 0;">{log.get('os', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px 0;">经纬度:</td>
                    <td style="padding: 8px 0;">{log.get('latitude', 'N/A')}, {log.get('longitude', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px 0;">国家:</td>
                    <td style="padding: 8px 0;">{log.get('country', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px 0;">省份:</td>
                    <td style="padding: 8px 0;">{log.get('region', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px 0;">城市:</td>
                    <td style="padding: 8px 0;">{log.get('city', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px 0;">时区:</td>
                    <td style="padding: 8px 0;">{log.get('timezone', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px 0;">ISP:</td>
                    <td style="padding: 8px 0;">{log.get('isp', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; padding: 8px 0;">用户代理:</td>
                    <td style="padding: 8px 0; word-break: break-all;">{log.get('user_agent', 'N/A')}</td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        text_browser.setHtml(details_html)
        
        # 设置布局
        layout = QVBoxLayout(details_dialog)
        layout.addWidget(text_browser)
        
        # 显示对话框
        details_dialog.exec_()
    
    def export_table(self):
        """导出表格为CSV文件"""
        from PyQt5.QtWidgets import QFileDialog
        import csv
        
        # 选择导出文件路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出表格", ".", "CSV Files (*.csv)"
        )
        if not file_path:
            return
        
        try:
            # 获取当前显示的日志数据
            display_logs = self.log_model.logs
            
            if not display_logs:
                QMessageBox.information(self, "提示", "没有数据可导出")
                return
            
            # 定义CSV文件头
            headers = [
                "时间", "IP地址", "设备类型", "浏览器", "操作系统",
                "纬度", "经度", "国家", "省份", "城市", "时区", "ISP", "用户代理"
            ]
            
            # 写入CSV文件
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
                for log in display_logs:
                    row = [
                        log.get('timestamp', 'N/A'),
                        log.get('public_ip', 'N/A'),
                        log.get('deviceType', 'N/A'),
                        log.get('browser', 'N/A'),
                        log.get('os', 'N/A'),
                        log.get('latitude', 'N/A'),
                        log.get('longitude', 'N/A'),
                        log.get('country', 'N/A'),
                        log.get('region', 'N/A'),
                        log.get('city', 'N/A'),
                        log.get('timezone', 'N/A'),
                        log.get('isp', 'N/A'),
                        log.get('user_agent', 'N/A')
                    ]
                    writer.writerow(row)
            
            QMessageBox.information(self, "成功", f"数据已导出到 {file_path}")
            self.status_label.setText(f"已导出 {len(display_logs)} 条记录到 CSV 文件")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
            self.status_label.setText(f"导出失败: {str(e)}")
    
    def out_of_china(self, lng, lat):
        """判断坐标是否在国外"""
        return (lng < 72.004 or lng > 137.8347) or (lat < 0.8293 or lat > 55.8271)
    
    def closeEvent(self, event):
        """窗口关闭事件，确保结束后台网站进程"""
        # 停止网站进程
        if self.website_running:
            self.stop_website()
        
        # 停止科技感后台进程
        if self.tech_website_running:
            self.stop_tech_website()
        
        # 接受关闭事件
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LogViewer()
    window.show()
    sys.exit(app.exec_())
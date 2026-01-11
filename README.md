# Tracker - 设备信息收集与日志查看系统

```
 ████████╗██╗   ██╗██████╗ ██╗     ███████╗    ███████╗███████╗██████╗ ██╗   ██╗███████╗██████╗ 
╚══██╔══╝██║   ██║██╔══██╗██║     ██╔════╝    ██╔════╝██╔════╝██╔══██╗██║   ██║██╔════╝██╔══██╗
   ██║   ██║   ██║██████╔╝██║     █████╗      ███████╗█████╗  ██████╔╝██║   ██║█████╗  ██████╔╝
   ██║   ██║   ██║██╔══██╗██║     ██╔══╝      ╚════██║██╔══╝  ██╔══██╗██║   ██║██╔══╝  ██╔══██╗
   ██║   ╚██████╔╝██║  ██║███████╗███████╗    ███████║███████╗██║  ██║╚██████╔╝███████╗██║  ██║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝    ╚══════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
```

一个功能完整的设备信息收集和日志查看系统，包含基于Flask的Web应用和基于PyQt5的日志查看器。

## 📋 项目简介

本项目提供了一个完整的设备信息收集和日志管理解决方案，主要包含两个核心组件：

1. **Flask Web应用**：用于收集访问者的设备信息、IP地址、地理位置等详细数据
2. **PyQt5日志查看器**：用于查看、筛选、管理收集到的日志数据

该系统可以帮助开发者或管理员了解访问者的设备信息和地理位置分布，适用于网站分析、设备统计、访问监控等场景。

## ✨ 功能特性

### Web应用功能
- ✅ 收集设备详细信息（操作系统、浏览器、CPU核心数、设备内存等）
- ✅ 识别设备类型（Desktop/Mobile/Tablet）
- ✅ 检测IP地址和地理位置信息
- ✅ 支持多种IP信息服务，提高可靠性
- ✅ 自动转换经纬度坐标系（WGS-84 → GCJ-02）
- ✅ 生成高德地图链接
- ✅ JSON格式日志存储
- ✅ 支持多设备访问
- ✅ 响应式设计，适配各种设备
- ✅ 后台静默运行选项

### 日志查看器功能
- ✅ 直观的表格视图展示日志数据
- ✅ 支持按IP地址、设备类型、平台、日期、时间段筛选
- ✅ 双击查看详细信息
- ✅ 支持删除选中日志
- ✅ 支持导出表格数据为CSV
- ✅ 网站管理功能（启动/停止网站，修改端口）
- ✅ 实时状态监控
- ✅ 支持刷新日志
- ✅ 支持打开多个日志文件
- ✅ 优雅的UI设计，支持主题样式
- ✅ 自动识别设备平台（iOS/Android/Windows/macOS/Linux）

## 🛠️ 技术栈

### 后端
- **Python 3.11**：主要开发语言
- **Flask**：Web应用框架
- **Requests**：HTTP请求库
- **JSON**：日志数据存储格式
- **Socket**：端口占用检查
- **Subprocess**：网站进程管理

### 前端
- **HTML5**：页面结构
- **CSS3**：样式设计
- **JavaScript**：交互逻辑
- **Geolocation API**：地理位置获取
- **Async/Await**：异步操作

### 日志查看器
- **PyQt5**：桌面应用框架
- **QAbstractTableModel**：数据模型
- **QSortFilterProxyModel**：数据筛选
- **QTableView**：表格视图
- **QMessageBox**：对话框
- **QTimer**：定时器

## 📁 项目结构

```
SiteConfig/
├── app.py                  # Flask Web应用主文件
├── log_viewer.py           # PyQt5日志查看器
├── requirements.txt        # 项目依赖
├── README.md               # 项目说明文档
├── device_info.json        # 日志存储文件
├── templates/              # HTML模板
│   └── index.html          # 主页面模板
└── static/                 # 静态资源（可选）
```

## 📦 安装步骤

### 1. 克隆仓库

```bash
git clone <repository-url>
cd SiteConfig
```

### 2. 创建虚拟环境（可选但推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

Tracker项目使用requirements.txt文件管理所有依赖，您可以通过以下命令快速安装：

#### Windows系统

```bash
# 使用pip安装依赖
pip install -r requirements.txt

# 如果pip版本较旧，建议先升级pip
python -m pip install --upgrade pip

# 然后再安装依赖
pip install -r requirements.txt
```

#### Linux/macOS系统

```bash
# 使用pip3安装依赖
pip3 install -r requirements.txt

# 如果pip3版本较旧，建议先升级pip3
python3 -m pip install --upgrade pip

# 然后再安装依赖
pip3 install -r requirements.txt
```

### 4. 安装额外依赖（如果需要）

#### PyQt5安装问题解决（Windows）

如果在Windows系统上遇到PyQt5 DLL加载失败问题，可以尝试以下命令：

```bash
pip install --force-reinstall --no-cache-dir PyQt5 PyQt5-sip PyQt5-Qt5
```

#### PyQt5安装问题解决（Linux）

在Linux系统上，可能需要安装系统依赖：

```bash
# Ubuntu/Debian系统
sudo apt-get update
sudo apt-get install -y python3-pyqt5 python3-pyqt5.qtwebkit

# 然后重新安装PyQt5
pip3 install --force-reinstall PyQt5
```

#### Ngrok安装（用于内网穿透，可选）

下载地址：[https://ngrok.com/download](https://ngrok.com/download)

安装完成后，将ngrok可执行文件添加到系统路径中，以便在终端中直接使用。

## 🚀 使用方法

Tracker支持多种运行方式，包括终端运行和GUI运行，适用于不同的操作系统。

### 1. 终端运行方式

#### 1.1 启动Web应用

##### Windows系统

```bash
# 直接启动（默认端口8001）
python app.py

# 指定端口启动
set FLASK_RUN_PORT=8080
python app.py

# 启动科技感后台（默认端口8002）
set BACKEND_TYPE=tech
set FLASK_RUN_PORT=8002
python app.py
```

##### Linux/macOS系统

```bash
# 直接启动（默认端口8001）
python3 app.py

# 指定端口启动
export FLASK_RUN_PORT=8080
python3 app.py

# 启动科技感后台（默认端口8002）
export BACKEND_TYPE=tech
export FLASK_RUN_PORT=8002
python3 app.py
```

#### 1.2 查看日志文件

```bash
# 查看JSON日志内容（终端）
cat device_info.json  # Linux/macOS
type device_info.json  # Windows

# 使用文本编辑器查看
nano device_info.json  # Linux/macOS
notepad device_info.json  # Windows
```

### 2. GUI运行方式

#### 2.1 启动日志查看器

##### Windows系统

```bash
# 直接启动GUI应用
python log_viewer.py
```

##### Linux/macOS系统

```bash
# 直接启动GUI应用
python3 log_viewer.py

# 或者使用可执行文件（如果已打包）
./log_viewer
```

#### 2.2 GUI功能使用说明

1. **查看日志**：启动后自动加载 `device_info.json` 中的日志数据
2. **筛选日志**：
   - 按IP地址搜索
   - 按设备类型筛选（Desktop/Mobile/Tablet/Unknown）
   - 按平台筛选（iOS/Android/Windows/macOS/Linux/Unknown）
   - 按日期筛选
   - 按时间段筛选
3. **删除日志**：
   - 选择要删除的日志行
   - 点击"删除选中"按钮
   - 确认删除操作
4. **查看详细信息**：
   - 双击任意日志行
   - 在弹出的对话框中查看完整的设备信息
5. **导出日志**：
   - 点击菜单栏中的"文件" → "导出表格"
   - 选择保存位置和文件名
   - 保存为CSV格式
6. **网站管理**：
   - 在"网站管理"区域输入端口号
   - 点击"启动网站"按钮启动标准Flask应用
   - 点击"停止网站"按钮停止Flask应用
   - 查看网站运行状态
7. **科技感后台管理**：
   - 在"科技感后台管理"区域设置端口（默认8002）和密码
   - 点击"启动科技后台"按钮启动科技感后台
   - 点击"停止科技后台"按钮停止科技感后台
   - 查看科技感后台运行状态

### 3. 访问Web应用

#### 3.1 标准后台

在浏览器中访问：
```
http://127.0.0.1:8001  # 默认端口，可自定义
```

#### 3.2 科技感后台

在浏览器中访问：
```
http://127.0.0.1:8002  # 默认端口，可自定义
```

输入设置的密码即可登录科技感后台。

### 4. 使用Ngrok进行内网穿透（可选）

#### Windows系统

```bash
# 下载并安装ngrok（https://ngrok.com/download）
# 启动ngrok服务
ngrok http 8001
```

#### Linux/macOS系统

```bash
# 下载ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz  # Linux
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-darwin-amd64.tgz  # macOS

# 解压并安装
tar xvzf ngrok-v3-stable-*.tgz
sudo mv ngrok /usr/local/bin/  # 可选，添加到系统路径

# 启动ngrok服务
ngrok http 8001
```

将生成的公网URL分享给其他设备访问。

## ⚙️ 配置说明

### Web应用配置

在 `app.py` 中可以修改以下配置：

```python
ADMIN_PASSWORD = 'Pzf75513'  # 管理员密码
LOG_FILE = 'device_info.json'  # 日志文件路径
```

### 日志查看器配置

在 `log_viewer.py` 中可以修改以下配置：

```python
self.log_file = "device_info.json"  # 默认日志文件路径
self.website_port = 8001  # 默认网站端口
```

## 📊 日志格式

日志以JSON格式存储在 `device_info.json` 文件中，每条日志包含以下字段：

| 字段名 | 描述 | 示例值 |
| ------ | ---- | ------ |
| timestamp | 访问时间 | "2026-01-10 19:35:10" |
| os | 操作系统 | "Windows NT 10.0" |
| platform | 平台 | "Win32" |
| cpuCores | CPU核心数 | 8 |
| deviceMemory | 设备内存 | 16 |
| gpuVendor | GPU厂商 | "NVIDIA" |
| gpu | GPU型号 | "GeForce GTX 1080" |
| resolution | 屏幕分辨率 | "1920x1080" |
| viewport | 视口大小 | "1920x922" |
| browser | 浏览器 | "Chrome 120.0.0.0" |
| public_ip | 公网IP | "119.184.72.92" |
| city | 城市 | "日照市" |
| region | 省份 | "山东省" |
| country | 国家 | "中国" |
| latitude | 纬度 | "35.586682" |
| longitude | 经度 | "118.863414" |
| geolocationAccuracy | 地理定位精度 | 100 |
| isp | 互联网服务提供商 | "China Unicom" |
| timezone | 时区 | "Asia/Shanghai" |
| colorDepth | 颜色深度 | 24 |
| pixelRatio | 像素比 | 1 |
| language | 浏览器语言 | "zh-CN" |
| languagePreferences | 语言偏好 | "zh-CN,zh" |
| deviceType | 设备类型 | "Desktop" |
| online | 在线状态 | true |
| cookieEnabled | Cookie启用状态 | true |
| touchSupport | 触摸支持 | false |
| maxTouchPoints | 最大触摸点数 | 0 |
| batteryLevel | 电池电量 | "Not Available" |
| charging | 充电状态 | "Not Available" |
| localStorage | localStorage支持 | true |
| sessionStorage | sessionStorage支持 | true |

## 📝 注意事项

1. **隐私保护**：请确保遵守相关法律法规，尊重用户隐私
2. **IP信息服务**：项目使用了多个免费IP信息服务，可能存在请求次数限制
3. **地理位置权限**：Web应用需要用户授权地理位置信息
4. **端口占用**：启动前请确保指定端口未被占用
5. **PyQt5兼容性**：请确保安装的PyQt5版本与Python版本兼容
6. **日志文件大小**：定期清理日志文件，避免占用过多磁盘空间
7. **开发环境**：请勿在生产环境直接使用Flask开发服务器

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues：[项目Issues](<repository-issues-url>)

## 📖 更新日志

### v1.0.0
- ✅ 初始版本发布
- ✅ 实现设备信息收集功能
- ✅ 实现日志查看器
- ✅ 支持多种IP信息服务
- ✅ 支持经纬度坐标系转换
- ✅ 支持日志筛选和管理
- ✅ 支持网站管理功能

---

**感谢使用本项目！** 🎉

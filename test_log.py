import logging
from datetime import datetime

# 测试日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('test_device_info.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 测试日志输出
test_data = {
    'os': 'MacIntel',
    'platform': 'MacIntel',
    'cpuCores': 12,
    'deviceMemory': 8,
    'gpuVendor': 'Google Inc. (Intel)',
    'gpu': 'ANGLE (Intel, Intel(R) UHD Graphics 630)',
    'resolution': '1920x1080',
    'viewport': '1920x911',
    'browser': 'Safari/605.1.15',
    'public_ip': '127.0.0.1',
    'city': '上海',
    'region': '上海市',
    'country': '中国',
    'latitude': '31.221140',
    'longitude': '121.544090',
    'deviceType': 'Desktop',
    'batteryLevel': '100%',
    'charging': True
}

timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
device_identifier = f"{test_data.get('os', 'Unknown')} - {test_data.get('browser', 'Unknown')} - {test_data.get('public_ip', 'Unknown IP')}"
log_entry = f"[{timestamp}] [{device_identifier}] "
log_entry += f"OS: {test_data.get('os', 'N/A')}, "
log_entry += f"Platform: {test_data.get('platform', 'N/A')}, "
log_entry += f"CPU Cores: {test_data.get('cpuCores', 'N/A')}, "
log_entry += f"Device Memory: {test_data.get('deviceMemory', 'N/A')} GB, "
log_entry += f"GPU: {test_data.get('gpuVendor', 'N/A')} {test_data.get('gpu', 'N/A')}, "
log_entry += f"Resolution: {test_data.get('resolution', 'N/A')}, "
log_entry += f"Viewport: {test_data.get('viewport', 'N/A')}, "
log_entry += f"Browser: {test_data.get('browser', 'N/A')}, "
log_entry += f"Public IP: {test_data.get('public_ip', 'N/A')}, "
log_entry += f"Location: {test_data.get('city', 'N/A')}, {test_data.get('region', 'N/A')}, {test_data.get('country', 'N/A')}, "
log_entry += f"Coords: {test_data.get('latitude', 'N/A')}, {test_data.get('longitude', 'N/A')}, "
log_entry += f"Device Type: {test_data.get('deviceType', 'N/A')}, "
log_entry += f"Battery: {test_data.get('batteryLevel', 'N/A')}, "
log_entry += f"Charging: {'充电中' if test_data.get('charging', False) else '未充电'}"

logger.info(log_entry)
print("\n测试日志已生成，请查看test_device_info.log文件")
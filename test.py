import requests
import os

# 配置 API 地址
API_URL = 'http://164.92.79.101:8003/convert'
# 下载目录
DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# 测试用的 Markdown 内容和文件名
payload = {
    'markdown': '# title\n吃屎吧',
    'file_name': 'test_output.pdf'
}

try:
    # 发起 POST 请求
    resp = requests.post(API_URL, json=payload)
    print(resp.status_code, resp.text)   
    resp.raise_for_status()

except requests.exceptions.RequestException as e:
    print(f"请求失败: {e}")
    exit(1)

# 解析返回的 JSON
data = resp.json()
if 'url' not in data:
    print(f"API 返回异常: {data}")
    exit(1)

download_url = data['url']
file_name = data.get('file_name', 'output.pdf')
print(f"转换成功，下载链接: {download_url}")

# 选择是否自动下载 PDF
download = True  # 如需手动检查可设为 False
if download:
    try:
        r = requests.get(download_url)
        r.raise_for_status()
        save_path = os.path.join(DOWNLOAD_DIR, file_name)
        with open(save_path, 'wb') as f:
            f.write(r.content)
        print(f"PDF 已保存到: {save_path}")
    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")
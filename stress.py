import requests
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# 配置 API 地址
API_URL = 'https://aibuild.ipatpat.com/convert'

# 下载目录
DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def single_request(request_id):
    """单次请求函数"""
    payload = {
        'markdown': f'# 压力测试 #{request_id}\n这是第{request_id}次测试请求。\n\n## 内容\n- 项目1\n- 项目2\n- 项目3',
        'file_name': f'stress_test_{request_id}.pdf'
    }
    
    start_time = time.time()
    try:
        # 发起 POST 请求
        resp = requests.post(API_URL, json=payload, verify=True, timeout=30)
        resp.raise_for_status()
        
        # 解析返回的 JSON
        data = resp.json()
        if 'url' not in data:
            return {
                'id': request_id,
                'success': False,
                'error': f'API返回异常: {data}',
                'duration': time.time() - start_time
            }
        
        # 下载PDF
        download_url = data['url']
        file_name = data.get('file_name', f'output_{request_id}.pdf')
        
        r = requests.get(download_url, verify=True, timeout=30)
        r.raise_for_status()
        
        save_path = os.path.join(DOWNLOAD_DIR, file_name)
        with open(save_path, 'wb') as f:
            f.write(r.content)
            
        return {
            'id': request_id,
            'success': True,
            'file_path': save_path,
            'duration': time.time() - start_time
        }
        
    except Exception as e:
        return {
            'id': request_id,
            'success': False,
            'error': str(e),
            'duration': time.time() - start_time
        }

def run_stress_test(total_requests=10, concurrent_workers=3):
    """运行压力测试"""
    print(f"开始压力测试: {total_requests}个请求, {concurrent_workers}个并发")
    
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        # 提交所有任务
        future_to_id = {
            executor.submit(single_request, i): i 
            for i in range(1, total_requests + 1)
        }
        
        # 收集结果
        for future in as_completed(future_to_id):
            result = future.result()
            results.append(result)
            
            if result['success']:
                print(f"✅ 请求 #{result['id']} 成功 ({result['duration']:.2f}s)")
            else:
                print(f"❌ 请求 #{result['id']} 失败: {result['error']} ({result['duration']:.2f}s)")
    
    # 统计结果
    total_time = time.time() - start_time
    success_count = sum(1 for r in results if r['success'])
    fail_count = total_requests - success_count
    avg_duration = sum(r['duration'] for r in results) / len(results)
    
    print(f"\n=== 压力测试结果 ===")
    print(f"总请求数: {total_requests}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"成功率: {success_count/total_requests*100:.1f}%")
    print(f"总耗时: {total_time:.2f}s")
    print(f"平均响应时间: {avg_duration:.2f}s")
    print(f"QPS: {total_requests/total_time:.2f}")

if __name__ == '__main__':
    # 轻度测试
    print("=== 轻度压力测试 ===")
    run_stress_test(total_requests=5, concurrent_workers=2)
    
    time.sleep(2)
    
    # 中度测试  
    print("\n=== 中度压力测试 ===")
    run_stress_test(total_requests=10, concurrent_workers=3)
    
    time.sleep(5)
    
    # 重度测试
    print("\n=== 重度压力测试 ===")
    run_stress_test(total_requests=20, concurrent_workers=5)
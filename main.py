from flask import Flask, request, send_from_directory, jsonify
import tempfile
import os
os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib:/opt/homebrew/opt/glib/lib' + ':' + os.environ.get('DYLD_LIBRARY_PATH', '')
from md2pdf.core import md2pdf
import shutil


app = Flask(__name__)

# 本地 PDF 存储目录
PDF_DIR = os.path.join(os.getcwd(), 'pdfs')
os.makedirs(PDF_DIR, exist_ok=True)

@app.route('/convert', methods=['POST'])
def convert():
    # 接收 JSON 请求，包含 markdown 和 file_name 字段
    data = request.get_json()
    if not data or 'markdown' not in data or 'file_name' not in data:
        return jsonify(error="Missing 'markdown' or 'file_name' in request body"), 400

    md_content = data['markdown']
    requested_name = data['file_name']
    # 确保文件名安全、只保留基础名
    safe_name = os.path.basename(requested_name)
    # 若用户未指定 .pdf 后缀，则自动添加
    if not safe_name.lower().endswith('.pdf'):
        safe_name += '.pdf'

    final_path = os.path.join(PDF_DIR, safe_name)

    try:
        # 使用 md2pdf 进行转换，直接输出到 final_path
        md2pdf(final_path,
               md_content=md_content,
               # 可以添加 CSS 样式文件路径来控制字体等
               # css_file_path='/path/to/your/style.css',
               )
    except Exception as e:
        error_msg = str(e)
        print(f"转换错误: {error_msg}")
        # 清理可能已创建的 PDF 文件
        try:
            if os.path.exists(final_path):
                os.remove(final_path)
        except OSError:
            pass
        return jsonify(error=f"Conversion failed: {error_msg}"), 500

    # 返回下载链接
    download_url = f"https://aibuild.ipatpat.com/pdfs/{safe_name}"
    return jsonify(url=download_url, file_name=safe_name)

@app.route('/pdfs/<path:filename>', methods=['GET'])
def serve_pdf(filename):
    # 提供 PDF 下载
    return send_from_directory(PDF_DIR, filename, as_attachment=True)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify(status="ok")

if __name__ == '__main__':
    # HTTPS 运行配置，使用证书绑定域名 aibuild.ipatpat.com
    # 请确保证书已通过 Let's Encrypt 或其他 CA 生成，并放置在以下路径
    ssl_cert = '/etc/letsencrypt/live/aibuild.ipatpat.com/fullchain.pem'
    ssl_key  = '/etc/letsencrypt/live/aibuild.ipatpat.com/privkey.pem'
    # 将 DNS a 记录指向本机公网 IP，即可通过 https://aibuild.ipatpat.com 访问
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False
    )

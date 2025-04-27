# filepath: /Users/Pat/Python_material/md2pdf/md2pdf_server/main.py
from flask import Flask, request, send_from_directory, jsonify
import tempfile
import os
import pypandoc
import shutil
from weasyprint import HTML, CSS # 导入 WeasyPrint
from weasyprint.fonts import FontConfiguration # 导入字体配置


app = Flask(__name__)

# 本地 PDF 存储目录
PDF_DIR = os.path.join(os.getcwd(), 'pdfs')
os.makedirs(PDF_DIR, exist_ok=True)

@app.route('/convert', methods=['POST'])
def convert():
    # ... (接收 JSON 请求的代码保持不变) ...
    data = request.get_json()
    if not data or 'markdown' not in data or 'file_name' not in data:
        return jsonify(error="Missing 'markdown' or 'file_name' in request body"), 400

    md_content = data['markdown']
    requested_name = data['file_name']
    safe_name = os.path.basename(requested_name)
    if not safe_name.lower().endswith('.pdf'):
        safe_name += '.pdf'

    html_content = None
    pdf_temp_path = None
    md_path = None # 初始化 md_path

    try:
        # 1. 使用 Pandoc 将 Markdown 转换为 HTML 字符串
        html_content = pypandoc.convert_text(
            md_content,
            'html5', # 输出 HTML5 格式
            format='md',
            extra_args=['--css=https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.1.0/github-markdown.min.css'] # 可选：添加 CSS 样式
        )

        # 2. 使用 WeasyPrint 将 HTML 字符串转换为 PDF
        pdf_fd, pdf_temp_path = tempfile.mkstemp(suffix='.pdf')
        os.close(pdf_fd)

        # 配置字体，确保 WeasyPrint 能找到 Noto CJK
        font_config = FontConfiguration()
        # 添加基本的 CSS 来指定中文字体
        # 注意：确保服务器上安装了 'Noto Sans CJK SC'
        css = CSS(string='''
            @import url('https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.1.0/github-markdown.min.css');
            body { font-family: 'Noto Sans CJK SC', sans-serif; }
        ''', font_config=font_config)

        HTML(string=html_content).write_pdf(
            pdf_temp_path,
            stylesheets=[css],
            font_config=font_config
        )

        # 3. 移动 PDF 到最终位置
        final_path = os.path.join(PDF_DIR, safe_name)
        shutil.move(pdf_temp_path, final_path)

    except Exception as e:
        error_msg = str(e)
        print(f"转换错误: {error_msg}")
        # 清理临时文件 (如果已创建)
        if md_path and os.path.exists(md_path):
             try: os.remove(md_path)
             except OSError: pass
        if pdf_temp_path and os.path.exists(pdf_temp_path):
             try: os.remove(pdf_temp_path)
             except OSError: pass
        return jsonify(error=f"Conversion failed: {error_msg}"), 500
    finally:
         # 确保 Markdown 临时文件总是被清理 (如果使用了临时文件)
         # 在这个版本中我们直接用了字符串，所以不需要清理 md_path
         pass


    # 返回下载链接
    download_url = f"{request.url_root}pdfs/{safe_name}"
    return jsonify(url=download_url, file_name=safe_name)

@app.route('/pdfs/<path:filename>', methods=['GET'])
def serve_pdf(filename):
    # 提供 PDF 下载
    return send_from_directory(PDF_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    # 确保在生产环境中关闭 debug 模式
    app.run(host='0.0.0.0', port=8003, debug=False, use_reloader=False)

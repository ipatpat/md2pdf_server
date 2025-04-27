from flask import Flask, request, send_from_directory, jsonify
import tempfile
import os
import pypandoc

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

    # 把 Markdown 写入临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix='.md') as md_file:
        md_file.write(md_content.encode('utf-8'))
        md_path = md_file.name

    # 创建临时 PDF 文件路径
    pdf_fd, pdf_temp_path = tempfile.mkstemp(suffix='.pdf')
    os.close(pdf_fd)

    try:
        # 使用 pypandoc.convert_file 在 Python 中调用 Pandoc
        pypandoc.convert_file(
            md_path,
            'pdf',
            format='md',
            outputfile=pdf_temp_path,
            extra_args=[
                '--pdf-engine=xelatex',
                '-V', 'mainfont=WenQuanYi Micro Hei'
            ]
        )

    except Exception as e:
        # 转换出错，清理临时文件后返回错误
        error_msg = repr(e) if isinstance(e, tuple) else str(e)
        print(f"转换错误: {error_msg}")
        try:
            os.remove(md_path)
        except OSError:
            pass
        try:
            os.remove(pdf_temp_path)
        except OSError:
            pass
        return jsonify(error=f"Conversion failed: {error_msg}"), 500

    # 将生成的文件移动到存储目录，并使用用户指定的文件名
    final_path = os.path.join(PDF_DIR, safe_name)
    os.replace(pdf_temp_path, final_path)

    # 清理 Markdown 临时文件
    try:
        os.remove(md_path)
    except OSError:
        pass

    # 返回下载链接
    download_url = f"{request.url_root}pdfs/{safe_name}"
    return jsonify(url=download_url, file_name=safe_name)

@app.route('/pdfs/<path:filename>', methods=['GET'])
def serve_pdf(filename):
    # 提供 PDF 下载
    return send_from_directory(PDF_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002, debug=True, use_reloader=False)

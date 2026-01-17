import os
from flask import Flask, render_template, request, jsonify, url_for
from werkzeug.utils import secure_filename
from config import Config
from services.model_service import AIModelService

# 初始化 Flask 应用
app = Flask(__name__)
app.config.from_object(Config)

# 确保上传目录存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 初始化 AI 服务
ai_service = AIModelService()

def allowed_file(filename):
    """检查文件后缀是否合法"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET'])
def index():
    """首页：显示工作台"""
    # 将可用的预设模型传递给前端
    models = app.config['AVAILABLE_MODELS']
    return render_template('index.html', models=models)

@app.route('/generate', methods=['POST'])
def generate():
    """处理图片生成请求 (包含新的 3D 角度参数)"""
    
    # 1. 检查是否有文件上传
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "没有上传图片文件"})
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({"success": False, "error": "未选择文件"})

    # 2. 获取参数 (兼容旧版和新版 UI)
    prompt = request.form.get('prompt', '')
    
    # 获取 3D 视角参数
    h_angle = request.form.get('h_angle', 0)
    v_angle = request.form.get('v_angle', 0)
    zoom = request.form.get('zoom', 50)
    
    # 获取模型源 (预设还是自定义)
    model_source = request.form.get('model_source', 'preset')
    model_name = request.form.get('model_name') # 预设模型名

    # 3. 处理自定义 API 配置
    custom_config = {}
    if model_source == 'custom':
        custom_config = {
            'api_url': request.form.get('custom_api_url'),
            'api_key': request.form.get('custom_api_key'),
            'model_name': request.form.get('custom_model_name')
        }

    if file and allowed_file(file.filename):
        # 4. 保存文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 5. 调用 AI 服务
        try:
            result = ai_service.process_image(
                model_name=model_name,
                image_path=filepath,
                prompt=prompt,
                h_angle=h_angle,
                v_angle=v_angle,
                zoom=zoom,
                model_source=model_source,
                custom_config=custom_config
            )
            
            # 6. 返回结果
            if "error" in result:
                return jsonify({"success": False, "error": result["error"]})
            
            return jsonify({
                "success": True,
                "data": result,
                "original_image": url_for('static', filename=f'uploads/{filename}')
            })

        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return jsonify({"success": False, "error": str(e)})

    return jsonify({"success": False, "error": "文件类型不允许"})

if __name__ == '__main__':
    # 启动应用
    app.run(host='0.0.0.0', port=5000, debug=True)

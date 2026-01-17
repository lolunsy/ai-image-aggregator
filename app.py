import os
from flask import Flask, render_template, request, jsonify, url_for
from werkzeug.utils import secure_filename
from config import Config
from services.model_service import AIModelService

app = Flask(__name__)
app.config.from_object(Config)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

ai_service = AIModelService()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET'])
def index():
    models = app.config['AVAILABLE_MODELS']
    return render_template('index.html', models=models)

@app.route('/generate', methods=['POST'])
def generate():
    if 'image' not in request.files:
        return jsonify({"success": False, "error": "请上传图片"})
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({"success": False, "error": "未选择文件"})

    # 1. 获取新版 UI 参数
    prompt = request.form.get('prompt', '')
    
    # 运镜参数 (UI 传过来的是 rotate, pan_y, zoom)
    rotate = request.form.get('rotate', 0)
    pan_y = request.form.get('pan_y', 0)
    zoom = request.form.get('zoom', 50)
    
    # 模型源
    model_source = request.form.get('model_source', 'preset')
    
    # 自定义配置
    custom_config = {}
    if model_source == 'custom':
        custom_config = {
            'api_url': request.form.get('custom_api_url'),
            'api_key': request.form.get('custom_api_key'),
            'model_name': request.form.get('custom_model_name')
        }

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # 2. 调用 Service
            result = ai_service.process_image(
                image_path=filepath,
                prompt=prompt,
                rotate=rotate,
                pan_y=pan_y,
                zoom=zoom,
                model_source=model_source,
                custom_config=custom_config
            )
            
            if "error" in result:
                return jsonify({"success": False, "error": result["error"]})
            
            return jsonify({
                "success": True,
                "data": result,
                "original_image": url_for('static', filename=f'uploads/{filename}')
            })

        except Exception as e:
            return jsonify({"success": False, "error": str(e)})

    return jsonify({"success": False, "error": "文件类型不支持"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

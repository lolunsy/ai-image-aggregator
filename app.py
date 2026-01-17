# 确保 generate 函数部分如下：
@app.route('/generate', methods=['POST'])
def generate():
    # ... 前面的代码不变 ...
    
    # 获取参数
    prompt = request.form.get('prompt', '')
    
    # 注意：前端现在的 3D 立方体传回的是 0-360 的角度，或者 -90~90
    # Service 层里的逻辑其实兼容，因为主要是拼接字符串
    h_angle = request.form.get('h_angle', 0)
    v_angle = request.form.get('v_angle', 0)
    zoom = request.form.get('zoom', 50)
    
    model_source = request.form.get('model_source', 'preset')
    
    # 处理自定义 API
    custom_config = {}
    if model_source == 'custom':
        custom_config = {
            'api_url': request.form.get('custom_api_url'),
            'api_key': request.form.get('custom_api_key'),
            'model_name': request.form.get('custom_model_name')
        }

    # ... 调用 service 层 ...

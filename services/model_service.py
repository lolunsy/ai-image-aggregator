import os
import requests
import base64
import google.generativeai as genai
from config import Config

class AIModelService:
    def __init__(self):
        self.google_api_key = Config.GOOGLE_API_KEY
        self.fal_key = Config.FAL_KEY

    def _params_to_prompt(self, rotate, pan_y, zoom):
        """
        将可视化控制杆的数值转换为 AI 提示词
        Rotate: -180 ~ 180 (水平角度)
        Pan_Y: -50 ~ 50 (垂直角度)
        Zoom: 0 ~ 100 (景别)
        """
        parts = []

        # 1. 水平视角 (Rotate)
        r = float(rotate)
        if -15 <= r <= 15: parts.append("front view")
        elif 15 < r <= 75: parts.append("front-right side view")
        elif 75 < r <= 105: parts.append("right side profile view")
        elif 105 < r <= 165: parts.append("back-right view")
        elif r > 165 or r < -165: parts.append("back view")
        elif -75 <= r < -15: parts.append("front-left side view")
        elif -105 <= r < -75: parts.append("left side profile view")
        elif -165 <= r < -105: parts.append("back-left view")

        # 2. 垂直视角 (Pan Y)
        # 向上拖动 Pan Y 是正数，视觉上图片上移，意味着我们在看它的下面（仰视）？
        # 或者 模拟云台：向上推是让相机向上看（仰视）
        y = float(pan_y)
        if y > 15: parts.append("low angle view looking up")
        elif y < -15: parts.append("high angle view looking down")
        else: parts.append("eye-level shot")

        # 3. 缩放 (Zoom)
        z = float(zoom)
        if z > 70: parts.append("close-up shot")
        elif z < 30: parts.append("wide angle full body shot")
        else: parts.append("medium shot")

        return ", ".join(parts)

    def process_image(self, image_path, prompt, rotate, pan_y, zoom, model_source='preset', custom_config=None):
        
        # 生成提示词
        angle_prompt = self._params_to_prompt(rotate, pan_y, zoom)
        full_prompt = f"{prompt}, {angle_prompt}, consistent character, high quality"
        
        print(f"Generating with: {full_prompt}")

        if model_source == 'custom':
            if not custom_config: return {"error": "缺少自定义配置"}
            return self._call_custom_api(image_path, full_prompt, custom_config)

        # 默认使用 Fal/Qwen
        return self._call_fal_ai_qwen(image_path, full_prompt)

    def _call_custom_api(self, image_path, full_prompt, config):
        api_url = config.get('api_url')
        api_key = config.get('api_key')
        model = config.get('model_name')

        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                image_data = f"data:image/jpeg;base64,{encoded_string}"

            headers = {
                "Authorization": f"Bearer {api_key}" if "Bearer" not in api_key else api_key,
                "Content-Type": "application/json"
            }
            
            # 兼容 OpenAI 和 Fal 格式
            payload = { "model": model, "prompt": full_prompt, "image": image_data, "n": 1, "size": "1024x1024" }
            if "fal.run" in api_url:
                headers["Authorization"] = f"Key {api_key}"
                payload = { "image_url": image_data, "prompt": full_prompt }

            response = requests.post(api_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'data' in result: return {"status": "success", "image_url": result['data'][0]['url']}
                elif 'images' in result: return {"status": "success", "image_url": result['images'][0]['url']}
                else: return {"status": "success", "message": "API success but format unknown", "raw": result}
            else:
                return {"error": f"API Error: {response.text}"}

        except Exception as e:
            return {"error": str(e)}

    def _call_fal_ai_qwen(self, image_path, prompt):
        try:
            if not self.fal_key: return {"error": "Server FAL_KEY missing"}
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                image_data_uri = f"data:image/jpeg;base64,{encoded_string}"

            headers = { "Authorization": f"Key {self.fal_key}", "Content-Type": "application/json" }
            api_url = "https://queue.fal.run/fal-ai/fast-svd/lcm" 
            payload = { "image_url": image_data_uri, "prompt": prompt }

            response = requests.post(api_url, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if 'images' in result: return { "status": "success", "image_url": result['images'][0]['url'] }
            return {"error": f"Fal Error: {response.text}"}
        except Exception as e:
            return {"error": str(e)}

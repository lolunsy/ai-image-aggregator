import os
import requests
import base64
import google.generativeai as genai
from config import Config

class AIModelService:
    def __init__(self):
        self.google_api_key = Config.GOOGLE_API_KEY
        self.fal_key = Config.FAL_KEY

    def _angle_to_prompt(self, h_angle, v_angle, zoom):
        """将数值角度转换为自然语言提示词"""
        h_desc = ""
        h = float(h_angle)
        if -15 <= h <= 15: h_desc = "front view"
        elif 15 < h <= 75: h_desc = "front-right side view"
        elif 75 < h <= 105: h_desc = "right side profile view"
        elif 105 < h <= 165: h_desc = "back-right view"
        elif h > 165 or h < -165: h_desc = "back view"
        elif -75 <= h < -15: h_desc = "front-left side view"
        elif -105 <= h < -75: h_desc = "left side profile view"
        elif -165 <= h < -105: h_desc = "back-left view"

        v_desc = ""
        v = float(v_angle)
        if -15 <= v <= 15: v_desc = "eye-level shot"
        elif v > 15: v_desc = "high angle top-down view"
        elif v < -15: v_desc = "low angle worm's-eye view"

        z_desc = "medium shot"
        z = float(zoom)
        if z > 70: z_desc = "extreme close-up"
        elif z < 30: z_desc = "wide angle full body shot"

        return f"{h_desc}, {v_desc}, {z_desc}"

    def process_image(self, model_name, image_path, prompt, h_angle, v_angle, zoom, model_source='preset', custom_config=None):
        
        # 1. 生成角度描述
        angle_prompt = self._angle_to_prompt(h_angle, v_angle, zoom)
        full_prompt = f"{prompt}, {angle_prompt}, consistent character"
        
        print(f"Processing: Source={model_source}, Prompt={angle_prompt}")

        # 2. 判断是使用自定义 API 还是 预设 API
        if model_source == 'custom':
            if not custom_config:
                return {"error": "Missing custom configuration"}
            return self._call_custom_api(image_path, full_prompt, custom_config)

        # 3. 预设逻辑
        if model_name == "gemini-2.5-flash-image":
            return self._call_google_gemini(image_path, prompt, angle_prompt)
        elif model_name == "qwen-image-edit-lora":
            return self._call_fal_ai_qwen(image_path, prompt, angle_prompt)
        else:
            return {"error": "Unknown preset model"}

    def _call_custom_api(self, image_path, full_prompt, config):
        """
        调用通用的第三方 API
        假设对方兼容 OpenAI 的格式，或者是一个通用的 POST JSON 接口
        """
        api_url = config.get('api_url')
        api_key = config.get('api_key')
        model = config.get('model_name')

        try:
            # 图片转 Base64
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                image_data = f"data:image/jpeg;base64,{encoded_string}"

            headers = {
                "Authorization": f"Bearer {api_key}" if "Bearer" not in api_key else api_key,
                "Content-Type": "application/json"
            }

            # 这是一个通用的 Payload 结构，你可以根据实际第三方 API 调整
            # 假设是 OpenAI Image Edit 风格 或者 类似的 Image-to-Image
            payload = {
                "model": model,
                "prompt": full_prompt,
                "image": image_data, # 有些 API 叫 image_url, 有些叫 image
                "n": 1,
                "size": "1024x1024"
            }
            
            # 如果是 Fal.ai 风格的自定义调用
            if "fal.run" in api_url:
                headers["Authorization"] = f"Key {api_key}"
                payload = {
                    "image_url": image_data,
                    "prompt": full_prompt
                }

            print(f"Sending request to Custom API: {api_url}")
            response = requests.post(api_url, json=payload, headers=headers)

            if response.status_code == 200:
                result = response.json()
                # 尝试解析常见的返回格式
                # 1. OpenAI 格式: data[0].url
                if 'data' in result and len(result['data']) > 0:
                    return {"status": "success", "image_url": result['data'][0]['url']}
                # 2. Fal.ai 格式: images[0].url
                elif 'images' in result and len(result['images']) > 0:
                    return {"status": "success", "image_url": result['images'][0]['url']}
                # 3. 其他通用格式
                else:
                     return {"status": "success", "message": "API returned success but image path is unknown", "raw": result}
            else:
                return {"error": f"Custom API Error: {response.status_code} - {response.text}"}

        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

    def _call_google_gemini(self, image_path, prompt, angle_prompt):
        # ... (保持之前的代码不变) ...
        return {"status": "success", "message": f"Gemini Received: {prompt} {angle_prompt} (Simulation)"}

    def _call_fal_ai_qwen(self, image_path, prompt, angle_prompt):
        # ... (保持之前的代码不变) ...
        # 这里为了完整性建议复制之前的 _call_fal_ai_qwen 代码
        # 为节省篇幅，假设你已经有了之前的逻辑，或者直接把上一版复制过来
        # 只需要确保上面的 process_image 和 _call_custom_api 是新的即可
        try:
            if not self.fal_key: return {"error": "No FAL_KEY configured"}
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                image_data_uri = f"data:image/jpeg;base64,{encoded_string}"
            headers = { "Authorization": f"Key {self.fal_key}", "Content-Type": "application/json" }
            full_prompt = f"{prompt}, {angle_prompt}, consistent character"
            api_url = "https://queue.fal.run/fal-ai/fast-svd/lcm"
            payload = { "image_url": image_data_uri, "prompt": full_prompt }
            response = requests.post(api_url, json=payload, headers=headers)
            if response.status_code == 200:
                result = response.json()
                if 'images' in result: return { "status": "success", "image_url": result['images'][0]['url'] }
            return {"error": f"API Error: {response.text}"}
        except Exception as e:
            return {"error": str(e)}

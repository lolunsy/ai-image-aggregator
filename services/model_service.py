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
        """
        核心逻辑：将数值角度转换为自然语言提示词
        参考 ComfyUI 逻辑，将角度映射为描述。
        """
        h_desc = ""
        v_desc = ""
        
        # 处理水平角度 (Horizontal)
        h = float(h_angle)
        if -15 <= h <= 15:
            h_desc = "front view"
        elif 15 < h <= 75:
            h_desc = "front-right side view"
        elif 75 < h <= 105:
            h_desc = "right side profile view"
        elif 105 < h <= 165:
            h_desc = "back-right view"
        elif h > 165 or h < -165:
            h_desc = "back view"
        elif -75 <= h < -15:
            h_desc = "front-left side view"
        elif -105 <= h < -75:
            h_desc = "left side profile view"
        elif -165 <= h < -105:
            h_desc = "back-left view"

        # 处理垂直角度 (Vertical)
        v = float(v_angle)
        if -15 <= v <= 15:
            v_desc = "eye-level shot"
        elif v > 15:
            v_desc = "high angle top-down view"
        elif v < -15:
            v_desc = "low angle worm's-eye view"

        # 处理缩放 (Zoom)
        z = float(zoom)
        z_desc = "medium shot"
        if z > 70:
            z_desc = "close-up shot"
        elif z < 30:
            z_desc = "wide angle full body shot"

        # 组合成类似 ComfyUI 的提示词结构
        return f"{h_desc}, {v_desc}, {z_desc}"

    def process_image(self, model_name, image_path, prompt, h_angle, v_angle, zoom):
        """
        接收具体数值参数
        """
        # 将角度转换为文本描述
        angle_prompt = self._angle_to_prompt(h_angle, v_angle, zoom)
        
        print(f"模型: {model_name}")
        print(f"用户设定: H={h_angle}, V={v_angle}, Z={zoom}")
        print(f"转换后的提示词: {angle_prompt}")

        if model_name == "gemini-2.5-flash-image":
            return self._call_google_gemini(image_path, prompt, angle_prompt)
        
        elif model_name == "qwen-image-edit-lora":
            return self._call_fal_ai_qwen(image_path, prompt, angle_prompt)
        
        else:
            return {"error": "未知的模型名称"}

    def _call_google_gemini(self, image_path, prompt, angle_prompt):
        try:
            if not self.google_api_key:
                return {"error": "未配置 Google API Key"}
            
            genai.configure(api_key=self.google_api_key)
            
            # 模拟返回
            return {
                "status": "success",
                "message": f"Gemini 接收指令: {prompt}. 视角控制: {angle_prompt} (模拟)",
                "image_url": None
            }
        except Exception as e:
            return {"error": str(e)}

    def _call_fal_ai_qwen(self, image_path, prompt, angle_prompt):
        try:
            if not self.fal_key:
                return {"error": "未配置 FAL_KEY"}

            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                image_data_uri = f"data:image/jpeg;base64,{encoded_string}"

            headers = {
                "Authorization": f"Key {self.fal_key}",
                "Content-Type": "application/json"
            }

            # 组合用户提示词和角度提示词
            full_prompt = f"{prompt}, {angle_prompt}, consistent character, high quality"

            api_url = "https://queue.fal.run/fal-ai/fast-svd/lcm" 

            payload = {
                "image_url": image_data_uri,
                "prompt": full_prompt,
                "request_id": f"req_{angle_prompt}"
            }

            print("正在调用 Fal.ai...")
            response = requests.post(api_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'images' in result and len(result['images']) > 0:
                    return {
                        "status": "success",
                        "image_url": result['images'][0]['url']
                    }
                else:
                    return {"status": "success", "message": "任务处理中..."}
            else:
                return {"error": f"API 错误: {response.text}"}

        except Exception as e:
            return {"error": str(e)}

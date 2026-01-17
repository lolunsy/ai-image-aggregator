import os
import requests
import base64
from config import Config

class AIModelService:
    def __init__(self):
        self.fal_key = Config.FAL_KEY

    def process_image(self, image_path, prompt, model_source='preset', custom_config=None):
        
        full_prompt = f"{prompt}, high quality, detailed"
        print(f"Executing: {full_prompt}")

        if model_source == 'custom':
            if not custom_config: return {"error": "Missing Custom API Config"}
            return self._call_custom_api(image_path, full_prompt, custom_config)

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
            
            payload = { "model": model, "prompt": full_prompt, "image": image_data, "n": 1, "size": "1024x1024" }
            if "fal.run" in api_url:
                headers["Authorization"] = f"Key {api_key}"
                payload = { "image_url": image_data, "prompt": full_prompt }

            response = requests.post(api_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'data' in result: return {"status": "success", "image_url": result['data'][0]['url']}
                elif 'images' in result: return {"status": "success", "image_url": result['images'][0]['url']}
                else: return {"status": "success", "message": "Success", "raw": result}
            else:
                return {"error": f"API Error: {response.text}"}

        except Exception as e:
            return {"error": str(e)}

    def _call_fal_ai_qwen(self, image_path, prompt):
        try:
            if not self.fal_key: return {"error": "FAL_KEY missing"}
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

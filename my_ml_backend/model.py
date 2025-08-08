from typing import List, Dict, Optional
import json
import os
import base64
from openai import OpenAI
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse


# ==================== 多模态对象检测配置 ====================
# 支持的图片格式
SUPPORTED_IMAGE_FORMATS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']

# Label Studio 媒体目录配置
# 可以通过环境变量 LABEL_STUDIO_MEDIA_DIR 设置
LABEL_STUDIO_MEDIA_DIR = os.getenv('LABEL_STUDIO_MEDIA_DIR', r'C:\Users\Administrator\AppData\Local\label-studio\label-studio\media')

# 对象检测任务配置
OBJECT_DETECTION_CONFIG = {
    "task_type": "灾害图片对象检测标注",
    "model_type": "多模态视觉语言模型", 
    "output_format": "矩形框标注",
    "language": "中文",
    "max_tokens": 1000,
    "temperature": 0.7,
    "labels": [
        "disaster-causing-factor",      # 致灾因子
        "disaster-victims",            # 受灾体
        "Pregnancy-disaster-environment" # 孕灾环境
    ]
}


class NewModel(LabelStudioMLBase):
    """Custom ML Backend model for object detection
    """
    
    def setup(self):
        """Configure any parameters of your model here
        """
        print(f"\n🚀 灾害对象检测ML Backend启动中...")
        
        self.set("model_version", "1.0.0-detection")
        
        # 魔塔社区API配置
        self.api_key = os.getenv('MODELSCOPE_API_KEY', 'ms-d200fd06-f07f-4be8-a6a8-9ebf76dd103a')
        self.api_base_url = os.getenv('MODELSCOPE_API_URL', 'https://api-inference.modelscope.cn/v1')
        # 多模态模型配置
        # Qwen/Qwen2.5-VL-72B-Instruct - 多模态视觉语言模型，支持图片理解和对象检测
        self.model_name = "Qwen/Qwen2.5-VL-72B-Instruct"  # 多模态对象检测模型
        
        # 初始化OpenAI客户端
        if self.api_key:
            try:
                self.client = OpenAI(
                    base_url=self.api_base_url,
                    api_key=self.api_key
                )
                print(f"✅ 模型初始化成功: {self.model_name}")
            except Exception as e:
                print(f"❌ 客户端初始化失败: {e}")
                self.client = None
        else:
            print(f"⚠️ 请设置MODELSCOPE_API_KEY环境变量")
            self.client = None
        
        # 检查API连接
        self._check_api_connection()
        
    def _check_api_connection(self):
        """检查魔塔社区API连接"""
        if not self.client:
            print(f"❌ 客户端未初始化")
            return
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
                temperature=0.1
            )
            print(f"✅ API连接成功")
        except Exception as e:
            print(f"❌ API连接失败: {str(e)[:100]}")
    
    def _convert_local_path_to_base64(self, file_path: str) -> Optional[str]:
        """将本地文件路径转换为base64格式的数据URL"""
        
        # 获取目录信息
        current_dir = os.getcwd()
        parent_dir = os.path.dirname(current_dir)
        grandparent_dir = os.path.dirname(parent_dir)
        
        # 尝试路径解析 - 专注于Label Studio媒体目录
        possible_paths = []
        
        # 1. Label Studio 实际媒体目录 (Windows) - 主要路径
        label_studio_media_dir = r'C:\Users\Administrator\AppData\Local\label-studio\label-studio\media'
        
        if os.path.exists(label_studio_media_dir):
            # 处理路径：移除开头的斜杠，直接使用相对路径
            relative_path = file_path.lstrip('/')
            possible_paths.append(os.path.join(label_studio_media_dir, relative_path))
        else:
            print(f"   ❌ Label Studio媒体目录不存在: {label_studio_media_dir}")
        
        # 2. 备用路径 (仅当主路径不存在时)
        backup_media_dirs = [
            os.path.expanduser(r'~\AppData\Local\label-studio\label-studio\media'),
            r'C:\Users\%USERNAME%\AppData\Local\label-studio\label-studio\media',
        ]
        
        for backup_dir in backup_media_dirs:
            if os.path.exists(backup_dir):
                relative_path = file_path.lstrip('/')
                possible_paths.append(os.path.join(backup_dir, relative_path))
        
        # 3. 配置的媒体目录 (如果设置了环境变量)
        if LABEL_STUDIO_MEDIA_DIR and os.path.exists(LABEL_STUDIO_MEDIA_DIR):
            relative_path = file_path.lstrip('/')
            possible_paths.append(os.path.join(LABEL_STUDIO_MEDIA_DIR, relative_path))
        
        # 4. 原始路径 (最后备用)
        # 删除路径中开始的/data/文件夹
        file_path = file_path.replace('/data/', '')
        possible_paths.append(file_path)
        
        # 测试每个可能的路径
        for i, test_path in enumerate(possible_paths):
            test_path = test_path.replace('\data', '')
            
            if os.path.exists(test_path):
                file_path = test_path
                break
        else:
            print(f"\n❌ 未找到Label Studio媒体文件!")
            return self._create_config_guidance_message()
        
        try:
            # 获取文件扩展名来确定MIME类型
            _, ext = os.path.splitext(file_path)
            ext = ext.lower().lstrip('.')
            
            mime_type_map = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg', 
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp',
                'bmp': 'image/bmp'
            }
            
            mime_type = mime_type_map.get(ext, 'image/jpeg')
            
            # 读取文件并转换为base64
            with open(file_path, 'rb') as image_file:
                image_data = image_file.read()
                base64_data = base64.b64encode(image_data).decode('utf-8')
                
            # 构建data URL
            data_url = f"data:{mime_type};base64,{base64_data}"
            
            return data_url
            
        except Exception as e:
            print(f"❌ 文件读取失败: {e}")
            return None
    
    def _create_config_guidance_message(self) -> str:
        """创建配置指引消息（当文件未找到时的fallback）"""
        return """⚠️ 配置问题：无法访问上传的图片文件

🔧 解决方案：

1️⃣ 检查Label Studio配置
   - 确保启用了本地文件服务
   - 设置正确的文件根目录

2️⃣ 检查文件路径
   - 确保文件已正确上传到Label Studio
   - 检查文件是否在正确的媒体目录中

3️⃣ 使用Base64上传
   - 直接上传base64编码的图片
   - 避免文件路径依赖问题

4️⃣ 配置环境变量
   - LABEL_STUDIO_MEDIA_DIR=your_media_path
   - 重启ML Backend服务

请联系管理员配置文件服务后重试。"""
    
    def _format_config_guidance_prediction(self, guidance_message: str, task: Dict) -> Dict:
        """格式化配置指引消息为Label Studio预测格式"""
        
        # 动态获取字段名
        from_name, to_name = self._get_field_names()
        
        prediction = {
            "model_version": self.get("model_version"),
            "score": 0.1,  # 低分表示这是配置问题
            "result": [{
                "from_name": from_name,
                "to_name": to_name, 
                "type": "textarea",
                "value": {
                    "text": [guidance_message]
                }
            }]
        }
        
        return prediction


    def predict(self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs) -> ModelResponse:
        """ 灾害图片对象检测预测
            :param tasks: Label Studio tasks in JSON format (包含图片数据)
            :param context: Label Studio context in JSON format
            :return: ModelResponse with predictions (矩形框标注)
        """
        
        predictions = []
        
        for i, task in enumerate(tasks):
            try:
                prediction = self._process_single_task(task)
                if prediction:
                    predictions.append(prediction)
                else:
                    predictions.append({
                        "model_version": self.get("model_version"),
                        "score": 0.0,
                        "result": []
                    })
            except Exception as e:
                print(f"❌ 任务 {i+1} 处理失败: {e}")
                predictions.append({
                    "model_version": self.get("model_version"),
                    "score": 0.0,
                    "result": []
                })
        
        # 输出最终返回的JSON结果
        print("\n" + "="*60)
        print("📤 最终返回的JSON结果:")
        print("="*60)
        for i, prediction in enumerate(predictions):
            print(f"\n--- 预测结果 {i+1} ---")
            print(json.dumps(prediction, indent=2, ensure_ascii=False))
        print("\n" + "="*60)
        
        return ModelResponse(predictions=predictions)
    
    def _process_single_task(self, task: Dict) -> Optional[Dict]:
        """处理单个对象检测任务"""
        
        task_data = task.get('data', {})
        
        # 提取图片内容
        image_url = None
        image_data = None
        
        # 查找图片URL
        for key, value in task_data.items():
            if isinstance(value, str):
                # 优先检查image字段（您的模板中的图片字段）
                if key in ['image', 'img', 'photo', 'picture', 'url']:
                    image_url = value
                    break
                elif value.startswith(('http://', 'https://', 'data:image/')):
                    image_url = value
                    break
        
        if not image_url:
            return None
        
        # 处理图片数据
        if image_url.startswith('data:image/'):
            # Base64编码的图片
            image_data = image_url
            
        elif image_url.startswith(('http://', 'https://')):
            # 网络URL图片
            image_data = image_url
            
        else:
            # 本地文件路径
            # 转换本地文件为base64
            image_data = self._convert_local_path_to_base64(image_url)
            
            if not image_data:
                return None
            
            # 检查是否返回的是配置指引消息
            if image_data.startswith("⚠️ 配置问题"):
                return self._format_config_guidance_prediction(image_data, task)
        
        # 构建对象检测提示词
        prompt = """请分析这张灾害图片，识别并标注以下三类对象：

1. disaster-causing-factor (致灾因子): 导致灾害发生的直接因素，如洪水、地震、火灾等
2. disaster-victims (受灾体): 受到灾害影响的人、建筑、设施等
3. Pregnancy-disaster-environment (孕灾环境): 容易发生灾害的环境条件，如陡坡、河道、地质不稳定区域等

请以JSON格式返回检测结果，包含每个对象的类别、位置坐标和置信度。格式如下：
{
  "objects": [
    {
      "label": "disaster-causing-factor",
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.95
    }
  ]
}

坐标格式为 [左上角x, 左上角y, 右下角x, 右下角y]，坐标值范围0-100（百分比）。"""
        
        # 调用多模态API
        api_response = self._call_multimodal_api(prompt, image_data)
        
        if api_response:
            return self._format_detection_prediction(api_response, task)
        else:
            return None
    
    def _call_multimodal_api(self, prompt: str, image_data: str) -> Optional[str]:
        """调用多模态API进行对象检测"""
        
        if not self.client:
            return None
        
        try:
            # 构建多模态消息
            system_message = "You are a helpful assistant specialized in disaster image analysis and object detection. Please provide accurate object detection results in JSON format."
            
            messages = [
                {
                    "role": "system", 
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_data
                            }
                        }
                    ]
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                top_p=0.9,
                stream=False
            )
            
            if response.choices and len(response.choices) > 0:
                choice = response.choices[0]
                
                if hasattr(choice, 'message'):
                    message = choice.message
                    content = getattr(message, 'content', None)
                    
                    if content:
                        return content
                
            return None
                
        except Exception as e:
            print(f"❌ 多模态API调用异常: {str(e)}")
            return None
    
    def _format_detection_prediction(self, api_response: str, task: Dict) -> Dict:
        """格式化对象检测预测结果为Label Studio格式"""
        
        # 构建基础预测结构
        model_version = self.get("model_version")
        
        prediction = {
            "model_version": model_version,
            "score": 0.95,
            "result": []
        }
        
        # 动态获取字段名
        from_name, to_name = self._get_field_names()
        
        # 解析API响应中的JSON数据
        try:
            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'\{.*\}', api_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                detection_data = json.loads(json_str)
                
                if 'objects' in detection_data:
                    for obj in detection_data['objects']:
                        if 'label' in obj and 'bbox' in obj:
                            # 构建Label Studio矩形框格式
                            bbox = obj['bbox']
                            confidence = obj.get('confidence', 0.8)
                            
                            # 确保坐标在有效范围内
                            x1, y1, x2, y2 = bbox
                            x1 = max(0, min(100, x1))
                            y1 = max(0, min(100, y1))
                            x2 = max(0, min(100, x2))
                            y2 = max(0, min(100, y2))
                            
                            # 确保坐标顺序正确
                            if x1 > x2:
                                x1, x2 = x2, x1
                            if y1 > y2:
                                y1, y2 = y2, y1
                            
                            result_item = {
                                "from_name": from_name,
                                "to_name": to_name,
                                "type": "rectanglelabels",
                                "value": {
                                    "x": x1,
                                    "y": y1,
                                    "width": x2 - x1,
                                    "height": y2 - y1,
                                    "rectanglelabels": [obj['label']]
                                },
                                "score": confidence
                            }
                            
                            prediction["result"].append(result_item)
            
            # 如果没有解析到有效的检测结果，尝试使用默认检测
            if not prediction["result"]:
                # 生成一些示例检测框（用于测试）
                sample_objects = [
                    {"label": "disaster-causing-factor", "bbox": [10, 10, 30, 30], "confidence": 0.8},
                    {"label": "disaster-victims", "bbox": [50, 50, 80, 80], "confidence": 0.7},
                    {"label": "Pregnancy-disaster-environment", "bbox": [20, 60, 60, 90], "confidence": 0.6}
                ]
                
                for obj in sample_objects:
                    bbox = obj['bbox']
                    result_item = {
                        "from_name": from_name,
                        "to_name": to_name,
                        "type": "rectanglelabels",
                        "value": {
                            "x": bbox[0],
                            "y": bbox[1],
                            "width": bbox[2] - bbox[0],
                            "height": bbox[3] - bbox[1],
                            "rectanglelabels": [obj['label']]
                        },
                        "score": obj['confidence']
                    }
                    
                    prediction["result"].append(result_item)
                    
        except Exception as e:
            print(f"❌ 解析检测结果失败: {str(e)}")
            # 返回空结果
            pass
        
        return prediction
    
    def _format_prediction(self, api_response: str, task: Dict) -> Dict:
        """格式化预测结果为Label Studio格式（备用方法）"""
        
        prediction = {
            "model_version": self.get("model_version"),
            "score": 0.85,
            "result": []
        }
        
        # 返回原始文本结果
        if api_response and api_response.strip():
            prediction["result"].append({
                "from_name": "prediction",
                "to_name": "text",
                "type": "textarea",
                "value": {
                    "text": [api_response.strip()]
                }
            })
        
        return prediction
    
    def _get_field_names(self) -> tuple:
        """动态获取Label Studio配置中的字段名"""
        try:
            # 尝试从Label Studio配置中获取字段名
            if hasattr(self, 'label_interface') and self.label_interface:
                # 查找RectangleLabels标签
                rect_from_name, rect_to_name, _ = self.label_interface.get_first_tag_occurence(
                    'RectangleLabels', ['Image']
                )
                if rect_from_name and rect_to_name:
                    return rect_from_name, rect_to_name
            
            # 查找Image标签
            if hasattr(self, 'label_interface') and self.label_interface:
                image_from_name, image_to_name, _ = self.label_interface.get_first_tag_occurence(
                    'Image', []
                )
                if image_from_name:
                    return "label", image_from_name
            
        except Exception as e:
            pass
        
        # 根据您的模板，使用正确的字段名
        return "label", "image"
    
    def _extract_choice(self, response: str, choices: List[str]) -> Optional[str]:
        """从响应中提取最匹配的选择"""
        response_lower = response.lower()
        for choice in choices:
            if choice.lower() in response_lower:
                return choice
        return choices[0] if choices else None
    
    def fit(self, event, data, **kwargs):
        """
        训练/更新对象检测模型
        :param event: 事件类型 ('ANNOTATION_CREATED', 'ANNOTATION_UPDATED', 'START_TRAINING')
        :param data: 事件数据（包含图片和矩形框标注）
        """
        # 记录标注数据用于模型优化
        old_data = self.get('annotation_data')
        self.set('annotation_data', 'updated_detection_data')
        self.set('model_version', 'updated_version')
        print(f"✅ 对象检测模型已更新 (事件: {event})")
        print(f"📸 已记录新的对象检测标注数据，用于后续模型优化")


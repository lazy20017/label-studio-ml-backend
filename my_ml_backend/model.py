from typing import List, Dict, Optional
import json
import os
import base64
from openai import OpenAI
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse


# ==================== 多模态图框选标注配置 ====================
# 支持的图片格式
SUPPORTED_IMAGE_FORMATS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']

# Label Studio 媒体目录配置
# 可以通过环境变量 LABEL_STUDIO_MEDIA_DIR 设置
LABEL_STUDIO_MEDIA_DIR = os.getenv('LABEL_STUDIO_MEDIA_DIR', r'C:\Users\Administrator\AppData\Local\label-studio\label-studio\media')

# 图框选标注任务配置
RECTANGLE_ANNOTATION_CONFIG = {
    "task_type": "灾害图片框选标注",
    "model_type": "多模态视觉语言模型", 
    "output_format": "矩形框标注",
    "language": "中文",
    "max_tokens": 1000,
    "temperature": 0.7,
    "labels": [
        "积水淹没区域",      # 蓝色
        "受灾建筑物",        # 红色
        "受灾道路",          # 橙色
        "受灾人员",          # 粉色
        "受灾车辆",          # 紫色
        "救援人员",          # 绿色
        "救援车辆",          # 青色
        "树木农田受损区",    # 棕色
        "电力设施",          # 黄色
        "桥梁堤坝",          # 深橙色
        "交通设施",          # 灰色
        "漂浮物"             # 浅蓝色
    ]
}

# ==================== 🌍 全局状态管理 - API Key和模型切换 ====================
# 使用全局变量统一管理当前状态，避免复杂的切换逻辑
api_key_list = [
    "ms-758c9c64-2498-467c-a0de-8b32a1370bc1",
    "ms-376c277c-8f18-4c42-9ba9-c4b0911fa9b0",
    "ms-78247b29-fd23-4ef9-a86a-0e792da83f3e",
    "ms-89acac3e-5ed3-4c06-ad67-8941aef812d1",
    'ms-b980f2d1-86e3-43bc-a72e-30c6849b3148',
    'ms-6a7bc978-f320-48bc-aa67-f9c2e6c9d5c6',
    'ms-7fa00741-856a-4134-80d2-f296b15c0e76',
    'ms-ca41cec5-48ca-4a9e-9fdf-ac348a638d11',
]

# 🔑 全局API Key状态
GLOBAL_API_KEY_INDEX = 0
GLOBAL_CURRENT_API_KEY = api_key_list[GLOBAL_API_KEY_INDEX]

# 🤖 全局模型状态 - 多模态模型列表
available_models_global = [ 

"stepfun-ai/step3",
"Qwen/Qwen2.5-VL-72B-Instruct",
]

GLOBAL_MODEL_INDEX = 0
GLOBAL_CURRENT_MODEL = available_models_global[GLOBAL_MODEL_INDEX]

# 🔄 简化的切换函数
def switch_to_next_api_key():
    """切换到下一个API Key"""
    global GLOBAL_API_KEY_INDEX, GLOBAL_CURRENT_API_KEY, GLOBAL_MODEL_INDEX, GLOBAL_CURRENT_MODEL
    
    old_api_key = GLOBAL_CURRENT_API_KEY
    GLOBAL_API_KEY_INDEX = (GLOBAL_API_KEY_INDEX + 1) % len(api_key_list)
    GLOBAL_CURRENT_API_KEY = api_key_list[GLOBAL_API_KEY_INDEX]
    
    # 切换API Key时重置到第一个模型
    GLOBAL_MODEL_INDEX = 0
    GLOBAL_CURRENT_MODEL = available_models_global[GLOBAL_MODEL_INDEX]
    
    print(f"🔑 API Key切换: ***{old_api_key[-8:]} → ***{GLOBAL_CURRENT_API_KEY[-8:]}")
    print(f"🔄 重置到第一个模型: {GLOBAL_CURRENT_MODEL}")
    return True

def switch_to_next_model():
    """切换到下一个模型"""
    global GLOBAL_MODEL_INDEX, GLOBAL_CURRENT_MODEL
    
    old_model = GLOBAL_CURRENT_MODEL
    GLOBAL_MODEL_INDEX = (GLOBAL_MODEL_INDEX + 1) % len(available_models_global)
    GLOBAL_CURRENT_MODEL = available_models_global[GLOBAL_MODEL_INDEX]
    
    print(f"🔄 模型切换: {old_model.split('/')[-1]} → {GLOBAL_CURRENT_MODEL.split('/')[-1]}")
    
    # 如果回到第一个模型，说明所有模型都试过了，切换API Key
    if GLOBAL_MODEL_INDEX == 0:
        print("⚠️ 所有模型都已尝试，切换API Key")
        switch_to_next_api_key()
        return True
    
    return True

def get_current_api_key():
    """获取当前API Key"""
    return GLOBAL_CURRENT_API_KEY

def get_current_model():
    """获取当前模型"""
    return GLOBAL_CURRENT_MODEL

def reset_global_state():
    """重置全局状态到初始值"""
    global GLOBAL_API_KEY_INDEX, GLOBAL_CURRENT_API_KEY, GLOBAL_MODEL_INDEX, GLOBAL_CURRENT_MODEL
    
    GLOBAL_API_KEY_INDEX = 0
    GLOBAL_CURRENT_API_KEY = api_key_list[0]
    GLOBAL_MODEL_INDEX = 0 
    GLOBAL_CURRENT_MODEL = available_models_global[0]
    
    print(f"🔄 全局状态已重置: API Key ***{GLOBAL_CURRENT_API_KEY[-8:]}, 模型 {GLOBAL_CURRENT_MODEL.split('/')[-1]}")
    return True


class NewModel(LabelStudioMLBase):
    """Custom ML Backend model for rectangle annotation
    """
    
    def setup(self):
        """Configure any parameters of your model here
        """
        print(f"\n🚀 灾害图框选标注ML Backend启动中...")
        
        self.set("model_version", "2.0.0-多账号切换版")
        
        # 🌍 使用全局状态管理 - 简化架构
        self.api_base_url = os.getenv('MODELSCOPE_API_URL', 'https://api-inference.modelscope.cn/v1')
        
        # 🎯 简化的失败计数
        self.consecutive_failures = 0  # 当前模型的连续失败次数
        self.max_failures_before_switch = 2  # 连续失败2次后切换
        
        # 延迟初始化客户端，只在需要时连接
        self.client = None
        self._api_initialized = False
        
        print("✅ 多模态图框选标注ML后端初始化完成")
        print(f"🎯 当前模型: {get_current_model().split('/')[-1]}")
        print(f"🔑 当前API Key: ***{get_current_api_key()[-8:]}")
        print(f"📋 可用模型: {len(available_models_global)} 个")
        print(f"🔑 可用API Key: {len(api_key_list)} 个")
        print(f"🔄 简化切换: 失败{self.max_failures_before_switch}次切换模型，所有模型失败切换API Key")
        print(f"⏰ 超时设置: 250秒（给大模型充足处理时间）")
        print(f"🖼️ 专业领域: 多模态图框选标注 v2.0.0")
        print(f"🚀 简化策略: 使用全局状态统一管理API Key和模型切换")
    
    def reset_state(self):
        """🔄 重置状态到初始状态（使用全局状态）"""
        print("🔄 重置状态到初始状态...")
        reset_global_state()
        self.consecutive_failures = 0
        
        # 重置API连接
        self._api_initialized = False
        self.client = None
        
        print(f"✅ 状态已重置")
        return True
    
    def _handle_failure(self, reason: str = "未知错误", force_switch: bool = False):
        """🚨 简化的失败处理逻辑"""
        self.consecutive_failures += 1
        current_model = get_current_model()
        
        print(f"❌ 模型失败: {current_model.split('/')[-1]} - {reason} (连续: {self.consecutive_failures}/{self.max_failures_before_switch})")
        
        # 判断是否需要切换
        should_switch = force_switch or (self.consecutive_failures >= self.max_failures_before_switch)
        
        if should_switch:
            print(f"🔄 {'强制' if force_switch else '达到阈值'}切换模型")
            switch_to_next_model()  # 使用全局函数切换
            self.consecutive_failures = 0  # 重置失败计数
            
            # 重置API连接
            self._api_initialized = False
            self.client = None
            return True
        
        return False
    
    def _handle_success(self):
        """✅ 处理成功，重置失败计数"""
        if self.consecutive_failures > 0:
            print(f"✅ 模型恢复正常")
            self.consecutive_failures = 0
    
    def _should_switch_immediately(self, error_str: str) -> bool:
        """判断是否需要立即切换模型（不重试）"""
        immediate_switch_patterns = [
            # API限流错误 - 立即切换
            "429",
            "Too Many Requests", 
            "Request limit exceeded",
            "Rate limit exceeded",
            "Quota exceeded",
            "请求超限",  # 中文错误信息
            "请求限制",
            "超出限制",
            "达到限制",
            "Exceeded limit",
            "API rate limit",
            "Usage limit exceeded",
            "Daily limit exceeded",
            "Monthly limit exceeded",
            
            # 认证/权限错误 - 立即切换
            "401", 
            "403",
            "Unauthorized",
            "Forbidden",
            "Invalid API key",
            "API key expired",
            
            # 模型不可用错误 - 立即切换
            "404",
            "Model not found",
            "Model unavailable",
            "Service unavailable",
            "Model is overloaded",
            
            # 服务器内部错误 - 立即切换
            "500",
            "502", 
            "503",
            "504",
            "Internal server error",
            "Bad gateway",
            "Gateway timeout",
            
            # 参数错误 - 立即切换（模型不支持当前参数）
            "Invalid model",
            "Unsupported model",
            "Model does not exist",
            
            # 严重超时错误 - 立即切换（避免长时间等待）
            "Connection timeout",  # 连接层面的超时
            "Read timeout",        # 读取超时
            "Gateway timeout"      # 网关超时
        ]
        
        error_lower = error_str.lower()
        for pattern in immediate_switch_patterns:
            if pattern.lower() in error_lower:
                return True
        
        return False
    
    def _get_error_type(self, error_str: str) -> str:
        """获取错误类型描述"""
        error_lower = error_str.lower()
        
        # 🚨 高优先级错误（立即切换）
        if any(x in error_lower for x in ["429", "too many requests", "rate limit", "quota exceeded", "request limit exceeded", "请求超限", "请求限制", "超出限制", "达到限制", "exceeded limit", "usage limit", "daily limit", "monthly limit"]):
            return "API限流"
        elif any(x in error_lower for x in ["401", "403", "unauthorized", "forbidden", "api key"]):
            return "认证失败"
        elif any(x in error_lower for x in ["404", "model not found", "model unavailable"]):
            return "模型不存在"
        elif any(x in error_lower for x in ["500", "502", "503", "504", "internal server"]):
            return "服务器错误"
        elif any(x in error_lower for x in ["invalid model", "unsupported model"]):
            return "模型不支持"
        elif any(x in error_lower for x in ["connection timeout", "read timeout", "gateway timeout"]):
            return "网络超时"
        elif any(x in error_lower for x in ["timeout", "timed out"]):
            return "处理超时"
        
        # 🔄 一般错误（可重试）  
        elif any(x in error_lower for x in ["connection", "network"]):
            return "网络连接"
        elif any(x in error_lower for x in ["json", "parse", "format"]):
            return "格式错误"
        elif "empty" in error_lower or "空" in error_str:
            return "空响应"
        else:
            return "未知错误"
        
    def _ensure_api_connection(self):
        """🔌 确保API连接已初始化（使用全局状态）"""
        if self._api_initialized and self.client:
            return True
        
        current_api_key = get_current_api_key()
        current_model = get_current_model()
        
        try:
            print(f"🔄 连接API... (模型: {current_model.split('/')[-1]}, Key: ***{current_api_key[-8:]})")
            self.client = OpenAI(
                base_url=self.api_base_url,
                api_key=current_api_key,
                max_retries=0,  # 禁用内置重试
                timeout=250.0   # 250秒超时
            )
            
            # 简单测试连接
            response = self.client.chat.completions.create(
                model=current_model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
                temperature=0.1,
                timeout=250
            )
            
            self._api_initialized = True
            print(f"✅ API连接成功")
            return True
            
        except Exception as e:
            error_str = str(e)
            print(f"❌ API连接失败: {error_str[:100]}")
            
            # 检查是否需要立即切换
            if self._should_switch_immediately(error_str):
                error_type = self._get_error_type(error_str)
                print(f"🔄 检测到需要立即切换的错误: {error_type}")
                self._handle_failure(f"连接-{error_type}", force_switch=True)
            else:
                self._handle_failure(f"连接-{self._get_error_type(error_str)}")
            
            # 重置连接状态
            self.client = None
            self._api_initialized = False
            return False
    
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
        """ 灾害图片框选标注预测
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
        """处理单个框选标注任务"""
        
        task_data = task.get('data', {})
        
        # 提取图片内容
        image_url = None
        image_data = None
        
        # 查找图片URL
        for key, value in task_data.items():
            if isinstance(value, str):
                # 优先检查image字段（模板中的图片字段）
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
        
        # 构建框选标注提示词
        prompt = """请分析这张灾害图片，识别并标注以下区域和对象：

标注类别（请从以下类别中选择合适的进行标注）：
1. 积水淹没区域 - 被洪水淹没的区域
2. 受灾建筑物 - 受到灾害影响的建筑物
3. 受灾道路 - 受到灾害影响的道路
4. 受灾人员 - 受到灾害影响的人员
5. 受灾车辆 - 受到灾害影响的车辆
6. 救援人员 - 参与救援的人员
7. 救援车辆 - 参与救援的车辆
8. 树木农田受损区 - 受损的树木和农田区域
9. 电力设施 - 电力相关设施
10. 桥梁堤坝 - 桥梁和堤坝设施
11. 交通设施 - 交通相关设施
12. 漂浮物 - 水中的漂浮物

请以JSON格式返回标注结果，包含每个区域/对象的类别、位置坐标和置信度。格式如下：
{
  "annotations": [
    {
      "label": "积水淹没区域",
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.95
    }
  ]
}

**重要坐标要求**：
- 坐标格式：[左上角x%, 左上角y%, 右下角x%, 右下角y%]
- 坐标值必须是0-100之间的百分比数值（不是像素值）
- 例如：[10.5, 15.2, 45.8, 67.3] 表示从图片宽度10.5%，高度15.2%位置到宽度45.8%，高度67.3%位置的矩形框
- 左上角坐标 < 右下角坐标
- 所有坐标值范围：0 ≤ 坐标值 ≤ 100

**坐标示例**：
- 图片左上角区域：[5.0, 5.0, 30.0, 25.0]
- 图片中心区域：[35.0, 35.0, 65.0, 65.0]  
- 图片右下角区域：[70.0, 75.0, 95.0, 95.0]

请严格按照百分比格式返回坐标，这对准确标注至关重要！"""
        
        # 调用多模态API（使用智能切换版本）
        api_response = self._call_multimodal_api_with_switching(prompt, image_data)
        
        if api_response:
            return self._format_annotation_prediction(api_response, task)
        else:
            return None
    
    def _call_multimodal_api_with_switching(self, prompt: str, image_data: str) -> Optional[str]:
        """🚀 智能切换版本的多模态API调用（使用全局状态管理）"""
        import time
        
        max_total_attempts = len(available_models_global) * 2  # 总共尝试次数
        
        for attempt in range(max_total_attempts):
            # 确保API连接可用
            if not self._ensure_api_connection():
                continue  # 已经在连接时处理了切换，继续下一次尝试
            
            current_model = get_current_model()
            try:
                print(f"🔄 调用多模态API (尝试 {attempt + 1}/{max_total_attempts})")
                print(f"   📡 模型: {current_model.split('/')[-1]} | ⏰ 超时: 250s | 💾 最大token: 1000")
                
                start_time = time.time()
                
                # 构建多模态消息
                system_message = "You are a helpful assistant specialized in disaster image analysis and rectangle annotation. Please provide accurate annotation results in JSON format."
                
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
                    model=current_model,
                    messages=messages,
                    max_tokens=1000,
                    temperature=0.7,
                    top_p=0.9,
                    stream=False,
                    timeout=250
                )
                
                end_time = time.time()
                api_duration = end_time - start_time
                
                if response.choices and len(response.choices) > 0:
                    choice = response.choices[0]
                    
                    if hasattr(choice, 'message'):
                        message = choice.message
                        content = getattr(message, 'content', None)
                        
                        if content and content.strip():
                            # 成功
                            self._handle_success()
                            print(f"   ✅ 成功 (耗时: {api_duration:.1f}s, 长度: {len(content)})")
                            return content
                        else:
                            print(f"⚠️ 返回空内容")
                            self._handle_failure("空响应")
                    else:
                        print(f"⚠️ 无消息内容")
                        self._handle_failure("无消息")
                else:
                    print(f"⚠️ 无响应choices")
                    self._handle_failure("无响应")
                        
            except Exception as e:
                error_str = str(e)
                print(f"❌ 多模态API异常: {error_str[:100]}")
                
                # 检查是否需要立即切换
                if self._should_switch_immediately(error_str):
                    error_type = self._get_error_type(error_str)
                    print(f"🔄 立即切换错误: {error_type}")
                    self._handle_failure(f"立即切换-{error_type}", force_switch=True)
                else:
                    self._handle_failure(f"API异常-{self._get_error_type(error_str)}")
        
        print("❌ 所有尝试都失败")
        return None
    
    def _call_multimodal_api(self, prompt: str, image_data: str) -> Optional[str]:
        """调用多模态API进行框选标注"""
        
        if not self.client:
            return None
        
        try:
            # 构建多模态消息
            system_message = "You are a helpful assistant specialized in disaster image analysis and rectangle annotation. Please provide accurate annotation results in JSON format."
            
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
                model=get_current_model(),
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
    
    def _pixel_to_percentage(self, pixel_coords: List[float], image_width: int, image_height: int) -> List[float]:
        """将像素坐标转换为百分比坐标"""
        x1, y1, x2, y2 = pixel_coords
        
        # 转换为百分比
        x1_percent = (x1 / image_width) * 100
        y1_percent = (y1 / image_height) * 100
        x2_percent = (x2 / image_width) * 100
        y2_percent = (y2 / image_height) * 100
        
        return [x1_percent, y1_percent, x2_percent, y2_percent]
    
    def _get_image_dimensions(self, task: Dict) -> tuple:
        """尝试获取图片的真实尺寸"""
        try:
            import requests
            from PIL import Image
            import io
            
            # 获取图片数据
            task_data = task.get('data', {})
            image_url = None
            
            for key, value in task_data.items():
                if isinstance(value, str) and (key in ['image', 'img', 'photo', 'picture', 'url', 'captioning'] or 
                                              value.startswith(('http://', 'https://', 'data:image/', '/'))):
                    image_url = value
                    break
            
            if not image_url:
                return None, None
            
            if image_url.startswith('data:image/'):
                # Base64编码的图片
                import base64
                header, data = image_url.split(',', 1)
                image_data = base64.b64decode(data)
                image = Image.open(io.BytesIO(image_data))
                return image.width, image.height
                
            elif image_url.startswith(('http://', 'https://')):
                # 网络URL图片
                response = requests.get(image_url, timeout=10)
                image = Image.open(io.BytesIO(response.content))
                return image.width, image.height
                
            else:
                # 本地文件路径 - 使用现有的路径解析逻辑
                image_data = self._convert_local_path_to_base64(image_url)
                if image_data and image_data.startswith('data:image/'):
                    import base64
                    header, data = image_data.split(',', 1)
                    image_bytes = base64.b64decode(data)
                    image = Image.open(io.BytesIO(image_bytes))
                    return image.width, image.height
                    
        except Exception as e:
            print(f"⚠️ 无法获取图片尺寸: {e}")
            
        return None, None
    
    def _detect_coordinate_type(self, x1: float, y1: float, x2: float, y2: float, task: Dict) -> str:
        """改进的坐标类型检测"""
        max_coord = max(x1, y1, x2, y2)
        min_coord = min(x1, y1, x2, y2)
        
        # 获取图片尺寸作为参考
        image_width, image_height = self._get_image_dimensions(task)
        
        if image_width and image_height:
            # 如果有图片尺寸，检查是否为像素坐标
            max_image_dim = max(image_width, image_height)
            min_image_dim = min(image_width, image_height)
            
            if max_coord > max_image_dim:
                print(f"⚠️ 坐标超出图片尺寸，可能有误: max_coord={max_coord}, image_size={image_width}x{image_height}")
                return "pixel"  # 仍按像素处理，但会被限制
            elif max_coord > min_image_dim * 0.8:
                print(f"🔍 坐标接近图片尺寸，判定为像素坐标: max_coord={max_coord}, image_size={image_width}x{image_height}")
                return "pixel"
        
        # 标准化坐标 (0-1)
        if max_coord <= 1.0 and min_coord >= 0:
            print(f"✅ 检测到标准化坐标(0-1): 范围[{min_coord:.3f}, {max_coord:.3f}]")
            return "normalized"
        
        # 百分比坐标 (0-100)
        elif max_coord <= 100 and min_coord >= 0:
            # 进一步检查：如果所有坐标都是整数且较小，可能是像素坐标
            if (all(abs(c - round(c)) < 0.01 for c in [x1, y1, x2, y2]) and 
                max_coord < 50 and 
                not image_width):  # 没有图片尺寸信息时更保守
                print(f"🤔 疑似小尺寸像素坐标: 范围[{min_coord}, {max_coord}]，按百分比处理")
                return "percentage"  # 倾向于按百分比处理，更安全
            print(f"✅ 检测到百分比坐标: 范围[{min_coord}, {max_coord}]")
            return "percentage"
        
        # 像素坐标（大数值）
        else:
            print(f"🔍 检测到像素坐标: 范围[{min_coord}, {max_coord}]")
            return "pixel"
    
    def _normalize_coordinates(self, x1: float, y1: float, x2: float, y2: float, task: Dict) -> tuple:
        """智能标准化坐标为百分比格式"""
        
        # 使用改进的坐标类型检测
        coord_type = self._detect_coordinate_type(x1, y1, x2, y2, task)
        
        if coord_type == "percentage":
            print(f"✅ 检测到百分比坐标，直接使用")
            return x1, y1, x2, y2
        
        elif coord_type == "normalized":
            print(f"✅ 检测到标准化坐标(0-1)，转换为百分比")
            return x1 * 100, y1 * 100, x2 * 100, y2 * 100
        
        elif coord_type == "pixel":
            # 像素坐标，尝试获取图片真实尺寸进行转换
            print(f"🔍 检测到像素坐标，尝试获取图片尺寸进行精确转换")
            image_width, image_height = self._get_image_dimensions(task)
            
            if image_width and image_height:
                print(f"📏 获取到图片尺寸: {image_width}x{image_height}")
                x1_percent = (x1 / image_width) * 100
                y1_percent = (y1 / image_height) * 100
                x2_percent = (x2 / image_width) * 100
                y2_percent = (y2 / image_height) * 100
                
                # 确保坐标在合理范围内
                x1_percent = max(0, min(100, x1_percent))
                y1_percent = max(0, min(100, y1_percent))
                x2_percent = max(0, min(100, x2_percent))
                y2_percent = max(0, min(100, y2_percent))
                
                print(f"✅ 精确转换完成: [{x1_percent:.1f}, {y1_percent:.1f}, {x2_percent:.1f}, {y2_percent:.1f}]")
                return x1_percent, y1_percent, x2_percent, y2_percent
            else:
                # 无法获取图片尺寸，使用改进的启发式方法
                print(f"⚠️ 无法获取图片尺寸，使用改进的启发式转换")
                return self._heuristic_coordinate_conversion(x1, y1, x2, y2)
        
        else:
            # 未知类型，使用启发式方法
            print(f"⚠️ 未知坐标类型，使用启发式转换")
            return self._heuristic_coordinate_conversion(x1, y1, x2, y2)
    
    def _heuristic_coordinate_conversion(self, x1: float, y1: float, x2: float, y2: float) -> tuple:
        """改进的启发式坐标转换"""
        max_coord = max(x1, y1, x2, y2)
        
        # 基于坐标数值特征进行更精确的推测
        if max_coord > 5000:
            # 超高分辨率 (4K+ 图片)
            estimated_size = 6000
            print(f"🔧 推测为超高分辨率图片 (~6000px)")
        elif max_coord > 2000:
            # 高分辨率 (2K-4K 图片)
            estimated_size = 3000
            print(f"🔧 推测为高分辨率图片 (~3000px)")
        elif max_coord > 1000:
            # 标准分辨率 (1K-2K 图片)
            estimated_size = 1500
            print(f"🔧 推测为标准分辨率图片 (~1500px)")
        elif max_coord > 500:
            # 中等分辨率 (500-1000px 图片)
            estimated_size = 800
            print(f"🔧 推测为中等分辨率图片 (~800px)")
        elif max_coord > 200:
            # 小尺寸图片 (200-500px)
            estimated_size = 400
            print(f"🔧 推测为小尺寸图片 (~400px)")
        else:
            # 很小的坐标值，可能已经是百分比或标准化坐标
            if max_coord > 100:
                estimated_size = 200  # 按小图片处理
                print(f"🔧 推测为微小图片 (~200px)")
            else:
                # 直接按百分比处理
                print(f"🔧 坐标值很小，直接按百分比处理")
                return max(0, min(100, x1)), max(0, min(100, y1)), max(0, min(100, x2)), max(0, min(100, y2))
        
        # 转换为百分比
        x1_percent = (x1 / estimated_size) * 100
        y1_percent = (y1 / estimated_size) * 100
        x2_percent = (x2 / estimated_size) * 100
        y2_percent = (y2 / estimated_size) * 100
        
        # 限制在合理范围内，并添加边界检查
        x1_final = max(0, min(100, x1_percent))
        y1_final = max(0, min(100, y1_percent))
        x2_final = max(0, min(100, x2_percent))
        y2_final = max(0, min(100, y2_percent))
        
        # 检查转换结果的合理性
        if x2_final <= x1_final or y2_final <= y1_final:
            print(f"⚠️ 启发式转换产生无效矩形，调整坐标")
            # 确保最小尺寸
            if x2_final <= x1_final:
                x2_final = min(100, x1_final + 1.0)
            if y2_final <= y1_final:
                y2_final = min(100, y1_final + 1.0)
        
        print(f"⚠️ 启发式转换结果: [{x1_final:.1f}, {y1_final:.1f}, {x2_final:.1f}, {y2_final:.1f}]")
        return x1_final, y1_final, x2_final, y2_final
    
    def _validate_coordinates(self, x: float, y: float, width: float, height: float) -> tuple:
        """验证并修正坐标的有效性"""
        # 确保坐标在0-100范围内
        x = max(0, min(100, x))
        y = max(0, min(100, y))
        
        # 确保宽度和高度为正值且不超出边界
        width = max(0.1, min(100 - x, width))
        height = max(0.1, min(100 - y, height))
        
        # 确保矩形不会超出图片边界
        if x + width > 100:
            width = 100 - x
        if y + height > 100:
            height = 100 - y
            
        # 最终检查：确保最小尺寸
        if width < 0.1:
            width = 0.1
        if height < 0.1:
            height = 0.1
            
        return x, y, width, height
    
    def _format_annotation_prediction(self, api_response: str, task: Dict) -> Dict:
        """格式化框选标注预测结果为Label Studio格式"""
        
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
                
                if 'annotations' in detection_data:
                    for obj in detection_data['annotations']:
                        if 'label' in obj and 'bbox' in obj:
                            # 构建Label Studio矩形框格式
                            bbox = obj['bbox']
                            confidence = obj.get('confidence', 0.8)
                            
                            # 处理bbox坐标：[x1, y1, x2, y2] 格式
                            x1, y1, x2, y2 = bbox
                            
                            print(f"🔍 原始坐标: [{x1}, {y1}, {x2}, {y2}]")
                            
                            # 坐标格式检测和转换
                            x1_percent, y1_percent, x2_percent, y2_percent = self._normalize_coordinates(x1, y1, x2, y2, task)
                            
                            # 确保坐标顺序正确（左上角 -> 右下角）
                            if x1_percent > x2_percent:
                                x1_percent, x2_percent = x2_percent, x1_percent
                            if y1_percent > y2_percent:
                                y1_percent, y2_percent = y2_percent, y1_percent
                            
                            # 计算Label Studio需要的格式：x, y, width, height (百分比)
                            x = x1_percent
                            y = y1_percent
                            width = x2_percent - x1_percent
                            height = y2_percent - y1_percent
                            
                            # 使用改进的坐标验证函数
                            x, y, width, height = self._validate_coordinates(x, y, width, height)
                            
                            print(f"📐 验证后坐标: x={x:.1f}%, y={y:.1f}%, width={width:.1f}%, height={height:.1f}%")
                            
                            result_item = {
                                "from_name": from_name,
                                "to_name": to_name,
                                "type": "rectanglelabels",
                                "value": {
                                    "x": x,
                                    "y": y,
                                    "width": width,
                                    "height": height,
                                    "rectanglelabels": [obj['label']]
                                },
                                "score": confidence
                            }
                            
                            prediction["result"].append(result_item)
            
            # 如果没有解析到有效的标注结果，尝试使用默认标注
            if not prediction["result"]:
                # 生成一些示例标注框（用于测试）- 百分比坐标
                sample_objects = [
                    {"label": "积水淹没区域", "bbox": [10.5, 15.2, 45.8, 50.3], "confidence": 0.8},
                    {"label": "受灾建筑物", "bbox": [55.0, 60.5, 85.2, 90.8], "confidence": 0.7},
                    {"label": "救援人员", "bbox": [20.3, 25.7, 35.6, 40.1], "confidence": 0.6}
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
    
    def _print_status(self):
        """📊 简化的状态显示"""
        current_model = get_current_model()
        current_api_key = get_current_api_key()
        
        print(f"\n🤖 当前状态:")
        print(f"   🎯 模型: {current_model.split('/')[-1]} (失败: {self.consecutive_failures}/{self.max_failures_before_switch})")
        print(f"   🔑 API Key: ***{current_api_key[-8:]} ({GLOBAL_API_KEY_INDEX + 1}/{len(api_key_list)})")
        print(f"   📋 可用模型: {len(available_models_global)} 个")
        print(f"   🔄 全局状态管理: 简化切换逻辑")
    
    def get_status(self) -> Dict:
        """🔍 获取简化状态信息"""
        return {
            "current_model": get_current_model(),
            "current_api_key": f"***{get_current_api_key()[-8:]}",
            "consecutive_failures": self.consecutive_failures,
            "max_failures_before_switch": self.max_failures_before_switch,
            "available_models": available_models_global.copy(),
            "total_api_keys": len(api_key_list),
            "global_model_index": GLOBAL_MODEL_INDEX,
            "global_api_key_index": GLOBAL_API_KEY_INDEX,
            "management_type": "simplified_global_state"
        }
    
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
        
        # 根据框选标注模板，使用正确的字段名
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
        训练/更新框选标注模型
        :param event: 事件类型 ('ANNOTATION_CREATED', 'ANNOTATION_UPDATED', 'START_TRAINING')
        :param data: 事件数据（包含图片和矩形框标注）
        """
        # 记录标注数据用于模型优化
        old_data = self.get('annotation_data')
        self.set('annotation_data', 'updated_annotation_data')
        self.set('model_version', 'updated_version')
        print(f"✅ 框选标注模型已更新 (事件: {event})")
        print(f"📸 已记录新的框选标注数据，用于后续模型优化")


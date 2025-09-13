from typing import List, Dict, Optional
import json
import os
import base64
import time
from openai import OpenAI
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse


# ==================== 多模态图片描述配置 ====================
# 支持的图片格式
SUPPORTED_IMAGE_FORMATS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']

# Label Studio 媒体目录配置
# 可以通过环境变量 LABEL_STUDIO_MEDIA_DIR 设置
LABEL_STUDIO_MEDIA_DIR = os.getenv('LABEL_STUDIO_MEDIA_DIR', r'C:\Users\Administrator\AppData\Local\label-studio\label-studio\media')

# 图片描述任务配置
IMAGE_DESCRIPTION_CONFIG = {
    "task_type": "图片描述文本标注",
    "model_type": "多模态视觉语言模型", 
    "output_format": "自然语言文本描述",
    "language": "中文",
    "max_tokens": 1000,
    "temperature": 0.7,
    "features": [
        "物体识别",
        "场景理解", 
        "颜色分析",
        "动作描述",
        "细节观察"
    ]
}

# ==================== 🌍 全局状态管理 - API Key和模型切换 ====================
# 使用全局变量统一管理当前状态，避免复杂的切换逻辑
api_key_list = [
    "ms-d200fd06-f07f-4be8-a6a8-9ebf76dd103a",  # 原始默认Key
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
"Qwen/Qwen2.5-VL-72B-Instruct",
"stepfun-ai/step3",
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
    """Custom ML Backend model
    """
    
    def setup(self):
        """Configure any parameters of your model here
        """
        print(f"\n🚀 图片描述ML Backend启动中...")
        
        self.set("model_version", "2.0.0-多账号切换版")
        
        # 🌍 使用全局状态管理 - 简化架构
        self.api_base_url = os.getenv('MODELSCOPE_API_URL', 'https://api-inference.modelscope.cn/v1')
        
        # 🎯 简化的失败计数
        self.consecutive_failures = 0  # 当前模型的连续失败次数
        self.max_failures_before_switch = 2  # 连续失败2次后切换
        
        # 延迟初始化客户端，只在需要时连接
        self.client = None
        self._api_initialized = False
        
        print("✅ 多模态图片描述ML后端初始化完成")
        print(f"🎯 当前模型: {get_current_model().split('/')[-1]}")
        print(f"🔑 当前API Key: ***{get_current_api_key()[-8:]}")
        print(f"📋 可用模型: {len(available_models_global)} 个")
        print(f"🔑 可用API Key: {len(api_key_list)} 个")
        print(f"🔄 简化切换: 失败{self.max_failures_before_switch}次切换模型，所有模型失败切换API Key")
        print(f"⏰ 超时设置: 250秒（给大模型充足处理时间）")
        print(f"🖼️ 专业领域: 多模态图片描述 v2.0.0")
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
            # 处理路径:移除开头的斜杠，直接使用相对路径
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
        """创建配置指引消息(当文件未找到时的fallback)"""
        return """⚠️ 配置问题:无法访问上传的图片文件

🔧 解决方案:

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
        """ 图片描述文本标注预测
            :param tasks: Label Studio tasks in JSON format (包含图片数据)
            :param context: Label Studio context in JSON format
            :return: ModelResponse with predictions (图片描述文本)
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
        """处理单个图片描述任务"""
        
        task_data = task.get('data', {})
        
        # 提取图片内容
        image_url = None
        image_data = None
        custom_prompt = ""
        
        # 查找图片URL
        for key, value in task_data.items():
            if isinstance(value, str):
                # 优先检查captioning字段(您的模板中的图片字段)
                if key in ['captioning', 'image', 'img', 'photo', 'picture', 'url']:
                    image_url = value
                    break
                elif value.startswith(('http://', 'https://', 'data:image/')):
                    image_url = value
                    break
                elif key in ['text', 'prompt', 'question', 'description']:
                    custom_prompt = value
        
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
        
        # 构建图片描述提示词
        if custom_prompt:
            prompt = f"请根据用户的要求描述这张图片:{custom_prompt}"
        else:
            prompt = """你是洪涝灾害分析专家。请对以下图片进行分析，并按照生产级标准输出。

要求:

1. **自主视觉思维链(Visual Chain-of-Thought)**:
   - 使用分步列表形式，每一步包含以下字段:
     1. **reasoning_level**:推理层次，可选值:
        - "perception"(感知层，直接从图片获取信息)  
        - "relationship"(关系推理层，分析对象或因素间关系)  
        - "semantic"(语义/因果推理层，判断灾害等级、原因和潜在影响)
     2. **reasoning / Why**:为什么做这步，说明观察或推理目的。
     3. **observation / How**:怎么做，说明具体观察或分析方法。
     4. **expected_outcome / What to obtain**:希望通过这步获得的信息或结果。
     5. **inference / Conclusion**:根据观察和分析得出的结论。
     6. **step_type**(可选):步骤类型，例如 "observation", "inference", "cause_analysis", "impact_estimation"。
     7. **confidence**(可选):分析可信度，例如 "高", "中", "低"。
     8. **time_reference**(可选):当前观察/过去/预测。
     9. **mapped_field**(可选):对应结构化字段。
   - 步骤按逻辑顺序编号，第1步、第2步、第3步……。
   - 模型自主推理，不需要提前提供分析步骤。
   - 示例格式:
[
  {
    "step": 1,
    "reasoning_level": "perception",
    "reasoning": "需要了解洪水严重程度，判断居民风险。",
    "observation": "观察到街道积水，水深及膝，多栋建筑底层被淹。",
    "expected_outcome": "获取受灾区域及影响范围。",
    "inference": "低洼街区受洪水直接影响，居民生活受阻。",
    "step_type": "observation",
    "confidence": "高",
    "time_reference": "当前",
    "mapped_field": "affected_area"
  },
  {
    "step": 2,
    "reasoning_level": "relationship",
    "reasoning": "分析建筑受灾与地势关系，判断洪水扩散路径。",
    "observation": "水位高的街道邻近低洼建筑，部分道路阻塞。",
    "expected_outcome": "理解洪水传播及受灾链条。",
    "inference": "洪水主要影响低洼区域，交通受阻。",
    "step_type": "impact_estimation",
    "confidence": "中",
    "time_reference": "当前",
    "mapped_field": "affected_area"
  },
  {
    "step": 3,
    "reasoning_level": "semantic",
    "reasoning": "判断灾害等级、原因及潜在影响。",
    "observation": "连续强降雨，排水不畅，低洼建筑淹水。",
    "expected_outcome": "确定灾害类型、等级及应对措施。",
    "inference": "该区域中度至重度洪水，居民需撤离，经济损失可能发生。",
    "step_type": "cause_analysis",
    "confidence": "中",
    "time_reference": "当前",
    "mapped_field": "disaster_level"
  }
]

2. **结构化总结(Structured Summary)**:
   - 核心维度(观察到就填，无法观察标记“未观察到”):
     - disaster_type(灾害类型)
     - affected_environment(承灾环境)
     - affected_area(受灾范围)
     - disaster_level(灾害等级)
     - disaster_time(灾害时间)
     - disaster_location(灾害地点)
     - disaster_cause(灾害原因)
     - disaster_consequence(灾害后果)
     - disaster_impact(灾害影响)
     - response_measures(灾害应对措施)
     - other_details(其他值得注意的细节)
   - 可选扩展维度(观察到就填，无法观察标记“未观察到”):
     - hydrological_features(水深、水流速度等)
     - affected_population
     - infrastructure_damage
     - environmental_factors
     - warning_signals
     - socioeconomic_impact
     - disaster_trend
     - recoverability
     - anomalies_or_unusual_observations
     - weather_conditions

3. **总体文本描述(overall_text_description)**:
   - 综合视觉思维链和结构化信息生成自然语言总结。
   - 语言简明、客观、专业，可直接用于报告、监测或新闻稿。

4. **输出要求**:
   - JSON 格式，包含四部分:
     1. "image_id":图片名称或ID
     2. "visual_cot":分步五维思维链
     3. "structured_description":结构化字段
     4. "overall_text_description":自然语言总结
   - 核心维度和可选扩展维度统一采用“观察到就填，未观察标记‘未观察到’”方式。"""
        
        # 调用多模态API（使用智能切换版本）
        api_response = self._call_multimodal_api_with_switching(prompt, image_data)
        
        if api_response:
            return self._format_description_prediction(api_response, task)
        else:
            return None
    
    def _call_multimodal_api_with_switching(self, prompt: str, image_data: str) -> Optional[str]:
        """🚀 智能切换版本的多模态API调用（使用全局状态管理）"""
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
                system_message = "You are a helpful assistant specialized in image description. Please provide detailed, accurate descriptions in Chinese."
                
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
        """调用多模态API进行图片描述（保留原方法作为备用）"""
        
        if not self.client:
                return None
                
        try:
            # 构建多模态消息
            system_message = "You are a helpful assistant specialized in image description. Please provide detailed, accurate descriptions in Chinese."
            
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
    
    def _format_description_prediction(self, api_response: str, task: Dict) -> Dict:
        """格式化图片描述预测结果为Label Studio格式"""
        
        # 构建基础预测结构
        model_version = self.get("model_version")
        
        prediction = {
            "model_version": model_version,
            "score": 0.95,
            "result": []
        }
        
        # 动态获取字段名
        from_name, to_name = self._get_field_names()
        
        # 处理API响应
        if api_response and api_response.strip():
            cleaned_response = self._clean_response_format(api_response.strip())
            
            # 构建Label Studio结果格式
            result_item = {
                "from_name": from_name,
                "to_name": to_name,
                "type": "textarea", 
                "value": {
                    "text": [cleaned_response]
                }
            }
            
            prediction["result"].append(result_item)
            
        else:
            default_message = "无法生成图片描述"
            result_item = {
                "from_name": from_name,
                "to_name": to_name, 
                "type": "textarea",
                "value": {
                    "text": [default_message]
                }
            }
            
            prediction["result"].append(result_item)
        
        return prediction
    
    def _clean_response_format(self, response: str) -> str:
        """清理API响应中的格式标记并验证JSON完整性"""
        import re
        
        # 移除```json和```标记
        cleaned = re.sub(r'```json\s*', '', response)
        cleaned = re.sub(r'\s*```', '', cleaned)
        
        # 移除其他代码块标记
        cleaned = re.sub(r'```[\w]*\s*', '', cleaned)
        
        # 移除markdown格式标记
        cleaned = re.sub(r'^\s*```\s*$', '', cleaned, flags=re.MULTILINE)
        
        # 清理多余的空白行
        cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
        
        # 验证和修复JSON结构
        cleaned = self._validate_and_fix_json(cleaned.strip())
        
        return cleaned
    
    def _validate_and_fix_json(self, text: str) -> str:
        """验证JSON结构完整性并尝试修复"""
        
        # 首先尝试解析JSON
        try:
            json.loads(text)
            print("✅ JSON结构验证通过")
            return text
        except json.JSONDecodeError as e:
            print(f"⚠️ 检测到JSON结构问题: {str(e)}")
            
            # 尝试修复常见的JSON问题
            fixed_text = self._fix_common_json_issues(text)
            
            # 再次验证修复后的JSON
            try:
                json.loads(fixed_text)
                print("✅ JSON结构修复成功")
                return fixed_text
            except json.JSONDecodeError as e2:
                print(f"❌ JSON修复失败: {str(e2)}")
                # 如果修复失败，返回一个标准的错误JSON结构
                return self._create_fallback_json_response(text)
    
    def _fix_common_json_issues(self, text: str) -> str:
        """修复常见的JSON问题"""
        import re
        
        print("🔧 尝试修复JSON结构...")
        
        # 1. 移除可能的非JSON前缀和后缀文本
        # 查找第一个{和最后一个}
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
            text = text[first_brace:last_brace + 1]
            print("   📝 提取JSON主体部分")
        
        # 2. 修复未闭合的字符串引号
        # 简单的引号修复：确保每行的引号是成对的
        lines = text.split('\n')
        fixed_lines = []
        
        for line in lines:
            # 计算引号数量
            quote_count = line.count('"') - line.count('\\"')  # 排除转义引号
            
            # 如果引号数量为奇数，可能缺少闭合引号
            if quote_count % 2 == 1:
                # 在行末添加引号（如果该行看起来像是值）
                stripped = line.rstrip()
                if stripped and not stripped.endswith(('"', ',', '}', ']')):
                    line = stripped + '"'
                    if not line.endswith(',') and not line.endswith('}'):
                        line += ','
            
            fixed_lines.append(line)
        
        text = '\n'.join(fixed_lines)
        
        # 3. 修复缺少的逗号
        # 在}前面的行如果没有逗号，添加逗号
        text = re.sub(r'(["\]}])\s*\n\s*(["\[{])', r'\1,\n\2', text)
        
        # 4. 修复多余的逗号
        # 移除}和]前面的多余逗号
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # 5. 修复未闭合的数组和对象
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        
        # 添加缺失的闭合括号
        text += '}' * open_braces
        text += ']' * open_brackets
        
        print(f"   🔧 修复完成: 添加了{open_braces}个{{}}和{open_brackets}个[]")
        
        return text
    
    def _create_fallback_json_response(self, original_text: str) -> str:
        """创建备用的JSON响应结构"""
        print("🆘 创建备用JSON响应")
        
        # 尝试从原始文本中提取一些信息
        extracted_info = self._extract_basic_info_from_text(original_text)
        
        fallback_response = {
            "image_id": "unknown",
            "visual_cot": [
                {
                    "step": 1,
                    "reasoning_level": "perception",
                    "reasoning": "由于JSON解析错误，进行基础分析",
                    "observation": extracted_info.get("observation", "无法完整解析API响应"),
                    "expected_outcome": "获取基础图片信息",
                    "inference": extracted_info.get("inference", "响应格式存在问题，已进行基础处理"),
                    "step_type": "error_handling",
                    "confidence": "低"
                }
            ],
            "structured_description": {
                "disaster_type": extracted_info.get("disaster_type", "未能识别"),
                "affected_area": extracted_info.get("affected_area", "未观察到"),
                "disaster_level": "未观察到",
                "parsing_status": "JSON格式错误，已使用备用结构"
            },
            "overall_text_description": extracted_info.get("description", f"由于响应格式问题，无法完整解析图片描述。原始响应片段：{original_text[:200]}...")
        }
        
        return json.dumps(fallback_response, ensure_ascii=False, indent=2)
    
    def _extract_basic_info_from_text(self, text: str) -> Dict[str, str]:
        """从损坏的文本中提取基础信息"""
        import re
        
        info = {}
        
        # 尝试提取灾害类型
        disaster_patterns = [
            r'["\'](洪水|洪涝|水灾|flooding)["\']',
            r'disaster_type["\']?\s*:\s*["\']([^"\']+)["\']',
            r'灾害类型["\']?\s*:\s*["\']([^"\']+)["\']'
        ]
        
        for pattern in disaster_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info["disaster_type"] = match.group(1)
                break
        
        # 尝试提取描述信息
        desc_patterns = [
            r'overall_text_description["\']?\s*:\s*["\']([^"\']{20,})["\']',
            r'总体.*?描述["\']?\s*:\s*["\']([^"\']{20,})["\']',
            r'描述["\']?\s*:\s*["\']([^"\']{20,})["\']'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info["description"] = match.group(1)
                break
        
        # 尝试提取观察信息
        obs_patterns = [
            r'observation["\']?\s*:\s*["\']([^"\']{10,})["\']',
            r'观察["\']?\s*:\s*["\']([^"\']{10,})["\']'
        ]
        
        for pattern in obs_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info["observation"] = match.group(1)
                break
        
        return info
    
    def _format_prediction(self, api_response: str, task: Dict) -> Dict:
        """格式化预测结果为Label Studio格式(备用方法)"""
        
        prediction = {
            "model_version": self.get("model_version"),
            "score": 0.85,
            "result": []
        }
        
        # 返回清理后的文本结果
        if api_response and api_response.strip():
            cleaned_response = self._clean_response_format(api_response.strip())
            prediction["result"].append({
                "from_name": "prediction",
                "to_name": "text",
                "type": "textarea",
                "value": {
                    "text": [cleaned_response]
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
                # 查找TextArea标签
                textarea_from_name, textarea_to_name, _ = self.label_interface.get_first_tag_occurence(
                    'TextArea', ['Image', 'Text', 'HyperText']
                )
                if textarea_from_name and textarea_to_name:
                    return textarea_from_name, textarea_to_name
            
            # 查找Image标签
            if hasattr(self, 'label_interface') and self.label_interface:
                image_from_name, image_to_name, _ = self.label_interface.get_first_tag_occurence(
                    'Image', []
                )
                if image_from_name:
                    return "caption", image_from_name
            
        except Exception as e:
            pass
        
        # 根据您的模板，使用正确的字段名
        return "caption", "image"
    
    def _extract_choice(self, response: str, choices: List[str]) -> Optional[str]:
        """从响应中提取最匹配的选择"""
        response_lower = response.lower()
        for choice in choices:
            if choice.lower() in response_lower:
                return choice
        return choices[0] if choices else None
    
    def fit(self, event, data, **kwargs):
        """
        训练/更新图片描述模型
        :param event: 事件类型 ('ANNOTATION_CREATED', 'ANNOTATION_UPDATED', 'START_TRAINING')
        :param data: 事件数据(包含图片和描述标注)
        """
        # 记录标注数据用于模型优化
        old_data = self.get('annotation_data')
        self.set('annotation_data', 'updated_description_data')
        self.set('model_version', 'updated_version')
        print(f"✅ 图片描述模型已更新 (事件: {event})")
        print(f"📸 已记录新的图片描述标注数据，用于后续模型优化")


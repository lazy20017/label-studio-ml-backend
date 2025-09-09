from typing import List, Dict, Optional
import json
import os
import time
from openai import OpenAI
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse

# 启动命令   label-studio-ml start my_ml_backend


# ==================== 命名实体配置 ====================
# 从配置文件导入实体配置
try:
    from entity_config import get_entity_config, get_entity_labels, get_all_categories, get_entities_by_category
    NER_ENTITY_CONFIG = get_entity_config()
    ENTITY_LABELS = get_entity_labels()
    print(f"✅ 加载了 {len(ENTITY_LABELS)} 种实体类型")
except ImportError:
    print("❌ 配置文件不存在，退出程序")
    exit()


# 生成JSON格式示例
def get_json_format_example():
    """生成JSON格式示例"""
    return """{{
  "entities": [
    {{
      "text": "实体文本",
      "start": 起始位置,
      "end": 结束位置,
      "label": "实体类型"
    }}
  ]
}}"""

def validate_label(label: str) -> str:
    """验证标签是否在有效标签列表中"""
    if not label:
        return None
    
    clean_label = label.strip()
    
    # 直接匹配标签名称
    if clean_label in ENTITY_LABELS:
        return clean_label
    
    return None

# 🌍 全局状态管理 - 简化的API Key和模型切换
# 使用全局变量统一管理当前状态，避免复杂的切换逻辑
api_key_list = [
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

# 🤖 全局模型状态  
# 推理模型太慢了
'''
    'Qwen/Qwen3-235B-A22B-Thinking-2507', 
    'deepseek-ai/DeepSeek-R1-0528',
    
'''
available_models_global = [ 


    'deepseek-ai/DeepSeek-V3',
    'Qwen/Qwen3-Coder-480B-A35B-Instruct',
    'Qwen/Qwen3-235B-A22B-Instruct-2507',
    'ZhipuAI/GLM-4.5', 
    'deepseek-ai/DeepSeek-V3.1',
 
]

# 🧠 推理模型列表 - 用户指定的4个模型都按推理模型处理
THINKING_MODELS = {
    'Qwen/Qwen3-235B-A22B-Thinking-2507',
    'ZhipuAI/GLM-4.5', 
    'deepseek-ai/DeepSeek-V3.1',
    'deepseek-ai/DeepSeek-R1-0528',
}

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

def is_thinking_model(model_name: str) -> bool:
    """检测是否为推理模型 - 检查是否在指定的推理模型列表中"""
    return model_name in THINKING_MODELS

class NewModel(LabelStudioMLBase):
    """Custom ML Backend model
    """
    
    def setup(self):
        """Configure any parameters of your model here
        """
        self.set("model_version", "2.0.0-洪涝灾害专用版")
        
        # 🌍 使用全局状态管理 - 简化架构
        self.api_base_url = os.getenv('MODELSCOPE_API_URL', 'https://api-inference.modelscope.cn/v1')
        
        # 🎯 简化的失败计数
        self.consecutive_failures = 0  # 当前模型的连续失败次数
        self.max_failures_before_switch = 2  # 连续失败2次后切换
        
        # 延迟初始化客户端，只在需要时连接
        self.client = None
        self._api_initialized = False
        
        print("✅ 洪涝灾害专用ML后端初始化完成")
        print(f"🎯 当前模型: {get_current_model().split('/')[-1]}")
        print(f"🔑 当前API Key: ***{get_current_api_key()[-8:]}")
        print(f"📋 可用模型: {len(available_models_global)} 个")
        print(f"🔑 可用API Key: {len(api_key_list)} 个")
        print(f"🔄 简化切换: 失败{self.max_failures_before_switch}次切换模型，所有模型失败切换API Key")
        print(f"⏰ 超时设置: 250秒（给大模型充足处理时间）")
        print(f"🌊 专业领域: 洪涝灾害知识提取 v2.0.0")
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
    


    def predict(self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs) -> ModelResponse:
        """ 命名实体识别预测
            :param tasks: Label Studio tasks in JSON format
            :param context: Label Studio context in JSON format
            :return: ModelResponse with predictions
        """
        total_tasks = len(tasks)
        predictions = []
        
        # 检查是否为实体标注任务
        if not self._is_annotation_task(tasks):
            print("ℹ️ 非标注任务，跳过大模型连接")
            # 返回空预测结果
            empty_predictions = []
            for task in tasks:
                empty_prediction = {
                    "model_version": self.get("model_version"),
                    "score": 0.0,
                    "result": []
                }
                empty_predictions.append(empty_prediction)
            return ModelResponse(predictions=empty_predictions)
        
        # 🔌 确保API连接（简化重试逻辑）
        max_attempts = len(available_models_global)  # 最多尝试所有模型
        
        for attempt in range(max_attempts):
            if self._ensure_api_connection():
                break  # 连接成功
            else:
                if attempt < max_attempts - 1:
                    print(f"🔄 连接失败，已自动切换到下一个配置 ({attempt + 1}/{max_attempts})")
                    continue
                else:
                    print("❌ 所有配置都无法连接，返回空结果")
                    empty_predictions = []
                    for task in tasks:
                        empty_prediction = {
                            "model_version": self.get("model_version"),
                            "score": 0.0,
                            "result": [],
                            "error": f"所有{len(available_models_global)}个模型都无法连接"
                        }
                        empty_predictions.append(empty_prediction)
                    return ModelResponse(predictions=empty_predictions)
        
        if total_tasks > 1:
            print(f"🚀 开始处理 {total_tasks} 个标注任务")
        
        start_time = time.time()
        
        for i, task in enumerate(tasks):
            if total_tasks > 1:  # 多任务时显示进度
                print(f"\n🔄 处理任务 {i+1}/{total_tasks}")
            
            # 记录开始时间
            task_start_time = time.time()
            
            try:
                prediction = self._process_single_task(task)
                task_end_time = time.time()
                task_duration = task_end_time - task_start_time
                
                if prediction and prediction.get('result') and len(prediction.get('result', [])) > 0:
                    # 成功识别到实体
                    predictions.append(prediction)
                    entities_count = len(prediction.get('result', []))
                    if total_tasks > 1:
                        print(f"✅ 任务 {i+1} 成功 (耗时: {task_duration:.1f}s, 实体: {entities_count})")
                else:
                    # 未识别到实体或处理失败
                    failed_prediction = {
                        "model_version": self.get("model_version"),
                        "score": 0.0,
                        "result": [],
                        "error": "未识别到任何实体",
                        "status": "failed"
                    }
                    predictions.append(failed_prediction)
                    if total_tasks > 1:
                        print(f"❌ 任务 {i+1} 失败 - 无实体 (耗时: {task_duration:.1f}s)")
                    
            except Exception as e:
                task_end_time = time.time()
                task_duration = task_end_time - task_start_time
                if total_tasks > 1:
                    print(f"❌ 任务 {i+1} 异常 (耗时: {task_duration:.1f}s): {str(e)[:50]}")
                failed_prediction = {
                    "model_version": self.get("model_version"),
                    "score": 0.0,
                    "result": [],
                    "error": f"处理异常: {str(e)}",
                    "status": "failed"
                }
                predictions.append(failed_prediction)
            
        
        # 处理完成后的总结
        end_time = time.time()
        total_duration = end_time - start_time
        processed_count = len(predictions)
        
        # 统计成功和失败的任务
        successful_tasks = sum(1 for p in predictions if p.get('result') and len(p.get('result', [])) > 0)
        failed_tasks = processed_count - successful_tasks
        total_entities = sum(len(p.get('result', [])) for p in predictions)
        
        if total_tasks > 1:
            print(f"\n📊 处理完成: {successful_tasks}/{processed_count} 成功, 总实体: {total_entities}, 耗时: {total_duration:.1f}s")
            if failed_tasks > 0:
                print(f"⚠️ {failed_tasks} 个任务处理失败")
            
            # 显示状态统计
            self._print_status()
        
        return ModelResponse(predictions=predictions)
    
    def _is_annotation_task(self, tasks: List[Dict]) -> bool:
        """判断是否为需要进行实体标注的任务"""
        if not tasks:
            return False
        
        # 检查任务是否包含需要标注的文本内容
        for task in tasks:
            task_data = task.get('data', {})
            
            # 检查是否有文本内容需要标注
            text_keys = ['text', 'content', 'prompt', 'question', 'description', 'query']
            has_text_content = False
            
            for key, value in task_data.items():
                if isinstance(value, str) and key in text_keys and value.strip():
                    has_text_content = True
                    break
            
            if has_text_content:
                # 检查是否已经有标注结果（如果有完整标注则可能是查看任务）
                annotations = task.get('annotations', [])
                if annotations:
                    # 如果有标注但是空的，说明需要预测
                    for annotation in annotations:
                        result = annotation.get('result', [])
                        if not result:  # 空标注，需要预测
                            return True
                else:
                    # 没有标注，需要预测
                    return True
        
        return False
    
    def _process_single_task(self, task: Dict) -> Optional[Dict]:
        """处理单个任务"""
        task_data = task.get('data', {})
        
        # 提取文本内容
        text_content = ""
        text_keys = ['text', 'content', 'prompt', 'question', 'description', 'query']
        
        for key, value in task_data.items():
            if isinstance(value, str) and key in text_keys:
                text_content = value
                break
        
        if not text_content:
            return None
        
        # 构建NER提示词（使用配置化的实体标签）
        json_format = get_json_format_example()
        
        # 按类别组织实体类型说明
        try:
            from entity_config import get_all_categories, get_entities_by_category
            categories = get_all_categories()
            categorized_examples = ""
            
            for category in categories:
                entities = get_entities_by_category(category)
                if entities:
                    # 特殊处理关系标签类别
                    if category == "关系标签":
                        categorized_examples += f"\n🔗 {category}类（语义关系实体）:\n"
                        for label_key, config in list(entities.items())[:8]:  # 关系标签显示更多
                            examples = "、".join(config['examples'][:3])  # 关系标签显示3个示例
                            description = config['description']
                            categorized_examples += f"   • {description}: {examples}\n"
                    else:
                        categorized_examples += f"\n📂 {category}类:\n"
                        for label_key, config in list(entities.items())[:5]:  # 每类最多显示5个实体，避免提示词过长
                            examples = "、".join(config['examples'][:2])  # 每个实体显示2个示例
                            description = config['description']
                            categorized_examples += f"   • {description}: {examples}\n"
            
            # 生成简化的实体列表（使用description）
            entity_descriptions = []
            for label_key in ENTITY_LABELS[:20]:  # 只显示前20个，避免过长
                if label_key in NER_ENTITY_CONFIG:
                    entity_descriptions.append(NER_ENTITY_CONFIG[label_key]['description'])
                else:
                    entity_descriptions.append(label_key)
            
            entity_labels_list = "、".join(entity_descriptions)
            if len(ENTITY_LABELS) > 20:
                entity_labels_list += f"等{len(ENTITY_LABELS)}种实体类型"
                
        except ImportError:
            # 备用方案：使用原来的格式
            categorized_examples = ""
            for label, config in NER_ENTITY_CONFIG.items():
                examples = "、".join(config['examples'][:2])
                categorized_examples += f"   {label}({config['description']}): {examples}\n"
            entity_labels_list = "、".join(ENTITY_LABELS)
        
        # 生成严格的标签列表（只显示标签名称，不显示描述）
        valid_labels_only = list(ENTITY_LABELS)
        labels_display = "、".join(valid_labels_only)
        
        prompt = f"""请对以下文本进行命名实体识别，识别出文本中存在的所有实体，包括传统的命名实体和关系表达。

📝 文本内容：
{text_content}

🎯 支持的实体类型及示例：{categorized_examples}

🔗 关系标签说明：
关系标签用于标注实体之间的语义关系，通常是动词短语或连接词。这些关系词同样作为实体进行标注：

💡 关系标签标注原则：
1. 标注完整的关系表达，而不是单个词汇
2. 包含关系动词及其前后的相关成分
3. 关系标签通常连接两个或多个其他实体
4. 示例：
   - "根据《防洪法》第十条规定" → "根据...规定"标注为"依据关系"
   - "水利部负责全国防汛工作" → "负责"标注为"责任关系"
   - "洪水导致农田受损" → "导致"标注为"因果关系"
   - "各部门协调配合抢险救灾" → "协调配合"标注为"协调关系"

🏥 疾病与健康实体说明：
疾病与健康类实体用于标注与洪涝灾害相关的疾病、健康状况和医疗防疫措施：
1. 疾病类型：传染病、水生疾病、环境病等
2. 健康状况：受伤、中毒、感染等状态描述
3. 医疗需求：救治、药品、医疗设备等需求
4. 防疫措施：消毒、疫苗、隔离等预防措施
示例：
   - "霍乱、痢疾等肠道传染病" → "疾病类型"
   - "灾民身体状况良好" → "健康状况"
   - "急需抗生素和消毒用品" → "医疗需求"
   - "对灾区进行全面消毒" → "防疫措施"

👥 人员信息实体说明：
人员信息类实体用于标注与人员相关的具体信息：
1. 人员信息：姓名、年龄、性别、身份等个人基本信息
2. 职务职称：职位、职级、专业技术职称等
3. 专业技能：专业能力、技术特长、工作经验等
4. 联系方式：电话、地址、邮箱等联系信息
示例：
   - "张三，男，45岁，党员" → "人员信息"
   - "高级工程师、项目负责人" → "职务职称"
   - "具有20年水利工程经验" → "专业技能"
   - "联系电话：139****8888" → "联系方式"

🔢 时间数量实体说明：
时间数量类实体用于标注各种时间和数量的具体信息：
1. 时间数量：具体的时间长度、期限、时长等
2. 持续时间：事件或状态的持续时长
3. 频率周期：重复发生的时间间隔、频率等
4. 数量规模：人数、物资数量、规模大小等
示例：
   - "连续降雨72小时" → "时间数量"
   - "警报持续3天" → "持续时间"
   - "每隔2小时巡查一次" → "频率周期"
   - "转移群众5000人" → "数量规模"

⚠️ 严格要求：
1. 识别文本中真实存在的所有实体，包括传统实体和关系
2. 准确标注实体的起始和结束位置（基于字符位置）
3. 标签名称必须严格使用下面列出的标签名称，一字不差
4. 禁止使用描述性文字、简化名称或任何变体形式
5. 如果实体类型不在标签列表中，则不要标注该实体
6. 关系标签要包含完整的关系表达，不要只标注单个动词

🔍 特别关注：
- 法律条款：识别"第X条"、"第X章"、"第X节"等法律条款格式
- 关系表达：识别表示依据、责任、管辖、因果等关系的动词短语
- 时序关系：识别表示时间先后的关系词汇
- 影响关系：识别表示影响、波及的关系表达

📋 请严格按照以下JSON格式返回结果：
{json_format}

🏷️ 严格使用以下标签名称（复制粘贴，一字不差）：
{labels_display}

❌ 禁止事项：
- 禁止使用描述性文字作为标签（如"政府部门"应使用"政府机构"）
- 禁止使用简化形式（如"条款"应使用"法律条款"）
- 禁止使用近似词汇（如"法规"应使用"法律法规"）
- 禁止自创标签名称
- 禁止只标注关系动词的单个词汇，要标注完整的关系表达

✅ 正确示例：
实体标签：
- 标签必须是："法律条款"，不能是"条款"、"法条"、"条文"
- 标签必须是："政府机构"，不能是"政府部门"、"机构"
- 标签必须是："法律法规"，不能是"法律"、"法规"、"条例"

关系标签：
- "根据《防洪法》规定" → "依据关系"
- "水务局负责河道管理" → "责任关系"  
- "洪水造成损失" → "因果关系"
- "各部门协调配合" → "协调关系"
- "汛期期间执行预案" → "执行关系"

疾病与健康标签：
- "霍乱疫情" → "疾病类型"
- "伤员情况稳定" → "健康状况"
- "需要医疗救助" → "医疗需求"
- "开展防疫消毒" → "防疫措施"

人员信息标签：
- "李明，工程师" → "人员信息"
- "防汛指挥长" → "职务职称"
- "水利专业技术" → "专业技能"
- "电话13912345678" → "联系方式"

时间数量标签：
- "持续48小时" → "时间数量"
- "警戒期3天" → "持续时间"
- "每2小时一次" → "频率周期"
- "转移5000人" → "数量规模"

请确保每个标签都从上面的列表中精确复制，关系标签要标注完整的关系表达！"""
        
        # 调用API
        api_response = self._call_modelscope_api(prompt)
        
        if api_response and api_response.strip():
            return self._format_prediction(api_response, task)
        
        # API调用失败或返回空响应
        print("❌ API调用失败或返回空响应")
        return None
    
    def _call_modelscope_api(self, prompt: str) -> Optional[str]:
        """🚀 简化的API调用（使用全局状态管理）"""
        max_total_attempts = len(available_models_global) * 2  # 总共尝试次数
        
        for attempt in range(max_total_attempts):
            # 确保API连接可用
            if not self._ensure_api_connection():
                continue  # 已经在连接时处理了切换，继续下一次尝试
            
            current_model = get_current_model()
            try:
                print(f"🔄 调用API (尝试 {attempt + 1}/{max_total_attempts})")
                print(f"   📡 模型: {current_model.split('/')[-1]} | ⏰ 超时: 250s | 💾 最大token: 2000")
                
                start_time = time.time()
                
                # 检测是否为推理模型
                is_thinking_model_flag = is_thinking_model(current_model)
                
                if is_thinking_model_flag:
                    # 推理模型使用流式处理
                    print("   🧠 检测到推理模型，使用流式处理")
                    content = self._handle_thinking_model_stream(current_model, prompt)
                else:
                    # 普通模型使用非流式处理
                    print("   📡 普通模型，使用非流式处理")
                    response = self.client.chat.completions.create(
                        model=current_model,
                        messages=[
                            {"role": "system", "content": "🌊 You are a specialized Knowledge Extraction Expert for Flood Disaster Management domain. 专注：洪涝灾害法律法规、应急预案、技术标准。能力：法律条款、应急流程、组织职责、技术标准、关系抽取。CRITICAL: You must extract both traditional entities AND relational expressions. Use EXACT label names from the provided list. Never use descriptions, abbreviations, or variations. For relation labels, extract complete phrases that express semantic relationships between entities. Always respond with valid JSON format containing only the specified labels."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=2000,
                        temperature=0.1,
                        top_p=0.9,
                        stream=False,
                        timeout=250
                    )
                    
                    if response.choices and len(response.choices) > 0:
                        content = response.choices[0].message.content
                        # 📋 详细输出普通模型接收到的信息
                        print(f"\n📥 =====  普通模型响应信息  =====")
                        print(f"📝 响应内容长度: {len(content) if content else 0}")
                        if content:
                            print(f"📝 完整响应内容:\n{content}")
                        print(f"📥 ==============================\n")
                    else:
                        content = None
                        print("❌ 普通模型响应为空或无choices")
                
                end_time = time.time()
                api_duration = end_time - start_time
                
                if content and content.strip():
                    # 成功
                    self._handle_success()
                    print(f"   ✅ 成功 (耗时: {api_duration:.1f}s, 长度: {len(content)})")
                    return content
                else:
                    print(f"⚠️ 返回空内容")
                    self._handle_failure("空响应")
                        
            except Exception as e:
                error_str = str(e)
                print(f"❌ API异常: {error_str[:100]}")
                
                # 检查是否需要立即切换
                if self._should_switch_immediately(error_str):
                    error_type = self._get_error_type(error_str)
                    print(f"🔄 立即切换错误: {error_type}")
                    self._handle_failure(f"立即切换-{error_type}", force_switch=True)
                else:
                    self._handle_failure(f"API异常-{self._get_error_type(error_str)}")
        
        print("❌ 所有尝试都失败")
        return None
    
    def _handle_thinking_model_stream(self, model: str, prompt: str) -> Optional[str]:
        """处理推理模型的流式响应"""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "🌊 You are a specialized Knowledge Extraction Expert for Flood Disaster Management domain. 专注：洪涝灾害法律法规、应急预案、技术标准。能力：法律条款、应急流程、组织职责、技术标准、关系抽取。CRITICAL: You must extract both traditional entities AND relational expressions. Use EXACT label names from the provided list. Never use descriptions, abbreviations, or variations. For relation labels, extract complete phrases that express semantic relationships between entities. Always respond with valid JSON format containing only the specified labels."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.1,
                top_p=0.9,
                stream=True,  # 推理模型使用流式
                timeout=250
            )
            
            reasoning_content = ""
            answer_content = ""
            done_reasoning = False
            
            print("   🔄 开始接收流式响应...")
            
            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                    # 推理过程内容
                    reasoning_chunk = chunk.choices[0].delta.reasoning_content
                    reasoning_content += reasoning_chunk
                    
                elif hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                    # 最终答案内容
                    answer_chunk = chunk.choices[0].delta.content
                    if not done_reasoning:
                        print("   🧠 推理完成，开始输出答案")
                        done_reasoning = True
                    answer_content += answer_chunk
            
            # 📋 详细输出接收到的信息，方便调试
            print(f"\n📥 =====  接收到的完整响应信息  =====")
            print(f"🧠 推理内容长度: {len(reasoning_content)}")
            if reasoning_content:
                print(f"🧠 推理内容前500字符:\n{reasoning_content[:500]}")
                if len(reasoning_content) > 500:
                    print(f"🧠 推理内容后500字符:\n{reasoning_content[-500:]}")
            
            print(f"\n📝 答案内容长度: {len(answer_content)}")
            if answer_content:
                print(f"📝 完整答案内容:\n{answer_content}")
            
            print(f"📥 ================================\n")
            
            # 优先使用答案内容，如果答案内容为空则使用推理内容
            if answer_content.strip():
                print(f"   ✅ 使用答案内容进行解析")
                # 对于DeepSeek模型，检查答案内容是否完整
                if 'deepseek' in model.lower():
                    print(f"   🔧 DeepSeek模型，检查JSON完整性...")
                    if not self._is_json_complete(answer_content):
                        print(f"   ⚠️ DeepSeek返回的JSON不完整，尝试修复")
                        repaired = self._repair_incomplete_json(answer_content)
                        if repaired:
                            return repaired
                return answer_content.strip()
            elif reasoning_content.strip():
                print(f"   ⚠️ 答案内容为空，尝试从推理内容提取")
                # 从推理内容中提取最终答案
                extracted = self._extract_answer_from_reasoning(reasoning_content)
                if extracted:
                    print(f"   📤 从推理内容提取的结果:\n{extracted[:500]}")
                return extracted
            else:
                print(f"   ❌ 推理和答案内容都为空")
                return None
                
        except Exception as e:
            print(f"   ❌ 流式处理失败: {str(e)[:100]}")
            raise e
    
    def _extract_answer_from_reasoning(self, reasoning_content: str) -> Optional[str]:
        """从推理内容中提取最终答案"""
        import re
        
        # 尝试提取JSON部分
        json_patterns = [
            r'```json\s*(.*?)\s*```',  # ```json 代码块
            r'\{[^{}]*"entities"[^{}]*:.*?\}',  # entities JSON
            r'\{.*?"entities".*?\}',  # 宽松的entities匹配
            r'\{.*\}',  # 最后的JSON匹配
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, reasoning_content, re.DOTALL)
            if matches:
                # 返回最后一个匹配的JSON（通常是最终结果）
                return matches[-1].strip()
        
        # 如果没有找到JSON，尝试提取答案部分
        answer_patterns = [
            r'(?:最终答案|答案|结果)[：:]\s*(.*)',
            r'(?:Final Answer|Answer)[：:]\s*(.*)',
            r'(?:因此|所以|综上)[，,]?\s*(.*)',
        ]
        
        for pattern in answer_patterns:
            match = re.search(pattern, reasoning_content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # 如果都找不到，返回推理内容的后半部分
        lines = reasoning_content.strip().split('\n')
        if len(lines) > 10:
            return '\n'.join(lines[-5:])  # 返回最后5行
        
        return reasoning_content.strip()
    
    def _repair_incomplete_json(self, json_str: str) -> Optional[str]:
        """修复不完整的JSON字符串"""
        try:
            print(f"🔧 开始修复JSON...")
            
            # 清理字符串
            cleaned = json_str.strip()
            if not cleaned:
                return None
            
            # 提取JSON部分（如果有代码块）
            import re
            json_match = re.search(r'\{.*', cleaned, re.DOTALL)
            if json_match:
                cleaned = json_match.group()
            
            print(f"🔧 清理后的JSON长度: {len(cleaned)}")
            print(f"🔧 清理后的JSON末尾50字符: ...{cleaned[-50:]}")
            
            # 首先尝试修复常见的JSON语法错误
            repaired = cleaned
            
            # 修复1: 移除末尾多余的逗号
            repaired = re.sub(r',\s*}', '}', repaired)
            repaired = re.sub(r',\s*]', ']', repaired)
            
            # 修复2: 确保JSON正确结束
            if '"entities"' in repaired and '[' in repaired:
                # 统计整个JSON的花括号和方括号平衡情况
                total_open_braces = repaired.count('{')
                total_close_braces = repaired.count('}')
                total_open_brackets = repaired.count('[')
                total_close_brackets = repaired.count(']')
                
                print(f"🔧 整体括号统计: 开花括号{total_open_braces}, 闭花括号{total_close_braces}")
                print(f"🔧 整体方括号统计: 开方括号{total_open_brackets}, 闭方括号{total_close_brackets}")
                
                # 检查是否以正确的符号结尾
                last_char = repaired.rstrip()[-1] if repaired.rstrip() else ''
                print(f"🔧 JSON最后字符: '{last_char}'")
                
                # 计算需要补全的括号数量
                missing_close_braces = total_open_braces - total_close_braces
                missing_close_brackets = total_open_brackets - total_close_brackets
                
                # 针对DeepSeek常见的情况：entities数组正确但缺少最外层花括号
                if last_char == ']' and missing_close_braces == 1 and missing_close_brackets == 0:
                    print(f"🔧 检测到DeepSeek典型错误：缺少最外层花括号")
                    repaired += '\n}'
                    print(f"🔧 添加最外层花括号后的JSON:\n{repaired}")
                    try:
                        json.loads(repaired)
                        print(f"✅ 添加最外层花括号修复成功")
                        return repaired
                    except json.JSONDecodeError as e:
                        print(f"❌ 添加花括号后仍有错误: {str(e)}")
                
                # 尝试直接解析看是否有其他语法错误
                if missing_close_braces == 0 and missing_close_brackets == 0:
                    print(f"🔧 括号已平衡，检查语法错误...")
                    try:
                        json.loads(repaired)
                        print(f"✅ JSON已经有效")
                        return repaired
                    except json.JSONDecodeError as e:
                        print(f"🔧 JSON语法错误: {str(e)}")
                        
                        # 修复3: 处理不完整的最后一个实体对象
                        if "Expecting ',' delimiter" in str(e):
                            print(f"🔧 处理不完整的实体对象...")
                            
                            # 找到最后一个完整的实体
                            entity_pattern = r'\{\s*"text":\s*"[^"]*",\s*"start":\s*\d+,\s*"end":\s*\d+,\s*"label":\s*"[^"]*"\s*\}'
                            matches = list(re.finditer(entity_pattern, repaired))
                            
                            if matches:
                                # 找到最后一个完整实体的结束位置
                                last_match = matches[-1]
                                last_entity_end = last_match.end()
                                
                                # 构建修复后的JSON
                                entities_part = repaired[:last_entity_end]
                                repaired = entities_part + '\n  ]\n}'
                                
                                print(f"🔧 移除不完整实体后的JSON:\n{repaired}")
                                try:
                                    json.loads(repaired)
                                    print(f"✅ 移除不完整实体修复成功")
                                    return repaired
                                except:
                                    pass
                
                # 一般的括号补全逻辑
                if missing_close_braces > 0 or missing_close_brackets > 0:
                    print(f"🔧 需要补全: {missing_close_braces}个}}, {missing_close_brackets}个]")
                    
                    # 补全花括号
                    for _ in range(missing_close_braces):
                        repaired += '\n    }'
                    
                    # 补全方括号
                    for _ in range(missing_close_brackets):
                        repaired += '\n  ]'
                    
                    # 确保最外层以花括号结尾
                    if not repaired.rstrip().endswith('}') and total_open_braces > total_close_braces:
                        repaired += '\n}'
                    
                    print(f"🔧 补全括号后的JSON:\n{repaired}")
                    try:
                        json.loads(repaired)
                        print(f"✅ 补全括号修复成功")
                        return repaired
                    except json.JSONDecodeError as e2:
                        print(f"❌ 补全括号后仍有错误: {str(e2)}")
            
            # 最后的尝试：重构JSON
            print(f"🔧 尝试重构JSON...")
            if '"entities"' in repaired:
                # 提取所有可能的实体
                entity_pattern = r'"text":\s*"([^"]*)",\s*"start":\s*(\d+),\s*"end":\s*(\d+),\s*"label":\s*"([^"]*)"'
                entities_matches = re.findall(entity_pattern, repaired)
                
                if entities_matches:
                    print(f"🔧 找到 {len(entities_matches)} 个完整实体，重构JSON")
                    
                    # 重新构建JSON
                    entities_list = []
                    for text, start, end, label in entities_matches:
                        entity = {
                            "text": text,
                            "start": int(start),
                            "end": int(end),
                            "label": label
                        }
                        entities_list.append(entity)
                    
                    reconstructed = {
                        "entities": entities_list
                    }
                    
                    reconstructed_json = json.dumps(reconstructed, ensure_ascii=False, indent=2)
                    print(f"🔧 重构的JSON:\n{reconstructed_json}")
                    return reconstructed_json
            
            print("❌ 所有修复策略都失败")
            return None
            
        except Exception as e:
            print(f"❌ JSON修复异常: {str(e)}")
            return None
    
    def _is_json_complete(self, json_str: str) -> bool:
        """检查JSON字符串是否完整"""
        try:
            # 简单的完整性检查
            cleaned = json_str.strip()
            if not cleaned:
                return False
            
            # 检查基本结构
            if not cleaned.startswith('{'):
                return False
            
            # 检查花括号平衡
            open_braces = cleaned.count('{')
            close_braces = cleaned.count('}')
            
            # 检查方括号平衡
            open_brackets = cleaned.count('[')
            close_brackets = cleaned.count(']')
            
            print(f"🔧 完整性检查: 开括号{open_braces}, 闭括号{close_braces}, 开方括号{open_brackets}, 闭方括号{close_brackets}")
            print(f"🔧 JSON开始: '{cleaned[:20]}...', 结束: '...{cleaned[-20:]}'")
            
            # 检查是否平衡
            if open_braces != close_braces or open_brackets != close_brackets:
                print(f"🔧 括号不平衡")
                return False
            
            # 即使括号平衡，也要检查是否以}结尾
            if not cleaned.endswith('}'):
                print(f"🔧 JSON不以}}结尾")
                return False
            
            # 尝试解析JSON
            try:
                json.loads(cleaned)
                print(f"🔧 JSON解析成功，格式完整")
                return True
            except json.JSONDecodeError as e:
                print(f"🔧 JSON解析失败，有语法错误: {str(e)}")
                return False
                
        except Exception as e:
            print(f"🔧 完整性检查异常: {str(e)}")
            return False
    
    def _map_invalid_label(self, invalid_label: str) -> Optional[str]:
        """映射无效标签到有效标签"""
        # 常见的标签映射关系
        label_mapping = {
            # 地理相关映射
            "影响范围": "行政区划",
            "地理位置": "行政区划", 
            "地区": "行政区划",
            "区域": "行政区划",
            "范围": "行政区划",
            
            # 时间相关映射
            "时间": "时间节点",
            "日期": "时间节点",
            "期间": "时间节点",
            
            # 灾害相关映射
            "灾害": "灾害类型",
            "自然灾害": "灾害类型",
            "事故": "灾害类型",
            
            # 机构相关映射
            "机构": "政府机构",
            "部门": "政府机构",
            "组织": "政府机构",
            
            # 法律相关映射
            "法律": "法律法规",
            "法规": "法律法规",
            "条例": "法律法规",
            "规定": "法律法规",
            
            # 数据相关映射
            "数据": "降雨数据",
            "数量": "降雨数据",
            "量级": "降雨数据",
        }
        
        # 直接映射
        if invalid_label in label_mapping:
            mapped = label_mapping[invalid_label]
            if mapped in ENTITY_LABELS:
                return mapped
        
        # 模糊匹配（包含关系）
        invalid_lower = invalid_label.lower()
        for invalid_key, valid_label in label_mapping.items():
            if invalid_key.lower() in invalid_lower or invalid_lower in invalid_key.lower():
                if valid_label in ENTITY_LABELS:
                    return valid_label
        
        # 如果还是找不到，尝试相似度匹配
        for valid_label in ENTITY_LABELS:
            # 简单的相似度检查（共同字符）
            common_chars = set(invalid_label) & set(valid_label)
            if len(common_chars) >= min(2, len(invalid_label) // 2):
                return valid_label
        
        return None
    
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
    
    def _format_prediction(self, api_response: str, task: Dict) -> Dict:
        """格式化预测结果为Label Studio格式"""
        
        prediction = {
            "model_version": self.get("model_version"),
            "score": 0.95,
            "result": []
        }
        
        # 尝试解析NER结果
        ner_results = self._parse_ner_response(api_response, task)
        if ner_results and len(ner_results) > 0:
            prediction["result"] = ner_results
            prediction["score"] = 0.95
            return prediction
        
        # 如果没有识别到任何实体，返回失败信息
        prediction["score"] = 0.0
        prediction["result"] = []
        return None
    
    def _parse_ner_response(self, api_response: str, task: Dict) -> Optional[List[Dict]]:
        """解析AI返回的命名实体识别JSON结果，并用正则表达式进行补充"""
        
        # 获取原始文本
        task_data = task.get('data', {})
        original_text = ""
        for key in ['text', 'content', 'prompt', 'question', 'description', 'query']:
            if key in task_data and isinstance(task_data[key], str):
                original_text = task_data[key]
                break
        
        if not original_text:
            return None
        
        # 初始化结果列表
        results = []
        ai_entities = []
        
        # 第一步：解析AI模型的识别结果
        if api_response and api_response.strip():
            ai_entities = self._parse_ai_entities(api_response, original_text)
            if ai_entities:
                results.extend(ai_entities)
        
        # 第二步：使用正则表达式进行补充识别
        regex_entities = self._extract_regex_entities(original_text, ai_entities)
        if regex_entities:
            results.extend(regex_entities)
        
        # 第三步：去重和排序
        final_results = self._deduplicate_entities(results)
        
        return final_results if final_results else None
    
    def _parse_ai_entities(self, api_response: str, original_text: str) -> List[Dict]:
        """解析AI模型返回的实体"""
        ai_results = []
        
        print(f"\n🔍 =====  开始解析AI响应  =====")
        print(f"📝 原始响应长度: {len(api_response)}")
        print(f"📝 原始响应内容:\n{api_response}")
        print(f"🔍 ============================\n")
        
        try:
            # 尝试直接解析JSON
            try:
                print("🔍 尝试直接解析JSON...")
                ner_data = json.loads(api_response.strip())
                print("✅ 直接解析JSON成功")
            except json.JSONDecodeError as e:
                print(f"❌ 直接JSON解析失败: {str(e)}")
                # 尝试提取JSON部分
                import re
                
                # 多种JSON提取策略
                patterns = [
                    r'\{[^{}]*"entities"[^{}]*:.*?\}',  # 最严格的entities匹配
                    r'\{.*?"entities".*?\}',            # 宽松的entities匹配
                    r'\{.*\}',                          # 最宽松的JSON匹配
                ]
                
                ner_data = None
                for i, pattern in enumerate(patterns):
                    print(f"🔍 尝试模式 {i+1}: {pattern}")
                    json_match = re.search(pattern, api_response, re.DOTALL)
                    if json_match:
                        extracted_json = json_match.group()
                        print(f"🔍 模式 {i+1} 提取到: {extracted_json[:200]}")
                        try:
                            ner_data = json.loads(extracted_json)
                            print(f"✅ 模式 {i+1} 解析成功")
                            break
                        except json.JSONDecodeError as e2:
                            print(f"❌ 模式 {i+1} 解析失败: {str(e2)}")
                            continue
                
                if not ner_data:
                    print("❌ 所有JSON提取模式都失败，尝试JSON修复...")
                    # 尝试修复不完整的JSON
                    repaired_json = self._repair_incomplete_json(api_response)
                    if repaired_json:
                        try:
                            ner_data = json.loads(repaired_json)
                            print("✅ JSON修复成功")
                        except json.JSONDecodeError as e3:
                            print(f"❌ JSON修复后仍然解析失败: {str(e3)}")
                            return ai_results
                    else:
                        print("❌ JSON修复失败")
                        return ai_results
            
            # 检查entities字段
            if 'entities' not in ner_data or not isinstance(ner_data['entities'], list):
                print(f"❌ 缺少entities字段或格式错误")
                print(f"📝 解析到的数据结构: {type(ner_data)}")
                print(f"📝 数据内容: {ner_data}")
                return ai_results
            
            entities = ner_data['entities']
            print(f"✅ 找到entities字段，包含 {len(entities)} 个实体")
            
            # 转换为Label Studio格式
            for i, entity in enumerate(entities):
                print(f"\n🔍 处理实体 {i+1}/{len(entities)}: {entity}")
                # 验证必需字段
                required_fields = ['text', 'start', 'end', 'label']
                missing_fields = [field for field in required_fields if field not in entity]
                if missing_fields:
                    print(f"   ❌ 缺少必需字段: {missing_fields}")
                    continue
                
                start = entity['start']
                end = entity['end']
                text = entity['text']
                original_label = entity['label']
                
                print(f"   📝 原始实体: text='{text}', start={start}, end={end}, label='{original_label}'")
                
                # 严格验证标签
                validated_label = validate_label(original_label)
                if not validated_label:
                    print(f"   ❌ 标签验证失败: '{original_label}' 不在有效标签列表中")
                    print(f"   📝 有效标签列表前10个: {list(ENTITY_LABELS)[:10]}")
                    # 尝试标签映射修正
                    mapped_label = self._map_invalid_label(original_label)
                    if mapped_label:
                        print(f"   🔧 尝试标签映射: '{original_label}' → '{mapped_label}'")
                        validated_label = mapped_label
                    else:
                        continue
                
                print(f"   ✅ 标签验证成功: '{original_label}' → '{validated_label}'")
                
                # 使用验证通过的标签
                label = validated_label
                
                # 验证位置信息基本合理性
                if not isinstance(start, int) or not isinstance(end, int) or start < 0:
                    print(f"   ❌ 位置信息格式错误: start={start}({type(start)}), end={end}({type(end)})")
                    continue
                
                print(f"   🔍 开始位置修正...")
                # 先尝试修正位置，再进行范围检查
                corrected_start, corrected_end, corrected_text = self._correct_entity_position(
                    original_text, text, start, end
                )
                
                # 检查修正后的位置是否合理
                if corrected_start is None or corrected_end is None or corrected_text is None:
                    print(f"   ❌ 位置修正失败: 无法在原文中找到实体")
                    continue
                
                # 验证修正后的位置不超出文本长度
                if corrected_end > len(original_text) or corrected_start < 0:
                    print(f"   ❌ 修正后位置超出范围: start={corrected_start}, end={corrected_end}, 文本长度={len(original_text)}")
                    continue
                
                print(f"   ✅ 位置修正成功: start={corrected_start}, end={corrected_end}, text='{corrected_text}'")
                
                if corrected_text:
                    # 验证修正后的实体是否合理
                    if self._is_valid_entity(corrected_text, validated_label):
                        result = {
                            "from_name": "label",
                            "to_name": "text",
                            "type": "labels",
                            "value": {
                                "start": corrected_start,
                                "end": corrected_end,
                                "text": corrected_text,
                                "labels": [label]
                            },
                            "source": "ai"  # 标记来源为AI
                        }
                        
                        ai_results.append(result)
                        print(f"   ✅ 实体添加成功: '{corrected_text}' [{label}]")
                    else:
                        print(f"   ❌ 实体验证失败: '{corrected_text}' 不符合 {validated_label} 类型要求")
            
            print(f"\n📊 AI实体解析结果: 成功处理 {len(ai_results)} 个实体")
            return ai_results
            
        except Exception as e:
            print(f"❌ AI实体解析异常: {str(e)}")
            return ai_results
    
    def _extract_regex_entities(self, original_text: str, existing_entities: List[Dict]) -> List[Dict]:
        """使用正则表达式补充识别实体"""
        regex_results = []
        
        try:
            # 获取已识别实体的位置范围，避免重复
            existing_ranges = set()
            for entity in existing_entities:
                value = entity.get('value', {})
                start = value.get('start', -1)
                end = value.get('end', -1)
                if start >= 0 and end > start:
                    # 扩展范围以避免重叠
                    for pos in range(max(0, start-1), min(len(original_text), end+1)):
                        existing_ranges.add(pos)
            
            # 从entity_config获取正则模式
            from entity_config import get_entity_config
            entity_config = get_entity_config()
            
            # 遍历所有配置的实体类型
            for label_key, config in entity_config.items():
                if 'patterns' not in config or not config['patterns']:
                    continue
                
                patterns = config['patterns']
                description = config['description']
                
                # 对每个正则模式进行匹配
                for pattern in patterns:
                    try:
                        import re
                        matches = re.finditer(pattern, original_text)
                        
                        for match in matches:
                            start = match.start()
                            end = match.end()
                            text = match.group()
                            
                            # 检查是否与已识别的实体重叠
                            overlapping = any(pos in existing_ranges for pos in range(start, end))
                            if overlapping:
                                continue
                            
                            # 验证实体是否合理
                            if self._is_valid_entity(text, label_key):
                                result = {
                                    "from_name": "label",
                                    "to_name": "text",
                                    "type": "labels",
                                    "value": {
                                        "start": start,
                                        "end": end,
                                        "text": text,
                                        "labels": [label_key]  # 使用标签键名而不是description
                                    },
                                    "source": "regex"  # 标记来源为正则
                                }
                                
                                regex_results.append(result)
                                
                                # 更新已识别范围
                                for pos in range(start, end):
                                    existing_ranges.add(pos)
                                
                    except re.error:
                        continue
            
            return regex_results
            
        except Exception:
            return regex_results
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """去重和排序实体"""
        
        # 按起始位置排序
        sorted_entities = sorted(entities, key=lambda x: x.get('value', {}).get('start', 0))
        
        # 去重逻辑：如果两个实体位置重叠超过50%，保留置信度高的
        deduplicated = []
        
        for current in sorted_entities:
            current_value = current.get('value', {})
            current_start = current_value.get('start', 0)
            current_end = current_value.get('end', 0)
            current_text = current_value.get('text', '')
            current_source = current.get('source', 'unknown')
            
            # 检查是否与已添加的实体重叠
            should_add = True
            for i, existing in enumerate(deduplicated):
                existing_value = existing.get('value', {})
                existing_start = existing_value.get('start', 0)
                existing_end = existing_value.get('end', 0)
                existing_text = existing_value.get('text', '')
                existing_source = existing.get('source', 'unknown')
                
                # 计算重叠度
                overlap_start = max(current_start, existing_start)
                overlap_end = min(current_end, existing_end)
                
                if overlap_start < overlap_end:  # 有重叠
                    overlap_length = overlap_end - overlap_start
                    current_length = current_end - current_start
                    existing_length = existing_end - existing_start
                    
                    # 计算重叠比例（相对于较短的实体）
                    min_length = min(current_length, existing_length)
                    overlap_ratio = overlap_length / min_length if min_length > 0 else 0
                    
                    if overlap_ratio > 0.5:  # 重叠超过50%
                        
                        # 优先级：AI > 正则，长实体 > 短实体
                        should_replace = False
                        if current_source == 'ai' and existing_source == 'regex':
                            should_replace = True
                        elif current_source == existing_source and current_length > existing_length:
                            should_replace = True
                        
                        if should_replace:
                            deduplicated[i] = current
                        
                        should_add = False
                        break
            
            if should_add:
                deduplicated.append(current)
        
        # 最终按位置排序
        final_results = sorted(deduplicated, key=lambda x: x.get('value', {}).get('start', 0))
        
        # 移除source标记（Label Studio不需要）
        for result in final_results:
            result.pop('source', None)
        
        return final_results
    
    def _correct_entity_position(self, original_text: str, entity_text: str, start: int, end: int) -> tuple:
        """修正实体位置"""
        # 首先检查原始位置是否正确
        if start < len(original_text) and end <= len(original_text):
            extracted = original_text[start:end]
            if extracted == entity_text:
                return start, end, entity_text
        
        # 清理实体文本（去除多余空格和标点）
        clean_entity = entity_text.strip()
        if not clean_entity:
            return None, None, None
        
        # 在原文中搜索实体文本
        try:
            # 尝试精确匹配
            exact_start = original_text.find(clean_entity)
            if exact_start != -1:
                exact_end = exact_start + len(clean_entity)
                return exact_start, exact_end, clean_entity
            
            # 尝试模糊匹配（去除标点符号）
            import re
            clean_text_for_search = re.sub(r'[^\w\u4e00-\u9fff]', '', clean_entity)
            if len(clean_text_for_search) >= 2:  # 至少2个字符才进行模糊匹配
                for i in range(len(original_text) - len(clean_text_for_search) + 1):
                    slice_text = original_text[i:i + len(clean_text_for_search)]
                    clean_slice = re.sub(r'[^\w\u4e00-\u9fff]', '', slice_text)
                    if clean_slice == clean_text_for_search:
                        return i, i + len(clean_text_for_search), slice_text
            
            # 如果还是找不到，尝试部分匹配
            if len(clean_entity) >= 3:
                core_part = clean_entity[:min(len(clean_entity), 5)]  # 取前几个字符作为核心
                core_start = original_text.find(core_part)
                if core_start != -1:
                    # 尝试扩展匹配
                    extended_end = min(core_start + len(clean_entity) + 2, len(original_text))
                    extended_text = original_text[core_start:extended_end]
                    return core_start, extended_end, extended_text
            
        except Exception:
            pass
        
        return None, None, None
    
    def _is_valid_entity(self, text: str, label: str) -> bool:
        """简化的实体验证（基础规则验证）"""
        if not text or len(text.strip()) < 1:
            return False
        
        # 去除首尾标点符号和空格
        clean_text = text.strip()
        
        # 不能只是标点符号
        import re
        if re.match(r'^[^\w\u4e00-\u9fff]+$', clean_text):
            return False
        
        # 基础长度验证
        if len(clean_text) < 1:
            return False
        
        # 验证标签是否有效
        if label not in ENTITY_LABELS:
            return False
        
        # 特殊验证：关系标签
        if label.endswith("关系"):
            # 关系标签应该包含动词或连接词
            relation_keywords = ['根据', '依据', '按照', '负责', '主管', '管辖', '导致', '造成', '引起', 
                               '之前', '之后', '同时', '包括', '包含', '属于', '影响', '波及', '协调', 
                               '配合', '执行', '实施', '补偿', '赔偿']
            
            if not any(keyword in clean_text for keyword in relation_keywords):
                # 对于关系标签，放宽验证，只要不是纯标点就接受
                pass
        
        return True
    
    
    def fit(self, event, data, **kwargs):
        """训练/更新模型"""
        self.set('my_data', 'updated_data')
        self.set('model_version', 'updated_version')
        print(f"✅ 模型已更新 ({event})")


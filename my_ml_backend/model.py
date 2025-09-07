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



class NewModel(LabelStudioMLBase):
    """Custom ML Backend model
    """
    
    def setup(self):
        """Configure any parameters of your model here
        """
        self.set("model_version", "2.0.0-洪涝灾害专用版")
        
        # 魔塔社区API配置
        self.api_key = os.getenv('MODELSCOPE_API_KEY', 'ms-7fa00741-856a-4134-80d2-f296b15c0e76')
        self.api_base_url = os.getenv('MODELSCOPE_API_URL', 'https://api-inference.modelscope.cn/v1')
        
        # 🔄 多模型配置 - 按稳定性和性能排序
        self.available_models = [
                'Qwen/Qwen3-Coder-480B-A35B-Instruct', # 备用模型1 - 最新Qwen3
                'Qwen/Qwen3-235B-A22B-Instruct-2507', # 备用模型4 - 容易超时，排最后
                'Qwen/Qwen3-235B-A22B',
                'Qwen/Qwen3-235B-A22B-Thinking-2507',               
                'deepseek-ai/DeepSeek-V3.1', # 备用模型2 - 中等参数量  
                'deepseek-ai/DeepSeek-R1-0528', # 备用模型3 - 平衡性能
                'deepseek-ai/DeepSeek-V3' ,
                'ZhipuAI/GLM-4.5', # 主力模型 - 稳定性好
               
        ]
        
        # 🎯 模型切换控制
        self.max_model_failures = 2  # 模型连续失败阈值
        
        # 🔄 程序启动时总是从第一个模型开始，运行时状态通过内存保持
        self.current_model_index = 0  # 每次启动都重置到第一个模型
        self.model_consecutive_failures = 0  # 重置失败计数
        self.model_failure_history = {}  # 重置失败历史
        
        # 📝 说明：程序启动时重置模型状态，但运行期间会智能切换模型
        # - 程序重启：从第一个模型开始
        # - 运行期间：遇到429等错误会智能切换到其他模型
        # - 状态保持：只在当前会话期间有效，重启后重置
        
        # 动态获取当前模型名称
        self.model_name = self.available_models[self.current_model_index]
        
        # 延迟初始化客户端，只在需要时连接
        self.client = None
        self._api_initialized = False
        
        print("✅ 洪涝灾害专用ML后端初始化完成")
        print(f"🎯 当前模型: {self.model_name} (索引: {self.current_model_index})")
        print(f"📋 备用模型: {len(self.available_models)-1} 个")
        print(f"🔄 智能切换: 429错误立即切换，连续失败{self.max_model_failures}次切换")
        print(f"⏰ 超时设置: 250秒（给大模型充足处理时间）")
        print(f"🌊 专业领域: 洪涝灾害知识提取 v2.0.0")
        print(f"🚀 启动策略: 每次程序启动都从第一个模型开始，运行期间智能切换")
    
    def _save_model_state(self):
        """💾 在运行期间临时保存模型状态（不持久化到磁盘）"""
        # 注意：为了确保每次程序启动都从第一个模型开始，
        # 这里不再将状态持久化到缓存，只在内存中保持状态
        # 这样程序重启后会自动重置到第一个模型
        pass  # 移除持久化逻辑，只保持运行时状态
    
    def reset_model_state(self):
        """🔄 重置模型状态到初始状态（手动调用）"""
        print("🔄 重置模型状态到初始状态...")
        self.current_model_index = 0
        self.model_consecutive_failures = 0
        self.model_failure_history = {}
        self.model_name = self.available_models[0]
        
        # 重置API连接
        self._api_initialized = False
        self.client = None
        
        print(f"✅ 状态已重置，当前模型: {self.model_name}")
        return True
        
    def _switch_to_next_model(self):
        """切换到下一个可用模型"""
        # 记录当前模型的失败
        current_model = self.available_models[self.current_model_index]
        if current_model not in self.model_failure_history:
            self.model_failure_history[current_model] = 0
        self.model_failure_history[current_model] += self.model_consecutive_failures
        
        # 切换到下一个模型
        old_model = self.model_name
        old_index = self.current_model_index
        
        self.current_model_index = (self.current_model_index + 1) % len(self.available_models)
        self.model_name = self.available_models[self.current_model_index]
        self.model_consecutive_failures = 0  # 重置新模型的失败计数
        
        # 重置API连接（强制重新连接新模型）
        self._api_initialized = False
        self.client = None
        
        print(f"🔄 模型切换: {old_model} → {self.model_name}")
        print(f"📊 切换原因: 连续失败 {self.max_model_failures} 次")
        
        # 如果回到了第一个模型，说明所有模型都试过了
        if self.current_model_index == 0 and old_index != 0:
            print("⚠️ 所有模型都已尝试，回到主力模型")
        
        # 注意：状态只在运行时保持，程序重启后会重置到第一个模型
        return True
    
    def _handle_model_failure(self, reason: str = "未知错误", force_switch: bool = False):
        """处理模型失败，决定是否切换模型"""
        self.model_consecutive_failures += 1
        current_model = self.available_models[self.current_model_index]
        
        print(f"❌ 模型 {current_model} 失败: {reason} (连续失败: {self.model_consecutive_failures}/{self.max_model_failures})")
        
        # 强制切换或达到失败阈值时切换模型
        should_switch = force_switch or (self.model_consecutive_failures >= self.max_model_failures)
        
        if should_switch:
            if len(self.available_models) > 1:  # 只有在有多个模型时才切换
                if force_switch:
                    print(f"🚨 强制切换模型: {reason}")
                else:
                    print(f"📊 达到失败阈值，切换模型")
                self._switch_to_next_model()
                return True  # 表示已切换模型
            else:
                print("⚠️ 只有一个模型可用，无法切换")
                return False
        
        return False  # 没有切换模型
    
    def _handle_model_success(self):
        """处理模型成功，重置失败计数"""
        if self.model_consecutive_failures > 0:
            print(f"✅ 模型 {self.model_name} 恢复正常")
            self.model_consecutive_failures = 0
    
    def _should_switch_immediately(self, error_str: str) -> bool:
        """判断是否需要立即切换模型（不重试）"""
        immediate_switch_patterns = [
            # API限流错误 - 立即切换
            "429",
            "Too Many Requests", 
            "Request limit exceeded",
            "Rate limit exceeded",
            "Quota exceeded",
            
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
        if any(x in error_lower for x in ["429", "too many requests", "rate limit", "quota exceeded"]):
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
        """确保API连接已初始化（延迟初始化）"""
        if self._api_initialized and self.client:
            return True
        
        if not self.api_key:
            print("⚠️ 请设置MODELSCOPE_API_KEY环境变量")
            return False
        
        try:
            print("🔄 正在连接大模型API...")
            self.client = OpenAI(
                base_url=self.api_base_url,
                api_key=self.api_key,
                max_retries=0,  # 🚨 禁用OpenAI内置重试，让智能切换接管
                timeout=250.0   # ⏰ 设置250秒超时，给大模型充足的处理时间
            )
            
            # 测试连接（使用较短的测试请求）
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
                temperature=0.1,
                timeout=250  # 测试连接使用250秒超时
            )
            
            self._api_initialized = True
            print("✅ 大模型API连接成功")
            return True
            
        except Exception as e:
            error_str = str(e)
            print(f"❌ API连接失败: {error_str[:100]}")
            
            # 🚨 检查是否需要立即切换模型（429等错误）
            should_switch_immediately = self._should_switch_immediately(error_str)
            
            if should_switch_immediately:
                error_type = self._get_error_type(error_str)
                print(f"🔄 连接测试检测到需要立即切换的错误: {error_type}")
                self._handle_model_failure(f"连接测试-{error_type}", force_switch=True)
                
                # 重置连接状态，让调用方可以重试下一个模型
                self.client = None
                self._api_initialized = False
                return False
            else:
                # 普通错误，不立即切换
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
        
        # 只在需要进行标注预测时才连接大模型
        if not self._ensure_api_connection():
            print("❌ 无法连接大模型API，返回空预测结果")
            empty_predictions = []
            for task in tasks:
                empty_prediction = {
                    "model_version": self.get("model_version"),
                    "score": 0.0,
                    "result": [],
                    "error": "API连接失败"
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
            
            # 显示模型使用统计
            self._print_model_statistics()
        
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

请确保每个标签都从上面的列表中精确复制，关系标签要标注完整的关系表达！"""
        
        # 调用API
        api_response = self._call_modelscope_api(prompt)
        
        if api_response and api_response.strip():
            return self._format_prediction(api_response, task)
        
        # API调用失败或返回空响应
        print("❌ API调用失败或返回空响应")
        return None
    
    def _call_modelscope_api(self, prompt: str) -> Optional[str]:
        """调用魔塔社区API（支持智能模型切换）"""
        max_retries_per_model = 2  # 每个模型最多重试2次再切换
        
        for attempt in range(max_retries_per_model):
            # 确保API连接可用
            if not self._ensure_api_connection():
                # 注意：_ensure_api_connection内部已经处理了429等需要立即切换的错误
                # 这里只需要处理普通的连接失败
                if self.model_consecutive_failures == 0:  # 如果失败计数为0，说明_ensure_api_connection没有处理
                    self._handle_model_failure("连接失败")
                
                if self._has_more_models_to_try():
                    continue  # 尝试下一个模型
                return None
            
            try:
                print(f"🔄 调用模型: {self.model_name} (尝试 {attempt + 1}/{max_retries_per_model})")
                print(f"   ⏰ 超时设置: 250秒 | 💾 最大token: 2000")
                
                start_time = time.time()
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "🌊 You are a specialized Knowledge Extraction Expert for Flood Disaster Management domain. 专注：洪涝灾害法律法规、应急预案、技术标准。能力：法律条款、应急流程、组织职责、技术标准、关系抽取。CRITICAL: You must extract both traditional entities AND relational expressions. Use EXACT label names from the provided list. Never use descriptions, abbreviations, or variations. For relation labels, extract complete phrases that express semantic relationships between entities. Always respond with valid JSON format containing only the specified labels."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000,
                    temperature=0.1,
                    top_p=0.9,
                    stream=False,
                    timeout=250  # 🕐 实体识别任务使用250秒超时
                )
                
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    end_time = time.time()
                    api_duration = end_time - start_time
                    
                    if content and content.strip():
                        # API调用成功，重置失败计数
                        self._handle_model_success()
                        print(f"   ✅ 调用成功 (耗时: {api_duration:.1f}s, 响应长度: {len(content)} 字符)")
                        return content
                    else:
                        print(f"⚠️ 模型 {self.model_name} 返回空内容")
                        # 空内容也算失败
                        self._handle_model_failure("空响应")
                else:
                    print(f"⚠️ 模型 {self.model_name} 响应格式异常")
                    self._handle_model_failure("格式异常")
                    
            except Exception as e:
                error_str = str(e)
                print(f"❌ 模型 {self.model_name} API调用异常: {error_str[:100]}")
                
                # 🚨 检查特殊错误类型，立即切换模型
                should_switch_immediately = self._should_switch_immediately(error_str)
                
                if should_switch_immediately:
                    print(f"🔄 检测到需要立即切换的错误: {self._get_error_type(error_str)}")
                    self._handle_model_failure("立即切换", force_switch=True)
                    if self._has_more_models_to_try():
                        break  # 立即跳出重试循环，切换模型
                    else:
                        print("❌ 所有模型都已尝试失败")
                        return None
                else:
                    self._handle_model_failure(f"API异常: {self._get_error_type(error_str)}")
            
            # 如果当前模型失败，检查是否需要切换
            if self.model_consecutive_failures >= self.max_model_failures:
                if self._has_more_models_to_try():
                    print(f"🔄 达到失败阈值，切换到下一个模型...")
                    break  # 跳出重试循环，切换模型
                else:
                    print("❌ 所有模型都已尝试失败")
                    return None
        
        # 如果所有重试都失败，返回None
        return None
    
    def _has_more_models_to_try(self) -> bool:
        """检查是否还有其他模型可以尝试"""
        return len(self.available_models) > 1
        
    def _print_model_statistics(self):
        """打印模型使用统计信息"""
        print(f"\n🤖 模型状态统计:")
        print(f"   🎯 当前模型: {self.model_name}")
        print(f"   📊 当前失败: {self.model_consecutive_failures}/{self.max_model_failures}")
        
        if self.model_failure_history:
            print(f"   📈 失败历史:")
            for model, failures in self.model_failure_history.items():
                if failures > 0:
                    model_short = model.split('/')[-1] if '/' in model else model
                    status = "❌" if failures >= self.max_model_failures else "⚠️"
                    print(f"     {status} {model_short}: {failures} 次")
        
        # 显示可用模型列表
        print(f"   🔧 可用模型池: {len(self.available_models)} 个")
        for i, model in enumerate(self.available_models):
            if i == self.current_model_index:
                status = "🎯 使用中"
            elif model in self.model_failure_history and self.model_failure_history[model] > 0:
                status = "❌ 已失败"
            else:
                status = "✅ 待用"
            
            model_short = model.split('/')[-1] if '/' in model else model
            print(f"     {status} {model_short}")
        
        print(f"   🔄 切换策略: 429错误立即切换，其他错误达到{self.max_model_failures}次后切换")
    
    def get_model_status(self) -> Dict:
        """获取模型状态信息（供外部调用）"""
        return {
            "current_model": self.model_name,
            "current_model_index": self.current_model_index,
            "consecutive_failures": self.model_consecutive_failures,
            "max_failures": self.max_model_failures,
            "available_models": self.available_models,
            "failure_history": self.model_failure_history.copy(),
            "status_persisted": False,  # 状态不持久化，程序重启后重置
            "restart_behavior": "程序重启后从第一个模型开始"
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
        
        try:
            # 尝试直接解析JSON
            try:
                ner_data = json.loads(api_response.strip())
            except json.JSONDecodeError as e:
                # 尝试提取JSON部分
                import re
                
                # 多种JSON提取策略
                patterns = [
                    r'\{[^{}]*"entities"[^{}]*:.*?\}',  # 最严格的entities匹配
                    r'\{.*?"entities".*?\}',            # 宽松的entities匹配
                    r'\{.*\}',                          # 最宽松的JSON匹配
                ]
                
                ner_data = None
                for pattern in patterns:
                    json_match = re.search(pattern, api_response, re.DOTALL)
                    if json_match:
                        try:
                            ner_data = json.loads(json_match.group())
                            break
                        except json.JSONDecodeError:
                            continue
                
                if not ner_data:
                    return ai_results
            
            # 检查entities字段
            if 'entities' not in ner_data or not isinstance(ner_data['entities'], list):
                return ai_results
            
            entities = ner_data['entities']
            
            # 转换为Label Studio格式
            for entity in entities:
                # 验证必需字段
                if not all(key in entity for key in ['text', 'start', 'end', 'label']):
                    continue
                
                start = entity['start']
                end = entity['end']
                text = entity['text']
                original_label = entity['label']
                
                # 严格验证标签
                validated_label = validate_label(original_label)
                if not validated_label:
                    continue
                
                # 使用验证通过的标签
                label = validated_label
                
                # 验证位置信息基本合理性
                if not isinstance(start, int) or not isinstance(end, int) or start < 0:
                    continue
                
                # 先尝试修正位置，再进行范围检查
                corrected_start, corrected_end, corrected_text = self._correct_entity_position(
                    original_text, text, start, end
                )
                
                # 检查修正后的位置是否合理
                if corrected_start is None or corrected_end is None or corrected_text is None:
                    continue
                
                # 验证修正后的位置不超出文本长度
                if corrected_end > len(original_text) or corrected_start < 0:
                    continue
                
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
            
            return ai_results
            
        except Exception:
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


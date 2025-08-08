from typing import List, Dict, Optional
import json
import os
from openai import OpenAI
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse


# ==================== 命名实体配置 ====================
# 从配置文件导入实体配置
try:
    from entity_config import get_entity_config, get_entity_labels
    NER_ENTITY_CONFIG = get_entity_config()
    ENTITY_LABELS = get_entity_labels()
    print(f"✅ 从配置文件加载了 {len(ENTITY_LABELS)} 种实体类型")
except ImportError:
    # 如果配置文件不存在，使用默认配置
    print("⚠️ 配置文件不存在，使用默认配置")
    NER_ENTITY_CONFIG = {
        "PER": {"description": "人名", "examples": ["张三", "李四"], "invalid_patterns": [r'发生', r'起火']},
        "LOC": {"description": "地名", "examples": ["北京", "上海"], "invalid_patterns": []},
        "ORG": {"description": "组织", "examples": ["公司", "学校"], "invalid_patterns": []},
        "TIME": {"description": "时间", "examples": ["今天", "明天"], "valid_patterns": [r'\d+年', r'\d+月']},
        "EVENT": {"description": "事件", "examples": ["会议", "活动", "火灾","起火","扑灭"], "invalid_patterns": []},
        "QUANTITY": {"description": "数量", "examples": ["100个", "50万"], "valid_patterns": [r'\d+']},
    }
    ENTITY_LABELS = list(NER_ENTITY_CONFIG.keys())

# 生成实体类型说明文本
def get_entity_types_description():
    """生成实体类型的说明文本"""
    descriptions = []
    for label, config in NER_ENTITY_CONFIG.items():
        descriptions.append(f"{label}({config['description']})")
    return "、".join(descriptions)

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


class NewModel(LabelStudioMLBase):
    """Custom ML Backend model
    """
    
    def setup(self):
        """Configure any parameters of your model here
        """
        self.set("model_version", "0.0.1")
        
        # 魔塔社区API配置
        self.api_key = os.getenv('MODELSCOPE_API_KEY', 'ms-d200fd06-f07f-4be8-a6a8-9ebf76dd103a')
        self.api_base_url = os.getenv('MODELSCOPE_API_URL', 'https://api-inference.modelscope.cn/v1')
        # 推荐的模型选择（按优先级）:
        # 1. Qwen/Qwen3-235B-A22B-Instruct-2507 - 最适合结构化输出
        # 2. Qwen/Qwen3-Coder-480B-A35B-Instruct - 代码和结构化数据处理
        # 3. Qwen/Qwen3-235B-A22B-Thinking-2507 - 思维链模型（输出格式复杂）
        self.model_name = "Qwen/Qwen3-235B-A22B-Instruct-2507"  # 更适合NER任务
        
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
        
        # 显示当前配置的实体标签
        self._show_entity_config()
        
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
    
    def _show_entity_config(self):
        """显示当前配置的实体标签"""
        print(f"\n📋 当前支持的命名实体类型:")
        print("="*50)
        
        for i, (label, config) in enumerate(NER_ENTITY_CONFIG.items(), 1):
            print(f"  {i}. {label} - {config['description']}")
            if config['examples']:
                examples = "、".join(config['examples'][:3])
                print(f"     示例: {examples}")
        
        print(f"\n💡 如需修改实体类型，请编辑model.py顶部的NER_ENTITY_CONFIG配置")
        print("="*50)
            


    def predict(self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs) -> ModelResponse:
        """ 命名实体识别预测
            :param tasks: Label Studio tasks in JSON format
            :param context: Label Studio context in JSON format
            :return: ModelResponse with predictions
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
        entity_types_desc = get_entity_types_description()
        json_format = get_json_format_example()
        
        # 生成示例
        examples_text = ""
        for label, config in NER_ENTITY_CONFIG.items():
            examples = "、".join(config['examples'][:3])  # 取前3个示例
            examples_text += f"   {label}({config['description']}): {examples}\n"
        
        prompt = f"""请对以下文本进行命名实体识别，识别出以下类型的实体：

文本内容：
{text_content}

实体类型说明：
{examples_text}
请严格按照以下JSON格式返回结果，不要添加任何解释或其他内容：
{json_format}

支持的实体类型：{entity_types_desc}"""
        
        # 调用API
        api_response = self._call_modelscope_api(prompt)
        
        if api_response:
            return self._format_prediction(api_response, task)
        
        return None
    
    def _call_modelscope_api(self, prompt: str) -> Optional[str]:
        """调用魔塔社区API"""
        if not self.client:
            print("❌ OpenAI客户端未初始化")
            return None
        
        print(f"📤 发送API请求...")
        print(f"   模型: {self.model_name}")
        print(f"   提示词长度: {len(prompt)} 字符")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant specialized in Named Entity Recognition. Always respond with valid JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.1,
                top_p=0.9,
                stream=False
            )
            
            print(f"📥 收到API响应")
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                print(f"✅ 响应内容长度: {len(content) if content else 0} 字符")
                if content:
                    print(f"📋 响应内容预览: {content[:300]}{'...' if len(content) > 300 else ''}")
                return content
            else:
                print("❌ API响应中没有choices")
                return None
                
        except Exception as e:
            print(f"❌ API调用失败: {str(e)}")
            print(f"   完整错误信息: {repr(e)}")
            return None
    
    def _format_prediction(self, api_response: str, task: Dict) -> Dict:
        """格式化预测结果为Label Studio格式"""
        print(f"\n🔄 格式化预测结果:")
        print(f"   API响应长度: {len(api_response)} 字符")
        print(f"   API响应内容: {api_response[:200]}{'...' if len(api_response) > 200 else ''}")
        
        prediction = {
            "model_version": self.get("model_version"),
            "score": 0.95,
            "result": []
        }
        
        # 尝试解析NER结果
        ner_results = self._parse_ner_response(api_response, task)
        if ner_results:
            prediction["result"] = ner_results
            print(f"✅ NER解析成功，识别到 {len(ner_results)} 个实体")
            for i, result in enumerate(ner_results):
                entity = result.get('value', {})
                text = entity.get('text', '')
                labels = entity.get('labels', [])
                start = entity.get('start', 0)
                end = entity.get('end', 0)
                print(f"   实体 {i+1}: [{text}] -> {labels} ({start}-{end})")
            return prediction
        
        # 备用方案：返回原始文本
        print("⚠️ NER解析失败，使用原始文本格式")
        prediction["result"].append({
            "from_name": "prediction",
            "to_name": "text",
            "type": "textarea",
            "value": {
                "text": [api_response]
            }
        })
        
        return prediction
    
    def _parse_ner_response(self, api_response: str, task: Dict) -> Optional[List[Dict]]:
        """解析AI返回的命名实体识别JSON结果"""
        print(f"\n🔍 开始解析NER响应...")
        
        if not api_response or not api_response.strip():
            print("❌ API响应为空")
            return None
        
        try:
            # 尝试直接解析JSON
            try:
                print("🔧 尝试直接JSON解析...")
                ner_data = json.loads(api_response.strip())
                print("✅ 直接JSON解析成功")
            except json.JSONDecodeError as e:
                print(f"⚠️ 直接JSON解析失败: {e}")
                # 尝试提取JSON部分
                import re
                print("🔧 尝试提取JSON片段...")
                
                # 多种JSON提取策略
                patterns = [
                    r'\{[^{}]*"entities"[^{}]*:.*?\}',  # 最严格的entities匹配
                    r'\{.*?"entities".*?\}',            # 宽松的entities匹配
                    r'\{.*\}',                          # 最宽松的JSON匹配
                ]
                
                ner_data = None
                for i, pattern in enumerate(patterns):
                    json_match = re.search(pattern, api_response, re.DOTALL)
                    if json_match:
                        try:
                            ner_data = json.loads(json_match.group())
                            print(f"✅ JSON提取成功 (策略 {i+1})")
                            break
                        except json.JSONDecodeError:
                            print(f"⚠️ JSON提取策略 {i+1} 失败")
                            continue
                
                if not ner_data:
                    print("❌ 所有JSON提取策略都失败")
                    print(f"📄 原始响应内容: {api_response}")
                    return None
            
            # 检查entities字段
            if 'entities' not in ner_data or not isinstance(ner_data['entities'], list):
                return None
            
            entities = ner_data['entities']
            
            # 获取原始文本
            task_data = task.get('data', {})
            original_text = ""
            for key in ['text', 'content', 'prompt', 'question', 'description', 'query']:
                if key in task_data and isinstance(task_data[key], str):
                    original_text = task_data[key]
                    break
            
            if not original_text:
                return None
            
            print(f"📝 原始文本: {original_text}")
            print(f"📏 原始文本长度: {len(original_text)} 字符")
            
            # 转换为Label Studio格式
            results = []
            for i, entity in enumerate(entities):
                # 验证必需字段
                if not all(key in entity for key in ['text', 'start', 'end', 'label']):
                    print(f"   ⚠️ 实体 {i+1} 缺少必需字段，跳过")
                    continue
                
                start = entity['start']
                end = entity['end']
                text = entity['text']
                label = entity['label']
                
                print(f"\n🔍 处理实体 {i+1}: {entity}")
                
                # 验证位置信息基本合理性
                if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
                    print(f"   ❌ 实体 {i+1} 位置信息无效 (start={start}, end={end})，跳过")
                    continue
                
                # 验证位置不超出文本长度
                if end > len(original_text):
                    print(f"   ❌ 实体 {i+1} 结束位置超出文本长度 (end={end}, text_len={len(original_text)})，跳过")
                    continue
                
                # 提取实际文本进行验证和修正
                extracted_text = original_text[start:end]
                
                print(f"   📋 AI提供的文本: '{text}'")
                print(f"   📋 位置提取的文本: '{extracted_text}'")
                print(f"   📍 位置: {start}-{end}")
                
                # 如果文本不匹配，尝试修正
                corrected_start, corrected_end, corrected_text = self._correct_entity_position(
                    original_text, text, start, end
                )
                
                if corrected_text:
                    # 验证修正后的实体是否合理（长度不能太短，不能只是标点符号）
                    if self._is_valid_entity(corrected_text, label):
                        result = {
                            "from_name": "label",
                            "to_name": "text",
                            "type": "labels",
                            "value": {
                                "start": corrected_start,
                                "end": corrected_end,
                                "text": corrected_text,
                                "labels": [label]
                            }
                        }
                        
                        results.append(result)
                        print(f"   ✅ 实体 {i+1} 已添加: '{corrected_text}' -> {label} ({corrected_start}-{corrected_end})")
                    else:
                        print(f"   ❌ 实体 {i+1} 验证失败: '{corrected_text}' 不是有效的 {label} 实体")
                else:
                    print(f"   ❌ 实体 {i+1} 无法修正位置，跳过")
            
            print(f"\n📊 最终有效实体数量: {len(results)}")
            return results if results else None
            
        except Exception as e:
            print(f"❌ 解析NER结果异常: {e}")
            return None
    
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
                print(f"   🔧 精确匹配修正: '{clean_entity}' ({exact_start}-{exact_end})")
                return exact_start, exact_end, clean_entity
            
            # 尝试模糊匹配（去除标点符号）
            import re
            clean_text_for_search = re.sub(r'[^\w\u4e00-\u9fff]', '', clean_entity)
            if len(clean_text_for_search) >= 2:  # 至少2个字符才进行模糊匹配
                for i in range(len(original_text) - len(clean_text_for_search) + 1):
                    slice_text = original_text[i:i + len(clean_text_for_search)]
                    clean_slice = re.sub(r'[^\w\u4e00-\u9fff]', '', slice_text)
                    if clean_slice == clean_text_for_search:
                        print(f"   🔧 模糊匹配修正: '{slice_text}' ({i}-{i + len(clean_text_for_search)})")
                        return i, i + len(clean_text_for_search), slice_text
            
            # 如果还是找不到，尝试部分匹配
            if len(clean_entity) >= 3:
                core_part = clean_entity[:min(len(clean_entity), 5)]  # 取前几个字符作为核心
                core_start = original_text.find(core_part)
                if core_start != -1:
                    # 尝试扩展匹配
                    extended_end = min(core_start + len(clean_entity) + 2, len(original_text))
                    extended_text = original_text[core_start:extended_end]
                    print(f"   🔧 部分匹配修正: '{extended_text}' ({core_start}-{extended_end})")
                    return core_start, extended_end, extended_text
            
        except Exception as e:
            print(f"   ❌ 位置修正失败: {e}")
        
        return None, None, None
    
    def _is_valid_entity(self, text: str, label: str) -> bool:
        """验证实体是否合理（使用配置化的验证规则）"""
        if not text or len(text.strip()) < 1:
            return False
        
        # 去除首尾标点符号和空格
        clean_text = text.strip()
        
        # 不能只是标点符号
        import re
        if re.match(r'^[^\w\u4e00-\u9fff]+$', clean_text):
            return False
        
        # 长度验证
        if len(clean_text) < 1:
            return False
        
        # 检查标签是否在配置中
        if label not in NER_ENTITY_CONFIG:
            return True  # 如果不在配置中，默认通过
        
        config = NER_ENTITY_CONFIG[label]
        
        # 检查无效模式（如果配置了）
        if 'invalid_patterns' in config:
            for pattern in config['invalid_patterns']:
                if re.search(pattern, clean_text):
                    return False
        
        # 检查有效模式（如果配置了）
        if 'valid_patterns' in config:
            valid_patterns = config['valid_patterns']
            has_valid_pattern = any(re.search(pattern, clean_text) for pattern in valid_patterns)
            if not has_valid_pattern and len(clean_text) < 4:
                return False
        
        return True
    
    def _extract_choice(self, response: str, choices: List[str]) -> Optional[str]:
        """从响应中提取最匹配的选择"""
        response_lower = response.lower()
        for choice in choices:
            if choice.lower() in response_lower:
                return choice
        return choices[0] if choices else None
    
    def fit(self, event, data, **kwargs):
        """
        训练/更新模型
        :param event: 事件类型 ('ANNOTATION_CREATED', 'ANNOTATION_UPDATED', 'START_TRAINING')
        :param data: 事件数据
        """
        # 更新缓存数据
        old_data = self.get('my_data')
        self.set('my_data', 'updated_data')
        self.set('model_version', 'updated_version')
        print(f"✅ 模型已更新 (事件: {event})")


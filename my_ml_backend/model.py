from typing import List, Dict, Optional
import json
import os
import time
from openai import OpenAI
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse


# ==================== 命名实体配置 ====================
# 从配置文件导入实体配置
try:
    from entity_config import get_entity_config, get_entity_labels, get_all_categories, get_entities_by_category
    NER_ENTITY_CONFIG = get_entity_config()
    ENTITY_LABELS = get_entity_labels()
    print(f"✅ 从配置文件加载了 {len(ENTITY_LABELS)} 种实体类型")
    print(f"📋 包含类别: {', '.join(get_all_categories())}")
except ImportError:
    # 如果配置文件不存在，使用默认配置
    print("⚠️ 配置文件不存在，退出程序!!!")
    exit()
   


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

# 简化的标签验证函数
def validate_label(label: str) -> str:
    """验证标签是否在有效标签列表中"""
    if not label:
        return None
    
    clean_label = label.strip()
    
    # 直接匹配标签名称
    if clean_label in ENTITY_LABELS:
        return clean_label
    
    # 如果不匹配，返回None
    print(f"   ❌ 无效标签: '{clean_label}' (不在有效标签列表中)")
    return None

def get_valid_label_list():
    """获取所有有效的标签列表用于提示"""
    try:
        from entity_config import get_entity_labels
        return get_entity_labels()
    except ImportError:
        return list(NER_ENTITY_CONFIG.keys())


class NewModel(LabelStudioMLBase):
    """Custom ML Backend model
    """
    
    def setup(self):
        """Configure any parameters of your model here
        """
        self.set("model_version", "0.0.1")
        
        # 魔塔社区API配置
        self.api_key = os.getenv('MODELSCOPE_API_KEY', 'ms-2c045fb7-f463-45bf-b0f9-a36d50b0400e')
        self.api_base_url = os.getenv('MODELSCOPE_API_URL', 'https://api-inference.modelscope.cn/v1')
        # 推荐的模型选择（按优先级）:
        # 1. Qwen/Qwen3-235B-A22B-Instruct-2507 - 最适合结构化输出
        # 2. Qwen/Qwen3-Coder-480B-A35B-Instruct - 代码和结构化数据处理
        # 3. Qwen/Qwen3-235B-A22B-Thinking-2507 - 思维链模型（输出格式复杂）
        # 4. moonshotai/Kimi-K2-Instruct-0905 - 更适合NER任务
        # 5. Qwen/Qwen3-30B-A3B-Instruct-2507
        self.model_name = "Qwen/Qwen3-30B-A3B-Instruct-2507"  # 更适合NER任务
        
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
                max_tokens=1000,
                temperature=0.1
            )
            print(f"✅ API连接成功")
        except Exception as e:
            print(f"❌ API连接失败: {str(e)[:100]}")
    
    def _show_entity_config(self):
        """显示当前配置的实体标签"""
        print(f"\n📋 当前支持的命名实体类型:")
        print("="*60)
        
        try:
            from entity_config import get_all_categories, get_entities_by_category
            categories = get_all_categories()
            
            for category in categories:
                entities = get_entities_by_category(category)
                if entities:
                    print(f"\n📂 {category}类 ({len(entities)}个实体):")
                    for i, (label, config) in enumerate(entities.items(), 1):
                        print(f"  {i:2d}. {label} - {config['description']}")
                        if config['examples']:
                            examples = "、".join(config['examples'][:2])
                            print(f"      示例: {examples}")
                            
        except ImportError:
            # 备用显示方式
            for i, (label, config) in enumerate(NER_ENTITY_CONFIG.items(), 1):
                print(f"  {i}. {label} - {config['description']}")
                if config['examples']:
                    examples = "、".join(config['examples'][:3])
                    print(f"     示例: {examples}")
        
        print(f"\n💡 总计: {len(ENTITY_LABELS)} 种实体类型")
        print(f"🔧 如需修改实体类型，请编辑entity_config.py文件")
        print("="*60)
    


    def predict(self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs) -> ModelResponse:
        """ 命名实体识别预测
            :param tasks: Label Studio tasks in JSON format
            :param context: Label Studio context in JSON format
            :return: ModelResponse with predictions
        """
        total_tasks = len(tasks)
        predictions = []
        
        print(f"🚀 开始处理 {total_tasks} 个任务")
        print("="*60)
        
        start_time = time.time()
        
        for i, task in enumerate(tasks):
            print(f"\n🔄 正在处理任务 {i+1}/{total_tasks}...")
            
            # 显示任务内容预览
            task_data = task.get('data', {})
            text_content = ""
            for key in ['text', 'content', 'prompt', 'question', 'description', 'query']:
                if key in task_data and isinstance(task_data[key], str):
                    text_content = task_data[key]
                    break
            
            if text_content:
                preview = text_content[:50] + "..." if len(text_content) > 50 else text_content
                print(f"   📝 文本预览: {preview}")
            
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
                    print(f"✅ 任务 {i+1} 处理成功 (耗时: {task_duration:.2f}秒, 实体数: {entities_count})")
                else:
                    # 未识别到实体或处理失败 - 返回错误标记
                    failed_prediction = {
                        "model_version": self.get("model_version"),
                        "score": 0.0,
                        "result": [],
                        "error": "未识别到任何实体",  # 添加错误标记
                        "status": "failed"  # 明确标记为失败
                    }
                    predictions.append(failed_prediction)
                    print(f"❌ 任务 {i+1} 处理失败 - 未识别到任何实体 (耗时: {task_duration:.2f}秒)")
                    
            except Exception as e:
                task_end_time = time.time()
                task_duration = task_end_time - task_start_time
                print(f"❌ 任务 {i+1} 处理异常 (耗时: {task_duration:.2f}秒): {e}")
                failed_prediction = {
                    "model_version": self.get("model_version"),
                    "score": 0.0,
                    "result": [],
                    "error": f"处理异常: {str(e)}",  # 添加错误信息
                    "status": "failed"  # 明确标记为失败
                }
                predictions.append(failed_prediction)
            
            # 强制刷新输出缓冲区
            import sys
            sys.stdout.flush()
        
        # 处理完成后的总结
        end_time = time.time()
        total_duration = end_time - start_time
        processed_count = len(predictions)
        
        print(f"\n📊 处理完成")
        print("="*60)
        print("📊 处理总结:")
        print(f"   处理任务: {processed_count}/{total_tasks} 个")
        print(f"   总耗时: {total_duration:.2f}秒")
        print(f"   平均耗时: {total_duration/processed_count:.2f}秒/任务" if processed_count > 0 else "   平均耗时: N/A")
        
        # 统计成功和失败的任务
        successful_tasks = sum(1 for p in predictions if p.get('result') and len(p.get('result', [])) > 0)
        failed_tasks = processed_count - successful_tasks
        total_entities = sum(len(p.get('result', [])) for p in predictions)
        
        print(f"   ✅ 成功任务: {successful_tasks}/{processed_count} 个 ({successful_tasks/processed_count*100:.1f}%)" if processed_count > 0 else "   ✅ 成功任务: 0 个")
        print(f"   ❌ 失败任务: {failed_tasks}/{processed_count} 个 ({failed_tasks/processed_count*100:.1f}%)" if processed_count > 0 else "   ❌ 失败任务: 0 个")
        print(f"   🏷️ 总实体数: {total_entities} 个")
        
        if successful_tasks > 0:
            avg_entities = total_entities / successful_tasks
            print(f"   📈 平均实体数: {avg_entities:.1f} 个/成功任务")
        
        print("="*60)
        
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
                    {"role": "system", "content": "You are a specialized Named Entity Recognition assistant for legal texts. CRITICAL: You must extract both traditional entities AND relational expressions. Use EXACT label names from the provided list. Never use descriptions, abbreviations, or variations. For relation labels, extract complete phrases that express semantic relationships between entities. Always respond with valid JSON format containing only the specified labels."},
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
        if ner_results and len(ner_results) > 0:
            prediction["result"] = ner_results
            prediction["score"] = 0.95  # 成功识别的置信度
            print(f"✅ NER解析成功，识别到 {len(ner_results)} 个实体")
            for i, result in enumerate(ner_results):
                entity = result.get('value', {})
                text = entity.get('text', '')
                labels = entity.get('labels', [])
                start = entity.get('start', 0)
                end = entity.get('end', 0)
                print(f"   实体 {i+1}: [{text}] -> {labels} ({start}-{end})")
            return prediction
        
        # 如果没有识别到任何实体，返回失败信息
        print("❌ NER解析失败，未识别到任何有效实体")
        prediction["score"] = 0.0  # 失败的置信度
        prediction["result"] = []   # 空结果
        return None  # 返回None表示处理失败
    
    def _parse_ner_response(self, api_response: str, task: Dict) -> Optional[List[Dict]]:
        """解析AI返回的命名实体识别JSON结果，并用正则表达式进行补充"""
        print(f"\n🔍 开始解析NER响应...")
        
        # 获取原始文本
        task_data = task.get('data', {})
        original_text = ""
        for key in ['text', 'content', 'prompt', 'question', 'description', 'query']:
            if key in task_data and isinstance(task_data[key], str):
                original_text = task_data[key]
                break
        
        if not original_text:
            print("❌ 无法获取原始文本")
            return None
        
        print(f"📝 原始文本: {original_text}")
        print(f"📏 原始文本长度: {len(original_text)} 字符")
        
        # 初始化结果列表
        results = []
        ai_entities = []
        
        # 第一步：解析AI模型的识别结果
        if api_response and api_response.strip():
            ai_entities = self._parse_ai_entities(api_response, original_text)
            if ai_entities:
                results.extend(ai_entities)
                print(f"🤖 AI模型识别到 {len(ai_entities)} 个实体")
        else:
            print("⚠️ AI响应为空，跳过AI实体解析")
        
        # 第二步：使用正则表达式进行补充识别
        regex_entities = self._extract_regex_entities(original_text, ai_entities)
        if regex_entities:
            results.extend(regex_entities)
            print(f"🔧 正则表达式补充识别到 {len(regex_entities)} 个实体")
        
        # 第三步：去重和排序
        final_results = self._deduplicate_entities(results)
        print(f"📊 去重后最终实体数量: {len(final_results)}")
        
        return final_results if final_results else None
    
    def _parse_ai_entities(self, api_response: str, original_text: str) -> List[Dict]:
        """解析AI模型返回的实体"""
        print(f"\n🤖 解析AI实体识别结果...")
        ai_results = []
        
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
                    return ai_results
            
            # 检查entities字段
            if 'entities' not in ner_data or not isinstance(ner_data['entities'], list):
                print("⚠️ 响应中没有有效的entities字段")
                return ai_results
            
            entities = ner_data['entities']
            
            # 转换为Label Studio格式
            for i, entity in enumerate(entities):
                # 验证必需字段
                if not all(key in entity for key in ['text', 'start', 'end', 'label']):
                    print(f"   ⚠️ AI实体 {i+1} 缺少必需字段，跳过")
                    continue
                
                start = entity['start']
                end = entity['end']
                text = entity['text']
                original_label = entity['label']
                
                print(f"\n🔍 处理AI实体 {i+1}: {entity}")
                
                # 严格验证标签
                validated_label = validate_label(original_label)
                if not validated_label:
                    print(f"   ❌ AI实体 {i+1} 标签无效: '{original_label}'，跳过")
                    continue
                
                # 使用验证通过的标签
                label = validated_label
                if validated_label in NER_ENTITY_CONFIG:
                    description = NER_ENTITY_CONFIG[validated_label]['description']
                    print(f"   ✅ 标签验证通过: '{original_label}' -> '{validated_label}' (描述: {description})")
                else:
                    print(f"   ✅ 标签验证通过: '{original_label}' -> '{label}'")
                
                # 验证位置信息基本合理性
                if not isinstance(start, int) or not isinstance(end, int) or start < 0:
                    print(f"   ❌ AI实体 {i+1} 位置信息无效 (start={start}, end={end})，跳过")
                    continue
                
                print(f"   📋 AI提供的文本: '{text}'")
                print(f"   📍 原始位置: {start}-{end}")
                
                # 先尝试修正位置，再进行范围检查
                corrected_start, corrected_end, corrected_text = self._correct_entity_position(
                    original_text, text, start, end
                )
                
                # 检查修正后的位置是否合理
                if corrected_start is None or corrected_end is None or corrected_text is None:
                    print(f"   ❌ AI实体 {i+1} 位置修正失败，跳过")
                    continue
                
                # 验证修正后的位置不超出文本长度
                if corrected_end > len(original_text) or corrected_start < 0:
                    print(f"   ❌ AI实体 {i+1} 修正后位置超出文本长度 (start={corrected_start}, end={corrected_end}, text_len={len(original_text)})，跳过")
                    continue
                
                print(f"   📋 修正后的文本: '{corrected_text}'")
                print(f"   📍 修正后位置: {corrected_start}-{corrected_end}")
                
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
                        print(f"   ✅ AI实体 {i+1} 已添加: '{corrected_text}' -> {label} ({corrected_start}-{corrected_end})")
                    else:
                        print(f"   ❌ AI实体 {i+1} 验证失败: '{corrected_text}' 不是有效的 {label} 实体")
                else:
                    print(f"   ❌ AI实体 {i+1} 无法修正位置，跳过")
            
            print(f"🤖 AI模型解析完成，有效实体: {len(ai_results)}")
            return ai_results
            
        except Exception as e:
            print(f"❌ 解析AI实体异常: {e}")
            return ai_results
    
    def _extract_regex_entities(self, original_text: str, existing_entities: List[Dict]) -> List[Dict]:
        """使用正则表达式补充识别实体"""
        print(f"\n🔧 开始正则表达式补充识别...")
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
                
                print(f"🔍 检查 {label_key} ({description}) 的正则模式...")
                
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
                                print(f"   ⚠️ 正则匹配 '{text}' ({start}-{end}) 与已识别实体重叠，跳过")
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
                                print(f"   ✅ 正则识别: '{text}' -> {label_key} (描述: {description}) ({start}-{end})")
                                
                                # 更新已识别范围
                                for pos in range(start, end):
                                    existing_ranges.add(pos)
                            else:
                                print(f"   ❌ 正则匹配 '{text}' 验证失败，跳过")
                                
                    except re.error as e:
                        print(f"   ❌ 正则模式错误 '{pattern}': {e}")
                        continue
            
            print(f"🔧 正则表达式补充完成，新增实体: {len(regex_results)}")
            return regex_results
            
        except Exception as e:
            print(f"❌ 正则表达式补充异常: {e}")
            return regex_results
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """去重和排序实体"""
        print(f"\n🔄 开始去重和排序实体...")
        
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
                        print(f"   🔄 发现重叠实体:")
                        print(f"      当前: '{current_text}' ({current_start}-{current_end}) [{current_source}]")
                        print(f"      已有: '{existing_text}' ({existing_start}-{existing_end}) [{existing_source}]")
                        print(f"      重叠比例: {overlap_ratio:.2%}")
                        
                        # 优先级：AI > 正则，长实体 > 短实体
                        should_replace = False
                        if current_source == 'ai' and existing_source == 'regex':
                            should_replace = True
                            print(f"      💡 AI识别优先于正则识别")
                        elif current_source == existing_source and current_length > existing_length:
                            should_replace = True
                            print(f"      💡 更长的实体优先")
                        elif current_source == existing_source and current_length == existing_length:
                            # 相同长度，保留原有的
                            should_replace = False
                            print(f"      💡 相同条件，保留原有实体")
                        
                        if should_replace:
                            deduplicated[i] = current
                            print(f"      ✅ 替换为当前实体")
                        else:
                            print(f"      ✅ 保留原有实体")
                        
                        should_add = False
                        break
            
            if should_add:
                deduplicated.append(current)
                print(f"   ✅ 添加实体: '{current_text}' -> {current_value.get('labels', [])} ({current_start}-{current_end}) [{current_source}]")
        
        # 最终按位置排序
        final_results = sorted(deduplicated, key=lambda x: x.get('value', {}).get('start', 0))
        
        # 移除source标记（Label Studio不需要）
        for result in final_results:
            result.pop('source', None)
        
        print(f"🔄 去重完成，最终实体数量: {len(final_results)}")
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
            print(f"   ⚠️ 实体文本 '{clean_text}' 的标签 '{label}' 不在有效标签列表中")
            return False
        
        # 特殊验证：关系标签
        if label.endswith("关系"):
            # 关系标签应该包含动词或连接词
            relation_keywords = ['根据', '依据', '按照', '负责', '主管', '管辖', '导致', '造成', '引起', 
                               '之前', '之后', '同时', '包括', '包含', '属于', '影响', '波及', '协调', 
                               '配合', '执行', '实施', '补偿', '赔偿']
            
            if not any(keyword in clean_text for keyword in relation_keywords):
                print(f"   ⚠️ 关系标签 '{label}' 的文本 '{clean_text}' 不包含关系关键词")
                # 对于关系标签，放宽验证，只要不是纯标点就接受
                pass
        
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


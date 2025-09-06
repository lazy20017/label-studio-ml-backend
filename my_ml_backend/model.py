from typing import List, Dict, Optional
import json
import os
import time
import datetime
from pathlib import Path
from openai import OpenAI
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse

# 导入处理配置
try:
    from processing_config import get_processing_config
    processing_config = get_processing_config()
except ImportError:
    print("⚠️ 处理配置文件不存在，使用默认配置")
    processing_config = None


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

# 标签验证和映射函数
def validate_and_map_label(original_label: str) -> str:
    """验证和映射标签名称，确保与配置文件一致，返回配置文件中的键名"""
    if not original_label:
        return None
    
    # 清理标签（去除多余空格）
    clean_label = original_label.strip()
    
    # 1. 直接匹配键名
    if clean_label in ENTITY_LABELS:
        return clean_label
    
    # 2. 匹配description（AI可能返回description格式的标签）
    for label_key, config in NER_ENTITY_CONFIG.items():
        if config['description'] == clean_label:
            print(f"   🔄 描述匹配: '{clean_label}' -> '{label_key}'")
            return label_key
    
    # 3. 常见的标签映射（处理AI可能返回的变体）
    # 基于entity_config.py中的实际标签名称进行映射
    label_mapping = {
        # 文档类映射
        "文档编号": "文号",
        "文档号": "文号", 
        "编号": "文号",
        "版本": "版本号",
        "修订": "版本号",
        "修正": "版本号",
        "附录": "附件",
        
        # 机构组织映射
        "组织": "机构组织",
        "机构": "机构组织",
        "群体": "人员",
        "人名": "人员",
        "职位": "职位职能",
        "职能": "职位职能",
        
        # 地理位置映射
        "地点": "地理位置",
        "位置": "地理位置",
        "地名": "地理位置",
        "区域": "区域信息",
        "行政区": "行政区划",
        "河段": "流域",
        
        # 时间映射
        "日期": "时间",
        "时段": "时间",
        "发布时间": "发布日期",
        "生效时间": "生效日期",
        
        # 灾害映射
        "灾害": "灾害类型",
        "事件": "灾害事件",
        "事故": "灾害事件",
        "后果": "事故后果",
        "决口": "溃坝",
        
        # 数值映射
        "数值": "数值指标",
        "指标": "数值指标",
        "警戒线": "阈值",
        "等级": "预警级别",
        "级别": "预警级别",
        
        # 监测预警映射
        "监测站": "监测站点",
        "监测设备": "监测站点",
        "预警": "预警信息",
        "预报": "预警信息",
        "模型": "预测模型",
        "方法": "预测模型",
        
        # 应急响应映射
        "启动条件": "触发条件",
        "应急等级": "响应级别",
        "指挥部": "指挥体系",
        "应对措施": "处置措施",
        "命令": "决策",
        
        # 救援映射
        "避难点": "疏散路线",
        "安置": "救助措施",
        "救援队伍": "救援力量",
        "装备": "物资装备",
        "运输": "物流运输",
        
        # 基础设施映射
        "设施": "基础设施",
        "损坏": "设施状态",
        "加固": "维修加固",
        
        # 财政映射
        "资金": "资金保障",
        "财政": "资金保障",
        "保险": "保险赔偿",
        "赔偿": "保险赔偿",
        "采购": "采购招标",
        "招标": "采购招标",
        "合同": "采购招标",
        
        # 证据映射
        "记录": "监测记录",
        "报表": "监测记录",
        "照片": "证据材料",
        "视频": "证据材料",
        "证据": "证据材料",
        "证人": "证人证词",
        "证词": "证人证词",
        
        # 监管映射
        "检查": "检查验收",
        "验收": "检查验收",
        "年检": "检查验收",
        "隐患": "隐患清单",
        "问题": "隐患清单",
        "执法": "监管措施",
        
        # 培训映射
        "演练": "演练培训",
        "培训": "演练培训",
        "能力": "能力清单",
        "资源": "能力清单",
        "预案": "预案条目",
        "章节": "预案条目",
        
        # 灾后映射
        "恢复": "恢复重建",
        "重建": "恢复重建",
        "善后": "善后保障",
        "心理": "善后保障",
        "总结": "总结建议",
        "建议": "总结建议",
        "教训": "总结建议",
        
        # 风险治理映射
        "风险": "风险评估",
        "评估": "风险评估",
        "区划": "风险评估",
        "标准": "设计标准",
        "规范": "设计标准",
        "治理": "长期治理",
        "适应": "长期治理",
        
        # 信息传播映射
        "联系人": "联系人信息",
        "渠道": "发布渠道",
        "媒体": "媒体舆情",
        "舆情": "媒体舆情",
        "报道": "媒体舆情",
        
        # 其他映射
        "协同": "跨界协同",
        "流域": "跨界协同",
        "政策": "政策变更",
        "变更": "政策变更",
        "历史": "政策变更",
        "群体": "脆弱群体",
        "资产": "关键资产",
        "经济": "关键资产",
        "算法": "模型算法",
        "数据": "数据来源",
        "引用": "数据来源",
        
        # 关系映射
        "位于": "位于关系",
        "主管": "责任关系",
        "责任": "责任关系",
        "触发": "因果关系",
        "导致": "因果关系",
        "引用": "依据关系",
        "依据": "依据关系",
        "包含": "包含关系",
        "属于": "包含关系",
        "影响": "影响关系",
        "受影响": "影响关系",
        "隶属": "隶属关系",
        "上下级": "隶属关系",
        "发起": "发起关系",
        "下达": "发起关系",
        "调配": "调配关系",
        "支援": "调配关系",
        "检测": "检测关系",
        "观测": "检测关系",
        "偿付": "补偿关系",
        "补偿": "补偿关系",
        "整改": "整改关系",
        "处理": "整改关系"
    }
    
    # 检查映射表
    if clean_label in label_mapping:
        mapped_label = label_mapping[clean_label]
        print(f"   🔄 标签映射: '{clean_label}' -> '{mapped_label}'")
        return mapped_label
    
    # 4. 模糊匹配（部分匹配）
    for valid_label in ENTITY_LABELS:
        # 检查是否包含关键词
        if clean_label in valid_label or valid_label in clean_label:
            print(f"   🔍 模糊匹配: '{clean_label}' -> '{valid_label}'")
            return valid_label
    
    # 5. 如果都无法匹配，返回None
    print(f"   ❌ 未找到匹配的标签: '{clean_label}'")
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
    
    def set_task_completed_callback(self, callback_func):
        """设置任务完成回调函数
        
        Args:
            callback_func: 回调函数，接受参数 (current_task_index, total_tasks, prediction_result)
        """
        self._task_completed_callback = callback_func
        print("✅ 已设置任务完成回调函数")
    
    def clear_task_completed_callback(self):
        """清除任务完成回调函数"""
        if hasattr(self, '_task_completed_callback'):
            delattr(self, '_task_completed_callback')
            print("✅ 已清除任务完成回调函数")


    def predict(self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs) -> ModelResponse:
        """ 命名实体识别预测（支持批量导出模式）
            :param tasks: Label Studio tasks in JSON format
            :param context: Label Studio context in JSON format
            :return: ModelResponse with predictions
        """
        # 使用配置化的参数
        if processing_config:
            MAX_BATCH_SIZE = processing_config.MAX_BATCH_SIZE
            MAX_PROCESSING_TIME = processing_config.MAX_PROCESSING_TIME
            print(f"📋 使用配置文件参数")
            if processing_config.ENABLE_DETAILED_LOGGING:
                print(processing_config.get_config_summary())
        else:
            # 备用配置
            MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', '10'))
            MAX_PROCESSING_TIME = int(os.getenv('MAX_PROCESSING_TIME', '45'))
            print(f"📋 使用环境变量/默认参数")
        
        total_tasks = len(tasks)
        predictions = []
        
        print(f"🚀 开始处理 {total_tasks} 个任务")
        print(f"⚙️ 配置: 最大批量={MAX_BATCH_SIZE}, 最大时间={MAX_PROCESSING_TIME}秒")
        print("="*60)
        
        # 检查是否启用批量导出模式
        export_mode = os.getenv('BATCH_EXPORT_MODE', 'false').lower() == 'true'
        export_threshold = int(os.getenv('BATCH_EXPORT_THRESHOLD', '3'))  # 默认20个任务以上启用导出模式
        
        if total_tasks >= export_threshold or export_mode:
            print(f"📁 任务数量({total_tasks})达到导出阈值({export_threshold})，启用批量导出模式")
            print(f"💡 将生成导出文件，请手动导入到Label Studio前端")
            return self._process_batch_export_mode(tasks)
        
        # 如果任务数量超过限制但不到导出阈值，使用分块处理
        elif total_tasks > MAX_BATCH_SIZE:
            print(f"📦 任务数量({total_tasks})超过限制({MAX_BATCH_SIZE})，启用分块处理")
            return self._process_tasks_in_chunks(tasks, MAX_BATCH_SIZE, MAX_PROCESSING_TIME)
        
        # 小批量处理：直接处理所有任务
        start_time = time.time()
        print(f"🔄 小批量处理模式: {total_tasks} 个任务")
        print("="*60)
        
        for i, task in enumerate(tasks):
            # 检查是否超时
            elapsed_time = time.time() - start_time
            if elapsed_time > MAX_PROCESSING_TIME:
                print(f"⏱️ 处理时间超过限制({MAX_PROCESSING_TIME}秒)，停止处理")
                print(f"📊 已处理: {i}/{total_tasks} 个任务")
                break
            
            print(f"\n🔄 正在处理任务 {i+1}/{total_tasks}...")
            print(f"⏱️ 已用时: {elapsed_time:.1f}秒, 剩余时间: {MAX_PROCESSING_TIME - elapsed_time:.1f}秒")
            
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
                
                if prediction:
                    predictions.append(prediction)
                    entities_count = len(prediction.get('result', []))
                    print(f"✅ 任务 {i+1} 处理成功 (耗时: {task_duration:.2f}秒, 实体数: {entities_count})")
                else:
                    prediction = {
                        "model_version": self.get("model_version"),
                        "score": 0.0,
                        "result": []
                    }
                    predictions.append(prediction)
                    print(f"⚠️ 任务 {i+1} 处理完成但无结果 (耗时: {task_duration:.2f}秒)")
                    
            except Exception as e:
                task_end_time = time.time()
                task_duration = task_end_time - task_start_time
                print(f"❌ 任务 {i+1} 处理失败 (耗时: {task_duration:.2f}秒): {e}")
                prediction = {
                    "model_version": self.get("model_version"),
                    "score": 0.0,
                    "result": []
                }
                predictions.append(prediction)
            
            # 对于批量任务，调用回调函数
            if hasattr(self, '_task_completed_callback') and callable(self._task_completed_callback):
                try:
                    self._task_completed_callback(i+1, total_tasks, prediction)
                except Exception as e:
                    print(f"⚠️ 回调函数执行失败: {e}")
            
            # 强制刷新输出缓冲区
            import sys
            sys.stdout.flush()
        
        # 处理完成后的总结
        end_time = time.time()
        total_duration = end_time - start_time
        processed_count = len(predictions)
        
        print(f"\n✅ 批量处理完成")
        print("="*60)
        print("📊 处理总结:")
        print(f"   处理任务: {processed_count}/{total_tasks} 个")
        print(f"   总耗时: {total_duration:.2f}秒")
        print(f"   平均耗时: {total_duration/processed_count:.2f}秒/任务" if processed_count > 0 else "   平均耗时: N/A")
        successful_tasks = sum(1 for p in predictions if p.get('result'))
        print(f"   成功任务: {successful_tasks}/{processed_count} 个")
        print(f"   总实体数: {sum(len(p.get('result', [])) for p in predictions)} 个")
        print("="*60)
        
        return ModelResponse(predictions=predictions)
    
    def _process_tasks_in_chunks(self, tasks: List[Dict], max_batch_size: int, max_processing_time: int) -> ModelResponse:
        """分块处理大批量任务，避免超时"""
        total_tasks = len(tasks)
        all_predictions = []
        
        # 计算分块数量
        total_chunks = (total_tasks + max_batch_size - 1) // max_batch_size
        
        print(f"📦 分块处理配置:")
        print(f"   总任务数: {total_tasks}")
        print(f"   每块大小: {max_batch_size}")
        print(f"   总块数: {total_chunks}")
        print(f"   每块最大时间: {max_processing_time}秒")
        print("="*60)
        
        start_time = time.time()
        
        for chunk_idx in range(total_chunks):
            chunk_start = chunk_idx * max_batch_size
            chunk_end = min(chunk_start + max_batch_size, total_tasks)
            chunk_tasks = tasks[chunk_start:chunk_end]
            
            print(f"\n📋 处理第 {chunk_idx + 1}/{total_chunks} 块")
            print(f"   任务范围: {chunk_start + 1}-{chunk_end}")
            print(f"   块大小: {len(chunk_tasks)}")
            
            # 处理当前块
            chunk_start_time = time.time()
            chunk_predictions = []
            
            for i, task in enumerate(chunk_tasks):
                task_index = chunk_start + i + 1
                
                # 检查总时间限制
                elapsed_total_time = time.time() - start_time
                if elapsed_total_time > max_processing_time * total_chunks:
                    print(f"⏱️ 总处理时间超过限制，停止处理")
                    print(f"📊 已处理: {len(all_predictions)}/{total_tasks} 个任务")
                    return ModelResponse(predictions=all_predictions)
                
                print(f"\n🔄 处理任务 {task_index}/{total_tasks} (块内: {i+1}/{len(chunk_tasks)})")
                
                try:
                    prediction = self._process_single_task(task)
                    
                    if prediction:
                        chunk_predictions.append(prediction)
                        entities_count = len(prediction.get('result', []))
                        print(f"✅ 任务 {task_index} 处理成功 (实体数: {entities_count})")
                    else:
                        prediction = {
                            "model_version": self.get("model_version"),
                            "score": 0.0,
                            "result": []
                        }
                        chunk_predictions.append(prediction)
                        print(f"⚠️ 任务 {task_index} 处理完成但无结果")
                        
                except Exception as e:
                    print(f"❌ 任务 {task_index} 处理失败: {e}")
                    prediction = {
                        "model_version": self.get("model_version"),
                        "score": 0.0,
                        "result": []
                    }
                    chunk_predictions.append(prediction)
                
                # 调用回调函数
                if hasattr(self, '_task_completed_callback') and callable(self._task_completed_callback):
                    try:
                        self._task_completed_callback(task_index, total_tasks, prediction)
                    except Exception as e:
                        print(f"⚠️ 回调函数执行失败: {e}")
            
            # 添加到总结果中
            all_predictions.extend(chunk_predictions)
            
            chunk_end_time = time.time()
            chunk_duration = chunk_end_time - chunk_start_time
            
            print(f"\n✅ 第 {chunk_idx + 1} 块处理完成")
            print(f"   耗时: {chunk_duration:.2f}秒")
            print(f"   成功任务: {sum(1 for p in chunk_predictions if p.get('result'))}/{len(chunk_predictions)}")
            print(f"   累计完成: {len(all_predictions)}/{total_tasks}")
            
            # 强制刷新输出
            import sys
            sys.stdout.flush()
        
        # 最终总结
        end_time = time.time()
        total_duration = end_time - start_time
        successful_tasks = sum(1 for p in all_predictions if p.get('result'))
        
        print(f"\n🎉 分块处理全部完成")
        print("="*60)
        print("📊 最终总结:")
        print(f"   处理任务: {len(all_predictions)}/{total_tasks}")
        print(f"   成功任务: {successful_tasks}/{len(all_predictions)}")
        print(f"   总耗时: {total_duration:.2f}秒")
        print(f"   平均耗时: {total_duration/len(all_predictions):.2f}秒/任务" if all_predictions else "   平均耗时: N/A")
        print(f"   总实体数: {sum(len(p.get('result', [])) for p in all_predictions)}")
        print("="*60)
        
        return ModelResponse(predictions=all_predictions)
    
    def _process_batch_export_mode(self, tasks: List[Dict]) -> ModelResponse:
        """批量导出模式：处理所有任务并生成导出文件"""
        total_tasks = len(tasks)
        all_predictions = []
        export_data = {
            "annotations": [],  # 改为annotations而不是predictions
            "metadata": {
                "processed_at": datetime.datetime.now().isoformat(),
                "total_tasks": total_tasks,
                "model_version": self.get("model_version"),
                "export_format": "label_studio_annotations"  # 更新格式标识
            }
        }
        
        # 创建导出目录
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"batch_annotations_{timestamp}.json"  # 改为annotations
        csv_filename = f"batch_annotations_{timestamp}.csv"   # 改为annotations
        log_filename = f"batch_processing_{timestamp}.log"
        
        json_filepath = export_dir / json_filename
        csv_filepath = export_dir / csv_filename
        log_filepath = export_dir / log_filename
        
        print(f"📁 批量导出模式启动")
        print(f"   总任务数: {total_tasks}")
        print(f"   导出目录: {export_dir.absolute()}")
        print(f"   JSON文件: {json_filename}")
        print(f"   CSV文件: {csv_filename}")
        print(f"   日志文件: {log_filename}")
        print("="*60)
        
        start_time = time.time()
        successful_count = 0
        failed_count = 0
        
        # 打开日志文件
        with open(log_filepath, 'w', encoding='utf-8') as log_file:
            def log_message(message):
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"[{timestamp}] {message}\n"
                log_file.write(log_entry)
                log_file.flush()
                print(message)
            
            log_message(f"开始批量处理 {total_tasks} 个任务")
            log_message(f"模型: {self.model_name}")
            log_message("="*60)
            
            for i, task in enumerate(tasks):
                task_start_time = time.time()
                task_id = task.get('id', f'task_{i+1}')
                
                log_message(f"\n🔄 处理任务 {i+1}/{total_tasks} (ID: {task_id})")
                
                # 显示任务内容预览
                task_data = task.get('data', {})
                text_content = ""
                for key in ['text', 'content', 'prompt', 'question', 'description', 'query']:
                    if key in task_data and isinstance(task_data[key], str):
                        text_content = task_data[key]
                        break
                
                if text_content:
                    preview = text_content[:100] + "..." if len(text_content) > 100 else text_content
                    log_message(f"   📝 文本预览: {preview}")
                
                try:
                    prediction = self._process_single_task(task)
                    task_end_time = time.time()
                    task_duration = task_end_time - task_start_time
                    
                    if prediction:
                        all_predictions.append(prediction)
                        entities_count = len(prediction.get('result', []))
                        
                        # 为导出格式添加任务信息（转换为标注格式）
                        annotation = {
                            "id": len(export_data["annotations"]) + 1,  # 标注ID
                            "task": task_id,
                            "result": prediction.get('result', []),  # 直接使用result，不包装在prediction中
                            "created_username": "ML-Backend",
                            "created_ago": "now",
                            "completed_by": 1,  # 系统用户ID
                            "was_cancelled": False,
                            "ground_truth": False,
                            "created_at": datetime.datetime.now().isoformat(),
                            "updated_at": datetime.datetime.now().isoformat(),
                            "lead_time": task_duration,
                            "task_data": task_data,
                            "entities_count": entities_count,
                            "model_version": self.get("model_version")
                        }
                        export_data["annotations"].append(annotation)
                        
                        successful_count += 1
                        log_message(f"✅ 任务 {i+1} 处理成功 (耗时: {task_duration:.2f}秒, 实体数: {entities_count})")
                    else:
                        prediction = {
                            "model_version": self.get("model_version"),
                            "score": 0.0,
                            "result": []
                        }
                        all_predictions.append(prediction)
                        
                        # 创建空的标注结果
                        annotation = {
                            "id": len(export_data["annotations"]) + 1,
                            "task": task_id,
                            "result": [],  # 空结果
                            "created_username": "ML-Backend",
                            "created_ago": "now",
                            "completed_by": 1,
                            "was_cancelled": False,
                            "ground_truth": False,
                            "created_at": datetime.datetime.now().isoformat(),
                            "updated_at": datetime.datetime.now().isoformat(),
                            "lead_time": task_duration,
                            "task_data": task_data,
                            "entities_count": 0,
                            "model_version": self.get("model_version"),
                            "status": "no_result"
                        }
                        export_data["annotations"].append(annotation)
                        
                        failed_count += 1
                        log_message(f"⚠️ 任务 {i+1} 处理完成但无结果 (耗时: {task_duration:.2f}秒)")
                        
                except Exception as e:
                    task_end_time = time.time()
                    task_duration = task_end_time - task_start_time
                    
                    prediction = {
                        "model_version": self.get("model_version"),
                        "score": 0.0,
                        "result": []
                    }
                    all_predictions.append(prediction)
                    
                    # 创建错误的标注结果
                    annotation = {
                        "id": len(export_data["annotations"]) + 1,
                        "task": task_id,
                        "result": [],  # 空结果
                        "created_username": "ML-Backend",
                        "created_ago": "now",
                        "completed_by": 1,
                        "was_cancelled": False,
                        "ground_truth": False,
                        "created_at": datetime.datetime.now().isoformat(),
                        "updated_at": datetime.datetime.now().isoformat(),
                        "lead_time": task_duration,
                        "task_data": task_data,
                        "entities_count": 0,
                        "model_version": self.get("model_version"),
                        "status": "error",
                        "error_message": str(e)
                    }
                    export_data["annotations"].append(annotation)
                    
                    failed_count += 1
                    log_message(f"❌ 任务 {i+1} 处理失败 (耗时: {task_duration:.2f}秒): {e}")
                
                # 每10个任务保存一次中间结果
                if (i + 1) % 10 == 0:
                    log_message(f"📊 中间进度: {i+1}/{total_tasks}, 成功: {successful_count}, 失败: {failed_count}")
        
        # 保存导出文件
        end_time = time.time()
        total_duration = end_time - start_time
        
        # 更新元数据
        export_data["metadata"].update({
            "processing_duration": total_duration,
            "successful_tasks": successful_count,
            "failed_tasks": failed_count,
            "total_entities": sum(ann.get("entities_count", 0) for ann in export_data["annotations"])
        })
        
        # 保存JSON文件
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        # 保存CSV文件
        self._save_csv_export(csv_filepath, export_data)
        
        # 生成最终报告
        print(f"\n🎉 批量处理完成")
        print("="*60)
        print("📊 处理总结:")
        print(f"   总任务数: {total_tasks}")
        print(f"   成功任务: {successful_count}")
        print(f"   失败任务: {failed_count}")
        print(f"   总耗时: {total_duration:.2f}秒")
        print(f"   平均耗时: {total_duration/total_tasks:.2f}秒/任务")
        print(f"   总实体数: {export_data['metadata']['total_entities']}")
        print("\n📁 导出文件:")
        print(f"   JSON文件: {json_filepath.absolute()}")
        print(f"   CSV文件: {csv_filepath.absolute()}")
        print(f"   日志文件: {log_filepath.absolute()}")
        print("\n💡 使用说明:")
        print("   1. 下载生成的JSON文件")
        print("   2. 在Label Studio前端选择'Import'")
        print("   3. 选择'Annotations'导入类型")
        print("   4. 上传JSON文件以导入所有标注结果")
        print("="*60)
        
        # 返回简化的响应（避免前端处理大量数据）
        summary_response = [{
            "model_version": self.get("model_version"),
            "score": 1.0,
            "result": [{
                "from_name": "prediction",
                "to_name": "text", 
                "type": "textarea",
                "value": {
                    "text": [f"批量标注完成！成功: {successful_count}/{total_tasks}\n"
                           f"导出文件: {json_filename}\n"
                           f"请下载文件并作为标注结果导入到Label Studio前端"]
                }
            }]
        }]
        
        return ModelResponse(predictions=summary_response)
    
    def _save_csv_export(self, csv_filepath: Path, export_data: dict):
        """保存CSV格式的导出文件"""
        import csv
        
        with open(csv_filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['annotation_id', 'task_id', 'text_content', 'entities_count', 'entities', 'processing_time', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for ann in export_data["annotations"]:
                task_data = ann.get("task_data", {})
                text_content = ""
                for key in ['text', 'content', 'prompt', 'question', 'description', 'query']:
                    if key in task_data and isinstance(task_data[key], str):
                        text_content = task_data[key]
                        break
                
                # 提取实体信息
                entities_info = []
                result = ann.get("result", [])
                for entity in result:
                    if entity.get("type") == "labels":
                        value = entity.get("value", {})
                        entities_info.append({
                            "text": value.get("text", ""),
                            "label": value.get("labels", []),
                            "start": value.get("start", 0),
                            "end": value.get("end", 0)
                        })
                
                writer.writerow({
                    'annotation_id': ann.get("id", ""),
                    'task_id': ann.get("task", ""),
                    'text_content': text_content[:200] + "..." if len(text_content) > 200 else text_content,
                    'entities_count': ann.get("entities_count", 0),
                    'entities': json.dumps(entities_info, ensure_ascii=False),
                    'processing_time': f"{ann.get('lead_time', 0):.2f}s",
                    'status': ann.get("status", "success")
                })
    
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
        
        prompt = f"""请对以下文本进行命名实体识别，识别出文本中存在的实体。

📝 文本内容：
{text_content}

🎯 支持的实体类型及示例：{categorized_examples}

⚠️ 重要说明：
1. 只识别文本中真实存在的实体，不要编造
2. 准确标注实体的起始和结束位置
3. 每个实体必须选择下面列出的标签类型之一
4. 标签名称必须完全匹配，不能使用近似或简化的名称
5. 如果不确定实体类型，选择最相近的类别

📋 请严格按照以下JSON格式返回结果：
{json_format}

🏷️ 所有有效的标签类型（必须严格使用以下标签之一）：
{entity_labels_list}

注意：标签名称必须与上面列出的完全一致，不接受任何变体或简化形式！"""
        
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
                original_label = entity['label']
                
                print(f"\n🔍 处理实体 {i+1}: {entity}")
                
                # 验证和映射标签
                validated_label_key = validate_and_map_label(original_label)
                if not validated_label_key:
                    print(f"   ❌ 实体 {i+1} 标签无效: '{original_label}'，跳过")
                    continue
                
                # 获取标签的description作为最终返回值
                if validated_label_key in NER_ENTITY_CONFIG:
                    label = NER_ENTITY_CONFIG[validated_label_key]['description']
                    print(f"   📝 标签映射: '{original_label}' -> '{validated_label_key}' -> '{label}'")
                else:
                    label = validated_label_key
                    print(f"   📝 标签已修正: '{original_label}' -> '{label}'")
                
                # 验证位置信息基本合理性
                if not isinstance(start, int) or not isinstance(end, int) or start < 0:
                    print(f"   ❌ 实体 {i+1} 位置信息无效 (start={start}, end={end})，跳过")
                    continue
                
                print(f"   📋 AI提供的文本: '{text}'")
                print(f"   📍 原始位置: {start}-{end}")
                
                # 先尝试修正位置，再进行范围检查
                corrected_start, corrected_end, corrected_text = self._correct_entity_position(
                    original_text, text, start, end
                )
                
                # 检查修正后的位置是否合理
                if corrected_start is None or corrected_end is None or corrected_text is None:
                    print(f"   ❌ 实体 {i+1} 位置修正失败，跳过")
                    continue
                
                # 验证修正后的位置不超出文本长度
                if corrected_end > len(original_text) or corrected_start < 0:
                    print(f"   ❌ 实体 {i+1} 修正后位置超出文本长度 (start={corrected_start}, end={corrected_end}, text_len={len(original_text)})，跳过")
                    continue
                
                print(f"   📋 修正后的文本: '{corrected_text}'")
                print(f"   📍 修正后位置: {corrected_start}-{corrected_end}")
                
                if corrected_text:
                    # 验证修正后的实体是否合理（长度不能太短，不能只是标点符号）
                    # 使用validated_label_key进行验证（配置文件中的键名）
                    if self._is_valid_entity(corrected_text, validated_label_key):
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


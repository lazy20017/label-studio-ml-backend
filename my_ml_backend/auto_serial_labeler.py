#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Label Studio 自动串行标注器

此程序自动从Label Studio获取未标注任务，逐个提交到ML Backend进行预测，
然后将标注结果保存回Label Studio。所有任务串行处理，确保前一个完成后再处理下一个。

功能特点：
- 🔄 串行处理：一个任务完成后再处理下一个
- 📊 实时进度：显示处理进度和统计信息
- 💾 自动保存：预测结果自动保存到Label Studio
- 🔁 错误重试：支持失败任务的自动重试
- 📝 详细日志：记录处理过程和错误信息
- ⚙️ 灵活配置：用户可自定义参数

作者: AI Assistant
创建时间: 2025-01-28
版本: 1.0.0
"""

import json
import time
import requests
import logging
import os
import sys
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime

# ================================
# 用户配置区域 - 请根据实际情况修改
# ================================


# Label Studio 配置
LABEL_STUDIO_URL = "http://localhost:8080"          # Label Studio服务地址
LABEL_STUDIO_API_TOKEN = "02be98ff6805d4d3c86f6b51bb0d538acb4c96e5"     # 您的API令牌，在Label Studio的Account Settings中获取
PROJECT_ID = 62                                     # 项目ID，在项目URL中可以找到

# ML Backend 配置  
ML_BACKEND_URL = "http://localhost:9090"            # ML Backend服务地址

# 处理配置
MAX_TASKS = None                                    # 最大处理任务数，None表示处理所有未标注任务
DELAY_BETWEEN_TASKS = 1.0                          # 任务间延迟时间（秒），避免对服务器造成压力
MAX_RETRIES = 0                                    # 失败任务的最大重试次数（0表示只尝试1次）
REQUEST_TIMEOUT = 300                              # 单个请求的超时时间（秒）

# 日志配置
LOG_LEVEL = logging.DEBUG                          # 日志级别：DEBUG, INFO, WARNING, ERROR (改为DEBUG以查看详细信息)
SAVE_DETAILED_LOG = True                           # 是否保存详细日志到文件

# ================================
# 程序代码 - 通常不需要修改
# ================================

# 配置日志
def setup_logging():
    """设置日志配置"""
    log_format = '%(asctime)s [%(levelname)s] %(message)s'
    
    # 控制台日志
    logging.basicConfig(
        level=LOG_LEVEL,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # 文件日志（如果启用）
    if SAVE_DETAILED_LOG:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"auto_labeler_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
        
        print(f"📁 详细日志将保存到: {log_file.absolute()}")

setup_logging()
logger = logging.getLogger(__name__)


class AutoSerialLabeler:
    """自动串行标注器类"""
    
    def __init__(self):
        """初始化标注器"""
        self.label_studio_url = LABEL_STUDIO_URL.rstrip('/')
        self.ml_backend_url = ML_BACKEND_URL.rstrip('/')
        self.api_token = LABEL_STUDIO_API_TOKEN
        self.project_id = PROJECT_ID
        
        # 验证配置
        self._validate_config()
        
        # 创建HTTP会话
        self.session = requests.Session()
        if self.api_token and self.api_token != "your_api_token_here":
            self.session.headers.update({
                'Authorization': f'Token {self.api_token}',
                'Content-Type': 'application/json'
            })
        
        # 统计信息
        self.stats = {
            'total_tasks': 0,
            'processed_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'start_time': None,
            'end_time': None,
            'errors': []
        }
        
        logger.info("✅ 自动串行标注器初始化完成")
        logger.info(f"   Label Studio: {self.label_studio_url}")
        logger.info(f"   ML Backend: {self.ml_backend_url}")
        logger.info(f"   项目ID: {self.project_id}")
    
    def _validate_config(self):
        """验证用户配置"""
        errors = []
        
        if not self.label_studio_url:
            errors.append("Label Studio URL不能为空")
        
        if not self.ml_backend_url:
            errors.append("ML Backend URL不能为空")
        
        if not self.api_token or self.api_token == "your_api_token_here":
            errors.append("请设置有效的API令牌")
        
        if not isinstance(self.project_id, int) or self.project_id <= 0:
            errors.append("项目ID必须是正整数")
        
        if errors:
            logger.error("❌ 配置验证失败:")
            for error in errors:
                logger.error(f"   • {error}")
            logger.error("\n💡 请在脚本顶部的配置区域修改相应参数")
            sys.exit(1)
    
    def test_connections(self):
        """测试服务连接"""
        logger.info("🔍 测试服务连接...")
        
        # 测试Label Studio连接
        try:
            response = self.session.get(f"{self.label_studio_url}/api/projects/{self.project_id}/")
            response.raise_for_status()
            project_info = response.json()
            logger.info(f"✅ Label Studio连接成功")
            logger.info(f"   项目名称: {project_info.get('title', 'Unknown')}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Label Studio连接失败: {e}")
            return False
        
        # 测试ML Backend连接
        try:
            response = requests.get(f"{self.ml_backend_url}/health", timeout=10)
            logger.info(f"✅ ML Backend连接成功")
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ ML Backend健康检查失败: {e}")
            logger.info("   将在实际预测时测试连接")
        
        return True
    
    def get_unlabeled_tasks(self) -> List[Dict]:
        """获取未标注的任务列表"""
        logger.info("🔍 获取未标注任务...")
        
        try:
            # 获取项目的所有任务
            params = {
                'project': self.project_id,
                'fields': 'all'
            }
            
            response = self.session.get(
                f"{self.label_studio_url}/api/tasks/",
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            # 检查响应内容类型
            response_data = response.json()
            logger.debug(f"📥 API响应类型: {type(response_data)}")
            logger.debug(f"📄 API响应内容预览: {str(response_data)[:200]}...")
            
            # 处理不同的响应格式
            if isinstance(response_data, str):
                logger.error(f"❌ API返回了字符串而不是JSON对象: {response_data[:100]}...")
                raise Exception("API响应格式错误：返回了字符串")
            elif isinstance(response_data, dict):
                # Label Studio API响应格式
                if 'tasks' in response_data:
                    all_tasks = response_data['tasks']
                    logger.info(f"📊 从Label Studio响应中获取到 {len(all_tasks)} 个任务")
                # 可能是分页响应
                elif 'results' in response_data:
                    all_tasks = response_data['results']
                    logger.info(f"📊 从分页响应中获取到 {len(all_tasks)} 个任务")
                else:
                    logger.error(f"❌ 字典响应中没有找到'tasks'或'results'字段: {list(response_data.keys())}")
                    raise Exception("API响应格式错误：字典中没有tasks或results字段")
            elif isinstance(response_data, list):
                all_tasks = response_data
                logger.info(f"📊 项目总任务数: {len(all_tasks)}")
            else:
                logger.error(f"❌ 未知的API响应格式: {type(response_data)}")
                raise Exception(f"API响应格式错误：未知类型 {type(response_data)}")
            
            # 验证任务格式
            if not all_tasks:
                logger.info("📋 项目中没有任务")
                return []
            
            # 检查第一个任务的格式
            first_task = all_tasks[0]
            if not isinstance(first_task, dict):
                logger.error(f"❌ 任务格式错误：期望字典，实际为 {type(first_task)}")
                raise Exception(f"任务格式错误：{type(first_task)}")
            
            logger.debug(f"📋 第一个任务格式: {json.dumps(first_task, ensure_ascii=False, indent=2)[:300]}...")
            
            # 筛选未标注的任务
            unlabeled_tasks = []
            for i, task in enumerate(all_tasks):
                if not isinstance(task, dict):
                    logger.warning(f"⚠️ 跳过格式错误的任务 {i}: {type(task)}")
                    continue
                    
                annotations = task.get('annotations', [])
                # 检查是否有有效的标注（未取消的）
                valid_annotations = [ann for ann in annotations if not ann.get('was_cancelled', False)]
                
                if not valid_annotations:
                    unlabeled_tasks.append(task)
            
            logger.info(f"🎯 未标注任务数: {len(unlabeled_tasks)}")
            
            # 应用任务数量限制
            if MAX_TASKS and len(unlabeled_tasks) > MAX_TASKS:
                unlabeled_tasks = unlabeled_tasks[:MAX_TASKS]
                logger.info(f"📋 限制处理数量为: {MAX_TASKS}")
            
            return unlabeled_tasks
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 获取任务列表失败: {e}")
            logger.error(f"   响应状态码: {getattr(e.response, 'status_code', 'N/A')}")
            logger.error(f"   响应内容: {getattr(e.response, 'text', 'N/A')[:200]}...")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON解析失败: {e}")
            logger.error(f"   响应内容: {response.text[:200]}...")
            raise
        except Exception as e:
            logger.error(f"❌ 处理任务列表时出错: {e}")
            logger.error(f"   错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"   堆栈跟踪: {traceback.format_exc()}")
            raise
    
    def predict_single_task(self, task: Dict) -> Optional[Dict]:
        """对单个任务进行预测"""
        task_id = task.get('id', 'unknown')
        
        try:
            # 构建预测请求
            request_data = {
                'tasks': [task],
                'model_version': 'latest',
                'project': f"{self.project_id}.{int(time.time())}",
                'params': {}
            }
            
            logger.debug(f"📤 发送预测请求: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
            
            # 发送预测请求
            response = requests.post(
                f"{self.ml_backend_url}/predict",
                json=request_data,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            # 解析响应
            prediction_result = response.json()
            logger.debug(f"📥 预测结果: {json.dumps(prediction_result, ensure_ascii=False, indent=2)}")
            
            return prediction_result
            
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ 任务 {task_id} 预测超时")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 任务 {task_id} 预测请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ 任务 {task_id} 预测处理异常: {e}")
            return None
    
    def save_annotation(self, task: Dict, prediction_result: Dict) -> bool:
        """保存预测结果为标注"""
        task_id = task.get('id')
        if not task_id:
            logger.error("❌ 任务ID为空，无法保存标注")
            return False
        
        try:
            logger.debug(f"🔍 预测结果类型: {type(prediction_result)}")
            logger.debug(f"📋 预测结果内容: {json.dumps(prediction_result, ensure_ascii=False, indent=2)[:500]}...")
            
            # 处理不同格式的预测结果
            results = []
            
            if isinstance(prediction_result, dict):
                # 检查是否有 'results' 字段
                if 'results' in prediction_result:
                    results = prediction_result['results']
                # 检查是否有 'predictions' 字段 (新的ModelResponse格式)
                elif 'predictions' in prediction_result:
                    predictions = prediction_result['predictions']
                    if predictions and len(predictions) > 0:
                        first_prediction = predictions[0]
                        if isinstance(first_prediction, dict) and 'result' in first_prediction:
                            results = [first_prediction]
                        elif isinstance(first_prediction, list):
                            # 可能是直接的结果列表
                            results = [{'result': first_prediction}]
                # 检查是否直接包含result字段
                elif 'result' in prediction_result:
                    results = [prediction_result]
                else:
                    logger.warning(f"⚠️ 未识别的预测结果格式，字段: {list(prediction_result.keys())}")
            elif isinstance(prediction_result, list):
                # 直接是结果列表
                results = prediction_result
            else:
                logger.error(f"❌ 预测结果格式错误: {type(prediction_result)}")
                return False
            
            if not results:
                logger.warning(f"⚠️ 任务 {task_id} 无预测结果")
                return False
            
            # 提取第一个结果的标注数据
            first_result = results[0]
            if isinstance(first_result, dict):
                result_data = first_result.get('result', [])
            else:
                result_data = first_result
            
            # 构建标注数据
            annotation_data = {
                'task': task_id,
                'result': result_data,
                'ground_truth': False,
                'was_cancelled': False,
                'created_username': 'Auto-ML-Labeler',
                'created_ago': 'now'
            }
            
            logger.debug(f"💾 保存标注数据: {json.dumps(annotation_data, ensure_ascii=False, indent=2)}")
            
            # 发送保存请求
            response = self.session.post(
                f"{self.label_studio_url}/api/tasks/{task_id}/annotations/",
                json=annotation_data,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            logger.debug(f"✅ 任务 {task_id} 标注保存成功")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 任务 {task_id} 标注保存失败: {e}")
            logger.error(f"   响应状态码: {getattr(e.response, 'status_code', 'N/A')}")
            logger.error(f"   响应内容: {getattr(e.response, 'text', 'N/A')[:200]}...")
            return False
        except Exception as e:
            logger.error(f"❌ 任务 {task_id} 标注保存异常: {e}")
            import traceback
            logger.error(f"   堆栈跟踪: {traceback.format_exc()}")
            return False
    
    def process_task_with_retry(self, task: Dict, max_retries: int = MAX_RETRIES) -> bool:
        """处理单个任务（包含重试机制）"""
        task_id = task.get('id', 'unknown')
        
        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(f"🔄 任务 {task_id} 第 {attempt + 1} 次尝试...")
                time.sleep(2 ** attempt)  # 指数退避
            
            try:
                # 显示任务内容预览
                task_data = task.get('data', {})
                for key in ['text', 'content', 'prompt', 'question', 'description']:
                    if key in task_data and isinstance(task_data[key], str):
                        preview = task_data[key][:100] + "..." if len(task_data[key]) > 100 else task_data[key]
                        logger.info(f"   📝 内容预览: {preview}")
                        break
                
                # 预测
                prediction_result = self.predict_single_task(task)
                if not prediction_result:
                    raise Exception("预测失败")
                
                # 检查ML Backend返回的错误标记
                if isinstance(prediction_result, dict):
                    # 检查predictions中是否有失败的预测
                    predictions = prediction_result.get('predictions', [])
                    if predictions:
                        first_prediction = predictions[0]
                        if (isinstance(first_prediction, dict) and 
                            (first_prediction.get('status') == 'failed' or 
                             'error' in first_prediction)):
                            error_msg = first_prediction.get('error', '预测失败')
                            raise Exception(f"ML Backend标记为失败: {error_msg}")
                    
                    # 检查直接的错误标记
                    if prediction_result.get('status') == 'failed' or 'error' in prediction_result:
                        error_msg = prediction_result.get('error', '预测失败')
                        raise Exception(f"ML Backend标记为失败: {error_msg}")
                
                # 先统计实体数量，判断是否真正成功
                entity_count = 0
                try:
                    if isinstance(prediction_result, dict):
                        # 检查不同的响应格式
                        if 'results' in prediction_result:
                            results = prediction_result['results']
                            if results and len(results) > 0:
                                entities = results[0].get('result', [])
                                entity_count = len(entities)
                        elif 'predictions' in prediction_result:
                            predictions = prediction_result['predictions']
                            if predictions and len(predictions) > 0:
                                first_prediction = predictions[0]
                                if isinstance(first_prediction, dict) and 'result' in first_prediction:
                                    entities = first_prediction['result']
                                    entity_count = len(entities)
                        elif 'result' in prediction_result:
                            entities = prediction_result['result']
                            entity_count = len(entities)
                except Exception as e:
                    logger.debug(f"⚠️ 统计实体数量时出错: {e}")
                    entity_count = 0
                
                # 检查是否识别到实体
                if entity_count == 0:
                    logger.error(f"❌ 任务 {task_id} 处理失败 - 未识别到任何实体")
                    # 即使预测成功但无实体，也应该记录为失败
                    raise Exception(f"未识别到任何实体 (返回了 {entity_count} 个实体)")
                
                # 保存标注
                if self.save_annotation(task, prediction_result):
                    logger.info(f"✅ 任务 {task_id} 处理成功 (识别到 {entity_count} 个实体)")
                    return True
                else:
                    raise Exception("标注保存失败")
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ 任务 {task_id} 尝试 {attempt + 1} 失败: {error_msg}")
                
                # 记录错误
                self.stats['errors'].append({
                    'task_id': task_id,
                    'attempt': attempt + 1,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                })
                
                if attempt == max_retries:
                    logger.error(f"❌ 任务 {task_id} 达到最大重试次数，放弃处理")
                    return False
        
        return False
    
    def run_serial_processing(self):
        """运行串行处理"""
        logger.info("🚀 开始自动串行标注")
        logger.info("=" * 60)
        
        # 初始化统计
        self.stats['start_time'] = datetime.now()
        
        try:
            # 测试连接
            if not self.test_connections():
                logger.error("❌ 服务连接测试失败，程序退出")
                return
            
            # 获取未标注任务
            tasks = self.get_unlabeled_tasks()
            
            if not tasks:
                logger.info("🎉 没有需要标注的任务")
                return
            
            self.stats['total_tasks'] = len(tasks)
            logger.info(f"📋 准备处理 {len(tasks)} 个任务")
            logger.info(f"⚙️ 配置: 任务间延迟={DELAY_BETWEEN_TASKS}秒, 最大重试={MAX_RETRIES}次")
            logger.info("=" * 60)
            
            # 逐个处理任务
            for i, task in enumerate(tasks):
                task_id = task.get('id', f'task_{i+1}')
                
                logger.info(f"\n{'='*40}")
                logger.info(f"🔄 处理任务 {i+1}/{len(tasks)} (ID: {task_id})")
                logger.info(f"{'='*40}")
                
                start_time = time.time()
                
                # 处理任务
                success = self.process_task_with_retry(task)
                
                end_time = time.time()
                duration = end_time - start_time
                
                # 更新统计
                self.stats['processed_tasks'] += 1
                if success:
                    self.stats['successful_tasks'] += 1
                else:
                    self.stats['failed_tasks'] += 1
                
                # 显示处理结果
                status = "✅ 成功" if success else "❌ 失败"
                logger.info(f"📊 任务 {i+1} 完成: {status} (耗时: {duration:.2f}秒)")
                
                # 显示进度
                progress = (i + 1) / len(tasks) * 100
                success_rate = (self.stats['successful_tasks'] / self.stats['processed_tasks']) * 100
                logger.info(f"📈 总进度: {i+1}/{len(tasks)} ({progress:.1f}%) | 成功率: {success_rate:.1f}%")
                
                # 任务间延迟
                if i < len(tasks) - 1 and DELAY_BETWEEN_TASKS > 0:
                    logger.info(f"⏱️ 等待 {DELAY_BETWEEN_TASKS}秒后处理下一个任务...")
                    time.sleep(DELAY_BETWEEN_TASKS)
            
            # 处理完成
            self.stats['end_time'] = datetime.now()
            self._print_final_summary()
            
        except KeyboardInterrupt:
            logger.warning("\n⚠️ 用户中断处理")
            self.stats['end_time'] = datetime.now()
            self._print_final_summary()
        except Exception as e:
            logger.error(f"❌ 处理过程中发生异常: {e}")
            raise
    
    def _print_final_summary(self):
        """打印最终处理摘要"""
        logger.info(f"\n🎉 自动标注处理完成")
        logger.info("=" * 60)
        logger.info("📊 处理摘要:")
        logger.info(f"   总任务数: {self.stats['total_tasks']}")
        logger.info(f"   已处理: {self.stats['processed_tasks']}")
        logger.info(f"   成功: {self.stats['successful_tasks']}")
        logger.info(f"   失败: {self.stats['failed_tasks']}")
        
        if self.stats['processed_tasks'] > 0:
            success_rate = (self.stats['successful_tasks'] / self.stats['processed_tasks']) * 100
            logger.info(f"   成功率: {success_rate:.1f}%")
        
        if self.stats['start_time'] and self.stats['end_time']:
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            logger.info(f"   总耗时: {duration:.2f}秒")
            if self.stats['processed_tasks'] > 0:
                avg_time = duration / self.stats['processed_tasks']
                logger.info(f"   平均耗时: {avg_time:.2f}秒/任务")
        
        # 错误摘要
        if self.stats['errors']:
            logger.info(f"\n❌ 错误摘要 ({len(self.stats['errors'])} 个错误):")
            error_counts = {}
            for error in self.stats['errors']:
                error_type = error['error'][:50] + "..." if len(error['error']) > 50 else error['error']
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
            for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"   • {error_type}: {count} 次")
        
        logger.info("=" * 60)


def main():
    """主函数"""
    print("🤖 Label Studio 自动串行标注器")
    print("=" * 60)
    print("📝 程序说明:")
    print("   • 自动获取未标注任务")
    print("   • 串行提交ML Backend进行预测")
    print("   • 自动保存标注结果到Label Studio")
    print("   • 支持失败重试和详细日志")
    print("=" * 60)
    print("⚙️ 配置检查:")
    print(f"   Label Studio: {LABEL_STUDIO_URL}")
    print(f"   ML Backend: {ML_BACKEND_URL}")
    print(f"   项目ID: {PROJECT_ID}")
    print(f"   最大任务数: {MAX_TASKS or '无限制'}")
    print(f"   任务间延迟: {DELAY_BETWEEN_TASKS}秒")
    print(f"   最大重试: {MAX_RETRIES}次")
    print("=" * 60)
    
    # 确认启动
    try:
        user_input = input("📋 确认配置无误，按回车开始处理，或输入 'q' 退出: ").strip().lower()
        if user_input == 'q':
            print("👋 程序退出")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n👋 程序退出")
        sys.exit(0)
    
    # 创建并运行标注器
    try:
        labeler = AutoSerialLabeler()
        labeler.run_serial_processing()
        
        print(f"\n🎉 处理完成! 成功: {labeler.stats['successful_tasks']}/{labeler.stats['processed_tasks']}")
        
    except KeyboardInterrupt:
        print("\n👋 用户中断程序")
    except Exception as e:
        logger.error(f"❌ 程序运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

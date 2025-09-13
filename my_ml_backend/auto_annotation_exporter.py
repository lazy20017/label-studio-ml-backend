#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Label Studio 项目标注结果导出器

此程序自动从Label Studio导出项目的标注结果，支持JSON格式导出。
专注于单个项目的高质量标注数据导出。

功能特点：
- 📋 单项目导出：专注于单个项目的标注结果导出
- 📂 智能命名：自动使用项目名称和时间戳生成文件名
- 📊 结构化输出：以JSON格式导出标注数据（支持简洁和完整格式）
- 🎯 完整数据：包含任务、标注、元数据等完整信息
- 📝 详细统计：显示导出进度和统计信息
- ⚙️ 灵活配置：用户可自定义参数

使用方法：
```bash
cd label-studio-ml-backend/my_ml_backend
python auto_annotation_exporter.py
```

作者: AI Assistant
创建时间: 2025-01-28
版本: 2.0.0
"""

import json
import time
import requests
import logging
import os
from typing import List, Dict, Optional, Union
from pathlib import Path
from datetime import datetime

# ================================
# 用户配置区域 - 请根据实际情况修改
# ================================

# 导出文件夹配置 - 使用绝对路径，方便修改
EXPORT_BASE_DIR = r"E:\pydemo\01LabelStudio-test\label-studio-ml-backend\my_ml_backend\exported_annotations"  # 导出文件夹绝对路径

# Label Studio 配置
LABEL_STUDIO_URL = "http://localhost:8080"          # Label Studio服务地址
LABEL_STUDIO_API_TOKEN = "02be98ff6805d4d3c86f6b51bb0d538acb4c96e5"     # 您的API令牌，在Label Studio的Account Settings中获取
REQUEST_TIMEOUT = 61                                # 单个请求的超时时间（秒）
DELAY_BETWEEN_REQUESTS = 0.5                       # 请求间延迟时间（秒），避免对服务器造成压力

# 导出选项
INCLUDE_TASK_DATA = True                            # 是否包含原始任务数据
INCLUDE_PREDICTIONS = True                          # 是否包含预测结果
INCLUDE_METADATA = True                             # 是否包含元数据
PRETTY_JSON = False                                 # 是否美化JSON输出（False=压缩格式）
SIMPLE_FORMAT = True                                # 是否使用简洁格式（仅导出任务数组）

# 日志配置
LOG_LEVEL = logging.DEBUG                           # 日志级别：DEBUG, INFO, WARNING, ERROR
SAVE_DETAILED_LOG = True                            # 是否保存详细日志到文件

# ================================
# 程序代码 - 通常不需要修改
# ================================

# 配置日志
def setup_logging():
    """设置日志配置"""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # 控制台日志处理器
    handlers = [logging.StreamHandler()]
    
    # 如果启用详细日志，添加文件处理器
    if SAVE_DETAILED_LOG:
        log_filename = f"auto_annotation_exporter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=LOG_LEVEL,
        format=log_format,
        handlers=handlers
    )

# 设置日志
setup_logging()
logger = logging.getLogger(__name__)


class AutoAnnotationExporter:
    """自动标注结果导出器类"""
    
    def __init__(self, 
                 label_studio_url: str = LABEL_STUDIO_URL,
                 api_token: str = LABEL_STUDIO_API_TOKEN,
                 output_dir: str = EXPORT_BASE_DIR):
        """
        初始化导出器
        
        Args:
            label_studio_url: Label Studio服务地址
            api_token: API访问令牌
            output_dir: 输出目录
        """
        self.label_studio_url = label_studio_url.rstrip('/')
        self.api_token = api_token
        self.output_dir = Path(output_dir)
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置HTTP会话
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        })
        
        # 统计信息
        self.stats = {
            'total_projects': 0,
            'exported_projects': 0,
            'total_tasks': 0,
            'total_annotations': 0,
            'errors': []
        }
        
        logger.info(f"🚀 标注结果导出器已初始化")
        logger.info(f"📍 Label Studio URL: {self.label_studio_url}")
        logger.info(f"📁 输出目录: {self.output_dir.absolute()}")
    
    def test_connection(self) -> bool:
        """测试与Label Studio的连接"""
        try:
            logger.info("🔗 测试Label Studio连接...")
            response = self.session.get(f"{self.label_studio_url}/api/projects/", timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ 连接成功")
                return True
            else:
                logger.error(f"❌ 连接失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 连接异常: {e}")
            return False
    
    def get_all_projects(self) -> Optional[List[Dict]]:
        """
        获取所有项目信息
        
        Returns:
            项目列表，包含id、title等信息，如果失败返回None
        """
        try:
            logger.info("📋 正在查询所有项目...")
            response = self.session.get(f"{self.label_studio_url}/api/projects/", timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查是否是分页响应
                if isinstance(data, dict) and 'results' in data:
                    projects = data['results']
                    total_count = data.get('count', len(projects))
                    logger.info(f"✅ 成功获取 {len(projects)} 个项目 (总计 {total_count} 个)")
                    
                    # 如果有更多页面，获取所有页面的数据
                    all_projects = projects.copy()
                    next_url = data.get('next')
                    while next_url:
                        logger.info(f"📄 获取下一页项目数据...")
                        next_response = self.session.get(next_url, timeout=REQUEST_TIMEOUT)
                        if next_response.status_code == 200:
                            next_data = next_response.json()
                            all_projects.extend(next_data.get('results', []))
                            next_url = next_data.get('next')
                        else:
                            logger.warning(f"⚠️ 获取下一页失败: {next_response.status_code}")
                            break
                    
                    logger.info(f"✅ 总共获取 {len(all_projects)} 个项目")
                    return all_projects
                elif isinstance(data, list):
                    # 直接返回列表
                    logger.info(f"✅ 成功获取 {len(data)} 个项目")
                    return data
                else:
                    logger.error(f"❌ 未知响应格式: {type(data)}")
                    return None
            else:
                logger.error(f"❌ 查询项目失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 查询项目异常: {e}")
            return None
    
    def get_project_tasks(self, project_id: int) -> Optional[List[Dict]]:
        """
        获取项目的所有任务
        
        Args:
            project_id: 项目ID
            
        Returns:
            任务列表，如果失败返回None
        """
        try:
            logger.debug(f"📋 获取项目 {project_id} 的任务...")
            
            # 尝试不同的API端点和参数组合
            api_attempts = [
                # 尝试1: 标准的任务API
                {
                    'url': f"{self.label_studio_url}/api/tasks/",
                    'params': {'project': project_id, 'fields': 'all'},
                    'desc': '标准任务API'
                },
                # 尝试2: 项目特定的任务API
                {
                    'url': f"{self.label_studio_url}/api/projects/{project_id}/tasks/",
                    'params': {},
                    'desc': '项目特定任务API'
                },
                # 尝试3: 简化参数
                {
                    'url': f"{self.label_studio_url}/api/tasks/",
                    'params': {'project': project_id},
                    'desc': '简化参数任务API'
                }
            ]
            
            response_data = None
            for attempt in api_attempts:
                try:
                    logger.debug(f"🔍 尝试 {attempt['desc']}: {attempt['url']}")
                    response = self.session.get(
                        attempt['url'],
                        params=attempt['params'],
                        timeout=REQUEST_TIMEOUT
                    )
                    response.raise_for_status()
                    
                    # 检查响应内容类型
                    response_data = response.json()
                    logger.debug(f"✅ {attempt['desc']} 成功，响应类型: {type(response_data)}")
                    
                    # 如果成功获取到数据，就跳出循环
                    if response_data is not None:
                        break
                        
                except Exception as e:
                    logger.debug(f"⚠️ {attempt['desc']} 失败: {e}")
                    continue
            
            if response_data is None:
                logger.error(f"❌ 所有API尝试都失败了")
                return None
            
            # 处理不同的响应格式
            if isinstance(response_data, dict) and 'results' in response_data:
                # 标准分页响应格式
                tasks = response_data['results']
                total_count = response_data.get('count', len(tasks))
                
                # 如果有更多页面，获取所有页面的数据
                all_tasks = tasks.copy()
                next_url = response_data.get('next')
                while next_url:
                    logger.debug(f"📄 获取下一页任务数据...")
                    next_response = self.session.get(next_url, timeout=REQUEST_TIMEOUT)
                    if next_response.status_code == 200:
                        next_data = next_response.json()
                        all_tasks.extend(next_data.get('results', []))
                        next_url = next_data.get('next')
                    else:
                        logger.warning(f"⚠️ 获取下一页任务失败: {next_response.status_code}")
                        break
                
                logger.debug(f"✅ 项目 {project_id} 总共获取 {len(all_tasks)} 个任务")
                return all_tasks
                
            elif isinstance(response_data, dict):
                # 处理dict响应但没有'results'字段的情况
                logger.debug(f"🔍 项目 {project_id} 响应格式分析: {list(response_data.keys())}")
                logger.debug(f"📊 响应数据大小: {len(response_data)} 个字段")
                logger.debug(f"📊 响应内容示例: {str(response_data)[:500]}...")
                
                # 检查是否是直接的任务对象或其他格式
                if 'id' in response_data and 'data' in response_data:
                    # 单个任务对象
                    logger.debug(f"✅ 项目 {project_id} 获取单个任务")
                    return [response_data]
                elif len(response_data) == 0:
                    # 空的dict响应
                    logger.debug(f"✅ 项目 {project_id} 无任务数据")
                    return []
                else:
                    # 检查常见的分页字段
                    if 'count' in response_data:
                        count = response_data.get('count', 0)
                        logger.debug(f"📊 API报告的任务总数: {count}")
                        if count == 0:
                            logger.info(f"📦 项目 {project_id} 确认无任务")
                            return []
                    
                    # 尝试从dict中提取任务数据
                    possible_task_keys = ['tasks', 'data', 'items', 'task_list', 'task_data']
                    for key in possible_task_keys:
                        if key in response_data:
                            tasks = response_data[key]
                            if isinstance(tasks, list):
                                logger.debug(f"✅ 项目 {project_id} 从字段 '{key}' 获取 {len(tasks)} 个任务")
                                return tasks
                            else:
                                logger.debug(f"🔍 字段 '{key}' 存在但不是列表类型: {type(tasks)}")
                    
                    # 检查是否是空项目的标准响应
                    empty_indicators = ['count', 'next', 'previous', 'results']
                    if all(key in response_data for key in empty_indicators) and response_data.get('count', 0) == 0:
                        logger.info(f"📦 项目 {project_id} 是标准的空结果响应")
                        return []
                    
                    # 如果上述方法都失败，记录详细信息并返回空列表
                    logger.warning(f"⚠️ 项目 {project_id} 未识别的dict响应格式")
                    logger.warning(f"📋 所有字段: {list(response_data.keys())}")
                    for key, value in response_data.items():
                        logger.debug(f"  - {key}: {type(value)} = {str(value)[:100]}...")
                    return []
                
            elif isinstance(response_data, list):
                # 直接返回任务列表
                logger.debug(f"✅ 项目 {project_id} 获取 {len(response_data)} 个任务")
                return response_data
            else:
                logger.error(f"❌ 项目 {project_id} 未知任务响应格式: {type(response_data)}")
                logger.debug(f"响应内容: {str(response_data)[:200]}...")
                return None
                
        except Exception as e:
            logger.error(f"❌ 获取项目 {project_id} 任务异常: {e}")
            return None
    
    def _extract_source_filename(self, task_data: Dict) -> str:
        """
        从任务数据中提取源文件名称
        
        Args:
            task_data: 任务数据字典
            
        Returns:
            源文件名称，如果未找到则返回"未知"
        """
        # 调试信息：记录任务数据结构
        logger.debug(f"🔍 分析任务数据结构: {list(task_data.keys()) if task_data else '空数据'}")
        
        # 常见的文件名字段列表
        filename_fields = [
            'filename', 'file_name', 'fileName', 'name', 'file', 
            'image', 'audio', 'video', 'document', 'text_file',
            'source_file', 'original_file', 'filepath', 'file_path',
            'title', 'source', 'input_file'  # 新增一些可能的字段
        ]
        
        # 首先检查直接的文件名字段
        for field in filename_fields:
            if field in task_data and task_data[field]:
                filename = str(task_data[field])
                logger.debug(f"✅ 从字段 '{field}' 找到文件名: {filename}")
                # 如果是完整路径，只取文件名部分
                if '/' in filename:
                    filename = filename.split('/')[-1]
                elif '\\' in filename:
                    filename = filename.split('\\')[-1]
                return filename
        
        # 检查嵌套字段（例如在 file 对象中）
        if 'file' in task_data and isinstance(task_data['file'], dict):
            file_obj = task_data['file']
            logger.debug(f"🔍 检查嵌套file对象: {list(file_obj.keys())}")
            for field in filename_fields:
                if field in file_obj and file_obj[field]:
                    filename = str(file_obj[field])
                    logger.debug(f"✅ 从嵌套字段 'file.{field}' 找到文件名: {filename}")
                    if '/' in filename:
                        filename = filename.split('/')[-1]
                    elif '\\' in filename:
                        filename = filename.split('\\')[-1]
                    return filename
        
        # 检查URL中的文件名
        url_fields = ['url', 'image_url', 'audio_url', 'video_url', 'file_url']
        for field in url_fields:
            if field in task_data and task_data[field]:
                url = str(task_data[field])
                logger.debug(f"🔍 检查URL字段 '{field}': {url}")
                # 从URL中提取文件名
                if '/' in url:
                    filename = url.split('/')[-1]
                    # 移除URL参数
                    if '?' in filename:
                        filename = filename.split('?')[0]
                    if filename and filename != '':
                        logger.debug(f"✅ 从URL字段 '{field}' 提取文件名: {filename}")
                        return filename
        
        # 检查text字段，有时文件名可能包含在文本中
        if 'text' in task_data and task_data['text']:
            text = str(task_data['text'])
            # 如果文本很短且包含文件扩展名，可能就是文件名
            if len(text) < 100 and ('.' in text):
                # 检查是否包含常见文件扩展名
                extensions = ['.txt', '.pdf', '.doc', '.docx', '.csv', '.json', '.xml', '.html']
                for ext in extensions:
                    if ext.lower() in text.lower():
                        # 尝试提取文件名
                        words = text.split()
                        for word in words:
                            if ext.lower() in word.lower():
                                logger.debug(f"✅ 从text字段推测文件名: {word}")
                                return word
        
        # 记录未找到文件名的情况
        logger.debug(f"⚠️ 未找到文件名，任务数据内容: {str(task_data)[:200]}...")
        
        # 如果都找不到，返回未知
        return "未知"
    
    def format_annotation_data(self, project: Dict, tasks: List[Dict]) -> Dict:
        """
        格式化标注数据
        
        Args:
            project: 项目信息
            tasks: 任务列表
            
        Returns:
            格式化后的标注数据
        """
        # 统计信息
        total_tasks = len(tasks)
        annotated_tasks = 0
        total_annotations = 0
        
        formatted_tasks = []
        
        for task in tasks:
            # 获取标注信息
            annotations = task.get('annotations', [])
            # 过滤掉已取消的标注
            valid_annotations = [ann for ann in annotations if not ann.get('was_cancelled', False)]
            
            if valid_annotations:
                annotated_tasks += 1
                total_annotations += len(valid_annotations)
            
            # 提取数据来源文件名称
            task_data = task.get('data', {})
            source_filename = self._extract_source_filename(task_data)
            
            # 格式化任务数据
            formatted_task = {
                'task_id': task.get('id'),
                'created_at': task.get('created_at'),
                'updated_at': task.get('updated_at'),
                'source_filename': source_filename,  # 添加数据来源文件名称字段
            }
            
            # 包含原始任务数据
            if INCLUDE_TASK_DATA:
                formatted_task['data'] = task.get('data', {})
            
            # 包含标注数据
            formatted_annotations = []
            for annotation in valid_annotations:
                formatted_annotation = {
                    'annotation_id': annotation.get('id'),
                    'created_at': annotation.get('created_at'),
                    'updated_at': annotation.get('updated_at'),
                    'created_by': annotation.get('created_by'),
                    'lead_time': annotation.get('lead_time'),
                    'result': annotation.get('result', [])
                }
                
                # 包含元数据
                if INCLUDE_METADATA:
                    formatted_annotation['metadata'] = {
                        'was_cancelled': annotation.get('was_cancelled', False),
                        'ground_truth': annotation.get('ground_truth', False),
                        'unique_id': annotation.get('unique_id'),
                        'import_id': annotation.get('import_id')
                    }
                
                formatted_annotations.append(formatted_annotation)
            
            formatted_task['annotations'] = formatted_annotations
            
            # 包含预测数据
            if INCLUDE_PREDICTIONS:
                predictions = task.get('predictions', [])
                formatted_predictions = []
                for prediction in predictions:
                    formatted_prediction = {
                        'prediction_id': prediction.get('id'),
                        'created_at': prediction.get('created_at'),
                        'model_version': prediction.get('model_version'),
                        'score': prediction.get('score'),
                        'result': prediction.get('result', [])
                    }
                    formatted_predictions.append(formatted_prediction)
                formatted_task['predictions'] = formatted_predictions
            
            formatted_tasks.append(formatted_task)
        
        # 更新统计信息
        self.stats['total_tasks'] += total_tasks
        self.stats['total_annotations'] += total_annotations
        
        # 构建完整的导出数据
        export_data = {
            'export_info': {
                'exported_at': datetime.now().isoformat(),
                'label_studio_url': self.label_studio_url,
                'exporter_version': '1.0.0'
            },
            'project_info': {
                'project_id': project.get('id'),
                'title': project.get('title'),
                'description': project.get('description'),
                'created_at': project.get('created_at'),
                'updated_at': project.get('updated_at'),
                'label_config': project.get('label_config')
            },
            'statistics': {
                'total_tasks': total_tasks,
                'annotated_tasks': annotated_tasks,
                'total_annotations': total_annotations,
                'completion_rate': (annotated_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            'tasks': formatted_tasks
        }
        
        return export_data
    
    def format_annotation_data_simple(self, project: Dict, tasks: List[Dict]) -> List[Dict]:
        """
        格式化标注数据为简洁格式（仅包含任务数组）
        
        Args:
            project: 项目信息
            tasks: 任务列表
            
        Returns:
            简洁格式的标注数据数组
        """
        simple_tasks = []
        
        for task in tasks:
            # 获取标注信息
            annotations = task.get('annotations', [])
            # 过滤掉已取消的标注
            valid_annotations = [ann for ann in annotations if not ann.get('was_cancelled', False)]
            
            for annotation in valid_annotations:
                # 获取任务文本
                text = task.get('data', {}).get('text', '')
                
                # 转换标注结果为简洁格式
                labels = []
                for result_item in annotation.get('result', []):
                    if result_item.get('type') == 'labels':
                        value = result_item.get('value', {})
                        label_info = {
                            'start': value.get('start'),
                            'end': value.get('end'), 
                            'text': value.get('text'),
                            'labels': value.get('labels', [])
                        }
                        labels.append(label_info)
                
                # 提取数据来源文件名称
                task_data = task.get('data', {})
                source_filename = self._extract_source_filename(task_data)
                
                # 构建简洁格式的任务
                simple_task = {
                    'text': text,
                    'id': task.get('id'),
                    'label': labels,
                    'annotator': annotation.get('created_by'),
                    'annotation_id': annotation.get('id'),
                    'created_at': annotation.get('created_at'),
                    'updated_at': annotation.get('updated_at'),
                    'lead_time': annotation.get('lead_time'),
                    'source_filename': source_filename  # 添加数据来源文件名称字段
                }
                
                simple_tasks.append(simple_task)
        
        return simple_tasks
    
    def export_project(self, project_id: int, output_file: Optional[str] = None) -> Optional[Dict]:
        """
        导出单个项目的标注结果
        
        Args:
            project_id: 项目ID
            output_file: 输出文件路径，如果为None则使用项目名称生成文件名
            
        Returns:
            导出的数据，如果失败返回None
        """
        try:
            logger.info(f"🔄 开始导出项目 {project_id}...")
            
            # 获取项目信息
            logger.debug(f"📋 获取项目 {project_id} 信息...")
            project_response = self.session.get(
                f"{self.label_studio_url}/api/projects/{project_id}/",
                timeout=REQUEST_TIMEOUT
            )
            project_response.raise_for_status()
            project = project_response.json()
            
            project_title = project.get('title', f'project_{project_id}')
            logger.info(f"📊 项目名称: {project_title}")
            
            # 获取项目任务
            tasks = self.get_project_tasks(project_id)
            if tasks is None:
                logger.error(f"❌ 无法获取项目 {project_id} 的任务")
                return None
            
            logger.info(f"📝 项目 {project_id} 共有 {len(tasks)} 个任务")
            
            # 格式化数据
            if SIMPLE_FORMAT:
                export_data = self.format_annotation_data_simple(project, tasks)
            else:
                export_data = self.format_annotation_data(project, tasks)
            
            # 生成输出文件名
            if output_file is None:
                # 清理项目名称，移除非法字符
                safe_title = "".join(c for c in project_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_title = safe_title.replace(' ', '_')
                
                # 生成时间戳
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                # 构造文件名
                output_file = f"{safe_title}_{timestamp}.json"
            
            # 保存到文件
            output_path = self.output_dir / output_file
            with open(output_path, 'w', encoding='utf-8') as f:
                if PRETTY_JSON:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(export_data, f, ensure_ascii=False)
            
            logger.info(f"💾 项目 {project_id} 标注结果已保存到: {output_path}")
            
            self.stats['exported_projects'] += 1
            logger.info(f"✅ 项目 {project_id} 导出完成")
            
            return export_data
            
        except Exception as e:
            error_msg = f"导出项目 {project_id} 失败: {e}"
            logger.error(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return None
    
    def batch_export_projects(self, start_id: int, end_id: int) -> Dict:
        """
        批量导出项目的标注结果
        
        Args:
            start_id: 开始项目ID
            end_id: 结束项目ID
            
        Returns:
            批量导出结果统计
        """
        logger.info(f"🔄 开始批量导出项目 {start_id} 到 {end_id}...")
        
        batch_stats = {
            'total_projects': 0,
            'successful_exports': 0,
            'failed_exports': 0,
            'exported_files': [],
            'failed_projects': []
        }
        
        # 确保ID范围有效
        if start_id > end_id:
            logger.error("❌ 开始项目ID不能大于结束项目ID")
            return batch_stats
        
        # 逐个导出项目
        for project_id in range(start_id, end_id + 1):
            logger.info(f"📦 正在导出项目 {project_id} ({project_id - start_id + 1}/{end_id - start_id + 1})")
            batch_stats['total_projects'] += 1
            
            try:
                result = self.export_project(project_id)
                if result:
                    batch_stats['successful_exports'] += 1
                    
                    # 记录导出的文件信息
                    projects = self.get_all_projects()
                    if projects:
                        project_info = next((p for p in projects if p.get('id') == project_id), None)
                        if project_info:
                            project_title = project_info.get('title', f'project_{project_id}')
                            safe_title = "".join(c for c in project_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                            safe_title = safe_title.replace(' ', '_')
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            filename = f"{safe_title}_{timestamp}.json"
                            batch_stats['exported_files'].append({
                                'project_id': project_id,
                                'title': project_title,
                                'filename': filename
                            })
                        else:
                            batch_stats['exported_files'].append({
                                'project_id': project_id,
                                'title': f'项目_{project_id}',
                                'filename': f'project_{project_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                            })
                    
                    logger.info(f"✅ 项目 {project_id} 导出成功")
                else:
                    batch_stats['failed_exports'] += 1
                    batch_stats['failed_projects'].append(project_id)
                    logger.warning(f"⚠️ 项目 {project_id} 导出失败")
            
            except Exception as e:
                batch_stats['failed_exports'] += 1
                batch_stats['failed_projects'].append(project_id)
                error_msg = f"项目 {project_id} 导出异常: {e}"
                logger.error(f"❌ {error_msg}")
                self.stats['errors'].append(error_msg)
            
            # 添加延迟避免对服务器造成压力
            if project_id < end_id:  # 最后一个项目不需要延迟
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # 打印批量导出总结
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 批量导出完成总结")
        logger.info(f"{'='*60}")
        logger.info(f"📋 项目范围: {start_id} - {end_id}")
        logger.info(f"✅ 成功导出: {batch_stats['successful_exports']}")
        logger.info(f"❌ 导出失败: {batch_stats['failed_exports']}")
        logger.info(f"📈 成功率: {(batch_stats['successful_exports'] / batch_stats['total_projects'] * 100):.1f}%")
        
        if batch_stats['failed_projects']:
            logger.info(f"❌ 失败的项目ID: {batch_stats['failed_projects']}")
        
        if batch_stats['exported_files']:
            logger.info(f"📁 导出的文件:")
            for file_info in batch_stats['exported_files']:
                logger.info(f"  - 项目 {file_info['project_id']}: {file_info['filename']}")
        
        logger.info(f"{'='*60}")
        
        return batch_stats
    
    def print_statistics(self):
        """打印导出统计信息"""
        print(f"\n{'='*60}")
        print(f"📊 标注结果导出统计信息")
        print(f"{'='*60}")
        print(f"📋 总项目数: {self.stats['total_projects']}")
        print(f"✅ 导出成功: {self.stats['exported_projects']}")
        print(f"❌ 导出失败: {self.stats['total_projects'] - self.stats['exported_projects']}")
        print(f"📝 总任务数: {self.stats['total_tasks']}")
        print(f"🏷️ 总标注数: {self.stats['total_annotations']}")
        
        if self.stats['total_projects'] > 0:
            success_rate = (self.stats['exported_projects'] / self.stats['total_projects']) * 100
            print(f"📈 导出成功率: {success_rate:.1f}%")
        
        if self.stats['errors']:
            print(f"\n❌ 错误信息:")
            for error in self.stats['errors']:
                print(f"  - {error}")
        
        print(f"📁 输出目录: {self.output_dir.absolute()}")
        print(f"{'='*60}")


def main():
    """主函数"""
    print("🚀 Label Studio 项目标注结果导出器")
    print("=" * 60)
    
    # 创建导出器实例
    exporter = AutoAnnotationExporter()
    
    # 测试连接
    if not exporter.test_connection():
        logger.error("❌ 无法连接到Label Studio，请检查配置")
        return
    
    # 交互式菜单
    while True:
        print(f"\n{'-'*50}")
        print("📋 选择操作:")
        print("1. 导出单个项目")
        print("2. 批量导出项目")
        print("3. 查看项目列表")
        print("4. 退出")
        print(f"{'-'*50}")
        
        choice = input("请选择操作 (1-4): ").strip()
        
        if choice == "1":
            # 导出单个项目
            try:
                project_id = int(input("请输入项目ID: ").strip())
                result = exporter.export_project(project_id)
                if result:
                    print(f"✅ 项目 {project_id} 导出成功")
                else:
                    print(f"❌ 项目 {project_id} 导出失败")
            except ValueError:
                print("❌ 请输入有效的项目ID")
        
        elif choice == "2":
            # 批量导出项目
            try:
                start_id = int(input("请输入开始项目ID: ").strip())
                end_id = int(input("请输入结束项目ID: ").strip())
                
                if start_id > end_id:
                    print("❌ 开始项目ID不能大于结束项目ID")
                    continue
                
                # 确认批量导出
                project_count = end_id - start_id + 1
                print(f"\n📋 即将批量导出 {project_count} 个项目 (ID: {start_id} - {end_id})")
                confirm = input("确认执行批量导出？(y/n): ").strip().lower()
                
                if confirm in ['y', 'yes', '是', '确认']:
                    batch_result = exporter.batch_export_projects(start_id, end_id)
                    print(f"\n🎉 批量导出完成！")
                    print(f"✅ 成功: {batch_result['successful_exports']}/{batch_result['total_projects']}")
                    print(f"❌ 失败: {batch_result['failed_exports']}/{batch_result['total_projects']}")
                    
                    if batch_result['exported_files']:
                        print(f"\n📁 导出的文件:")
                        for file_info in batch_result['exported_files']:
                            print(f"  - {file_info['filename']}")
                else:
                    print("⏹️ 取消批量导出")
                    
            except ValueError:
                print("❌ 请输入有效的项目ID")
        
        elif choice == "3":
            # 查看项目列表
            projects = exporter.get_all_projects()
            if projects:
                print(f"\n📋 找到 {len(projects)} 个项目:")
                print(f"{'ID':<5} {'项目名称':<40} {'任务数':<8} {'创建时间':<20}")
                print("-" * 75)
                
                for project in projects:
                    title = project.get('title', '未命名')
                    if len(title) > 38:
                        title = title[:35] + "..."
                    
                    task_count = project.get('task_number', 0)
                    
                    created_at = project.get('created_at', '')
                    if created_at:
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            created_at = dt.strftime('%Y-%m-%d %H:%M')
                        except:
                            created_at = created_at[:16] if len(created_at) > 16 else created_at
                    else:
                        created_at = "未知"
                    
                    print(f"{project['id']:<5} {title:<40} {task_count:<8} {created_at:<20}")
                    
                # 显示ID范围提示
                if projects:
                    min_id = min(p.get('id', 0) for p in projects)
                    max_id = max(p.get('id', 0) for p in projects)
                    print(f"\n💡 提示: 项目ID范围为 {min_id} - {max_id}")
            else:
                print("❌ 无法获取项目列表")
        
        elif choice == "4":
            print("👋 感谢使用 Label Studio 标注结果导出器")
            break
        
        else:
            print("❌ 无效选择，请输入 1-4")
    
    # 显示最终统计
    exporter.print_statistics()


if __name__ == "__main__":
    main()

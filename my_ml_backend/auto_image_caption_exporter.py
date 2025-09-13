#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图生文标注结果导出器

此程序专门用于导出Label Studio中图生文（Image Captioning）项目的标注结果。
能够处理caption字段中的转义字符，并添加源文件名称字段。

功能特点：
- 🖼️ 专门处理图生文标注任务
- 📋 自动提取源图片文件名
- 🔧 处理caption字段中的转义字符（\n, \", \\等）
- 📂 智能文件名生成和导出
- 📊 详细的导出统计信息
- 🎯 支持单个项目和批量导出
- 📝 支持多种导出格式

使用方法：
```bash
cd label-studio-ml-backend/my_ml_backend
python auto_image_caption_exporter.py
```

作者: AI Assistant
创建时间: 2025-09-13
版本: 1.0.0
"""

import json
import time
import requests
import logging
import os
import re
from typing import List, Dict, Optional, Union
from pathlib import Path
from datetime import datetime

# ================================
# 用户配置区域 - 请根据实际情况修改
# ================================

# 导出文件夹配置
EXPORT_BASE_DIR = "outfile"  # 使用相对路径，导出到outfile文件夹

# Label Studio 配置
LABEL_STUDIO_URL = "http://localhost:8080"
LABEL_STUDIO_API_TOKEN = "02be98ff6805d4d3c86f6b51bb0d538acb4c96e5"
REQUEST_TIMEOUT = 61
DELAY_BETWEEN_REQUESTS = 0.5

# 导出选项
PRETTY_JSON = True  # 美化JSON输出
INCLUDE_METADATA = True  # 包含元数据
PROCESS_ESCAPE_CHARS = True  # 处理转义字符

# 日志配置
LOG_LEVEL = logging.INFO
SAVE_DETAILED_LOG = True

# ================================
# 程序代码
# ================================

def setup_logging():
    """设置日志配置"""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # 控制台日志处理器
    handlers = [logging.StreamHandler()]
    
    # 如果启用详细日志，添加文件处理器
    if SAVE_DETAILED_LOG:
        log_filename = f"auto_image_caption_exporter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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


class AutoImageCaptionExporter:
    """图生文标注结果导出器类"""
    
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
            'processed_captions': 0,
            'extracted_filenames': 0,
            'errors': []
        }
        
        logger.info(f"🚀 图生文标注结果导出器已初始化")
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
        """获取所有项目信息"""
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
        """获取项目的所有任务 - 支持分页获取所有任务"""
        logger.info(f"📋 获取项目 {project_id} 的所有任务...")
        
        try:
            all_tasks = []
            page = 1
            per_page = 100  # 每页获取数量，与Label Studio默认值保持一致
            total_pages = None
            
            # 循环获取所有页面的任务
            while True:
                logger.debug(f"📄 获取第 {page} 页任务...")
                
                # 获取项目的任务（分页）
                params = {
                    'project': project_id,
                    'fields': 'all',
                    'page': page,
                    'page_size': per_page  # 明确设置每页大小
                }
                
                response = self.session.get(
                    f"{self.label_studio_url}/api/tasks/",
                    params=params,
                    timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                
                # 检查响应内容类型
                response_data = response.json()
                logger.debug(f"📥 第{page}页API响应类型: {type(response_data)}")
                
                # 处理不同的响应格式
                page_tasks = []
                if isinstance(response_data, dict):
                    # Label Studio分页API响应格式
                    if 'results' in response_data:
                        page_tasks = response_data['results']
                        # 获取总页数信息
                        if total_pages is None:
                            total_count = response_data.get('count', 0)
                            total_pages = (total_count + per_page - 1) // per_page  # 向上取整
                            logger.info(f"📊 项目 {project_id} 总任务数: {total_count}, 总页数: {total_pages}")
                        
                        logger.debug(f"📄 第{page}页获取到 {len(page_tasks)} 个任务")
                    # 兼容旧格式
                    elif 'tasks' in response_data:
                        page_tasks = response_data['tasks']
                        logger.debug(f"📄 第{page}页获取到 {len(page_tasks)} 个任务（旧格式）")
                    else:
                        logger.error(f"❌ 第{page}页字典响应中没有找到'results'或'tasks'字段: {list(response_data.keys())}")
                        break
                elif isinstance(response_data, list):
                    # 直接返回任务列表（可能是非分页的旧版本API）
                    page_tasks = response_data
                    logger.info(f"📄 获取到任务列表（非分页格式）: {len(page_tasks)} 个任务")
                    all_tasks.extend(page_tasks)
                    break  # 非分页格式，直接跳出循环
                else:
                    logger.error(f"❌ 第{page}页未知的API响应格式: {type(response_data)}")
                    break
                
                # 添加本页任务到总列表
                if page_tasks:
                    all_tasks.extend(page_tasks)
                    logger.debug(f"📄 第{page}页添加 {len(page_tasks)} 个任务，累计: {len(all_tasks)} 个")
                else:
                    logger.info(f"📄 第{page}页没有更多任务，停止分页获取")
                    break
                
                # 检查是否还有更多页面
                if len(page_tasks) < per_page:
                    # 当前页的任务数少于每页大小，说明这是最后一页
                    logger.info(f"📄 第{page}页是最后一页（{len(page_tasks)} < {per_page}）")
                    break
                
                # 如果有总页数信息，检查是否已获取完所有页面
                if total_pages and page >= total_pages:
                    logger.info(f"📄 已获取所有 {total_pages} 页")
                    break
                
                page += 1
                
                # 安全检查：防止无限循环
                if page > 1000:  # 假设最多1000页
                    logger.warning(f"⚠️ 达到最大页数限制 {page}，停止获取")
                    break
                
                # 页面间稍微延迟，避免API请求过于频繁
                time.sleep(0.1)
            
            logger.info(f"📊 项目 {project_id} 分页获取完成: 共 {len(all_tasks)} 个任务（{page} 页）")
            
            # 验证任务格式
            if not all_tasks:
                logger.info("📋 项目中没有任务")
                return []
            
            # 检查第一个任务的格式
            first_task = all_tasks[0]
            logger.debug(f"🔍 第一个任务结构: {list(first_task.keys()) if isinstance(first_task, dict) else type(first_task)}")
            
            return all_tasks
            
        except Exception as e:
            logger.error(f"❌ 获取项目 {project_id} 任务异常: {e}")
            return None
    
    def extract_source_filename(self, task_data: Dict) -> str:
        """
        从任务数据中提取源图片文件名
        
        Args:
            task_data: 任务数据字典
            
        Returns:
            源图片文件名，如果未找到则返回"未知"
        """
        logger.debug(f"🔍 分析任务数据结构: {list(task_data.keys()) if task_data else '空数据'}")
        
        # 图生文任务常见的字段名
        image_fields = [
            'captioning',  # 您的模板中使用的字段
            'image', 'img', 'photo', 'picture', 'url',
            'image_url', 'file_url', 'file_path', 'filepath',
            'filename', 'file_name', 'source_file'
        ]
        
        # 检查直接的图片字段
        for field in image_fields:
            if field in task_data and task_data[field]:
                file_path = str(task_data[field])
                logger.debug(f"✅ 从字段 '{field}' 找到文件路径: {file_path}")
                
                # 提取文件名
                filename = self._extract_filename_from_path(file_path)
                if filename != "未知":
                    self.stats['extracted_filenames'] += 1
                    return filename
        
        # 如果都找不到，返回未知
        logger.debug(f"⚠️ 未找到图片文件名，任务数据: {str(task_data)[:200]}...")
        return "未知"
    
    def _extract_filename_from_path(self, file_path: str) -> str:
        """从文件路径中提取文件名，并去掉随机数前缀"""
        if not file_path:
            return "未知"
        
        # 移除URL参数
        if '?' in file_path:
            file_path = file_path.split('?')[0]
        
        # 提取文件名
        if '/' in file_path:
            filename = file_path.split('/')[-1]
        elif '\\' in file_path:
            filename = file_path.split('\\')[-1]
        else:
            filename = file_path
        
        # 如果文件名为空或只有扩展名，返回完整路径的最后部分
        if not filename or filename.startswith('.'):
            return file_path
        
        # 去掉随机数前缀：如果文件名包含"-"，从第一个"-"后面开始取
        # 例如: "195022b1-PIC_000045.jpg" -> "PIC_000045.jpg"
        if '-' in filename:
            # 找到第一个"-"的位置，取后面的部分作为真正的源文件名
            dash_index = filename.find('-')
            if dash_index >= 0 and dash_index < len(filename) - 1:
                clean_filename = filename[dash_index + 1:]
                logger.debug(f"🧹 去掉随机数前缀: {filename} -> {clean_filename}")
                return clean_filename
        
        return filename
    
    def process_escape_characters(self, text: str) -> str:
        """
        处理caption字段中的转义字符
        
        Args:
            text: 包含转义字符的文本
            
        Returns:
            处理后的正常文本
        """
        if not text or not isinstance(text, str):
            return text
        
        try:
            # 处理常见的转义字符
            processed_text = text
            
            # 处理换行符
            processed_text = processed_text.replace('\\n', '\n')
            
            # 处理引号
            processed_text = processed_text.replace('\\"', '"')
            
            # 处理反斜杠
            processed_text = processed_text.replace('\\\\', '\\')
            
            # 处理制表符
            processed_text = processed_text.replace('\\t', '\t')
            
            # 处理回车符
            processed_text = processed_text.replace('\\r', '\r')
            
            logger.debug(f"🔧 处理转义字符: {len(text)} -> {len(processed_text)} 字符")
            self.stats['processed_captions'] += 1
            
            return processed_text
            
        except Exception as e:
            logger.warning(f"⚠️ 处理转义字符失败: {e}")
            return text
    
    def format_image_caption_data(self, project: Dict, tasks: List[Dict]) -> List[Dict]:
        """
        格式化图生文标注数据
        
        Args:
            project: 项目信息
            tasks: 任务列表
            
        Returns:
            格式化后的图生文标注数据数组
        """
        formatted_tasks = []
        
        for task in tasks:
            # 获取标注信息
            annotations = task.get('annotations', [])
            # 过滤掉已取消的标注
            valid_annotations = [ann for ann in annotations if not ann.get('was_cancelled', False)]
            
            if not valid_annotations:
                continue
            
            for annotation in valid_annotations:
                # 提取任务数据
                task_data = task.get('data', {})
                
                # 提取源图片文件名
                source_filename = self.extract_source_filename(task_data)
                
                # 提取图片路径（captioning字段）
                captioning_path = task_data.get('captioning', '')
                
                # 提取caption内容
                caption_text = ""
                for result_item in annotation.get('result', []):
                    if result_item.get('type') == 'textarea':
                        value = result_item.get('value', {})
                        text_list = value.get('text', [])
                        if text_list:
                            caption_text = text_list[0] if isinstance(text_list, list) else str(text_list)
                            break
                
                # 处理caption中的转义字符
                if PROCESS_ESCAPE_CHARS and caption_text:
                    caption_text = self.process_escape_characters(caption_text)
                
                # 构建格式化的任务数据
                formatted_task = {
                    'captioning': captioning_path,
                    'id': task.get('id'),
                    'caption': caption_text,
                    'source_filename': source_filename,  # 添加源文件名字段
                    'annotator': annotation.get('created_by'),
                    'annotation_id': annotation.get('id'),
                    'created_at': annotation.get('created_at'),
                    'updated_at': annotation.get('updated_at'),
                    'lead_time': annotation.get('lead_time')
                }
                
                # 包含元数据
                if INCLUDE_METADATA:
                    formatted_task['metadata'] = {
                        'project_id': project.get('id'),
                        'project_title': project.get('title'),
                        'was_cancelled': annotation.get('was_cancelled', False),
                        'ground_truth': annotation.get('ground_truth', False),
                        'unique_id': annotation.get('unique_id'),
                        'import_id': annotation.get('import_id')
                    }
                
                formatted_tasks.append(formatted_task)
        
        # 更新统计信息
        self.stats['total_tasks'] += len(tasks)
        self.stats['total_annotations'] += len(formatted_tasks)
        
        return formatted_tasks
    
    def export_project(self, project_id: int, output_file: Optional[str] = None) -> Optional[List[Dict]]:
        """
        导出单个项目的图生文标注结果
        
        Args:
            project_id: 项目ID
            output_file: 输出文件路径，如果为None则使用项目名称生成文件名
            
        Returns:
            导出的数据，如果失败返回None
        """
        try:
            logger.info(f"🔄 开始导出项目 {project_id} 的图生文标注结果...")
            
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
            
            # 格式化图生文数据
            export_data = self.format_image_caption_data(project, tasks)
            
            if not export_data:
                logger.warning(f"⚠️ 项目 {project_id} 没有有效的图生文标注数据")
                return []
            
            logger.info(f"✅ 项目 {project_id} 共有 {len(export_data)} 条有效的图生文标注")
            
            # 生成输出文件名
            if output_file is None:
                # 清理项目名称，移除非法字符
                safe_title = "".join(c for c in project_title if c.isalnum() or c in (' ', '-', '_', '（', '）', '(', ')')).rstrip()
                safe_title = safe_title.replace(' ', '_').replace('（', '(').replace('）', ')')
                
                # 如果清理后的标题为空，则使用项目ID作为后备
                if not safe_title:
                    safe_title = f"project_{project_id}"
                
                # 生成时间戳
                timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
                
                # 构造文件名，使用项目名称和时间戳
                output_file = f"{safe_title}-{timestamp}-{hash(str(export_data))%1000000:06x}.json"
            
            # 保存到文件
            output_path = self.output_dir / output_file
            with open(output_path, 'w', encoding='utf-8') as f:
                if PRETTY_JSON:
                    json.dump(export_data, f, ensure_ascii=False, indent=4)
                else:
                    json.dump(export_data, f, ensure_ascii=False)
            
            logger.info(f"💾 项目 {project_id} 图生文标注结果已保存到: {output_path}")
            
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
        批量导出项目的图生文标注结果
        
        Args:
            start_id: 开始项目ID
            end_id: 结束项目ID
            
        Returns:
            批量导出结果统计
        """
        logger.info(f"🔄 开始批量导出项目 {start_id} 到 {end_id} 的图生文标注结果...")
        
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
                if result is not None:
                    batch_stats['successful_exports'] += 1
                    
                    # 生成文件名用于记录（需要获取项目名称）
                    try:
                        project_response = self.session.get(
                            f"{self.label_studio_url}/api/projects/{project_id}/",
                            timeout=REQUEST_TIMEOUT
                        )
                        if project_response.status_code == 200:
                            project_info = project_response.json()
                            project_title = project_info.get('title', f'project_{project_id}')
                            # 清理项目名称
                            safe_title = "".join(c for c in project_title if c.isalnum() or c in (' ', '-', '_', '（', '）', '(', ')')).rstrip()
                            safe_title = safe_title.replace(' ', '_').replace('（', '(').replace('）', ')')
                            if not safe_title:
                                safe_title = f"project_{project_id}"
                        else:
                            safe_title = f"project_{project_id}"
                    except:
                        safe_title = f"project_{project_id}"
                    
                    timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
                    filename = f"{safe_title}-{timestamp}-{hash(str(result))%1000000:06x}.json"
                    
                    batch_stats['exported_files'].append({
                        'project_id': project_id,
                        'filename': filename,
                        'annotation_count': len(result) if isinstance(result, list) else 0
                    })
                    
                    logger.info(f"✅ 项目 {project_id} 导出成功 ({len(result) if isinstance(result, list) else 0} 条标注)")
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
            if project_id < end_id:
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # 打印批量导出总结
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 批量图生文导出完成总结")
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
                logger.info(f"  - 项目 {file_info['project_id']}: {file_info['filename']} ({file_info['annotation_count']} 条标注)")
        
        logger.info(f"{'='*60}")
        
        return batch_stats
    
    def print_statistics(self):
        """打印导出统计信息"""
        print(f"\n{'='*60}")
        print(f"📊 图生文标注导出统计信息")
        print(f"{'='*60}")
        print(f"📋 总项目数: {self.stats['total_projects']}")
        print(f"✅ 导出成功: {self.stats['exported_projects']}")
        print(f"❌ 导出失败: {self.stats['total_projects'] - self.stats['exported_projects']}")
        print(f"📝 总任务数: {self.stats['total_tasks']}")
        print(f"🏷️ 总标注数: {self.stats['total_annotations']}")
        print(f"🔧 处理转义字符: {self.stats['processed_captions']} 个caption")
        print(f"📁 提取文件名: {self.stats['extracted_filenames']} 个文件")
        
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
    print("🖼️ Label Studio 图生文标注结果导出器")
    print("=" * 60)
    
    # 创建导出器实例
    exporter = AutoImageCaptionExporter()
    
    # 测试连接
    if not exporter.test_connection():
        logger.error("❌ 无法连接到Label Studio，请检查配置")
        return
    
    # 交互式菜单
    while True:
        print(f"\n{'-'*50}")
        print("📋 选择操作:")
        print("1. 导出单个项目的图生文标注")
        print("2. 批量导出项目的图生文标注")
        print("3. 查看项目列表")
        print("4. 退出")
        print(f"{'-'*50}")
        
        choice = input("请选择操作 (1-4): ").strip()
        
        if choice == "1":
            # 导出单个项目
            try:
                project_id = int(input("请输入项目ID: ").strip())
                result = exporter.export_project(project_id)
                if result is not None:
                    print(f"✅ 项目 {project_id} 导出成功，共 {len(result)} 条图生文标注")
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
                print(f"\n📋 即将批量导出 {project_count} 个项目的图生文标注 (ID: {start_id} - {end_id})")
                confirm = input("确认执行批量导出？(y/n): ").strip().lower()
                
                if confirm in ['y', 'yes', '是', '确认']:
                    batch_result = exporter.batch_export_projects(start_id, end_id)
                    print(f"\n🎉 批量导出完成！")
                    print(f"✅ 成功: {batch_result['successful_exports']}/{batch_result['total_projects']}")
                    print(f"❌ 失败: {batch_result['failed_exports']}/{batch_result['total_projects']}")
                    
                    if batch_result['exported_files']:
                        print(f"\n📁 导出的文件:")
                        for file_info in batch_result['exported_files']:
                            print(f"  - {file_info['filename']} ({file_info['annotation_count']} 条标注)")
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
            print("👋 感谢使用图生文标注结果导出器")
            break
        
        else:
            print("❌ 无效选择，请输入 1-4")
    
    # 显示最终统计
    exporter.print_statistics()


if __name__ == "__main__":
    main()

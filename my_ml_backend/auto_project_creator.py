#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Label Studio 项目自动创建器

功能：
1. 扫描inputfile文件夹下的所有txt文件
2. 根据每个文件名创建对应的Label Studio项目
3. 配置项目使用文本命名实体提取标签
4. 导入对应的文档到项目中
5. 返回每个项目的编号

使用方法：
```bash
cd label-studio-ml-backend/my_ml_backend
python auto_project_creator.py
```

作者: AI Assistant
创建时间: 2025-01-28
版本: 1.0.0
"""

import os
import json
import requests
import logging
import time
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# ================================
# 用户配置区域
# ================================

# Label Studio 配置
LABEL_STUDIO_URL = "http://localhost:8080"
LABEL_STUDIO_API_TOKEN = "02be98ff6805d4d3c86f6b51bb0d538acb4c96e5"

# ML Backend 配置
ML_BACKEND_URL = "http://localhost:9090"
ML_BACKEND_TITLE = "自动标注后端"
ML_BACKEND_DESCRIPTION = "用于文本命名实体识别的自动标注后端"
ML_BACKEND_TIMEOUT = 30  # ML Backend 连接超时时间
REUSE_EXISTING_BACKEND = True  # 是否重复使用已存在的ML Backend

# 文件路径配置
INPUT_FILE_DIR = "inputfile"  # 相对于当前目录的inputfile文件夹
LABEL_CONFIG_FILE = "文本命名实体提取标签.md"  # 标签配置文件

# 项目配置
PROJECT_DESCRIPTION_TEMPLATE = "基于{filename}的文本命名实体提取项目，自动创建于{date}"
DELAY_BETWEEN_REQUESTS = 0.5  # 请求间延迟，避免对服务器造成压力

# ================================
# 日志配置
# ================================

def setup_logging():
    """设置日志配置"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"project_creator_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    print(f"📁 详细日志将保存到: {log_file.absolute()}")

setup_logging()
logger = logging.getLogger(__name__)


class ProjectAutoCreator:
    """项目自动创建器"""
    
    def __init__(self):
        """初始化创建器"""
        self.label_studio_url = LABEL_STUDIO_URL.rstrip('/')
        self.ml_backend_url = ML_BACKEND_URL.rstrip('/')
        self.api_token = LABEL_STUDIO_API_TOKEN
        self.ml_backend_title = ML_BACKEND_TITLE
        self.ml_backend_description = ML_BACKEND_DESCRIPTION
        self.ml_backend_timeout = ML_BACKEND_TIMEOUT
        self.reuse_existing_backend = REUSE_EXISTING_BACKEND
        
        # 验证配置
        self._validate_config()
        
        # 创建HTTP会话
        self.session = requests.Session()
        if self.api_token and self.api_token != "your_api_token_here":
            self.session.headers.update({
                'Authorization': f'Token {self.api_token}',
                'Content-Type': 'application/json'
            })
        
        # 读取标签配置
        self.label_config = self._load_label_config()
        
        # 统计信息
        self.stats = {
            'total_files': 0,
            'created_projects': 0,
            'failed_projects': 0,
            'imported_documents': 0,
            'failed_imports': 0,
            'imported_tasks': 0,  # 新增：导入的任务总数
            'project_list': [],
            'errors': []
        }
        
        logger.info("✅ 项目自动创建器初始化完成")
        self._display_configuration()
    
    def _display_configuration(self):
        """显示配置信息"""
        logger.info("\n" + "="*60)
        logger.info("⚙️ 项目自动创建器配置")
        logger.info("="*60)
        logger.info(f"📡 Label Studio: {self.label_studio_url}")
        logger.info(f"🤖 ML Backend: {self.ml_backend_url}")
        logger.info(f"   • 标题: {self.ml_backend_title}")
        logger.info(f"   • 描述: {self.ml_backend_description}")
        logger.info(f"   • 连接超时: {self.ml_backend_timeout}秒")
        logger.info(f"   • 重用现有: {'是' if self.reuse_existing_backend else '否'}")
        logger.info(f"📁 输入文件夹: {INPUT_FILE_DIR}")
        logger.info(f"🏷️ 标签配置: {LABEL_CONFIG_FILE}")
        logger.info(f"⏱️ 请求延迟: {DELAY_BETWEEN_REQUESTS}秒")
        logger.info("="*60)
    
    def _validate_config(self):
        """验证配置"""
        errors = []
        
        if not self.label_studio_url:
            errors.append("Label Studio URL不能为空")
        
        if not self.api_token or self.api_token == "your_api_token_here":
            errors.append("请设置有效的API令牌")
        
        if not os.path.exists(INPUT_FILE_DIR):
            errors.append(f"输入文件目录不存在: {INPUT_FILE_DIR}")
        
        if not os.path.exists(LABEL_CONFIG_FILE):
            errors.append(f"标签配置文件不存在: {LABEL_CONFIG_FILE}")
        
        if errors:
            logger.error("❌ 配置验证失败:")
            for error in errors:
                logger.error(f"   • {error}")
            raise ValueError("配置验证失败")
    
    def _load_label_config(self) -> str:
        """加载标签配置"""
        try:
            with open(LABEL_CONFIG_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取XML配置部分
            start_marker = '<View>'
            end_marker = '</View>'
            
            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker) + len(end_marker)
            
            if start_idx == -1 or end_idx == -1:
                raise ValueError("无法找到有效的标签配置")
            
            config = content[start_idx:end_idx]
            logger.info("✅ 标签配置加载成功")
            return config
            
        except Exception as e:
            logger.error(f"❌ 加载标签配置失败: {e}")
            raise
    
    def _clean_text_content(self, text: str) -> str:
        """清理文本内容，删除空行"""
        lines = text.split('\n')
        # 删除空行和只包含空白字符的行
        cleaned_lines = [line for line in lines if line.strip()]
        return '\n'.join(cleaned_lines)
    
    def _split_paragraph_into_sentences(self, paragraph: str) -> List[str]:
        """将段落按句子分割
        
        Args:
            paragraph: 待分割的段落
            
        Returns:
            句子列表
        """
        # 定义句子分割符（中英文句号、问号、感叹号）
        sentence_endings = r'[。！？.!?]+'
        
        # 使用正则表达式分割句子，保留分割符
        sentences = re.split(f'({sentence_endings})', paragraph)
        
        # 重新组合句子和标点
        result_sentences = []
        temp_sentence = ""
        
        for part in sentences:
            if not part.strip():
                continue
                
            temp_sentence += part
            
            # 如果遇到句子结尾标点，结束当前句子
            if re.match(sentence_endings, part):
                if temp_sentence.strip():
                    result_sentences.append(temp_sentence.strip())
                    temp_sentence = ""
        
        # 添加最后一个句子（如果没有结尾标点）
        if temp_sentence.strip():
            result_sentences.append(temp_sentence.strip())
        
        # 过滤掉空句子
        return [s for s in result_sentences if s.strip()]
    
    def _combine_sentences_into_chunks(self, sentences: List[str], max_length: int = 300) -> List[str]:
        """将句子组合成不超过指定长度的文本块
        
        Args:
            sentences: 句子列表
            max_length: 每个文本块的最大长度
            
        Returns:
            文本块列表
        """
        if not sentences:
            return []
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # 如果单个句子就超过最大长度，单独作为一个块
            if len(sentence) > max_length:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                chunks.append(sentence)
                continue
            
            # 检查加入当前句子后是否超长
            test_chunk = current_chunk + sentence if not current_chunk else current_chunk + sentence
            
            if len(test_chunk) <= max_length:
                # 不超长，加入当前块
                current_chunk = test_chunk
            else:
                # 超长了，保存当前块并开始新块
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        # 添加最后一个块
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _process_long_paragraph(self, paragraph: str, max_paragraph_length: int = 500, max_chunk_length: int = 300) -> List[str]:
        """处理超长段落，按句子分割并重新组合
        
        Args:
            paragraph: 待处理的段落
            max_paragraph_length: 段落最大长度，超过此长度会进行分割
            max_chunk_length: 分割后每块的最大长度
            
        Returns:
            处理后的文本块列表
        """
        if len(paragraph) <= max_paragraph_length:
            # 段落长度在范围内，直接返回
            return [paragraph]
        
        logger.info(f"📏 处理超长段落: {len(paragraph)} 字符 -> 分割为多个块（每块≤{max_chunk_length}字符）")
        
        # 按句子分割
        sentences = self._split_paragraph_into_sentences(paragraph)
        
        if not sentences:
            return [paragraph]  # 如果分割失败，返回原段落
        
        logger.info(f"   🔍 分割为 {len(sentences)} 个句子")
        
        # 重新组合句子
        chunks = self._combine_sentences_into_chunks(sentences, max_chunk_length)
        
        logger.info(f"   📦 组合为 {len(chunks)} 个文本块")
        for i, chunk in enumerate(chunks):
            logger.info(f"      块{i+1}: {len(chunk)} 字符 - {chunk[:50]}{'...' if len(chunk) > 50 else ''}")
        
        return chunks
    
    def _split_text_into_paragraphs(self, text: str) -> List[str]:
        """将文本按自然段分割成段落列表，自动处理超长段落"""
        # 先按双换行符分割（标准段落分隔）
        paragraphs = text.split('\n\n')
        
        # 如果双换行符分割后只有一个段落，说明没有空行分隔
        # 则按单行进行分割（适合每行都是独立内容的文件）
        if len(paragraphs) == 1:
            lines = text.split('\n')
            paragraphs = []
            
            for line in lines:
                line = line.strip()
                if line:  # 非空行作为独立段落
                    paragraphs.append(line)
        else:
            # 如果有双换行符分割，进一步处理每个段落
            cleaned_paragraphs = []
            for para in paragraphs:
                para = para.strip()
                if para:
                    cleaned_paragraphs.append(para)
            paragraphs = cleaned_paragraphs
        
        # 新增：处理超长段落
        final_paragraphs = []
        long_paragraph_count = 0
        
        for paragraph in paragraphs:
            if len(paragraph) > 500:  # 超过500字符的段落需要分割
                long_paragraph_count += 1
                logger.info(f"🔍 发现超长段落 #{long_paragraph_count}: {len(paragraph)} 字符")
                
                # 使用智能分割处理超长段落
                chunks = self._process_long_paragraph(paragraph, max_paragraph_length=500, max_chunk_length=300)
                final_paragraphs.extend(chunks)
            else:
                final_paragraphs.append(paragraph)
        
        if long_paragraph_count > 0:
            original_count = len(paragraphs)
            final_count = len(final_paragraphs)
            logger.info(f"📊 超长段落处理完成:")
            logger.info(f"   原始段落数: {original_count}")
            logger.info(f"   处理后段落数: {final_count}")
            logger.info(f"   增加段落数: {final_count - original_count}")
        
        return final_paragraphs
    
    def scan_input_files(self, max_files=0) -> List[Tuple[str, str]]:
        """扫描输入文件夹，返回(文件路径, 文件名)列表
        
        Args:
            max_files (int): 最大文件数量，0表示无限制
        """
        logger.info(f"🔍 扫描输入文件夹: {INPUT_FILE_DIR}")
        
        file_list = []
        input_path = Path(INPUT_FILE_DIR)
        
        # 递归扫描所有txt文件
        for txt_file in input_path.rglob("*.txt"):
            relative_path = txt_file.relative_to(input_path)
            # 使用相对路径作为项目名称，替换路径分隔符为下划线
            project_name = str(relative_path).replace('\\', '_').replace('/', '_').replace('.txt', '')
            
            # 限制项目名称长度不超过50个字符
            if len(project_name) > 50:
                project_name = project_name[:49]  # 保留前49个字符
                logger.info(f"📏 项目名称过长，已截断: {project_name}...")
            
            file_list.append((str(txt_file), project_name))
        
        # 应用文件数量限制
        total_found = len(file_list)
        if max_files > 0 and len(file_list) > max_files:
            file_list = file_list[:max_files]
            logger.warning(f"⚠️ 文件数量限制: 找到 {total_found} 个文件，仅处理前 {max_files} 个")
        
        self.stats['total_files'] = len(file_list)
        logger.info(f"📂 将处理 {len(file_list)} 个txt文件")
        
        # 显示前10个文件作为示例
        for i, (filepath, name) in enumerate(file_list[:10]):
            logger.info(f"   {i+1}. {name} -> {filepath}")
        
        if len(file_list) > 10:
            logger.info(f"   ... 还有 {len(file_list) - 10} 个文件")
        
        return file_list
    
    def create_project(self, project_name: str, file_path: str) -> Optional[int]:
        """创建Label Studio项目"""
        logger.info(f"🏗️ 创建项目: {project_name}")
        
        try:
            # 准备项目数据
            project_data = {
                "title": project_name,
                "description": PROJECT_DESCRIPTION_TEMPLATE.format(
                    filename=os.path.basename(file_path),
                    date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
                "label_config": self.label_config,
                "show_instruction": True,
                "show_skip_button": False,
                "enable_empty_annotation": False
            }
            
            # 发送创建请求
            response = self.session.post(
                f"{self.label_studio_url}/api/projects/",
                json=project_data,
                timeout=30
            )
            
            response.raise_for_status()
            project_info = response.json()
            project_id = project_info['id']
            
            logger.info(f"✅ 项目创建成功，ID: {project_id}")
            
            # 配置ML Backend
            self._configure_ml_backend(project_id)
            
            self.stats['created_projects'] += 1
            self.stats['project_list'].append({
                'name': project_name,
                'id': project_id,
                'file_path': file_path,
                'status': 'created'
            })
            
            return project_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 创建项目失败: {e}")
            self.stats['failed_projects'] += 1
            self.stats['errors'].append(f"创建项目 {project_name} 失败: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ 创建项目时发生未知错误: {e}")
            self.stats['failed_projects'] += 1
            self.stats['errors'].append(f"创建项目 {project_name} 时发生未知错误: {e}")
            return None
    
    def _find_existing_ml_backend(self, project_id: int) -> Optional[int]:
        """查找已存在的ML Backend（针对特定项目）"""
        try:
            response = self.session.get(
                f"{self.label_studio_url}/api/ml",
                timeout=self.ml_backend_timeout
            )
            
            if response.status_code == 200:
                backends = response.json()
                for backend in backends:
                    # 检查URL匹配且连接到指定项目
                    if (backend.get('url') == self.ml_backend_url and 
                        backend.get('project') == project_id):
                        logger.info(f"🔍 找到已存在的ML Backend（项目 {project_id}），ID: {backend['id']}")
                        return backend['id']
                
                # 如果没有找到项目特定的backend，查找通用的
                for backend in backends:
                    if backend.get('url') == self.ml_backend_url and not backend.get('project'):
                        logger.info(f"🔍 找到通用ML Backend，ID: {backend['id']}")
                        return backend['id']
            
            return None
            
        except Exception as e:
            logger.warning(f"⚠️ 查找ML Backend时出错: {e}")
            return None
    
    def _create_ml_backend(self, project_id: int) -> Optional[int]:
        """为指定项目创建新的ML Backend"""
        try:
            ml_backend_data = {
                "url": self.ml_backend_url,
                "title": self.ml_backend_title,
                "description": self.ml_backend_description,
                "project": project_id  # 新版本Label Studio要求的字段
            }
            
            logger.info(f"🔧 为项目 {project_id} 创建ML Backend: {self.ml_backend_url}")
            response = self.session.post(
                f"{self.label_studio_url}/api/ml",
                json=ml_backend_data,
                timeout=self.ml_backend_timeout
            )
            
            if response.status_code in [200, 201]:
                ml_backend_info = response.json()
                ml_backend_id = ml_backend_info.get('id')
                logger.info(f"✅ ML Backend创建成功，ID: {ml_backend_id}")
                return ml_backend_id
            else:
                logger.error(f"❌ ML Backend创建失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 创建ML Backend时出错: {e}")
            return None
    
    def _connect_ml_backend_to_project(self, ml_backend_id: int, project_id: int) -> bool:
        """将ML Backend连接到项目"""
        try:
            connect_data = {
                "url": self.ml_backend_url,  # Label Studio API需要url参数进行健康检查
                "project": project_id
            }
            
            logger.info(f"🔗 连接ML Backend {ml_backend_id} 到项目 {project_id}")
            connect_response = self.session.patch(
                f"{self.label_studio_url}/api/ml/{ml_backend_id}",
                json=connect_data,
                timeout=self.ml_backend_timeout
            )
            
            if connect_response.status_code in [200, 201]:
                logger.info(f"✅ ML Backend连接到项目成功")
                return True
            else:
                logger.error(f"❌ ML Backend连接失败: {connect_response.status_code} - {connect_response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 连接ML Backend到项目时出错: {e}")
            return False
    
    def _configure_ml_backend(self, project_id: int):
        """为项目配置ML Backend"""
        logger.info(f"⚙️ 为项目 {project_id} 配置ML Backend...")
        
        # 获取ML Backend ID
        ml_backend_id = None
        
        if self.reuse_existing_backend:
            # 尝试找到已存在的ML Backend
            ml_backend_id = self._find_existing_ml_backend(project_id)
        
        if ml_backend_id is None:
            # 创建新的ML Backend
            ml_backend_id = self._create_ml_backend(project_id)
        
        if ml_backend_id is not None:
            # 检查是否需要连接到项目（如果backend是新创建的且带project字段，则已经连接）
            # 或者是通用backend需要连接
            if self.reuse_existing_backend:
                # 如果重用现有backend，可能需要连接到项目
                success = self._connect_ml_backend_to_project(ml_backend_id, project_id)
                if success:
                    logger.info(f"🎉 项目 {project_id} 的ML Backend配置完成")
                else:
                    logger.warning(f"⚠️ 项目 {project_id} 的ML Backend连接失败")
            else:
                # 新创建的backend已经连接到项目
                logger.info(f"🎉 项目 {project_id} 的ML Backend配置完成")
        else:
            logger.warning(f"⚠️ 无法为项目 {project_id} 配置ML Backend")
    
    def import_document(self, project_id: int, file_path: str) -> Tuple[bool, int]:
        """导入文档到项目，按段落分割为多个任务
        
        Returns:
            Tuple[bool, int]: (是否成功, 创建的任务数)
        """
        filename = os.path.basename(file_path)
        logger.info(f"📥 导入文档: {filename} -> 项目 {project_id}")
        
        try:
            # 读取文档内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                logger.warning(f"⚠️ 文件内容为空: {file_path}")
                return False, 0
            
            # 按段落分割文本
            paragraphs = self._split_text_into_paragraphs(content)
            
            if not paragraphs:
                logger.warning(f"⚠️ 未找到有效段落: {file_path}")
                return False, 0
            
            logger.info(f"📄 发现 {len(paragraphs)} 个段落，将创建 {len(paragraphs)} 个任务")
            
            # 为每个段落创建任务数据
            task_list = []
            for i, paragraph in enumerate(paragraphs, 1):
                task_data = {
                    "data": {
                        "text": paragraph,
                        "source_file": filename,  # 记录来源文件
                        "paragraph_index": i,     # 段落序号
                        "total_paragraphs": len(paragraphs)  # 总段落数
                    }
                }
                task_list.append(task_data)
            
            # 批量导入任务
            logger.info(f"🔄 批量导入 {len(task_list)} 个任务...")
            response = self.session.post(
                f"{self.label_studio_url}/api/projects/{project_id}/import",
                json=task_list,
                timeout=120  # 增加超时时间，因为可能有很多任务
            )
            
            response.raise_for_status()
            result = response.json()
            
            task_count = result.get('task_count', 0)
            if task_count > 0:
                logger.info(f"✅ 文档导入成功！")
                logger.info(f"   📊 创建任务数: {task_count}")
                logger.info(f"   📝 来源段落: {len(paragraphs)}")
                logger.info(f"   📁 源文件: {filename}")
                self.stats['imported_documents'] += 1
                # 新增：记录导入的任务数
                if 'imported_tasks' not in self.stats:
                    self.stats['imported_tasks'] = 0
                self.stats['imported_tasks'] += task_count
                return True, task_count
            else:
                logger.error(f"❌ 文档导入失败，无任务创建")
                self.stats['failed_imports'] += 1
                return False, 0
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 导入文档失败: {e}")
            self.stats['failed_imports'] += 1
            self.stats['errors'].append(f"导入文档 {file_path} 失败: {e}")
            return False, 0
        except Exception as e:
            logger.error(f"❌ 导入文档时发生未知错误: {e}")
            self.stats['failed_imports'] += 1
            self.stats['errors'].append(f"导入文档 {file_path} 时发生未知错误: {e}")
            return False, 0
    
    def test_connection(self) -> bool:
        """测试Label Studio和ML Backend连接"""
        logger.info("🔍 测试服务连接...")
        
        # 测试Label Studio连接
        try:
            response = self.session.get(f"{self.label_studio_url}/api/projects/")
            response.raise_for_status()
            logger.info("✅ Label Studio连接成功")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Label Studio连接失败: {e}")
            return False
        
        # 测试ML Backend连接
        try:
            import requests
            response = requests.get(f"{self.ml_backend_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ ML Backend连接成功")
            else:
                logger.warning(f"⚠️ ML Backend健康检查失败，状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ ML Backend连接测试失败: {e}")
            logger.info("   注意: ML Backend连接失败不会阻止项目创建，但自动标注功能可能不可用")
        
        return True
    
    def run(self, max_projects=0) -> Dict:
        """执行完整的项目创建流程
        
        Args:
            max_projects (int): 最大创建项目数量，0表示无限制
        """
        logger.info("🚀 开始自动创建项目流程")
        start_time = datetime.now()
        
        # 测试连接
        if not self.test_connection():
            logger.error("❌ 连接测试失败，终止操作")
            return self.stats
        
        # 扫描文件
        file_list = self.scan_input_files(max_files=max_projects)
        if not file_list:
            logger.warning("⚠️ 未找到任何txt文件")
            return self.stats
        
        # 创建项目并导入文档
        logger.info(f"🏗️ 开始创建 {len(file_list)} 个项目...")
        
        for i, (file_path, project_name) in enumerate(file_list, 1):
            logger.info(f"\n📋 处理进度: {i}/{len(file_list)} - {project_name}")
            
            # 创建项目
            project_id = self.create_project(project_name, file_path)
            
            if project_id:
                # 导入文档
                success, task_count = self.import_document(project_id, file_path)
                
                # 更新项目状态
                for project in self.stats['project_list']:
                    if project['id'] == project_id:
                        project['status'] = 'imported' if success else 'import_failed'
                        if success:
                            project['task_count'] = task_count  # 记录任务数量
                        break
            
            # 延迟避免过快请求
            if i < len(file_list):
                time.sleep(DELAY_BETWEEN_REQUESTS)
        
        # 计算总用时
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 生成报告
        self._print_summary(duration)
        
        return self.stats
    
    def _print_summary(self, duration: float):
        """打印执行摘要"""
        logger.info("\n" + "="*60)
        logger.info("📊 项目创建完成摘要")
        logger.info("="*60)
        
        logger.info(f"⏱️  总用时: {duration:.1f}秒")
        logger.info(f"📁 扫描文件: {self.stats['total_files']}")
        logger.info(f"✅ 创建项目: {self.stats['created_projects']}")
        logger.info(f"❌ 创建失败: {self.stats['failed_projects']}")
        logger.info(f"📥 导入成功: {self.stats['imported_documents']}")
        logger.info(f"💥 导入失败: {self.stats['failed_imports']}")
        logger.info(f"📝 创建任务: {self.stats['imported_tasks']} 个（按段落分割）")
        
        if self.stats['project_list']:
            logger.info(f"\n🏷️ 创建的项目列表:")
            for project in self.stats['project_list']:
                status_emoji = "✅" if project['status'] == 'imported' else "⚠️" if project['status'] == 'import_failed' else "❌"
                task_info = f"({project.get('task_count', 0)} 个任务)" if project.get('task_count') else ""
                logger.info(f"   {status_emoji} [{project['id']:2d}] {project['name']} {task_info}")
        
        if self.stats['errors']:
            logger.info(f"\n⚠️ 错误详情:")
            for error in self.stats['errors'][:10]:  # 最多显示10个错误
                logger.info(f"   • {error}")
            if len(self.stats['errors']) > 10:
                logger.info(f"   ... 还有 {len(self.stats['errors']) - 10} 个错误")
        
        logger.info(f"\n🎯 成功率:")
        if self.stats['total_files'] > 0:
            project_success_rate = (self.stats['created_projects'] / self.stats['total_files']) * 100
            import_success_rate = (self.stats['imported_documents'] / self.stats['total_files']) * 100
            avg_tasks_per_file = self.stats['imported_tasks'] / self.stats['imported_documents'] if self.stats['imported_documents'] > 0 else 0
            logger.info(f"   项目创建成功率: {project_success_rate:.1f}%")
            logger.info(f"   文档导入成功率: {import_success_rate:.1f}%")
            logger.info(f"   平均每个文档任务数: {avg_tasks_per_file:.1f} 个")


def main(max_projects=0):
    """主函数
    
    Args:
        max_projects (int): 最大创建项目数量，0表示无限制
    """
    try:
        creator = ProjectAutoCreator()
        stats = creator.run(max_projects=max_projects)
        
        # 返回项目编号列表
        project_ids = [p['id'] for p in stats['project_list'] if p['status'] != 'failed']
        
        print(f"\n🎉 操作完成！创建了 {len(project_ids)} 个项目")
        print(f"📋 项目编号列表: {project_ids}")
        
        return project_ids
        
    except KeyboardInterrupt:
        logger.info("\n👋 用户中断操作")
    except Exception as e:
        logger.error(f"\n💥 程序执行失败: {e}")
        raise


if __name__ == "__main__":
    main()

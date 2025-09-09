#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Label Studio 标签配置自动更新器

此程序自动从"文本命名实体提取标签.md"文件中读取新的标签配置，
并批量更新Label Studio中指定项目的标签配置参数。

功能特点：N
- 🔄 批量更新：支持一次性更新多个项目的标签配置
- 📝 配置解析：自动解析Markdown文件中的Label Studio XML配置
- 💾 配置备份：更新前自动备份原有配置，支持回滚
- 🔍 配置验证：验证新配置的格式正确性
- 📊 实时进度：显示更新进度和统计信息
- 🔁 错误重试：支持失败项目的自动重试
- 📋 详细日志：记录更新过程和错误信息
- ⚙️ 灵活配置：用户可自定义参数

使用方法：
```bash
cd label-studio-ml-backend/my_ml_backend
python auto_config_updater.py
```

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
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
import xml.etree.ElementTree as ET

# ================================
# 用户配置区域 - 请根据实际情况修改
# ================================

# Label Studio 配置
LABEL_STUDIO_URL = "http://localhost:8080"          # Label Studio服务地址
LABEL_STUDIO_API_TOKEN = "02be98ff6805d4d3c86f6b51bb0d538acb4c96e5"     # 您的API令牌
PROJECT_IDS = list(range(693, 942, 1))             # 要更新的项目ID列表

# 配置文件路径
CONFIG_FILE_PATH = "文本命名实体提取标签.md"          # 新标签配置文件路径

# 更新配置
MAX_RETRIES = 3                                      # 失败项目的最大重试次数
REQUEST_TIMEOUT = 30                                 # 单个请求的超时时间（秒）
DELAY_BETWEEN_PROJECTS = 1.0                        # 项目间延迟时间（秒）
BACKUP_CONFIGS = True                                # 是否备份原有配置
VALIDATE_XML = True                                  # 是否验证XML格式

# 备份配置
BACKUP_DIR = "config_backups"                        # 备份目录
BACKUP_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"           # 备份时间戳格式

# ================================
# 程序实现部分
# ================================

class LabelStudioConfigUpdater:
    """Label Studio 配置更新器"""
    
    def __init__(self):
        """初始化更新器"""
        self.label_studio_url = LABEL_STUDIO_URL.rstrip('/')
        self.api_token = LABEL_STUDIO_API_TOKEN
        self.project_ids = PROJECT_IDS
        self.config_file_path = CONFIG_FILE_PATH
        
        # 统计信息
        self.stats = {
            'total_projects': len(self.project_ids),
            'successful_updates': 0,
            'failed_updates': 0,
            'skipped_projects': 0,
            'backup_count': 0,
            'start_time': None,
            'end_time': None
        }
        
        # 设置日志
        self._setup_logging()
        
        # 创建备份目录
        if BACKUP_CONFIGS:
            self.backup_dir = Path(BACKUP_DIR)
            self.backup_dir.mkdir(exist_ok=True)
            
        # 存储新配置
        self.new_config = None
        
    def _setup_logging(self):
        """设置日志记录"""
        # 创建logs目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 配置日志格式
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        
        # 配置文件日志
        log_filename = f"config_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_dir / log_filename, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
    def load_new_config(self) -> bool:
        """从Markdown文件加载新的标签配置"""
        try:
            # 首先尝试相对路径
            config_path = Path(self.config_file_path)
            
            # 如果相对路径不存在，尝试在脚本所在目录查找
            if not config_path.exists():
                script_dir = Path(__file__).parent
                config_path = script_dir / self.config_file_path
                
            if not config_path.exists():
                self.logger.error(f"❌ 配置文件不存在: {self.config_file_path}")
                self.logger.error(f"   已尝试路径: {Path(self.config_file_path).absolute()}")
                self.logger.error(f"   已尝试路径: {config_path.absolute()}")
                return False
                
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 提取XML配置部分
            # 查找<View>到</View>之间的内容
            xml_pattern = r'<View>.*?</View>'
            match = re.search(xml_pattern, content, re.DOTALL)
            
            if not match:
                self.logger.error("❌ 未在配置文件中找到有效的Label Studio XML配置")
                return False
                
            self.new_config = match.group(0)
            
            # 验证XML格式
            if VALIDATE_XML and not self._validate_xml_config(self.new_config):
                return False
                
            self.logger.info(f"✅ 成功加载新配置，包含 {self._count_labels(self.new_config)} 个标签")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 加载配置文件失败: {str(e)}")
            return False
            
    def _validate_xml_config(self, xml_config: str) -> bool:
        """验证XML配置格式"""
        try:
            ET.fromstring(xml_config)
            self.logger.info("✅ XML配置格式验证通过")
            return True
        except ET.ParseError as e:
            self.logger.error(f"❌ XML配置格式错误: {str(e)}")
            return False
            
    def _count_labels(self, xml_config: str) -> int:
        """统计配置中的标签数量"""
        try:
            root = ET.fromstring(xml_config)
            labels = root.findall('.//Label')
            return len(labels)
        except:
            return 0
            
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """发送HTTP请求"""
        headers = {
            'Authorization': f'Token {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                **kwargs
            )
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ 请求失败: {str(e)}")
            return None
            
    def get_project_info(self, project_id: int) -> Optional[Dict]:
        """获取项目信息"""
        url = f"{self.label_studio_url}/api/projects/{project_id}/"
        response = self._make_request('GET', url)
        
        if response and response.status_code == 200:
            return response.json()
        elif response and response.status_code == 404:
            self.logger.warning(f"⚠️ 项目 {project_id} 不存在")
            return None
        else:
            error_msg = f"获取项目 {project_id} 信息失败"
            if response:
                error_msg += f" (状态码: {response.status_code})"
            self.logger.error(f"❌ {error_msg}")
            return None
            
    def backup_project_config(self, project_id: int, project_info: Dict) -> bool:
        """备份项目配置"""
        if not BACKUP_CONFIGS:
            return True
            
        try:
            timestamp = datetime.now().strftime(BACKUP_TIMESTAMP_FORMAT)
            backup_filename = f"project_{project_id}_config_{timestamp}.json"
            backup_path = self.backup_dir / backup_filename
            
            # 准备备份数据
            backup_data = {
                'project_id': project_id,
                'backup_time': datetime.now().isoformat(),
                'project_title': project_info.get('title', ''),
                'original_config': project_info.get('label_config', ''),
                'project_info': project_info
            }
            
            # 保存备份
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
                
            self.stats['backup_count'] += 1
            self.logger.info(f"✅ 已备份项目 {project_id} 配置到: {backup_filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 备份项目 {project_id} 配置失败: {str(e)}")
            return False
            
    def update_project_config(self, project_id: int) -> bool:
        """更新单个项目的标签配置"""
        try:
            # 获取项目信息
            project_info = self.get_project_info(project_id)
            if not project_info:
                self.stats['skipped_projects'] += 1
                return False
                
            project_title = project_info.get('title', f'项目{project_id}')
            self.logger.info(f"🔄 开始更新项目 {project_id}: {project_title}")
            
            # 备份原有配置
            if not self.backup_project_config(project_id, project_info):
                self.logger.warning(f"⚠️ 项目 {project_id} 配置备份失败，但继续更新")
                
            # 准备更新数据
            update_data = {
                'label_config': self.new_config
            }
            
            # 发送更新请求
            url = f"{self.label_studio_url}/api/projects/{project_id}/"
            response = self._make_request('PATCH', url, json=update_data)
            
            if response and response.status_code == 200:
                self.logger.info(f"✅ 项目 {project_id} 配置更新成功")
                self.stats['successful_updates'] += 1
                return True
            else:
                error_msg = f"项目 {project_id} 配置更新失败"
                if response:
                    error_msg += f" (状态码: {response.status_code})"
                    try:
                        error_detail = response.json()
                        error_msg += f" - {error_detail}"
                    except:
                        pass
                self.logger.error(f"❌ {error_msg}")
                self.stats['failed_updates'] += 1
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 更新项目 {project_id} 时发生异常: {str(e)}")
            self.stats['failed_updates'] += 1
            return False
            
    def update_all_projects(self):
        """批量更新所有项目配置"""
        self.logger.info(f"🚀 开始批量更新 {len(self.project_ids)} 个项目的标签配置")
        self.stats['start_time'] = datetime.now()
        
        for i, project_id in enumerate(self.project_ids, 1):
            self.logger.info(f"\n📊 进度: {i}/{len(self.project_ids)} - 处理项目 {project_id}")
            
            # 更新项目配置（支持重试）
            success = False
            for attempt in range(MAX_RETRIES + 1):
                if attempt > 0:
                    self.logger.info(f"🔄 项目 {project_id} 第 {attempt} 次重试")
                    
                success = self.update_project_config(project_id)
                if success:
                    break
                    
                if attempt < MAX_RETRIES:
                    time.sleep(2)  # 重试前等待
                    
            if not success:
                self.logger.error(f"❌ 项目 {project_id} 在 {MAX_RETRIES + 1} 次尝试后仍然失败")
                
            # 项目间延迟
            if i < len(self.project_ids):
                time.sleep(DELAY_BETWEEN_PROJECTS)
                
        self.stats['end_time'] = datetime.now()
        
    def print_summary(self):
        """打印更新总结"""
        duration = self.stats['end_time'] - self.stats['start_time']
        
        print(f"\n" + "="*60)
        print(f"🎯 Label Studio 标签配置更新完成！")
        print(f"="*60)
        print(f"📊 统计信息:")
        print(f"   • 总项目数: {self.stats['total_projects']}")
        print(f"   • 成功更新: {self.stats['successful_updates']}")
        print(f"   • 更新失败: {self.stats['failed_updates']}")
        print(f"   • 跳过项目: {self.stats['skipped_projects']}")
        print(f"   • 配置备份: {self.stats['backup_count']}")
        print(f"   • 总用时: {duration}")
        
        success_rate = (self.stats['successful_updates'] / self.stats['total_projects']) * 100
        print(f"   • 成功率: {success_rate:.1f}%")
        
        if BACKUP_CONFIGS and self.stats['backup_count'] > 0:
            print(f"\n💾 配置备份:")
            print(f"   • 备份目录: {BACKUP_DIR}")
            print(f"   • 备份文件数: {self.stats['backup_count']}")
            
        print(f"="*60)
        
    def run(self):
        """运行配置更新器"""
        try:
            print(f"🌊 Label Studio 标签配置自动更新器")
            print(f"📋 配置文件: {self.config_file_path}")
            print(f"🎯 目标项目: {len(self.project_ids)} 个")
            print(f"🔗 Label Studio: {self.label_studio_url}")
            
            # 加载新配置
            if not self.load_new_config():
                return False
                
            # 确认继续
            print(f"\n⚠️ 即将更新 {len(self.project_ids)} 个项目的标签配置")
            print(f"   项目ID范围: {min(self.project_ids)} - {max(self.project_ids)}")
            if BACKUP_CONFIGS:
                print(f"   将自动备份原有配置到: {BACKUP_DIR}")
            
            response = input("\n是否继续？(y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("❌ 操作已取消")
                return False
                
            # 开始更新
            self.update_all_projects()
            
            # 打印总结
            self.print_summary()
            
            return self.stats['successful_updates'] > 0
            
        except KeyboardInterrupt:
            print(f"\n⚠️ 操作被用户中断")
            return False
        except Exception as e:
            self.logger.error(f"❌ 程序运行时发生异常: {str(e)}")
            return False


def main():
    """主函数"""
    try:
        updater = LabelStudioConfigUpdater()
        success = updater.run()
        
        if success:
            print(f"\n🎉 配置更新任务完成！")
            return 0
        else:
            print(f"\n❌ 配置更新任务失败！")
            return 1
            
    except Exception as e:
        print(f"❌ 程序启动失败: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())

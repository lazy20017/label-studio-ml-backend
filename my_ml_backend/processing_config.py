#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
处理配置管理
"""

import os
from typing import Dict, Any

class ProcessingConfig:
    """处理配置类"""
    
    def __init__(self):
        # 批量处理配置
        self.MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', '10'))
        self.MAX_PROCESSING_TIME = int(os.getenv('MAX_PROCESSING_TIME', '45'))
        self.CHUNK_PROCESSING_TIME = int(os.getenv('CHUNK_PROCESSING_TIME', '30'))
        
        # API配置
        self.API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
        self.API_RETRY_COUNT = int(os.getenv('API_RETRY_COUNT', '2'))
        self.API_RETRY_DELAY = float(os.getenv('API_RETRY_DELAY', '1.0'))
        
        # 性能配置
        self.ENABLE_PROGRESS_LOGGING = os.getenv('ENABLE_PROGRESS_LOGGING', 'true').lower() == 'true'
        self.ENABLE_DETAILED_LOGGING = os.getenv('ENABLE_DETAILED_LOGGING', 'false').lower() == 'true'
        self.OUTPUT_BUFFER_FLUSH = os.getenv('OUTPUT_BUFFER_FLUSH', 'true').lower() == 'true'
        
        # 错误处理配置
        self.CONTINUE_ON_ERROR = os.getenv('CONTINUE_ON_ERROR', 'true').lower() == 'true'
        self.ERROR_RETRY_COUNT = int(os.getenv('ERROR_RETRY_COUNT', '1'))
        
    def get_config_summary(self) -> str:
        """获取配置总结"""
        return f"""
📋 处理配置总结:
   批量配置:
     - 最大批量大小: {self.MAX_BATCH_SIZE}
     - 最大处理时间: {self.MAX_PROCESSING_TIME}秒
     - 块处理时间: {self.CHUNK_PROCESSING_TIME}秒
   
   API配置:
     - API超时: {self.API_TIMEOUT}秒
     - 重试次数: {self.API_RETRY_COUNT}次
     - 重试延迟: {self.API_RETRY_DELAY}秒
   
   性能配置:
     - 进度日志: {'启用' if self.ENABLE_PROGRESS_LOGGING else '禁用'}
     - 详细日志: {'启用' if self.ENABLE_DETAILED_LOGGING else '禁用'}
     - 输出刷新: {'启用' if self.OUTPUT_BUFFER_FLUSH else '禁用'}
   
   错误处理:
     - 遇错继续: {'是' if self.CONTINUE_ON_ERROR else '否'}
     - 错误重试: {self.ERROR_RETRY_COUNT}次
"""
    
    def get_batch_size_recommendation(self, total_tasks: int) -> int:
        """根据任务总数推荐批量大小"""
        if total_tasks <= 5:
            return total_tasks
        elif total_tasks <= 20:
            return min(10, total_tasks)
        elif total_tasks <= 50:
            return min(15, total_tasks)
        else:
            return self.MAX_BATCH_SIZE
    
    def get_processing_time_recommendation(self, task_count: int) -> int:
        """根据任务数量推荐处理时间"""
        # 假设每个任务平均需要3-5秒
        estimated_time = task_count * 4
        
        # 添加20%的缓冲时间
        recommended_time = int(estimated_time * 1.2)
        
        # 但不能超过最大限制
        return min(recommended_time, self.MAX_PROCESSING_TIME)
    
    def update_from_env(self):
        """从环境变量更新配置"""
        self.__init__()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'batch': {
                'max_batch_size': self.MAX_BATCH_SIZE,
                'max_processing_time': self.MAX_PROCESSING_TIME,
                'chunk_processing_time': self.CHUNK_PROCESSING_TIME,
            },
            'api': {
                'timeout': self.API_TIMEOUT,
                'retry_count': self.API_RETRY_COUNT,
                'retry_delay': self.API_RETRY_DELAY,
            },
            'performance': {
                'progress_logging': self.ENABLE_PROGRESS_LOGGING,
                'detailed_logging': self.ENABLE_DETAILED_LOGGING,
                'output_buffer_flush': self.OUTPUT_BUFFER_FLUSH,
            },
            'error_handling': {
                'continue_on_error': self.CONTINUE_ON_ERROR,
                'error_retry_count': self.ERROR_RETRY_COUNT,
            }
        }

# 全局配置实例
config = ProcessingConfig()

def get_processing_config() -> ProcessingConfig:
    """获取处理配置"""
    return config

def update_config_from_env():
    """从环境变量更新配置"""
    global config
    config.update_from_env()

if __name__ == "__main__":
    # 测试配置
    cfg = ProcessingConfig()
    print(cfg.get_config_summary())
    
    # 测试推荐
    for task_count in [3, 8, 15, 25, 50, 100]:
        batch_size = cfg.get_batch_size_recommendation(task_count)
        time_limit = cfg.get_processing_time_recommendation(batch_size)
        print(f"任务数: {task_count:3d} -> 推荐批量: {batch_size:2d}, 推荐时间: {time_limit:2d}秒")

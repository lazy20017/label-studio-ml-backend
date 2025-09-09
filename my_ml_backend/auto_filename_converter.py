#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件名转换工具程序
功能：
1. 遍历指定文件夹及其子文件夹中的所有文件，指定文件夹为inputfile
2. 将文件名中的标点符号（除书名号外）替换为"-"
3. 裁剪文件名长度，保留前40个字符
4. 将文件名添加到文件内容的开始位置作为单独段落
5. 优化文档内容：删除空白行，合并少于10个字符的段落
6. 记录转换过程和结果

使用方法：
```bash
cd label-studio-ml-backend/my_ml_backend
python auto_filename_converter.py
```


"""

import os
import re
import logging
from datetime import datetime
from pathlib import Path

class FilenameConverter:
    def __init__(self, target_directory):
        """
        初始化文件名转换器
        
        Args:
            target_directory (str): 要处理的目标目录绝对路径
        """
        self.target_directory = Path(target_directory).resolve()
        self.setup_logging()
        self.conversion_count = 0
        self.error_count = 0
        self.content_modified_count = 0
        self.content_optimized_count = 0
        
    def setup_logging(self):
        """设置日志记录"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"filename_converter_{timestamp}.log"
        log_path = Path(__file__).parent / "logs" / log_filename
        
        # 确保logs目录存在
        log_path.parent.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"文件名转换器启动 - 目标目录: {self.target_directory}")
    
    def clean_filename(self, filename):
        """
        清理文件名
        
        Args:
            filename (str): 原始文件名
            
        Returns:
            str: 清理后的文件名
        """
        # 分离文件名和扩展名
        name_part, ext_part = os.path.splitext(filename)
        
        # 定义需要替换的标点符号（排除书名号《》、字母、数字、中文、下划线、连字符）
        # 包括常见的标点符号：！@#$%^&*()+={}[]|\\:";'<>?,./ 等
        punctuation_pattern = r'[^\w\u4e00-\u9fff《》\-_]'
        
        # 替换标点符号为"-"
        cleaned_name = re.sub(punctuation_pattern, '-', name_part)
        
        # 去除连续的"-"
        cleaned_name = re.sub(r'-+', '-', cleaned_name)
        
        # 去除首尾的"-"
        cleaned_name = cleaned_name.strip('-')
        
        # 裁剪到40个字符
        if len(cleaned_name) > 40:
            cleaned_name = cleaned_name[:40]
            # 如果裁剪后末尾是"-"，则去除
            cleaned_name = cleaned_name.rstrip('-')
        
        # 重新组合文件名
        new_filename = cleaned_name + ext_part
        
        return new_filename
    
    def is_filename_needs_conversion(self, original_name, cleaned_name):
        """
        检查文件名是否需要转换
        
        Args:
            original_name (str): 原始文件名
            cleaned_name (str): 清理后的文件名
            
        Returns:
            bool: 是否需要转换
        """
        return original_name != cleaned_name
    
    def optimize_content(self, content):
        """
        优化文档内容：删除空白行，合并少于10个字符的段落
        
        Args:
            content (str): 原始文档内容
            
        Returns:
            str: 优化后的文档内容
        """
        if not content.strip():
            return content
        
        # 按行分割内容
        lines = content.split('\n')
        
        # 删除空白行，保留非空行并去除首尾空格
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        if not non_empty_lines:
            return content
        
        # 合并短段落（少于10个字符的段落与下一段合并，但保留标题等重要内容）
        optimized_paragraphs = []
        i = 0
        
        while i < len(non_empty_lines):
            current_line = non_empty_lines[i]
            
            # 如果当前行少于10个字符且不是最后一行且不是第一行（标题），尝试与下一行合并
            if len(current_line) < 10 and i < len(non_empty_lines) - 1 and i > 0:
                next_line = non_empty_lines[i + 1]
                # 合并当前行和下一行，用空格连接
                merged_line = f"{current_line} {next_line}"
                optimized_paragraphs.append(merged_line)
                i += 2  # 跳过下一行，因为已经合并了
            else:
                optimized_paragraphs.append(current_line)
                i += 1
        
        # 用单个换行符连接所有行，完全删除空行
        return '\n'.join(optimized_paragraphs)
    
    def add_filename_to_content(self, file_path, filename_without_ext):
        """
        将文件名添加到文件内容的开始位置，并优化文档内容
        
        Args:
            file_path (Path): 文件路径对象
            filename_without_ext (str): 不含扩展名的文件名
            
        Returns:
            bool: 操作是否成功
        """
        try:
            # 只处理文本文件
            if file_path.suffix.lower() not in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml']:
                self.logger.debug(f"跳过非文本文件: {file_path.name}")
                return True
            
            # 读取原始文件内容
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
            except UnicodeDecodeError:
                # 如果UTF-8解码失败，尝试其他编码
                try:
                    with open(file_path, 'r', encoding='gbk') as f:
                        original_content = f.read()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        original_content = f.read()
            
            # 检查文件内容是否已经以文件名开头
            lines = original_content.split('\n')
            content_needs_filename = not (lines and lines[0].strip() == filename_without_ext)
            
            # 优化文档内容：删除空白行，合并短段落
            optimized_content = self.optimize_content(original_content)
            content_was_optimized = optimized_content != original_content
            
            # 如果内容需要添加文件名，则在开头添加
            if content_needs_filename:
                new_content = f"{filename_without_ext}\n\n{optimized_content}"
            else:
                new_content = optimized_content
            
            # 如果内容没有任何变化，则跳过写入
            if new_content == original_content:
                self.logger.debug(f"文件内容无需修改: {file_path.name}")
                return True
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # 更新统计计数
            if content_needs_filename:
                self.content_modified_count += 1
            if content_was_optimized:
                self.content_optimized_count += 1
            
            # 记录操作日志
            operations = []
            if content_needs_filename:
                operations.append("添加文件名")
            if content_was_optimized:
                operations.append("优化内容")
            
            if operations:
                operation_desc = "、".join(operations)
                self.logger.info(f"文件处理完成 ({operation_desc}): {file_path.name}")
            
            return True
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"修改文件内容失败 '{file_path}': {str(e)}")
            return False
    
    def convert_file(self, file_path):
        """
        转换单个文件的文件名
        
        Args:
            file_path (Path): 文件路径对象
            
        Returns:
            bool: 转换是否成功
        """
        try:
            original_name = file_path.name
            cleaned_name = self.clean_filename(original_name)
            
            if not self.is_filename_needs_conversion(original_name, cleaned_name):
                self.logger.debug(f"文件名无需转换: {original_name}")
                # 即使文件名不需要转换，也要添加文件名到内容开头
                name_without_ext = os.path.splitext(original_name)[0]
                self.add_filename_to_content(file_path, name_without_ext)
                return True
            
            new_path = file_path.parent / cleaned_name
            
            # 检查目标文件名是否已存在
            if new_path.exists():
                counter = 1
                name_part, ext_part = os.path.splitext(cleaned_name)
                while new_path.exists():
                    new_name = f"{name_part}_{counter}{ext_part}"
                    new_path = file_path.parent / new_name
                    counter += 1
                cleaned_name = new_name
            
            # 重命名文件
            file_path.rename(new_path)
            self.conversion_count += 1
            
            self.logger.info(f"文件重命名成功: '{original_name}' -> '{cleaned_name}'")
            
            # 将文件名（不含扩展名）添加到文件内容开头
            name_without_ext = os.path.splitext(cleaned_name)[0]
            self.add_filename_to_content(new_path, name_without_ext)
            
            return True
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"重命名文件失败 '{file_path}': {str(e)}")
            return False
    
    def process_directory(self):
        """
        处理目录中的所有文件
        """
        if not self.target_directory.exists():
            self.logger.error(f"目标目录不存在: {self.target_directory}")
            return False
        
        if not self.target_directory.is_dir():
            self.logger.error(f"目标路径不是目录: {self.target_directory}")
            return False
        
        self.logger.info("开始处理文件...")
        
        # 递归遍历所有文件
        for root, dirs, files in os.walk(self.target_directory):
            root_path = Path(root)
            
            self.logger.info(f"处理目录: {root_path}")
            
            for filename in files:
                file_path = root_path / filename
                self.convert_file(file_path)
        
        # 输出统计结果
        self.logger.info(f"处理完成 - 文件名转换: {self.conversion_count} 个, 内容修改: {self.content_modified_count} 个, 内容优化: {self.content_optimized_count} 个, 错误: {self.error_count} 个")
        print(f"\n处理完成!")
        print(f"文件名转换: {self.conversion_count} 个文件")
        print(f"内容修改: {self.content_modified_count} 个文件")
        print(f"内容优化: {self.content_optimized_count} 个文件")
        print(f"错误: {self.error_count} 个")
        
        return True

def main():
    """主函数"""
    # 设置目标目录的绝对路径
    # 这里使用当前项目的inputfile目录作为示例
    current_dir = Path(__file__).parent
    target_directory = current_dir / "inputfile"
    
    print("=== 文件名转换工具 ===")
    print(f"目标目录: {target_directory.absolute()}")
    print("将按顺序执行以下6个功能:")
    print("1. 将文件名中的标点符号（除书名号《》外）替换为'-'")
    print("2. 裁剪文件名长度到40个字符")
    print("3. 将文件名添加到文件内容的开始位置作为单独段落")
    print("4. 删除文档中的空白行")
    print("5. 合并少于10个字符的段落与下一段")
    print("6. 递归处理所有子目录")
    print()
    
    # 确认是否继续
    user_input = input("是否开始处理? (y/N): ").strip().lower()
    if user_input not in ['y', 'yes', '是']:
        print("操作已取消")
        return
    
    # 创建转换器并执行转换
    converter = FilenameConverter(target_directory)
    success = converter.process_directory()
    
    if success:
        print("文件名转换完成!")
    else:
        print("文件名转换过程中出现错误，请查看日志文件")

if __name__ == "__main__":
    main()

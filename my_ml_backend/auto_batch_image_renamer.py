#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量图片重命名工具
将指定文件夹下的图片文件按照 PIC_000001, PIC_000002... 的格式重命名
"""

import os
import shutil
from pathlib import Path
import logging

# ====== 配置区域 - 请修改以下路径 ======
# 图片文件夹的绝对路径（请根据实际情况修改）
IMAGE_FOLDER_PATH = r"E:\001 项目数据集\inputfile"

# 支持的图片格式（扩展名）
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'}

# 重命名前缀
FILE_PREFIX = "PIC_"

# 数字位数（6位数字，如 000001）
NUMBER_DIGITS = 6

# 是否创建备份（推荐开启）
CREATE_BACKUP = True

# 备份文件夹名称
BACKUP_FOLDER_NAME = "backup_original_names"

# 是否递归处理子文件夹
RECURSIVE_PROCESS = True

# 子文件夹处理方式：
# "flatten" - 将所有文件重命名到根目录（扁平化）
# "keep_structure" - 保持原有文件夹结构，在每个文件夹内重命名
# "separate_numbering" - 保持结构，但全局统一编号
SUBFOLDER_MODE = "separate_numbering"
# ====== 配置区域结束 ======


class AutoBatchImageRenamer:
    """批量图片重命名工具类"""
    
    def __init__(self, folder_path: str):
        """
        初始化重命名工具
        
        Args:
            folder_path: 图片文件夹路径
        """
        self.folder_path = Path(folder_path)
        self.backup_path = self.folder_path / BACKUP_FOLDER_NAME
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('image_renamer.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def validate_folder(self) -> bool:
        """
        验证文件夹是否存在且可访问
        
        Returns:
            bool: 验证结果
        """
        if not self.folder_path.exists():
            self.logger.error(f"❌ 文件夹不存在: {self.folder_path}")
            return False
            
        if not self.folder_path.is_dir():
            self.logger.error(f"❌ 路径不是文件夹: {self.folder_path}")
            return False
            
        return True
    
    def get_image_files(self) -> list:
        """
        获取文件夹中的所有图片文件
        
        Returns:
            list: 图片文件路径列表
        """
        image_files = []
        
        if RECURSIVE_PROCESS:
            # 递归获取所有图片文件
            for file_path in self.folder_path.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    # 跳过备份文件夹中的文件
                    if BACKUP_FOLDER_NAME not in str(file_path.relative_to(self.folder_path)):
                        image_files.append(file_path)
        else:
            # 只处理根目录的文件
            for file_path in self.folder_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                    image_files.append(file_path)
        
        # 按相对路径排序，确保重命名的一致性
        image_files.sort(key=lambda x: str(x.relative_to(self.folder_path)).lower())
        
        self.logger.info(f"📊 找到 {len(image_files)} 个图片文件")
        if RECURSIVE_PROCESS:
            # 显示文件夹分布统计
            folder_stats = {}
            for file_path in image_files:
                folder = file_path.parent.relative_to(self.folder_path)
                folder_key = str(folder) if folder != Path('.') else "根目录"
                folder_stats[folder_key] = folder_stats.get(folder_key, 0) + 1
            
            self.logger.info("📁 文件分布统计:")
            for folder, count in sorted(folder_stats.items()):
                self.logger.info(f"   {folder}: {count} 个文件")
        
        return image_files
    
    def _generate_new_path(self, file_path: Path, index: int) -> tuple:
        """
        根据配置生成新的文件路径
        
        Args:
            file_path: 原始文件路径
            index: 文件索引（从1开始）
            
        Returns:
            tuple: (新文件名, 新文件完整路径)
        """
        new_name = f"{FILE_PREFIX}{index:0{NUMBER_DIGITS}d}{file_path.suffix}"
        
        if SUBFOLDER_MODE == "flatten":
            # 扁平化：所有文件移动到根目录
            new_path = self.folder_path / new_name
        elif SUBFOLDER_MODE == "keep_structure":
            # 保持结构：在原文件夹内重命名
            new_path = file_path.parent / new_name
        else:  # separate_numbering
            # 保持结构但全局编号：在原文件夹内重命名
            new_path = file_path.parent / new_name
            
        return new_name, new_path
    
    def create_backup(self, image_files: list) -> bool:
        """
        创建原始文件名的备份
        
        Args:
            image_files: 图片文件列表
            
        Returns:
            bool: 备份是否成功
        """
        if not CREATE_BACKUP:
            return True
            
        try:
            # 创建备份文件夹
            self.backup_path.mkdir(exist_ok=True)
            
            # 创建文件名映射记录
            mapping_file = self.backup_path / "filename_mapping.txt"
            
            with open(mapping_file, 'w', encoding='utf-8') as f:
                f.write("原始文件路径 -> 新文件路径\n")
                f.write("=" * 80 + "\n")
                f.write(f"处理模式: {SUBFOLDER_MODE}\n")
                f.write(f"递归处理: {'是' if RECURSIVE_PROCESS else '否'}\n")
                f.write("=" * 80 + "\n\n")
                
                for i, file_path in enumerate(image_files, 1):
                    original_relative_path = file_path.relative_to(self.folder_path)
                    new_name, new_path = self._generate_new_path(file_path, i)
                    new_relative_path = new_path.relative_to(self.folder_path)
                    f.write(f"{original_relative_path} -> {new_relative_path}\n")
            
            self.logger.info(f"📋 文件名映射已保存到: {mapping_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 创建备份失败: {e}")
            return False
    
    def check_name_conflicts(self, image_files: list) -> bool:
        """
        检查重命名是否会产生文件名冲突
        
        Args:
            image_files: 图片文件列表
            
        Returns:
            bool: 是否存在冲突
        """
        new_paths = set()
        conflicts = []
        
        for i, file_path in enumerate(image_files, 1):
            new_name, new_path = self._generate_new_path(file_path, i)
            
            # 检查路径冲突
            if str(new_path) in new_paths:
                conflicts.append(f"{new_path} (重复路径)")
            else:
                new_paths.add(str(new_path))
                
            # 检查目标文件是否已存在（且不是当前要重命名的文件）
            if new_path.exists() and new_path != file_path:
                conflicts.append(f"{new_path} (文件已存在)")
                
            # 如果是扁平化模式，需要确保目标目录存在
            if SUBFOLDER_MODE == "flatten" and new_path.parent != self.folder_path:
                # 这种情况下目标应该是根目录，不应该发生
                conflicts.append(f"{new_path} (扁平化模式路径错误)")
        
        if conflicts:
            self.logger.error(f"❌ 发现文件名冲突: {conflicts}")
            return False
            
        return True
    
    def rename_files(self, image_files: list) -> bool:
        """
        执行文件重命名
        
        Args:
            image_files: 图片文件列表
            
        Returns:
            bool: 重命名是否成功
        """
        success_count = 0
        failed_files = []
        moved_count = 0  # 移动到不同文件夹的文件数
        
        self.logger.info("🔄 开始重命名文件...")
        
        for i, file_path in enumerate(image_files, 1):
            try:
                # 生成新文件路径
                new_name, new_path = self._generate_new_path(file_path, i)
                
                # 如果新路径与原路径相同，跳过
                if file_path == new_path:
                    self.logger.info(f"⏭️  跳过 {file_path.relative_to(self.folder_path)} (已是目标格式)")
                    success_count += 1
                    continue
                
                # 确保目标目录存在
                new_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 执行重命名/移动
                original_relative = file_path.relative_to(self.folder_path)
                new_relative = new_path.relative_to(self.folder_path)
                
                file_path.rename(new_path)
                success_count += 1
                
                # 检查是否移动了文件夹
                if file_path.parent != new_path.parent:
                    moved_count += 1
                    self.logger.info(f"📁 {original_relative} -> {new_relative}")
                else:
                    self.logger.info(f"✅ {original_relative} -> {new_relative}")
                
            except Exception as e:
                relative_path = file_path.relative_to(self.folder_path)
                failed_files.append(f"{relative_path}: {str(e)}")
                self.logger.error(f"❌ 重命名失败 {relative_path}: {e}")
        
        # 输出结果统计
        self.logger.info(f"📊 重命名完成: 成功 {success_count}/{len(image_files)}")
        if moved_count > 0:
            self.logger.info(f"📁 移动文件: {moved_count} 个")
        
        if failed_files:
            self.logger.error(f"❌ 失败的文件: {failed_files}")
            return False
            
        return True
    
    def run(self) -> bool:
        """
        执行批量重命名
        
        Returns:
            bool: 操作是否成功
        """
        self.logger.info("🚀 批量图片重命名工具启动")
        self.logger.info(f"📁 目标文件夹: {self.folder_path}")
        
        # 1. 验证文件夹
        if not self.validate_folder():
            return False
        
        # 2. 获取图片文件
        image_files = self.get_image_files()
        if not image_files:
            self.logger.warning("⚠️  未找到图片文件")
            return False
        
        # 3. 显示将要处理的文件
        self.logger.info("📋 将要重命名的文件:")
        for i, file_path in enumerate(image_files[:10], 1):  # 只显示前10个
            new_name, new_path = self._generate_new_path(file_path, i)
            original_relative = file_path.relative_to(self.folder_path)
            new_relative = new_path.relative_to(self.folder_path)
            self.logger.info(f"   {original_relative} -> {new_relative}")
        
        if len(image_files) > 10:
            self.logger.info(f"   ... 还有 {len(image_files) - 10} 个文件")
        
        # 4. 检查文件名冲突
        if not self.check_name_conflicts(image_files):
            return False
        
        # 5. 创建备份
        if not self.create_backup(image_files):
            self.logger.warning("⚠️  备份创建失败，但继续执行重命名")
        
        # 6. 确认操作
        print("\n" + "="*60)
        print(f"📁 目标文件夹: {self.folder_path}")
        print(f"📊 找到图片文件: {len(image_files)} 个")
        print(f"🔄 重命名格式: {FILE_PREFIX}{'0'*NUMBER_DIGITS}1, {FILE_PREFIX}{'0'*NUMBER_DIGITS}2, ...")
        print(f"📂 递归处理: {'启用' if RECURSIVE_PROCESS else '禁用'}")
        if RECURSIVE_PROCESS:
            mode_desc = {
                "flatten": "扁平化 - 所有文件移动到根目录",
                "keep_structure": "保持结构 - 在各自文件夹内重命名", 
                "separate_numbering": "保持结构 - 全局统一编号"
            }
            print(f"📂 处理模式: {mode_desc.get(SUBFOLDER_MODE, SUBFOLDER_MODE)}")
        print(f"💾 备份设置: {'启用' if CREATE_BACKUP else '禁用'}")
        print("="*60)
        
        while True:
            confirm = input("\n确认执行重命名操作吗？(y/n): ").strip().lower()
            if confirm in ['y', 'yes', '是']:
                break
            elif confirm in ['n', 'no', '否']:
                self.logger.info("❌ 用户取消操作")
                return False
            else:
                print("请输入 y 或 n")
        
        # 7. 执行重命名
        success = self.rename_files(image_files)
        
        if success:
            self.logger.info("🎉 批量重命名完成！")
        else:
            self.logger.error("❌ 批量重命名失败")
        
        return success


def main():
    """主函数"""
    print("🖼️  批量图片重命名工具")
    print("="*50)
    
    # 显示当前配置
    print(f"📁 目标文件夹: {IMAGE_FOLDER_PATH}")
    print(f"🔤 重命名格式: {FILE_PREFIX}{'0'*NUMBER_DIGITS}1{'.jpg'}")
    print(f"📋 支持格式: {', '.join(SUPPORTED_EXTENSIONS)}")
    print(f"🔄 递归处理: {'启用' if RECURSIVE_PROCESS else '禁用'}")
    print(f"📂 子文件夹处理: {SUBFOLDER_MODE}")
    print(f"💾 备份设置: {'启用' if CREATE_BACKUP else '禁用'}")
    print("="*50)
    
    # 检查文件夹路径是否已配置
    if IMAGE_FOLDER_PATH == r"E:\pydemo\01LabelStudio-test\images":
        print("⚠️  请在程序开头修改 IMAGE_FOLDER_PATH 为您的实际图片文件夹路径！")
        input("按回车键继续测试，或 Ctrl+C 退出...")
    
    # 创建重命名工具并执行
    renamer = AutoBatchImageRenamer(IMAGE_FOLDER_PATH)
    renamer.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断操作")
    except Exception as e:
        print(f"\n\n💥 程序异常: {e}")
        logging.error(f"程序异常: {e}", exc_info=True)

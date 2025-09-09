#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目自动创建器运行脚本
简化的入口点，包含基本的前置检查和用户交互

使用方法：
```bash
cd label-studio-ml-backend/my_ml_backend
python auto_run_project_creator.py
```

"""

import os
import sys
from pathlib import Path

# ========== 全局配置 ==========
MAX_PROJECTS_LIMIT = 1000  # 最多创建的项目数量限制
# 说明：
# - 此限制防止意外创建过多项目
# - 如需创建更多项目，请修改此值
# - 设置为 0 表示无限制（不推荐）
# - 项目名称会自动限制在50个字符以内（超过时保留前49个字符）
# ==============================

# 获取脚本所在目录，确保相对路径正确
SCRIPT_DIR = Path(__file__).parent.absolute()
os.chdir(SCRIPT_DIR)  # 切换到脚本所在目录

def print_banner():
    """打印程序横幅"""
    limit_text = "无限制" if MAX_PROJECTS_LIMIT == 0 else f"最多 {MAX_PROJECTS_LIMIT} 个"
    print(f"""
🌊 Label Studio 项目自动创建器 🌊
=====================================
功能：自动扫描txt文件并创建Label Studio项目
作者：AI Assistant
版本：1.0.0
项目数量限制：{limit_text}
=====================================
    """)

def quick_check():
    """快速检查环境"""
    print("🔍 快速环境检查...")
    
    issues = []
    warnings = []
    
    # 检查必需文件
    if not os.path.exists("auto_project_creator.py"):
        issues.append("缺少 auto_project_creator.py")
    
    if not os.path.exists("文本命名实体提取标签.md"):
        issues.append("缺少 文本命名实体提取标签.md")
    
    if not os.path.exists("inputfile"):
        issues.append("缺少 inputfile 文件夹")
    else:
        # 检查txt文件
        txt_files = list(Path("inputfile").rglob("*.txt"))
        if not txt_files:
            issues.append("inputfile 文件夹中没有txt文件")
        else:
            print(f"✅ 找到 {len(txt_files)} 个txt文件")
            
            # 检查项目数量限制
            if MAX_PROJECTS_LIMIT == 0:
                print(f"✅ 项目数量: {len(txt_files)} (无限制模式)")
            elif len(txt_files) > MAX_PROJECTS_LIMIT:
                warnings.append(f"发现 {len(txt_files)} 个txt文件，超过了最大限制 {MAX_PROJECTS_LIMIT} 个")
                warnings.append(f"将只处理前 {MAX_PROJECTS_LIMIT} 个文件")
                print(f"⚠️ 项目数量限制: 只会创建前 {MAX_PROJECTS_LIMIT} 个项目")
            else:
                print(f"✅ 项目数量: {len(txt_files)}/{MAX_PROJECTS_LIMIT} (在限制范围内)")
    
    # 显示警告
    if warnings:
        print("⚠️ 注意事项:")
        for warning in warnings:
            print(f"   • {warning}")
    
    # 显示错误
    if issues:
        print("❌ 环境检查失败:")
        for issue in issues:
            print(f"   • {issue}")
        print("\n💡 建议运行: python test_project_creator.py 进行详细检查")
        return False
    
    print("✅ 环境检查通过")
    return True

def main():
    """主函数"""
    print_banner()
    
    # 快速检查
    if not quick_check():
        return False
    
    # 用户确认
    print("\n📋 即将执行的操作:")
    print("   1. 测试Label Studio和ML Backend连接")
    print("   2. 扫描 inputfile 文件夹下的所有txt文件")
    print("   3. 为每个文件创建Label Studio项目")
    print("   4. 配置文本命名实体提取标签")
    print("   5. 自动连接ML Backend到每个项目")
    print("   6. 导入对应文档到项目中")
    if MAX_PROJECTS_LIMIT == 0:
        print(f"\n🔢 项目数量限制: 无限制 (将处理所有txt文件)")
    else:
        print(f"\n🔢 项目数量限制: 最多创建 {MAX_PROJECTS_LIMIT} 个项目")
    
    # 检查API令牌配置
    try:
        from auto_project_creator import LABEL_STUDIO_API_TOKEN
        if not LABEL_STUDIO_API_TOKEN or LABEL_STUDIO_API_TOKEN == "your_api_token_here":
            print("\n⚠️ 警告: API令牌未配置")
            print("请先在 auto_project_creator.py 中设置正确的API令牌")
            return False
        print(f"\n✅ API令牌已配置: {LABEL_STUDIO_API_TOKEN[:10]}...")
    except ImportError:
        print("\n❌ 无法加载配置，请检查 auto_project_creator.py 文件")
        return False
    
    # 用户确认
    print(f"\n❓ 确认执行吗？(y/N): ", end="")
    try:
        response = input().strip().lower()
        if response not in ['y', 'yes', '是']:
            print("👋 操作已取消")
            return False
    except KeyboardInterrupt:
        print("\n👋 操作已取消")
        return False
    
    # 运行项目创建器
    print("\n🚀 开始创建项目...")
    if MAX_PROJECTS_LIMIT == 0:
        print(f"📊 项目数量限制: 无限制")
    else:
        print(f"📊 项目数量限制: {MAX_PROJECTS_LIMIT} 个")
    try:
        from auto_project_creator import main as run_creator
        # 注意：这里假设 auto_project_creator 支持项目数量限制参数
        # 如果不支持，需要修改 auto_project_creator.py 来接受此参数
        project_ids = run_creator(max_projects=MAX_PROJECTS_LIMIT)
        
        if project_ids:
            print(f"\n🎉 成功完成！")
            print(f"📋 创建的项目编号: {project_ids}")
            if MAX_PROJECTS_LIMIT == 0:
                print(f"📊 实际创建数量: {len(project_ids)} (无限制模式)")
            else:
                print(f"📊 实际创建数量: {len(project_ids)}/{MAX_PROJECTS_LIMIT}")
            print(f"\n🌐 访问 Label Studio: http://localhost:8080")
            print(f"   您可以在项目列表中看到新创建的项目")
            return True
        else:
            print("\n⚠️ 没有成功创建任何项目")
            return False
            
    except KeyboardInterrupt:
        print("\n👋 用户中断操作")
        return False
    except Exception as e:
        print(f"\n💥 执行失败: {e}")
        print("💡 建议:")
        print("   1. 检查 Label Studio 是否正在运行 (http://localhost:8080)")
        print("   2. 检查 ML Backend 是否正在运行 (http://localhost:9090)")
        print("   3. 检查 API 令牌是否正确")
        print("   4. 查看日志文件了解详细错误信息")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✨ 程序执行完成")
        else:
            print("\n❌ 程序执行失败")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 程序被中断")
        sys.exit(130)  # 130 = 128 + SIGINT

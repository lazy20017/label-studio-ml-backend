#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 auto_config_updater.py 程序

此脚本用于测试配置更新器的各个功能组件，确保程序能正常工作。
"""

import json
import sys
from pathlib import Path
from auto_config_updater import LabelStudioConfigUpdater

def test_config_loading():
    """测试配置文件加载功能"""
    print("🧪 测试配置文件加载...")
    
    updater = LabelStudioConfigUpdater()
    
    # 测试加载配置
    success = updater.load_new_config()
    if success:
        print("✅ 配置文件加载成功")
        print(f"   标签数量: {updater._count_labels(updater.new_config)}")
        
        # 显示部分配置内容
        lines = updater.new_config.split('\n')[:10]
        print("   配置预览:")
        for line in lines:
            if line.strip():
                print(f"     {line.strip()}")
        if len(updater.new_config.split('\n')) > 10:
            print("     ...")
            
        return True
    else:
        print("❌ 配置文件加载失败")
        return False

def test_xml_validation():
    """测试XML验证功能"""
    print("\n🧪 测试XML验证...")
    
    updater = LabelStudioConfigUpdater()
    
    # 测试有效的XML
    valid_xml = """<View>
  <Text name="text" value="$text"/>
  <Labels name="label" toName="text">
    <Label value="测试标签" background="red"/>
  </Labels>
</View>"""
    
    if updater._validate_xml_config(valid_xml):
        print("✅ 有效XML验证通过")
    else:
        print("❌ 有效XML验证失败")
        return False
        
    # 测试无效的XML
    invalid_xml = """<View>
  <Text name="text" value="$text"/>
  <Labels name="label" toName="text">
    <Label value="测试标签" background="red"
  </Labels>
</View>"""
    
    if not updater._validate_xml_config(invalid_xml):
        print("✅ 无效XML验证正确拒绝")
        return True
    else:
        print("❌ 无效XML验证未能正确拒绝")
        return False

def test_label_counting():
    """测试标签计数功能"""
    print("\n🧪 测试标签计数...")
    
    updater = LabelStudioConfigUpdater()
    
    test_xml = """<View>
  <Text name="text" value="$text"/>
  <Labels name="label" toName="text">
    <Label value="标签1" background="red"/>
    <Label value="标签2" background="blue"/>
    <Label value="标签3" background="green"/>
  </Labels>
</View>"""
    
    count = updater._count_labels(test_xml)
    if count == 3:
        print(f"✅ 标签计数正确: {count}")
        return True
    else:
        print(f"❌ 标签计数错误: 期望3，实际{count}")
        return False

def test_backup_directory():
    """测试备份目录创建"""
    print("\n🧪 测试备份目录...")
    
    updater = LabelStudioConfigUpdater()
    
    if hasattr(updater, 'backup_dir') and updater.backup_dir.exists():
        print(f"✅ 备份目录已创建: {updater.backup_dir}")
        return True
    else:
        print("❌ 备份目录创建失败")
        return False

def test_connection():
    """测试Label Studio连接（不执行实际操作）"""
    print("\n🧪 测试Label Studio连接...")
    
    updater = LabelStudioConfigUpdater()
    
    # 只测试URL格式，不发送实际请求
    if updater.label_studio_url and updater.api_token:
        print(f"✅ 连接配置正确")
        print(f"   URL: {updater.label_studio_url}")
        print(f"   Token: {updater.api_token[:10]}...")
        return True
    else:
        print("❌ 连接配置缺失")
        return False

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行 auto_config_updater 测试套件\n")
    
    tests = [
        ("配置文件加载", test_config_loading),
        ("XML验证", test_xml_validation),
        ("标签计数", test_label_counting),
        ("备份目录", test_backup_directory),
        ("连接配置", test_connection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {str(e)}")
    
    print(f"\n📊 测试结果:")
    print(f"   通过: {passed}/{total}")
    print(f"   失败: {total-passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！auto_config_updater 程序准备就绪")
        return True
    else:
        print("⚠️ 部分测试失败，请检查配置")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

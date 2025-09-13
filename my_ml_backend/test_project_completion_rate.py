#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试项目完成率统计功能
"""

from auto_query_projects import get_task_summary_range, LabelStudioProjectQuery

def test_project_completion_rate():
    """测试新增的项目完成率功能"""
    print("🧪 测试项目完成率统计功能")
    print("=" * 60)
    
    # 测试小范围查询
    print("\n1. 🔗 测试Label Studio连接...")
    query = LabelStudioProjectQuery()
    if not query.test_connection():
        print("❌ 连接失败，请检查Label Studio服务")
        return False
    
    print("\n2. 📋 测试小范围项目统计（项目ID 2-3）...")
    try:
        summary = query.get_task_count_summary(2, 3)
        if summary:
            print("✅ 获取统计数据成功")
            
            # 验证新字段是否存在
            required_fields = [
                'project_count', 'completed_projects', 'project_completion_rate',
                'total_tasks', 'total_finished_tasks', 'completion_rate'
            ]
            
            print("\n3. 🔍 验证新增字段...")
            missing_fields = []
            for field in required_fields:
                if field not in summary:
                    missing_fields.append(field)
                else:
                    print(f"   ✅ {field}: {summary[field]}")
            
            if missing_fields:
                print(f"❌ 缺少字段: {missing_fields}")
                return False
            
            # 验证计算逻辑
            print("\n4. 🧮 验证计算逻辑...")
            projects = summary['projects']
            
            # 手动计算完成项目数
            manual_completed = 0
            for project in projects:
                if project['task_count'] > 0 and project['finished_task_count'] == project['task_count']:
                    manual_completed += 1
                    print(f"   🏆 完成项目: ID {project['id']} ({project['title'][:20]}...)")
            
            # 验证计算结果
            if manual_completed == summary['completed_projects']:
                print(f"   ✅ 完成项目数计算正确: {manual_completed}")
            else:
                print(f"   ❌ 完成项目数计算错误: 预期 {manual_completed}, 实际 {summary['completed_projects']}")
                return False
            
            # 验证项目完成率
            expected_rate = (manual_completed / summary['project_count'] * 100) if summary['project_count'] > 0 else 0.0
            if abs(expected_rate - summary['project_completion_rate']) < 0.01:
                print(f"   ✅ 项目完成率计算正确: {expected_rate:.1f}%")
            else:
                print(f"   ❌ 项目完成率计算错误: 预期 {expected_rate:.1f}%, 实际 {summary['project_completion_rate']:.1f}%")
                return False
            
            print("\n5. 📊 显示完整统计报告...")
            query.display_task_summary(summary)
            
            return True
            
        else:
            print("❌ 获取统计数据失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

def test_convenience_function():
    """测试便捷函数"""
    print("\n" + "=" * 60)
    print("🚀 测试便捷函数")
    print("=" * 60)
    
    try:
        print("📊 调用便捷函数 get_task_summary_range(2, 3)...")
        summary = get_task_summary_range(2, 3, display=True, save_file=False)
        
        if summary and 'project_completion_rate' in summary:
            print(f"\n✅ 便捷函数测试成功")
            print(f"   📁 项目总数: {summary['project_count']}")
            print(f"   🏆 完成项目数: {summary['completed_projects']}")
            print(f"   📊 项目完成率: {summary['project_completion_rate']:.1f}%")
            print(f"   📋 任务总数: {summary['total_tasks']}")
            print(f"   📈 任务完成率: {summary['completion_rate']:.1f}%")
            return True
        else:
            print("❌ 便捷函数测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 便捷函数测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🎯 项目完成率统计功能测试")
    print("=" * 60)
    
    # 执行测试
    test1_result = test_project_completion_rate()
    test2_result = test_convenience_function()
    
    # 显示结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print(f"🧪 基础功能测试: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"🚀 便捷函数测试: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        print("\n🎉 所有测试通过！项目完成率统计功能正常工作")
        print("\n💡 新功能说明:")
        print("   📊 项目完成率: 完全完成的项目数 / 总项目数 * 100%")
        print("   📈 任务完成率: 已完成任务数 / 总任务数 * 100%")
        print("   🏆 完成项目: 所有任务都已完成的项目")
        print("\n✨ 统计报告现在包含更丰富的完成度分析！")
    else:
        print("\n❌ 部分测试失败，请检查代码")

if __name__ == "__main__":
    main()



#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Label Studio 项目查询器
功能：
1. 查询并显示Label Studio中所有项目的名称和编号
2. 统计指定范围项目的任务完成情况
3. 计算项目完成率和任务完成率
4. 批量删除项目

主要统计指标：
- 项目完成率：完全完成的项目数量占总项目数量的百分比
- 任务完成率：已完成任务数量占总任务数量的百分比
- 完成项目数：所有任务都已完成的项目数量

使用方法：
```bash
cd label-studio-ml-backend/my_ml_backend
python auto_query_projects.py
```

"""

import requests
import json
from typing import List, Dict, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

class LabelStudioProjectQuery:
    """Label Studio 项目查询类"""
    
    def __init__(self, label_studio_url: str = "http://localhost:8080", 
                 token: str = "02be98ff6805d4d3c86f6b51bb0d538acb4c96e5"):
        """
        初始化查询器
        
        Args:
            label_studio_url: Label Studio服务地址
            token: API访问令牌
        """
        self.label_studio_url = label_studio_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {self.token}",
            "Content-Type": "application/json"
        })
        
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
            response = self.session.get(f"{self.label_studio_url}/api/projects/", timeout=15)
            
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
                        logger.info(f"📄 获取下一页数据...")
                        next_response = self.session.get(next_url, timeout=15)
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
                logger.error(f"❌ 查询失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 查询异常: {e}")
            return None
    
    def format_project_info(self, projects: List[Dict]) -> List[Dict]:
        """
        格式化项目信息，提取关键字段
        
        Args:
            projects: 原始项目数据
            
        Returns:
            格式化后的项目信息列表
        """
        formatted_projects = []
        
        for project in projects:
            formatted_project = {
                'id': project.get('id'),
                'title': project.get('title', '未命名项目'),
                'description': project.get('description', ''),
                'created_at': project.get('created_at', ''),
                'updated_at': project.get('updated_at', ''),
                'task_count': project.get('task_number', 0),
                'total_annotations': project.get('total_annotations_number', 0),
                'finished_task_count': project.get('finished_task_number', 0)
            }
            formatted_projects.append(formatted_project)
            
        return formatted_projects
    
    def display_projects(self, projects: List[Dict]) -> None:
        """
        显示项目信息
        
        Args:
            projects: 项目信息列表
        """
        if not projects:
            print("📭 没有找到任何项目")
            return
            
        print(f"\n{'='*80}")
        print(f"📊 Label Studio 项目列表 (共 {len(projects)} 个项目)")
        print(f"{'='*80}")
        print(f"{'ID':<5} {'项目名称':<30} {'任务数':<8} {'完成数':<8} {'创建时间':<20}")
        print(f"{'-'*80}")
        
        for project in projects:
            # 截断过长的标题
            title = project['title']
            if len(title) > 28:
                title = title[:25] + "..."
                
            # 格式化创建时间
            created_at = project['created_at']
            if created_at:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_at = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    created_at = created_at[:16] if len(created_at) > 16 else created_at
            else:
                created_at = "未知"
                
            print(f"{project['id']:<5} {title:<30} {project['task_count']:<8} "
                  f"{project['finished_task_count']:<8} {created_at:<20}")
        
        print(f"{'-'*80}")
        
        # 显示统计信息
        total_tasks = sum(p['task_count'] for p in projects)
        total_finished = sum(p['finished_task_count'] for p in projects)
        total_annotations = sum(p['total_annotations'] for p in projects)
        
        print(f"📈 统计信息:")
        print(f"   - 项目总数: {len(projects)}")
        print(f"   - 任务总数: {total_tasks}")
        print(f"   - 已完成: {total_finished}")
        print(f"   - 总标注数: {total_annotations}")
        
        if total_tasks > 0:
            completion_rate = (total_finished / total_tasks) * 100
            print(f"   - 完成率: {completion_rate:.1f}%")
        
        print(f"{'='*80}\n")
    
    def save_to_file(self, projects: List[Dict], filename: str = "labelstudio_projects.json") -> bool:
        """
        将项目信息保存到文件
        
        Args:
            projects: 项目信息列表
            filename: 保存文件名
            
        Returns:
            是否保存成功
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(projects, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 项目信息已保存到: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存文件失败: {e}")
            return False
    
    def delete_project(self, project_id: int) -> bool:
        """
        删除单个项目
        
        Args:
            project_id: 要删除的项目ID
            
        Returns:
            是否删除成功
        """
        try:
            logger.info(f"🗑️ 正在删除项目 ID: {project_id}")
            response = self.session.delete(f"{self.label_studio_url}/api/projects/{project_id}/", timeout=15)
            
            if response.status_code == 204:  # 删除成功通常返回204 No Content
                logger.info(f"✅ 项目 {project_id} 删除成功")
                return True
            elif response.status_code == 404:
                logger.warning(f"⚠️ 项目 {project_id} 不存在")
                return False
            else:
                logger.error(f"❌ 删除项目 {project_id} 失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 删除项目 {project_id} 异常: {e}")
            return False
    
    def delete_projects_batch(self, project_ids: List[int], confirm: bool = True) -> Dict[str, List[int]]:
        """
        批量删除项目
        
        Args:
            project_ids: 要删除的项目ID列表
            confirm: 是否需要确认，默认True
            
        Returns:
            删除结果字典，包含成功和失败的项目ID列表
        """
        if not project_ids:
            logger.warning("⚠️ 没有指定要删除的项目")
            return {"success": [], "failed": []}
        
        # 获取当前项目列表用于验证
        current_projects = self.get_all_projects()
        if current_projects is None:
            logger.error("❌ 无法获取当前项目列表")
            return {"success": [], "failed": project_ids}
        
        # 验证项目ID是否存在
        existing_ids = {p['id'] for p in current_projects}
        valid_ids = [pid for pid in project_ids if pid in existing_ids]
        invalid_ids = [pid for pid in project_ids if pid not in existing_ids]
        
        if invalid_ids:
            logger.warning(f"⚠️ 以下项目ID不存在: {invalid_ids}")
        
        if not valid_ids:
            logger.warning("⚠️ 没有有效的项目ID可删除")
            return {"success": [], "failed": project_ids}
        
        # 显示要删除的项目信息
        print(f"\n🗑️ 准备删除以下 {len(valid_ids)} 个项目:")
        print("-" * 60)
        for project in current_projects:
            if project['id'] in valid_ids:
                print(f"ID: {project['id']:<5} | 名称: {project.get('title', '未命名')}")
        print("-" * 60)
        
        # 确认删除
        if confirm:
            print(f"\n⚠️  警告：此操作将永久删除这些项目及其所有数据！")
            response = input("请输入 'YES' 确认删除，或按回车取消: ").strip()
            if response != 'YES':
                logger.info("❌ 删除操作已取消")
                return {"success": [], "failed": valid_ids}
        
        # 执行删除
        logger.info(f"🚀 开始批量删除 {len(valid_ids)} 个项目...")
        success_ids = []
        failed_ids = []
        
        for i, project_id in enumerate(valid_ids, 1):
            logger.info(f"📋 进度: {i}/{len(valid_ids)} - 删除项目 {project_id}")
            
            if self.delete_project(project_id):
                success_ids.append(project_id)
            else:
                failed_ids.append(project_id)
        
        # 显示结果
        print(f"\n✅ 批量删除完成！")
        print(f"   - 成功删除: {len(success_ids)} 个项目")
        print(f"   - 删除失败: {len(failed_ids)} 个项目")
        
        if success_ids:
            print(f"   - 成功删除的项目ID: {success_ids}")
        if failed_ids:
            print(f"   - 删除失败的项目ID: {failed_ids}")
        
        return {
            "success": success_ids,
            "failed": failed_ids + invalid_ids
        }
    
    def get_project_list(self) -> Optional[List[Dict]]:
        """
        获取项目列表的主要方法
        
        Returns:
            格式化的项目信息列表
        """
        # 测试连接
        if not self.test_connection():
            return None
        
        # 获取项目数据
        raw_projects = self.get_all_projects()
        if raw_projects is None:
            return None
        
        # 格式化数据
        formatted_projects = self.format_project_info(raw_projects)
        
        return formatted_projects
    
    def get_projects_in_range(self, start_id: int, end_id: int) -> Optional[List[Dict]]:
        """
        获取指定ID范围内的项目信息
        
        Args:
            start_id: 起始项目ID（包含）
            end_id: 结束项目ID（包含）
            
        Returns:
            指定范围内的项目信息列表
        """
        try:
            logger.info(f"📋 查询项目ID范围: {start_id} - {end_id}")
            
            # 获取所有项目
            all_projects = self.get_project_list()
            if all_projects is None:
                return None
            
            # 筛选指定范围的项目
            range_projects = [
                project for project in all_projects 
                if start_id <= project['id'] <= end_id
            ]
            
            logger.info(f"✅ 找到 {len(range_projects)} 个项目在范围 {start_id}-{end_id} 内")
            return range_projects
            
        except Exception as e:
            logger.error(f"❌ 查询范围项目异常: {e}")
            return None
    
    def get_task_count_summary(self, start_id: int, end_id: int) -> Optional[Dict]:
        """
        获取指定ID范围内的任务数量统计
        
        Args:
            start_id: 起始项目ID（包含）
            end_id: 结束项目ID（包含）
            
        Returns:
            任务统计信息字典
        """
        try:
            logger.info(f"📊 统计项目ID {start_id}-{end_id} 的任务数量...")
            
            # 获取范围内的项目
            projects = self.get_projects_in_range(start_id, end_id)
            if projects is None:
                return None
            
            if not projects:
                logger.warning(f"⚠️ 在范围 {start_id}-{end_id} 内未找到任何项目")
                return {
                    'range_start': start_id,
                    'range_end': end_id,
                    'project_count': 0,
                    'completed_projects': 0,
                    'project_completion_rate': 0.0,
                    'total_tasks': 0,
                    'total_finished_tasks': 0,
                    'total_annotations': 0,
                    'completion_rate': 0.0,
                    'projects': []
                }
            
            # 计算统计信息
            total_tasks = sum(p['task_count'] for p in projects)
            total_finished = sum(p['finished_task_count'] for p in projects)
            total_annotations = sum(p['total_annotations'] for p in projects)
            completion_rate = (total_finished / total_tasks * 100) if total_tasks > 0 else 0.0
            
            # 计算完成项目统计率 - 完全完成的项目数量
            completed_projects = 0
            for project in projects:
                if project['task_count'] > 0 and project['finished_task_count'] == project['task_count']:
                    completed_projects += 1
            
            project_completion_rate = (completed_projects / len(projects) * 100) if len(projects) > 0 else 0.0
            
            summary = {
                'range_start': start_id,
                'range_end': end_id,
                'project_count': len(projects),
                'completed_projects': completed_projects,
                'project_completion_rate': project_completion_rate,
                'total_tasks': total_tasks,
                'total_finished_tasks': total_finished,
                'total_annotations': total_annotations,
                'completion_rate': completion_rate,
                'projects': projects
            }
            
            logger.info(f"✅ 统计完成: {len(projects)}个项目，总任务数 {total_tasks}")
            return summary
            
        except Exception as e:
            logger.error(f"❌ 统计任务数量异常: {e}")
            return None
    
    def display_task_summary(self, summary: Dict) -> None:
        """
        显示任务统计信息
        
        Args:
            summary: 任务统计信息字典
        """
        if not summary:
            print("📭 没有找到任何统计数据")
            return
        
        print(f"\n{'='*80}")
        print(f"📊 项目任务统计报告")
        print(f"{'='*80}")
        print(f"🎯 项目ID范围: {summary['range_start']} - {summary['range_end']}")
        print(f"📁 项目总数: {summary['project_count']} 个")
        print(f"🏆 完成项目数: {summary['completed_projects']} 个")
        print(f"📊 项目完成率: {summary['project_completion_rate']:.1f}%")
        print(f"📋 任务总数: {summary['total_tasks']} 个")
        print(f"✅ 已完成任务: {summary['total_finished_tasks']} 个")
        print(f"🏷️ 总标注数: {summary['total_annotations']} 个")
        print(f"📈 任务完成率: {summary['completion_rate']:.1f}%")
        print(f"{'='*80}")
        
        if summary['projects']:
            print(f"\n📋 详细项目列表:")
            print(f"{'ID':<6} {'项目名称':<35} {'任务数':<8} {'完成数':<8} {'完成率':<8}")
            print(f"{'-'*80}")
            
            for project in summary['projects']:
                # 截断过长的标题
                title = project['title']
                if len(title) > 33:
                    title = title[:30] + "..."
                
                # 计算项目完成率
                proj_completion = (project['finished_task_count'] / project['task_count'] * 100) if project['task_count'] > 0 else 0.0
                
                print(f"{project['id']:<6} {title:<35} {project['task_count']:<8} "
                      f"{project['finished_task_count']:<8} {proj_completion:.1f}%")
            
            print(f"{'-'*80}")
        
        print(f"\n💡 使用建议:")
        
        # 项目完成率分析
        if summary['project_completion_rate'] == 0:
            print(f"   🔴 无完成项目，所有项目都需要继续标注")
        elif summary['project_completion_rate'] < 20:
            print(f"   ⚠️ 完成项目较少({summary['project_completion_rate']:.1f}%)，建议集中资源完成部分项目")
        elif summary['project_completion_rate'] < 50:
            print(f"   🟡 部分项目已完成({summary['project_completion_rate']:.1f}%)，继续推进其他项目")
        else:
            print(f"   🟢 大部分项目已完成({summary['project_completion_rate']:.1f}%)，进展良好")
        
        # 任务完成率分析
        if summary['completion_rate'] < 50:
            print(f"   ⚠️ 任务完成率较低({summary['completion_rate']:.1f}%)，建议加快标注进度")
        elif summary['completion_rate'] < 80:
            print(f"   🟡 任务进展良好({summary['completion_rate']:.1f}%)，继续保持")
        else:
            print(f"   🟢 任务完成率很高({summary['completion_rate']:.1f}%)，接近完成")
        
        # 项目规模分析
        if summary['total_tasks'] > 1000:
            print(f"   📊 任务量较大({summary['total_tasks']}个)，建议合理分配资源")
        
        # 项目数量和完成状态综合分析
        if summary['project_count'] > 0:
            avg_tasks_per_project = summary['total_tasks'] / summary['project_count']
            if avg_tasks_per_project > 100:
                print(f"   🎯 平均每项目任务较多({avg_tasks_per_project:.0f}个)，建议优先完成小项目")
        
        print(f"{'='*80}\n")


def interactive_menu(query: LabelStudioProjectQuery) -> Optional[List[Dict]]:
    """
    交互式菜单
    
    Args:
        query: 查询器实例
        
    Returns:
        项目列表
    """
    while True:
        print("\n" + "=" * 60)
        print("🚀 Label Studio 项目管理器")
        print("=" * 60)
        print("1. 查看所有项目")
        print("2. 查询项目范围任务统计")
        print("3. 删除单个项目")
        print("4. 批量删除项目")
        print("5. 退出")
        print("-" * 60)
        
        choice = input("请选择操作 (1-5): ").strip()
        
        if choice == "1":
            # 查看项目列表
            projects = query.get_project_list()
            if projects is not None:
                query.display_projects(projects)
                query.save_to_file(projects)
                return projects
            else:
                print("❌ 无法获取项目信息")
                
        elif choice == "2":
            # 查询项目范围任务统计
            print("\n📊 项目任务统计查询")
            print("=" * 40)
            
            try:
                start_id = int(input("请输入起始项目ID: ").strip())
                end_id = int(input("请输入结束项目ID: ").strip())
                
                if start_id > end_id:
                    print("❌ 起始ID不能大于结束ID")
                    continue
                
                # 获取任务统计
                summary = query.get_task_count_summary(start_id, end_id)
                if summary is not None:
                    query.display_task_summary(summary)
                    
                    # 保存统计结果到文件
                    filename = f"task_summary_{start_id}_{end_id}.json"
                    try:
                        with open(filename, 'w', encoding='utf-8') as f:
                            import json
                            json.dump(summary, f, ensure_ascii=False, indent=2)
                        print(f"💾 统计结果已保存到: {filename}")
                    except Exception as e:
                        print(f"⚠️ 保存文件失败: {e}")
                        
                else:
                    print("❌ 无法获取任务统计信息")
                    
            except ValueError:
                print("❌ 请输入有效的项目ID (数字)")
                
        elif choice == "3":
            # 删除单个项目
            projects = query.get_project_list()
            if projects is None:
                print("❌ 无法获取项目信息")
                continue
                
            query.display_projects(projects)
            
            try:
                project_id = int(input("\n请输入要删除的项目ID: ").strip())
                result = query.delete_projects_batch([project_id])
                if result["success"]:
                    print(f"✅ 项目 {project_id} 删除成功")
                else:
                    print(f"❌ 项目 {project_id} 删除失败")
            except ValueError:
                print("❌ 请输入有效的项目ID")
                
        elif choice == "4":
            # 批量删除项目
            projects = query.get_project_list()
            if projects is None:
                print("❌ 无法获取项目信息")
                continue
                
            query.display_projects(projects)
            
            print("\n📝 请输入要删除的项目ID，用逗号分隔 (例如: 1,2,3)")
            print("💡 提示：可以从上面的项目列表中复制ID")
            ids_input = input("项目ID列表: ").strip()
            
            if not ids_input:
                print("❌ 未输入任何项目ID")
                continue
                
            try:
                # 解析项目ID列表
                project_ids = []
                for id_str in ids_input.split(','):
                    id_str = id_str.strip()
                    if id_str:
                        project_ids.append(int(id_str))
                
                if not project_ids:
                    print("❌ 未找到有效的项目ID")
                    continue
                
                # 执行批量删除
                result = query.delete_projects_batch(project_ids)
                
            except ValueError:
                print("❌ 请输入有效的项目ID (数字)")
                
        elif choice == "5":
            print("👋 感谢使用 Label Studio 项目管理器")
            break
            
        else:
            print("❌ 无效选择，请输入 1-5")
    
    return None


def get_task_summary_range(start_id: int, end_id: int, display: bool = True, save_file: bool = True) -> Optional[Dict]:
    """
    快速查询指定范围项目的任务统计 - 便捷函数
    
    Args:
        start_id: 起始项目ID（包含）
        end_id: 结束项目ID（包含）
        display: 是否显示统计结果，默认True
        save_file: 是否保存统计结果到文件，默认True
        
    Returns:
        任务统计信息字典
        
    Example:
        # 查询超星801到956的所有项目任务统计
        summary = get_task_summary_range(801, 956)
        print(f"项目总数: {summary['project_count']}")
        print(f"完成项目数: {summary['completed_projects']}")
        print(f"项目完成率: {summary['project_completion_rate']:.1f}%")
        print(f"总任务数: {summary['total_tasks']}")
        print(f"任务完成率: {summary['completion_rate']:.1f}%")
    """
    print(f"📊 Label Studio 项目任务统计工具")
    print(f"🎯 查询范围: 项目ID {start_id} - {end_id}")
    print("=" * 50)
    
    # 创建查询器实例
    query = LabelStudioProjectQuery()
    
    # 获取任务统计
    summary = query.get_task_count_summary(start_id, end_id)
    
    if summary is not None:
        # 显示结果
        if display:
            query.display_task_summary(summary)
        
        # 保存到文件
        if save_file:
            filename = f"task_summary_{start_id}_{end_id}.json"
            try:
                import json
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(summary, f, ensure_ascii=False, indent=2)
                print(f"💾 统计结果已保存到: {filename}")
            except Exception as e:
                print(f"⚠️ 保存文件失败: {e}")
    
    return summary


def delete_projects_by_list(project_ids_to_delete: List[int], confirm: bool = True) -> Dict[str, List[int]]:
    """
    通过列表删除指定的项目 - 便捷函数
    
    Args:
        project_ids_to_delete: 要删除的项目ID列表
        confirm: 是否需要确认，默认True
        
    Returns:
        删除结果字典
        
    Example:
        # 删除项目ID为 1, 3, 5 的项目
        result = delete_projects_by_list([1, 3, 5])
        print(f"成功删除: {result['success']}")
        print(f"删除失败: {result['failed']}")
    """
    print("🚀 Label Studio 批量项目删除工具")
    print("=" * 50)
    
    # 创建查询器实例
    query = LabelStudioProjectQuery()
    
    # 执行批量删除
    return query.delete_projects_batch(project_ids_to_delete, confirm=confirm)


def main():
    """主函数"""
    print("🚀 Label Studio 项目管理器启动...")
    
    # 创建查询器实例
    query = LabelStudioProjectQuery()
    
    # 启动交互式菜单
    return interactive_menu(query)


if __name__ == "__main__":
    # ========== 快速查询任务统计示例 ==========
    print("📊 Label Studio 项目任务统计功能演示")
    print("=" * 60)
    
    # 示例1：查询超星801到956的所有项目任务统计
    print("\n🎯 示例查询: 超星801到956项目任务统计")
    # summary = get_task_summary_range(801, 956)
    # if summary:
    #     print(f"✅ 查询成功！总任务数: {summary['total_tasks']}")
    
    # 运行主程序 - 交互式菜单
    project_list = main()
    
    # 如果需要在其他地方使用项目列表，可以这样访问：
    if project_list:
        print(f"\n🔍 可通过变量 'project_list' 访问项目数据")
        print(f"项目数量: {len(project_list)}")
    
    # ========== 任务统计查询使用示例 ==========
    # 以下是一些使用新功能的示例，取消注释即可使用：
    
    # 示例1：查询超星801到956的所有项目任务统计
    # summary = get_task_summary_range(801, 956)
    # if summary:
    #     print(f"项目总数: {summary['project_count']}")
    #     print(f"完成项目数: {summary['completed_projects']}")
    #     print(f"项目完成率: {summary['project_completion_rate']:.1f}%")
    #     print(f"总任务数: {summary['total_tasks']}")
    #     print(f"任务完成率: {summary['completion_rate']:.1f}%")
    
    # 示例2：只获取统计数据，不显示详细信息
    # summary = get_task_summary_range(801, 956, display=False, save_file=False)
    
    # 示例3：通过类实例进行更精细的控制
    # query = LabelStudioProjectQuery()
    # projects_in_range = query.get_projects_in_range(801, 956)
    # if projects_in_range:
    #     print(f"找到 {len(projects_in_range)} 个项目")
    
    # ========== 批量删除使用示例 ==========
    # 示例1：删除指定的项目ID列表
    # projects_to_delete = [1, 3, 5]  # 要删除的项目ID列表
    # result = delete_projects_by_list(projects_to_delete, confirm=True)
    # print(f"删除结果: 成功 {len(result['success'])} 个，失败 {len(result['failed'])} 个")
    
    # 示例2：不需要确认的批量删除（谨慎使用！）
    # projects_to_delete = [7, 8, 9]
    # result = delete_projects_by_list(projects_to_delete, confirm=False)

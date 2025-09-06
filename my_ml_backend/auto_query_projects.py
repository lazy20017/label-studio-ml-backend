#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Label Studio 项目查询器
功能：查询并显示Label Studio中所有项目的名称和编号
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
        print("2. 删除单个项目")
        print("3. 批量删除项目")
        print("4. 退出")
        print("-" * 60)
        
        choice = input("请选择操作 (1-4): ").strip()
        
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
                
        elif choice == "3":
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
                
        elif choice == "4":
            print("👋 感谢使用 Label Studio 项目管理器")
            break
            
        else:
            print("❌ 无效选择，请输入 1-4")
    
    return None


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
    # ========== 默认删除项目 14-23 ==========
    print("🗑️ 自动删除项目 ID 14-23...")
    projects_to_delete = list(range(30, 1000))  # 生成 [14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    result = delete_projects_by_list(projects_to_delete, confirm=True)
    print(f"删除结果: 成功 {len(result['success'])} 个，失败 {len(result['failed'])} 个")
    
    # 运行主程序
    project_list = main()
    
    # 如果需要在其他地方使用项目列表，可以这样访问：
    if project_list:
        print(f"\n🔍 可通过变量 'project_list' 访问项目数据")
        print(f"项目数量: {len(project_list)}")
        
        # 示例：打印所有项目的ID和名称
        print("\n📝 项目ID和名称列表:")
        for project in project_list:
            print(f"  - ID: {project['id']}, 名称: {project['title']}")
    
    # ========== 其他批量删除使用示例 ==========
    # 如果你需要直接通过代码删除其他项目，可以取消注释下面的代码：
    
    # 示例1：删除指定的项目ID列表
    # projects_to_delete = [1, 3, 5]  # 要删除的项目ID列表
    # result = delete_projects_by_list(projects_to_delete, confirm=True)
    # print(f"删除结果: 成功 {len(result['success'])} 个，失败 {len(result['failed'])} 个")
    
    # 示例2：不需要确认的批量删除（谨慎使用！）
    # projects_to_delete = [7, 8, 9]
    # result = delete_projects_by_list(projects_to_delete, confirm=False)
    
    # 示例3：通过类实例进行更复杂的操作
    # query = LabelStudioProjectQuery()
    # result = query.delete_projects_batch([2, 4, 6], confirm=True)

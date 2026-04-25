"""
管理工具模块 - 为AI核心提供管理数据访问能力
Admin Tools Module - Provides admin data access for AI Core
"""
from typing import Dict, Any, Optional, List
from langchain.tools import BaseTool
from pydantic import BaseModel, Field


class GetSystemStatsInput(BaseModel):
    """获取系统统计的输入参数"""
    pass  # 不需要参数


class GetSystemStatsTool(BaseTool):
    """获取系统统计信息的工具"""
    name: str = "get_system_stats"
    description: str = """获取系统统计信息，包括用户数据和决策数据。
    返回：
    - 用户统计：总用户数、活跃用户数、24小时活跃用户数、7天新增用户数
    - 决策统计：总决策数、今日决策数、本周决策数、平均选项数、决策分类统计
    
    使用场景：
    - 用户询问"系统有多少用户"
    - 用户询问"今天有多少决策"
    - 用户询问"用户活跃度如何"
    - 用户询问"系统运行状况"
    """
    args_schema: type[BaseModel] = GetSystemStatsInput
    
    def _run(self) -> Dict[str, Any]:
        """执行工具"""
        try:
            from backend.admin.admin_service import get_admin_service
            admin_service = get_admin_service()
            result = admin_service.get_system_stats()
            
            if result['success']:
                return {
                    'success': True,
                    'data': result['data']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', '获取统计信息失败')
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'获取系统统计失败: {str(e)}'
            }
    
    async def _arun(self) -> Dict[str, Any]:
        """异步执行"""
        return self._run()


class GetUsersInput(BaseModel):
    """获取用户列表的输入参数"""
    page: int = Field(default=1, description="页码，从1开始")
    page_size: int = Field(default=20, description="每页数量，最大100")
    search: Optional[str] = Field(default=None, description="搜索关键词，可搜索用户名、昵称、邮箱")


class GetUsersTool(BaseTool):
    """获取用户列表的工具"""
    name: str = "get_users"
    description: str = """获取用户列表，支持分页和搜索。
    
    参数：
    - page: 页码（默认1）
    - page_size: 每页数量（默认20，最大100）
    - search: 搜索关键词（可选，搜索用户名、昵称、邮箱）
    
    返回：
    - 用户列表：包含用户ID、用户名、昵称、邮箱、状态、创建时间等
    - 分页信息：总数、当前页、总页数
    
    使用场景：
    - 用户询问"有哪些用户"
    - 用户询问"查找某个用户"
    - 用户询问"最近注册的用户"
    """
    args_schema: type[BaseModel] = GetUsersInput
    
    def _run(self, page: int = 1, page_size: int = 20, search: Optional[str] = None) -> Dict[str, Any]:
        """执行工具"""
        try:
            from backend.admin.admin_service import get_admin_service
            admin_service = get_admin_service()
            result = admin_service.get_all_users(page, page_size, search)
            
            if result['success']:
                return {
                    'success': True,
                    'data': result['data']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', '获取用户列表失败')
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'获取用户列表失败: {str(e)}'
            }
    
    async def _arun(self, page: int = 1, page_size: int = 20, search: Optional[str] = None) -> Dict[str, Any]:
        """异步执行"""
        return self._run(page, page_size, search)


class GetUserDetailInput(BaseModel):
    """获取用户详情的输入参数"""
    user_id: str = Field(description="用户ID")


class GetUserDetailTool(BaseTool):
    """获取用户详细信息的工具"""
    name: str = "get_user_detail"
    description: str = """获取指定用户的详细信息。
    
    参数：
    - user_id: 用户ID
    
    返回：
    - 用户基本信息：用户名、昵称、邮箱、状态
    - 账户信息：创建时间、最后登录时间
    - 活动统计：决策数量、知识图谱节点数等
    
    使用场景：
    - 用户询问"某个用户的详细信息"
    - 用户询问"某个用户的活动情况"
    - 用户询问"某个用户什么时候注册的"
    """
    args_schema: type[BaseModel] = GetUserDetailInput
    
    def _run(self, user_id: str) -> Dict[str, Any]:
        """执行工具"""
        try:
            from backend.admin.admin_service import get_admin_service
            admin_service = get_admin_service()
            result = admin_service.get_user_detail(user_id)
            
            if result['success']:
                return {
                    'success': True,
                    'data': result['data']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', '用户不存在')
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'获取用户详情失败: {str(e)}'
            }
    
    async def _arun(self, user_id: str) -> Dict[str, Any]:
        """异步执行"""
        return self._run(user_id)


class GetRecentActivitiesInput(BaseModel):
    """获取最近活动的输入参数"""
    limit: int = Field(default=20, description="返回的活动数量，最大100")


class GetRecentActivitiesTool(BaseTool):
    """获取最近活动的工具"""
    name: str = "get_recent_activities"
    description: str = """获取系统最近的活动记录。
    
    参数：
    - limit: 返回的活动数量（默认20，最大100）
    
    返回：
    - 活动列表：包含用户操作、时间戳、操作类型等
    
    使用场景：
    - 用户询问"最近有什么活动"
    - 用户询问"用户最近在做什么"
    - 用户询问"系统活动情况"
    """
    args_schema: type[BaseModel] = GetRecentActivitiesInput
    
    def _run(self, limit: int = 20) -> Dict[str, Any]:
        """执行工具"""
        try:
            from backend.admin.admin_service import get_admin_service
            admin_service = get_admin_service()
            result = admin_service.get_recent_activities(limit)
            
            if result['success']:
                return {
                    'success': True,
                    'data': result['data']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', '获取活动记录失败')
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'获取活动记录失败: {str(e)}'
            }
    
    async def _arun(self, limit: int = 20) -> Dict[str, Any]:
        """异步执行"""
        return self._run(limit)


def get_admin_tools() -> List[BaseTool]:
    """获取所有管理工具"""
    return [
        GetSystemStatsTool(),
        GetUsersTool(),
        GetUserDetailTool(),
        GetRecentActivitiesTool(),
    ]

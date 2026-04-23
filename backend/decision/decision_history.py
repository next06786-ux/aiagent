"""
决策历史记录管理模块
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    import mysql.connector
    from mysql.connector import Error
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("警告: mysql-connector-python 未安装，决策历史功能将不可用")
    print("请运行: pip install mysql-connector-python")

logger = logging.getLogger(__name__)


class DecisionHistoryManager:
    """决策历史记录管理器"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        初始化历史记录管理器
        
        Args:
            db_config: 数据库配置
        """
        if not MYSQL_AVAILABLE:
            logger.warning("MySQL connector 不可用，历史记录功能已禁用")
            self.enabled = False
            return
        
        self.enabled = True
        self.db_config = db_config
        self._ensure_table_exists()
    
    def _get_connection(self):
        """获取数据库连接"""
        if not self.enabled:
            raise RuntimeError("MySQL connector 不可用")
        return mysql.connector.connect(**self.db_config)
    
    def _ensure_table_exists(self):
        """确保历史记录表存在"""
        if not self.enabled:
            return
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS decision_histories (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                session_id VARCHAR(36) NOT NULL,
                question TEXT NOT NULL,
                decision_type VARCHAR(50),
                options_data JSON NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            cursor.execute(create_table_sql)
            conn.commit()
            logger.info("决策历史表已就绪")
            
        except Error as e:
            logger.error(f"创建决策历史表失败: {e}")
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def save_history(
        self,
        history_id: str,
        user_id: str,
        session_id: str,
        question: str,
        decision_type: str,
        options_data: Dict[str, Any]
    ) -> bool:
        """
        保存决策历史
        
        Args:
            history_id: 历史记录ID
            user_id: 用户ID
            session_id: 会话ID
            question: 决策问题
            decision_type: 决策类型
            options_data: 选项数据（包含所有Agent的完整数据）
        
        Returns:
            是否保存成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            sql = """
            INSERT INTO decision_histories 
            (id, user_id, session_id, question, decision_type, options_data, completed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                history_id,
                user_id,
                session_id,
                question,
                decision_type,
                json.dumps(options_data, ensure_ascii=False),
                datetime.now()
            )
            
            cursor.execute(sql, values)
            conn.commit()
            
            logger.info(f"决策历史已保存: {history_id}")
            return True
            
        except Error as e:
            logger.error(f"保存决策历史失败: {e}")
            return False
        except Exception as e:
            logger.error(f"保存决策历史失败: {e}")
            return False
        finally:
            try:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
            except:
                pass
    
    def get_history_list(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        获取用户的历史决策列表
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            历史列表和总数
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # 查询总数
            count_sql = "SELECT COUNT(*) as total FROM decision_histories WHERE user_id = %s"
            cursor.execute(count_sql, (user_id,))
            total = cursor.fetchone()['total']
            
            # 查询列表
            list_sql = """
            SELECT 
                id,
                session_id,
                question,
                decision_type,
                created_at,
                completed_at,
                JSON_LENGTH(options_data) as options_count
            FROM decision_histories
            WHERE user_id = %s
            ORDER BY completed_at DESC, created_at DESC
            LIMIT %s OFFSET %s
            """
            
            cursor.execute(list_sql, (user_id, limit, offset))
            histories = cursor.fetchall()
            
            # 转换日期格式
            for history in histories:
                if history['created_at']:
                    history['created_at'] = history['created_at'].isoformat()
                if history['completed_at']:
                    history['completed_at'] = history['completed_at'].isoformat()
            
            return {
                'success': True,
                'histories': histories,
                'total': total
            }
            
        except Error as e:
            logger.error(f"获取历史列表失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'histories': [],
                'total': 0
            }
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def get_history_detail(self, history_id: str) -> Optional[Dict[str, Any]]:
        """
        获取历史决策详情
        
        Args:
            history_id: 历史记录ID
        
        Returns:
            历史详情数据
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            
            sql = """
            SELECT 
                id,
                user_id,
                session_id,
                question,
                decision_type,
                options_data,
                created_at,
                completed_at
            FROM decision_histories
            WHERE id = %s
            """
            
            cursor.execute(sql, (history_id,))
            history = cursor.fetchone()
            
            if history:
                # 解析 JSON 数据
                history['options_data'] = json.loads(history['options_data'])
                
                # 转换日期格式
                if history['created_at']:
                    history['created_at'] = history['created_at'].isoformat()
                if history['completed_at']:
                    history['completed_at'] = history['completed_at'].isoformat()
                
                return history
            
            return None
            
        except Error as e:
            logger.error(f"获取历史详情失败: {e}")
            return None
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()
    
    def delete_history(self, history_id: str, user_id: str) -> bool:
        """
        删除历史记录
        
        Args:
            history_id: 历史记录ID
            user_id: 用户ID（用于权限验证）
        
        Returns:
            是否删除成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            sql = "DELETE FROM decision_histories WHERE id = %s AND user_id = %s"
            cursor.execute(sql, (history_id, user_id))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"历史记录已删除: {history_id}")
                return True
            else:
                logger.warning(f"历史记录不存在或无权限: {history_id}")
                return False
            
        except Error as e:
            logger.error(f"删除历史记录失败: {e}")
            return False
        finally:
            if conn.is_connected():
                cursor.close()
                conn.close()

"""
数据同步客户端
从主服务器同步用户对话数据到GPU服务器进行训练
"""
import os
import json
import asyncio
import httpx
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class SyncConfig:
    """同步配置"""
    # 主服务器地址
    main_server_url: str = os.environ.get("MAIN_SERVER_URL", "http://localhost:8080")
    main_server_api_key: str = os.environ.get("MAIN_SERVER_API_KEY", "")
    
    # GPU服务器地址（本地）
    gpu_server_url: str = "http://localhost:8000"
    gpu_server_api_key: str = os.environ.get("GPU_API_KEY", "your-secret-api-key-change-me")
    
    # 同步设置
    min_conversations: int = 20  # 最少对话数才触发训练
    sync_interval_hours: int = 24  # 同步间隔（小时）
    
    # 数据目录
    data_dir: str = os.environ.get("DATA_DIR", "/root/autodl-tmp")
    sync_status_file: str = os.path.join(data_dir, "sync_status.json")


class DataSyncClient:
    """数据同步客户端"""
    
    def __init__(self, config: SyncConfig = None):
        self.config = config or SyncConfig()
        self.sync_status = self._load_sync_status()
    
    def _load_sync_status(self) -> Dict:
        """加载同步状态"""
        if os.path.exists(self.config.sync_status_file):
            with open(self.config.sync_status_file, 'r') as f:
                return json.load(f)
        return {"users": {}, "last_full_sync": None}
    
    def _save_sync_status(self):
        """保存同步状态"""
        os.makedirs(os.path.dirname(self.config.sync_status_file), exist_ok=True)
        with open(self.config.sync_status_file, 'w') as f:
            json.dump(self.sync_status, f, indent=2, ensure_ascii=False)
    
    async def fetch_user_conversations(self, user_id: str) -> List[Dict]:
        """从主服务器获取用户对话数据"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.get(
                    f"{self.config.main_server_url}/api/conversations/{user_id}",
                    headers={"X-API-Key": self.config.main_server_api_key}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("conversations", [])
                else:
                    print(f"❌ 获取用户 {user_id} 对话失败: {response.status_code}")
                    return []
            except Exception as e:
                print(f"❌ 连接主服务器失败: {e}")
                return []
    
    async def fetch_users_needing_training(self) -> List[str]:
        """获取需要训练的用户列表"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.config.main_server_url}/api/users/training-candidates",
                    headers={"X-API-Key": self.config.main_server_api_key}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("users", [])
                else:
                    print(f"❌ 获取训练候选用户失败: {response.status_code}")
                    return []
            except Exception as e:
                print(f"❌ 连接主服务器失败: {e}")
                return []
    
    async def trigger_training(self, user_id: str, conversations: List[Dict]) -> Dict:
        """触发GPU服务器训练"""
        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                response = await client.post(
                    f"{self.config.gpu_server_url}/train",
                    json={
                        "user_id": user_id,
                        "conversations": conversations
                    },
                    headers={"X-API-Key": self.config.gpu_server_api_key}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"训练请求失败: {response.status_code}"}
            except Exception as e:
                return {"error": f"连接GPU服务器失败: {e}"}
    
    async def check_training_status(self, user_id: str) -> Dict:
        """检查训练状态"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    f"{self.config.gpu_server_url}/train/status/{user_id}",
                    headers={"X-API-Key": self.config.gpu_server_api_key}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"状态查询失败: {response.status_code}"}
            except Exception as e:
                return {"error": f"连接GPU服务器失败: {e}"}
    
    async def sync_and_train_user(self, user_id: str) -> Dict:
        """同步并训练单个用户"""
        print(f"\n{'='*50}")
        print(f"🔄 同步用户: {user_id}")
        print(f"{'='*50}")
        
        # 1. 获取对话数据
        print("📥 获取对话数据...")
        conversations = await self.fetch_user_conversations(user_id)
        
        if not conversations:
            return {"user_id": user_id, "status": "no_data", "message": "没有对话数据"}
        
        print(f"✅ 获取到 {len(conversations)} 条对话")
        
        # 2. 检查数据量
        if len(conversations) < self.config.min_conversations:
            return {
                "user_id": user_id,
                "status": "insufficient_data",
                "message": f"数据量不足: {len(conversations)} < {self.config.min_conversations}"
            }
        
        # 3. 检查是否需要重新训练
        user_status = self.sync_status["users"].get(user_id, {})
        last_count = user_status.get("conversation_count", 0)
        
        if len(conversations) <= last_count:
            return {
                "user_id": user_id,
                "status": "no_new_data",
                "message": f"没有新数据: {len(conversations)} <= {last_count}"
            }
        
        # 4. 触发训练
        print("🚀 触发训练...")
        result = await self.trigger_training(user_id, conversations)
        
        if "error" not in result:
            # 更新同步状态
            self.sync_status["users"][user_id] = {
                "last_sync": datetime.now().isoformat(),
                "conversation_count": len(conversations),
                "training_triggered": True
            }
            self._save_sync_status()
        
        return {
            "user_id": user_id,
            "status": "training_started" if "error" not in result else "error",
            "conversations": len(conversations),
            "result": result
        }
    
    async def sync_all_users(self) -> List[Dict]:
        """同步所有需要训练的用户"""
        print("\n" + "="*60)
        print("🔄 开始全量同步")
        print("="*60)
        
        # 获取需要训练的用户
        users = await self.fetch_users_needing_training()
        
        if not users:
            print("ℹ️ 没有需要训练的用户")
            return []
        
        print(f"📋 找到 {len(users)} 个待训练用户")
        
        results = []
        for user_id in users:
            result = await self.sync_and_train_user(user_id)
            results.append(result)
            
            # 如果开始训练，等待一段时间再处理下一个
            if result.get("status") == "training_started":
                print("⏳ 等待训练完成...")
                await self._wait_for_training(user_id)
        
        # 更新全量同步时间
        self.sync_status["last_full_sync"] = datetime.now().isoformat()
        self._save_sync_status()
        
        return results
    
    async def _wait_for_training(self, user_id: str, timeout: int = 3600):
        """等待训练完成"""
        start_time = datetime.now()
        
        while True:
            status = await self.check_training_status(user_id)
            
            if not status.get("is_training", False):
                print(f"✅ 用户 {user_id} 训练完成")
                return status
            
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                print(f"⚠️ 用户 {user_id} 训练超时")
                return {"status": "timeout"}
            
            print(f"⏳ 训练中... ({int(elapsed)}s)")
            await asyncio.sleep(30)


class ScheduledSyncRunner:
    """定时同步运行器"""
    
    def __init__(self, config: SyncConfig = None):
        self.config = config or SyncConfig()
        self.client = DataSyncClient(config)
        self.running = False
    
    async def run(self):
        """运行定时同步"""
        self.running = True
        print(f"🕐 定时同步启动，间隔: {self.config.sync_interval_hours} 小时")
        
        while self.running:
            try:
                await self.client.sync_all_users()
            except Exception as e:
                print(f"❌ 同步出错: {e}")
            
            # 等待下次同步
            await asyncio.sleep(self.config.sync_interval_hours * 3600)
    
    def stop(self):
        """停止同步"""
        self.running = False


# 命令行工具
async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="数据同步客户端")
    parser.add_argument("--user", help="同步指定用户")
    parser.add_argument("--all", action="store_true", help="同步所有用户")
    parser.add_argument("--daemon", action="store_true", help="后台运行定时同步")
    parser.add_argument("--status", help="查询用户训练状态")
    
    args = parser.parse_args()
    
    client = DataSyncClient()
    
    if args.user:
        result = await client.sync_and_train_user(args.user)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.all:
        results = await client.sync_all_users()
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    elif args.daemon:
        runner = ScheduledSyncRunner()
        await runner.run()
    
    elif args.status:
        status = await client.check_training_status(args.status)
        print(json.dumps(status, indent=2, ensure_ascii=False))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())

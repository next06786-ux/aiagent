"""
数据备份和恢复管理器
自动备份用户数据、模型、配置等
"""
import os
import shutil
import json
import zipfile
from datetime import datetime
from typing import List, Dict
import glob


class BackupManager:
    """备份管理器"""
    
    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
        
        # 需要备份的目录和文件
        self.backup_targets = {
            "database": "./backend/lifeswarm.db",
            "rag_data": "./backend/data/production_rag",
            "lora_models": "./models/lora",
            "decisions": "./data/decisions",
            "simulations": "./data/simulations",
            "feedback": "./data/decision_feedback",
            "config": "./data/scheduler_config.json"
        }
    
    def create_backup(self, backup_name: str = None) -> str:
        """
        创建完整备份
        
        Args:
            backup_name: 备份名称（可选）
        
        Returns:
            备份文件路径
        """
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = os.path.join(self.backup_dir, f"{backup_name}.zip")
        
        print(f"\n{'='*60}")
        print(f"创建备份: {backup_name}")
        print(f"{'='*60}\n")
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for target_name, target_path in self.backup_targets.items():
                if os.path.exists(target_path):
                    if os.path.isfile(target_path):
                        # 备份单个文件
                        zipf.write(target_path, arcname=f"{target_name}/{os.path.basename(target_path)}")
                        print(f"✅ 已备份: {target_name} (文件)")
                    elif os.path.isdir(target_path):
                        # 备份整个目录
                        for root, dirs, files in os.walk(target_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.join(
                                    target_name,
                                    os.path.relpath(file_path, target_path)
                                )
                                zipf.write(file_path, arcname=arcname)
                        print(f"✅ 已备份: {target_name} (目录)")
                else:
                    print(f"⏭️  跳过: {target_name} (不存在)")
            
            # 添加备份元数据
            metadata = {
                "backup_name": backup_name,
                "created_at": datetime.now().isoformat(),
                "targets": list(self.backup_targets.keys())
            }
            zipf.writestr("metadata.json", json.dumps(metadata, indent=2))
        
        file_size = os.path.getsize(backup_path) / (1024 * 1024)
        
        print(f"\n{'='*60}")
        print(f"✅ 备份完成!")
        print(f"   文件: {backup_path}")
        print(f"   大小: {file_size:.2f} MB")
        print(f"{'='*60}\n")
        
        return backup_path
    
    def restore_backup(self, backup_path: str, targets: List[str] = None):
        """
        恢复备份
        
        Args:
            backup_path: 备份文件路径
            targets: 要恢复的目标列表（None表示全部）
        """
        if not os.path.exists(backup_path):
            print(f"❌ 备份文件不存在: {backup_path}")
            return
        
        print(f"\n{'='*60}")
        print(f"恢复备份: {backup_path}")
        print(f"{'='*60}\n")
        
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            # 读取元数据
            try:
                metadata_str = zipf.read("metadata.json").decode('utf-8')
                metadata = json.loads(metadata_str)
                print(f"备份信息:")
                print(f"  名称: {metadata['backup_name']}")
                print(f"  创建时间: {metadata['created_at']}")
                print()
            except:
                print("⚠️  无法读取备份元数据\n")
            
            # 确定要恢复的目标
            if targets is None:
                targets = list(self.backup_targets.keys())
            
            for target_name in targets:
                if target_name not in self.backup_targets:
                    print(f"⏭️  跳过: {target_name} (未知目标)")
                    continue
                
                target_path = self.backup_targets[target_name]
                
                # 提取该目标的所有文件
                target_files = [f for f in zipf.namelist() if f.startswith(f"{target_name}/")]
                
                if not target_files:
                    print(f"⏭️  跳过: {target_name} (备份中不存在)")
                    continue
                
                # 创建目标目录
                if os.path.isdir(target_path) or target_name in ["rag_data", "lora_models", "decisions", "simulations", "feedback"]:
                    os.makedirs(target_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                # 提取文件
                for file_path in target_files:
                    if file_path.endswith('/'):
                        continue
                    
                    # 计算目标路径
                    rel_path = file_path[len(f"{target_name}/"):]
                    if os.path.isdir(target_path):
                        dest_path = os.path.join(target_path, rel_path)
                    else:
                        dest_path = target_path
                    
                    # 创建目录
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    # 提取文件
                    with zipf.open(file_path) as source, open(dest_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                
                print(f"✅ 已恢复: {target_name}")
        
        print(f"\n{'='*60}")
        print(f"✅ 恢复完成!")
        print(f"{'='*60}\n")
    
    def list_backups(self) -> List[Dict]:
        """列出所有备份"""
        backups = []
        
        for backup_file in glob.glob(os.path.join(self.backup_dir, "*.zip")):
            file_size = os.path.getsize(backup_file) / (1024 * 1024)
            created_time = datetime.fromtimestamp(os.path.getctime(backup_file))
            
            # 尝试读取元数据
            try:
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    metadata_str = zipf.read("metadata.json").decode('utf-8')
                    metadata = json.loads(metadata_str)
            except:
                metadata = {}
            
            backups.append({
                "file": backup_file,
                "name": os.path.basename(backup_file),
                "size_mb": file_size,
                "created_at": created_time.isoformat(),
                "metadata": metadata
            })
        
        # 按创建时间排序
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return backups
    
    def delete_old_backups(self, keep_count: int = 5):
        """删除旧备份，只保留最新的N个"""
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            print(f"✅ 备份数量 ({len(backups)}) 在限制内 ({keep_count})")
            return
        
        # 删除旧备份
        to_delete = backups[keep_count:]
        
        print(f"\n删除 {len(to_delete)} 个旧备份...")
        for backup in to_delete:
            os.remove(backup["file"])
            print(f"  🗑️  {backup['name']}")
        
        print(f"✅ 清理完成，保留最新 {keep_count} 个备份\n")
    
    def auto_backup(self, keep_count: int = 5) -> str:
        """自动备份（创建新备份并清理旧备份）"""
        backup_path = self.create_backup()
        self.delete_old_backups(keep_count)
        return backup_path


# 测试代码
if __name__ == "__main__":
    manager = BackupManager()
    
    print("="*60)
    print("备份管理器测试")
    print("="*60)
    
    # 列出现有备份
    print("\n1. 列出现有备份:")
    backups = manager.list_backups()
    if backups:
        for backup in backups:
            print(f"  - {backup['name']} ({backup['size_mb']:.2f} MB)")
    else:
        print("  (无备份)")
    
    # 创建新备份
    print("\n2. 创建新备份:")
    backup_path = manager.create_backup()
    
    # 再次列出备份
    print("\n3. 更新后的备份列表:")
    backups = manager.list_backups()
    for backup in backups:
        print(f"  - {backup['name']} ({backup['size_mb']:.2f} MB)")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

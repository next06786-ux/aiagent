"""
系统管理脚本
提供系统维护、备份、健康检查等功能
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def show_menu():
    """显示菜单"""
    print("\n" + "="*70)
    print("  LifeSim AI 系统管理")
    print("="*70)
    print("\n功能菜单:")
    print("  1. 系统健康检查")
    print("  2. 性能统计")
    print("  3. 创建备份")
    print("  4. 列出备份")
    print("  5. 恢复备份")
    print("  6. 清理旧备份")
    print("  7. 查看系统信息")
    print("  0. 退出")
    print("\n" + "="*70)


def health_check():
    """健康检查"""
    from backend.utils.health_checker import HealthChecker
    
    checker = HealthChecker()
    results = checker.check_all()
    
    # 保存结果
    import json
    os.makedirs("./data", exist_ok=True)
    with open("./data/health_check.json", 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\n✅ 健康检查结果已保存到: ./data/health_check.json")


def performance_stats():
    """性能统计"""
    from backend.utils.performance_monitor import get_monitor
    
    monitor = get_monitor()
    stats = monitor.get_statistics()
    
    print("\n" + "="*60)
    print("性能统计")
    print("="*60)
    print(f"\n总调用数: {stats['total_calls']}")
    print(f"慢查询数: {stats['slow_queries']}")
    print(f"错误总数: {stats['total_errors']}")
    
    print(f"\n系统指标:")
    print(f"  CPU: {stats['system']['cpu_percent']:.1f}%")
    print(f"  内存: {stats['system']['memory_percent']:.1f}%")
    print(f"  已用内存: {stats['system']['memory_used_mb']:.1f} MB")
    print(f"  磁盘: {stats['system']['disk_percent']:.1f}%")
    
    if stats['endpoints']:
        print(f"\n端点统计:")
        for endpoint, data in stats['endpoints'].items():
            print(f"\n  {endpoint}:")
            print(f"    调用次数: {data['calls']}")
            print(f"    平均耗时: {data['avg_duration']:.3f}s")
            print(f"    最小耗时: {data['min_duration']:.3f}s")
            print(f"    最大耗时: {data['max_duration']:.3f}s")
            print(f"    错误次数: {data['errors']}")
    
    # 保存报告
    monitor.save_report()


def create_backup():
    """创建备份"""
    from backend.utils.backup_manager import BackupManager
    
    manager = BackupManager()
    backup_path = manager.auto_backup()
    
    print(f"\n✅ 备份已创建: {backup_path}")


def list_backups():
    """列出备份"""
    from backend.utils.backup_manager import BackupManager
    
    manager = BackupManager()
    backups = manager.list_backups()
    
    print("\n" + "="*60)
    print("备份列表")
    print("="*60)
    
    if not backups:
        print("\n(无备份)")
        return
    
    for i, backup in enumerate(backups, 1):
        print(f"\n{i}. {backup['name']}")
        print(f"   大小: {backup['size_mb']:.2f} MB")
        print(f"   创建时间: {backup['created_at']}")
        if backup.get('metadata'):
            print(f"   备份项: {', '.join(backup['metadata'].get('targets', []))}")


def restore_backup():
    """恢复备份"""
    from backend.utils.backup_manager import BackupManager
    
    manager = BackupManager()
    backups = manager.list_backups()
    
    if not backups:
        print("\n❌ 没有可用的备份")
        return
    
    # 显示备份列表
    print("\n可用备份:")
    for i, backup in enumerate(backups, 1):
        print(f"  {i}. {backup['name']} ({backup['size_mb']:.2f} MB)")
    
    # 选择备份
    try:
        choice = int(input("\n请选择要恢复的备份编号 (0取消): "))
        if choice == 0:
            print("已取消")
            return
        
        if 1 <= choice <= len(backups):
            backup = backups[choice - 1]
            
            # 确认
            confirm = input(f"\n⚠️  确认要恢复备份 '{backup['name']}' 吗？这将覆盖现有数据！(yes/no): ")
            if confirm.lower() == 'yes':
                manager.restore_backup(backup['file'])
                print("\n✅ 备份恢复完成")
            else:
                print("已取消")
        else:
            print("❌ 无效的选择")
    except ValueError:
        print("❌ 请输入有效的数字")
    except KeyboardInterrupt:
        print("\n已取消")


def clean_old_backups():
    """清理旧备份"""
    from backend.utils.backup_manager import BackupManager
    
    manager = BackupManager()
    
    try:
        keep_count = int(input("\n保留最新的几个备份？(默认5): ") or "5")
        manager.delete_old_backups(keep_count)
    except ValueError:
        print("❌ 请输入有效的数字")
    except KeyboardInterrupt:
        print("\n已取消")


def system_info():
    """系统信息"""
    import psutil
    import platform
    
    print("\n" + "="*60)
    print("系统信息")
    print("="*60)
    
    print(f"\n操作系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {platform.python_version()}")
    
    print(f"\nCPU:")
    print(f"  核心数: {psutil.cpu_count()}")
    print(f"  使用率: {psutil.cpu_percent(interval=1)}%")
    
    mem = psutil.virtual_memory()
    print(f"\n内存:")
    print(f"  总量: {mem.total / (1024**3):.2f} GB")
    print(f"  已用: {mem.used / (1024**3):.2f} GB")
    print(f"  可用: {mem.available / (1024**3):.2f} GB")
    print(f"  使用率: {mem.percent}%")
    
    disk = psutil.disk_usage('/')
    print(f"\n磁盘:")
    print(f"  总量: {disk.total / (1024**3):.2f} GB")
    print(f"  已用: {disk.used / (1024**3):.2f} GB")
    print(f"  可用: {disk.free / (1024**3):.2f} GB")
    print(f"  使用率: {disk.percent}%")
    
    # 检查关键目录
    print(f"\n数据目录:")
    dirs_to_check = [
        ("数据库", "./backend/lifeswarm.db"),
        ("RAG数据", "./backend/data/production_rag"),
        ("LoRA模型", "./models/lora"),
        ("决策记录", "./data/simulations"),
        ("备份", "./backups")
    ]
    
    for name, path in dirs_to_check:
        if os.path.exists(path):
            if os.path.isfile(path):
                size = os.path.getsize(path) / (1024**2)
                print(f"  {name}: {size:.2f} MB")
            else:
                # 计算目录大小
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        total_size += os.path.getsize(filepath)
                print(f"  {name}: {total_size / (1024**2):.2f} MB")
        else:
            print(f"  {name}: (不存在)")


def main():
    """主函数"""
    while True:
        show_menu()
        
        try:
            choice = input("\n请选择功能 (0-7): ").strip()
            
            if choice == '0':
                print("\n再见！")
                break
            elif choice == '1':
                health_check()
            elif choice == '2':
                performance_stats()
            elif choice == '3':
                create_backup()
            elif choice == '4':
                list_backups()
            elif choice == '5':
                restore_backup()
            elif choice == '6':
                clean_old_backups()
            elif choice == '7':
                system_info()
            else:
                print("\n❌ 无效的选择，请重试")
            
            input("\n按回车键继续...")
            
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            input("\n按回车键继续...")


if __name__ == "__main__":
    main()

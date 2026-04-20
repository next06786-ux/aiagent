"""
数据库初始化脚本
创建所有必要的表和索引
"""

import mysql.connector
from mysql.connector import Error
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self, host='localhost', user='lifeswarm', password='lifeswarm123', database='lifeswarm'):
        """初始化数据库连接"""
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
    
    def connect(self):
        """连接到数据库"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4'
            )
            logger.info(f"Connected to database {self.database}")
            return True
        except Error as e:
            logger.error(f"Error connecting to database: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Disconnected from database")
    
    def execute_query(self, query):
        """执行查询"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
            logger.info(f"Query executed successfully")
            return True
        except Error as e:
            logger.error(f"Error executing query: {e}")
            self.connection.rollback()
            return False
    
    def create_tables(self):
        """创建所有表"""
        
        # 1. 用户表
        users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(255),
            email VARCHAR(255),
            password_hash VARCHAR(255),
            phone VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_email (email)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        # 2. 传感器数据表
        sensor_data_table = """
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id VARCHAR(255) NOT NULL,
            timestamp DATETIME NOT NULL,
            heart_rate FLOAT,
            steps INT,
            accelerometer_x FLOAT,
            accelerometer_y FLOAT,
            accelerometer_z FLOAT,
            gyroscope_x FLOAT,
            gyroscope_y FLOAT,
            gyroscope_z FLOAT,
            light FLOAT,
            pressure FLOAT,
            temperature FLOAT,
            blood_oxygen FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_timestamp (user_id, timestamp),
            INDEX idx_timestamp (timestamp),
            INDEX idx_user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        # 3. 健康数据表
        health_data_table = """
        CREATE TABLE IF NOT EXISTS health_data (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id VARCHAR(255) NOT NULL,
            timestamp DATETIME NOT NULL,
            sleep_hours FLOAT,
            sleep_quality FLOAT,
            exercise_minutes INT,
            calories_burned FLOAT,
            active_minutes INT,
            blood_pressure_systolic FLOAT,
            blood_pressure_diastolic FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_timestamp (user_id, timestamp),
            INDEX idx_user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        # 4. 应用使用数据表
        app_usage_table = """
        CREATE TABLE IF NOT EXISTS app_usage (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id VARCHAR(255) NOT NULL,
            app_name VARCHAR(255),
            app_category VARCHAR(100),
            usage_duration_minutes FLOAT,
            launch_count INT,
            timestamp DATETIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_timestamp (user_id, timestamp),
            INDEX idx_user_id (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        # 5. 每日统计表
        daily_statistics_table = """
        CREATE TABLE IF NOT EXISTS daily_statistics (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id VARCHAR(255) NOT NULL,
            date DATE NOT NULL,
            heart_rate_avg FLOAT,
            heart_rate_min FLOAT,
            heart_rate_max FLOAT,
            steps_total INT,
            temperature_avg FLOAT,
            blood_oxygen_avg FLOAT,
            sleep_hours FLOAT,
            exercise_minutes INT,
            data_points INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_user_date (user_id, date),
            INDEX idx_user_id (user_id),
            INDEX idx_date (date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        # 6. 决策记录表
        decisions_table = """
        CREATE TABLE IF NOT EXISTS decisions (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id VARCHAR(255) NOT NULL,
            decision_id VARCHAR(255) UNIQUE NOT NULL,
            decision_type VARCHAR(100),
            recommendation TEXT,
            reasoning TEXT,
            confidence FLOAT,
            expected_impact JSON,
            user_feedback TEXT,
            actual_impact JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        # 7. 强化学习训练记录表
        rl_training_table = """
        CREATE TABLE IF NOT EXISTS rl_training (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id VARCHAR(255) NOT NULL,
            episode INT,
            state JSON,
            action VARCHAR(255),
            reward FLOAT,
            q_value FLOAT,
            strategy VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_episode (episode)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        # 8. 涌现事件表
        emergence_events_table = """
        CREATE TABLE IF NOT EXISTS emergence_events (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id VARCHAR(255) NOT NULL,
            event_id VARCHAR(255) UNIQUE NOT NULL,
            emergence_type VARCHAR(100),
            description TEXT,
            involved_metrics JSON,
            strength FLOAT,
            confidence FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_type (emergence_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        # 9. 用户反馈表
        user_feedback_table = """
        CREATE TABLE IF NOT EXISTS user_feedback (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id VARCHAR(255) NOT NULL,
            feedback_type VARCHAR(100),
            rating INT,
            comment TEXT,
            related_decision_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_id (user_id),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        tables = [
            ("users", users_table),
            ("sensor_data", sensor_data_table),
            ("health_data", health_data_table),
            ("app_usage", app_usage_table),
            ("daily_statistics", daily_statistics_table),
            ("decisions", decisions_table),
            ("rl_training", rl_training_table),
            ("emergence_events", emergence_events_table),
            ("user_feedback", user_feedback_table)
        ]
        
        for table_name, table_query in tables:
            logger.info(f"Creating table: {table_name}")
            if self.execute_query(table_query):
                logger.info(f"✓ Table {table_name} created successfully")
            else:
                logger.error(f"✗ Failed to create table {table_name}")
    
    def create_indexes(self):
        """创建额外的索引以优化查询"""
        
        indexes = [
            # 传感器数据索引
            "CREATE INDEX IF NOT EXISTS idx_sensor_user_date ON sensor_data(user_id, DATE(timestamp));",
            "CREATE INDEX IF NOT EXISTS idx_sensor_heart_rate ON sensor_data(heart_rate);",
            
            # 健康数据索引
            "CREATE INDEX IF NOT EXISTS idx_health_user_date ON health_data(user_id, DATE(timestamp));",
            
            # 应用使用索引
            "CREATE INDEX IF NOT EXISTS idx_app_category ON app_usage(app_category);",
            
            # 决策索引
            "CREATE INDEX IF NOT EXISTS idx_decision_type ON decisions(decision_type);",
            "CREATE INDEX IF NOT EXISTS idx_decision_confidence ON decisions(confidence);",
            
            # 强化学习索引
            "CREATE INDEX IF NOT EXISTS idx_rl_user_episode ON rl_training(user_id, episode);",
            
            # 涌现事件索引
            "CREATE INDEX IF NOT EXISTS idx_emergence_strength ON emergence_events(strength);",
        ]
        
        for index_query in indexes:
            logger.info(f"Creating index: {index_query[:50]}...")
            self.execute_query(index_query)
    
    def initialize(self):
        """初始化数据库"""
        logger.info("Starting database initialization...")
        
        if not self.connect():
            logger.error("Failed to connect to database")
            return False
        
        try:
            self.create_tables()
            self.create_indexes()
            logger.info("✓ Database initialization completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            return False
        finally:
            self.disconnect()


def main():
    """主函数"""
    import sys
    import os
    from dotenv import load_dotenv
    
    # 加载环境变量
    load_dotenv()
    
    # 优先从环境变量读取，其次命令行参数，最后默认值
    host = os.getenv('MYSQL_HOST') or (sys.argv[1] if len(sys.argv) > 1 else 'localhost')
    user = os.getenv('MYSQL_USER') or (sys.argv[2] if len(sys.argv) > 2 else 'lifeswarm')
    password = os.getenv('MYSQL_PASSWORD') or (sys.argv[3] if len(sys.argv) > 3 else 'lifeswarm123')
    database = os.getenv('MYSQL_DATABASE') or (sys.argv[4] if len(sys.argv) > 4 else 'lifeswarm')
    
    logger.info(f"Initializing database: {database} on {host}")
    
    initializer = DatabaseInitializer(host, user, password, database)
    success = initializer.initialize()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


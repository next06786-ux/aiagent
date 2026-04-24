-- 为 conversation_history 表添加 Agent 对话相关字段
-- 执行时间: 2026-04-24

-- 添加 agent_type 字段
ALTER TABLE conversation_history 
ADD COLUMN agent_type VARCHAR(20) AFTER user_id,
ADD INDEX idx_agent_type (agent_type);

-- 添加 conversation_id 字段
ALTER TABLE conversation_history 
ADD COLUMN conversation_id VARCHAR(100) AFTER agent_type,
ADD INDEX idx_conversation_id (conversation_id);

-- 添加 conversation_title 字段
ALTER TABLE conversation_history 
ADD COLUMN conversation_title VARCHAR(200) AFTER conversation_id;

-- 添加 retrieval_stats 字段
ALTER TABLE conversation_history 
ADD COLUMN retrieval_stats JSON AFTER context;

-- 验证字段是否添加成功
DESCRIBE conversation_history;

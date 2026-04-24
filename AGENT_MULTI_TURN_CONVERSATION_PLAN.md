# Agent多轮对话改进方案

## 问题分析

当前WebSocket Agent对话的问题：
1. **后端**：处理完一条消息后就结束，没有循环等待下一条消息
2. **前端**：每次发送消息都创建新的WebSocket连接，收到响应后立即关闭
3. **结果**：每次对话都是独立的，无法实现真正的多轮对话

## 改进方案

### 后端改进（main.py）

将单次处理改为循环处理，参考 `/ws/chat` 的实现：

```python
@app.websocket("/ws/agent-chat")
async def websocket_agent_chat(websocket: WebSocket):
    """支持多轮对话的WebSocket Agent"""
    import uuid
    session_id = f"agent_session_{uuid.uuid4().hex[:16]}"
    user_id = None
    agent = None  # 复用同一个Agent实例
    agent_type = None
    
    try:
        await websocket.accept()
        print(f"✅ [WebSocket Agent] 连接已建立: {session_id}")
        
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id
        })
        
        # ===== 主循环：持续接收消息 =====
        while True:
            try:
                # 接收客户端消息
                message_data = await websocket.receive_text()
                request_data = json.loads(message_data)
                
                # 第一次消息：验证token并创建Agent
                if user_id is None:
                    from backend.auth.auth_service import get_auth_service
                    auth_service = get_auth_service()
                    token = request_data.get("token", "")
                    user_id = auth_service.verify_token(token)
                    
                    if not user_id:
                        await websocket.send_json({
                            "type": "error",
                            "error": "Token无效或已过期"
                        })
                        break
                    
                    # 注册WebSocket连接
                    await ws_manager.connect(websocket, user_id, session_id)
                    
                    # 获取Agent类型
                    agent_type = request_data.get("agent_type", "relationship")
                    
                    # 创建Agent（只创建一次，后续复用）
                    agent = await _create_agent_with_websocket(
                        user_id, agent_type, session_id
                    )
                
                # 获取消息内容
                message = request_data.get("message", "")
                if not message:
                    await websocket.send_json({
                        "type": "error",
                        "error": "消息不能为空"
                    })
                    continue  # 继续等待下一条消息
                
                print(f"📨 [WebSocket Agent] 收到消息: {message[:50]}...")
                
                # 处理消息
                result = await _process_agent_message(agent, message, user_id, session_id)
                
                # 发送响应
                await ws_manager.send_message(user_id, session_id, {
                    "type": "response",
                    "content": result['response'],
                    "metadata": {
                        "mode": result.get('mode'),
                        "agent_used": result.get('agent_used'),
                        "tool_calls": result.get('tool_calls', []),
                        "retrieval_stats": result.get('retrieval_stats', {})
                    },
                    "timestamp": datetime.now().isoformat()
                })
                
                print(f"✅ [WebSocket Agent] 消息处理完成，等待下一条消息...")
                
            except WebSocketDisconnect:
                print(f"✓ [WebSocket Agent] 客户端主动断开连接")
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "error": "消息格式错误"
                })
                continue
            except Exception as e:
                print(f"❌ [WebSocket Agent] 处理消息失败: {e}")
                import traceback
                traceback.print_exc()
                await websocket.send_json({
                    "type": "error",
                    "error": str(e)
                })
                continue  # 继续等待下一条消息
    
    except WebSocketDisconnect:
        print(f"✓ [WebSocket Agent] 连接已断开: {session_id}")
    except Exception as e:
        print(f"❌ [WebSocket Agent] 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if user_id:
            ws_manager.disconnect(user_id, session_id)
        print(f"🔌 [WebSocket Agent] 连接清理完成: {session_id}")


async def _create_agent_with_websocket(user_id: str, agent_type: str, session_id: str):
    """创建带WebSocket回调的Agent"""
    from backend.agents.langchain_specialized_agents import create_langchain_agent
    from backend.learning.rag_manager import RAGManager
    from backend.learning.unified_hybrid_retrieval import UnifiedHybridRetrieval
    from backend.agents.mcp_integration import MCPHost
    from backend.agents.specialized_mcp_servers import (
        WebSearchMCPServer,
        RelationshipMCPServer,
        EducationMCPServer
    )
    import os
    
    # 获取系统实例
    llm_service = get_or_init_llm_service()
    rag_system = RAGManager.get_system(user_id)
    retrieval_system = UnifiedHybridRetrieval(user_id)
    
    # 创建MCP Host
    mcp_host = MCPHost(user_id=user_id)
    
    # 注册工具
    search_api_key = os.getenv("QWEN_SEARCH_API_KEY")
    search_host = os.getenv("QWEN_SEARCH_HOST")
    
    mcp_host.register_server(WebSearchMCPServer(
        api_key=search_api_key,
        host=search_host,
        workspace=os.getenv("QWEN_SEARCH_WORKSPACE", "default"),
        service_id=os.getenv("QWEN_SEARCH_SERVICE_ID", "ops-web-search-001")
    ))
    
    if agent_type == 'relationship':
        mcp_host.register_server(RelationshipMCPServer())
    elif agent_type == 'education':
        mcp_host.register_server(EducationMCPServer())
    
    # 创建WebSocket回调
    loop = asyncio.get_event_loop()
    
    def sync_callback_wrapper(event_type: str, data: dict):
        """同步包装器"""
        async def send_callback():
            if event_type == "tool_call":
                status = data.get("status")
                tool_name = data.get("tool_name")
                
                if status == "running":
                    await ws_manager.send_message(user_id, session_id, {
                        "type": "tool_start",
                        "tool_name": tool_name,
                        "server_name": "Unknown",
                        "timestamp": datetime.now().isoformat()
                    })
                elif status == "completed":
                    await ws_manager.send_message(user_id, session_id, {
                        "type": "tool_complete",
                        "tool_name": tool_name,
                        "server_name": "Unknown",
                        "result": data.get("output", "")[:100],
                        "timestamp": datetime.now().isoformat()
                    })
                elif status == "error":
                    await ws_manager.send_message(user_id, session_id, {
                        "type": "tool_failed",
                        "tool_name": tool_name,
                        "server_name": "Unknown",
                        "error": data.get("error", ""),
                        "timestamp": datetime.now().isoformat()
                    })
            
            elif event_type == "memory_retrieval":
                retrieval_type = data.get("type")
                
                if retrieval_type == "retrieval_start":
                    await ws_manager.send_message(user_id, session_id, {
                        "type": "retrieval_start",
                        "query": data.get("query"),
                        "reason": data.get("reason"),
                        "agent_type": data.get("agent_type"),
                        "timestamp": data.get("timestamp")
                    })
                elif retrieval_type == "retrieval_complete":
                    await ws_manager.send_message(user_id, session_id, {
                        "type": "retrieval_complete",
                        "query": data.get("query"),
                        "reason": data.get("reason"),
                        "results_count": data.get("results_count"),
                        "sources": data.get("sources", []),
                        "timestamp": data.get("timestamp")
                    })
        
        try:
            future = asyncio.run_coroutine_threadsafe(send_callback(), loop)
            return future.result(timeout=0.5)
        except Exception as e:
            print(f"⚠️  回调执行失败: {event_type} - {e}")
    
    # 创建Agent
    agent = create_langchain_agent(
        agent_type=agent_type,
        user_id=user_id,
        llm_service=llm_service,
        rag_system=rag_system,
        retrieval_system=retrieval_system,
        use_workflow=True,
        mcp_host=mcp_host,
        websocket_callback=sync_callback_wrapper
    )
    
    await agent.initialize()
    
    print(f"✅ [WebSocket Agent] Agent创建完成: {agent_type}")
    return agent


async def _process_agent_message(agent, message: str, user_id: str, session_id: str):
    """处理Agent消息"""
    import concurrent.futures
    
    loop = asyncio.get_event_loop()
    
    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(
            pool,
            agent.process,
            message
        )
    
    return result
```

### 前端改进（AgentChatDialog.tsx）

复用同一个WebSocket连接，不要每次都关闭：

```typescript
export function AgentChatDialog({ agentType, agentName, agentColor, token, onClose }: AgentChatDialogProps) {
  // ... 其他状态 ...
  
  // 在组件挂载时建立WebSocket连接
  useEffect(() => {
    const wsUrl = API_BASE_URL.replace('http', 'ws') + '/ws/agent-chat';
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[WebSocket] 连接已建立');
      
      // 发送初始化消息（包含token和agent_type）
      ws.send(JSON.stringify({
        token: token,
        agent_type: agentType,
        message: '' // 空消息，仅用于初始化
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('[WebSocket] 收到消息:', data);

      switch (data.type) {
        case 'connected':
          console.log('[WebSocket] 会话ID:', data.session_id);
          break;

        case 'retrieval_start':
          // ... 处理记忆检索开始 ...
          break;

        case 'retrieval_complete':
          // ... 处理记忆检索完成 ...
          break;

        case 'tool_start':
          // ... 处理工具开始 ...
          break;

        case 'tool_complete':
          // ... 处理工具完成 ...
          break;

        case 'response':
          console.log('[WebSocket] 收到响应');
          
          // 创建助手消息
          const assistantMessage: Message = {
            role: 'assistant',
            content: data.content,
            timestamp: new Date(),
            retrievalStats: data.metadata?.retrieval_stats,
            toolCalls: data.metadata?.tool_calls || []
          };
          
          setMessages(prev => [...prev, assistantMessage]);
          setCurrentToolCalls([]);
          setIsLoading(false);
          
          // ⚠️ 不要关闭连接！继续等待下一条消息
          // ws.close(); // ❌ 删除这行
          break;

        case 'error':
          console.error('[WebSocket] 错误:', data.error);
          const errorMessage: Message = {
            role: 'assistant',
            content: '抱歉，我现在遇到了一些问题。请稍后再试。',
            timestamp: new Date()
          };
          setMessages(prev => [...prev, errorMessage]);
          setCurrentToolCalls([]);
          setIsLoading(false);
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('[WebSocket] 连接错误:', error);
    };

    ws.onclose = () => {
      console.log('[WebSocket] 连接已关闭');
      wsRef.current = null;
    };

    // 清理函数：组件卸载时关闭连接
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [agentType, token]); // 只在组件挂载时执行一次

  // 发送消息（复用现有连接）
  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setCurrentToolCalls([]);

    // 使用现有的WebSocket连接发送消息
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        message: userMessage.content,
        conversation_id: conversationId,
        conversation_history: messages.slice(1).map(m => ({
          role: m.role,
          content: m.content
        }))
      }));
    } else {
      console.error('[WebSocket] 连接未建立或已关闭');
      setIsLoading(false);
    }
  };

  // ... 其他代码 ...
}
```

## 改进效果

1. **后端**：
   - WebSocket连接保持打开状态
   - Agent实例被复用，保留对话上下文
   - 持续等待并处理多条消息

2. **前端**：
   - 组件挂载时建立一次WebSocket连接
   - 发送多条消息复用同一个连接
   - 组件卸载时才关闭连接

3. **用户体验**：
   - 真正的多轮对话
   - 更快的响应速度（无需重新建立连接）
   - Agent能记住之前的对话内容

## 实施步骤

1. 修改 `backend/main.py` 中的 `/ws/agent-chat` 端点
2. 修改 `web/src/components/AgentChatDialog.tsx` 中的WebSocket逻辑
3. 测试多轮对话功能
4. 验证工具调用和记忆检索的实时显示

## 注意事项

1. **连接管理**：确保在组件卸载时正确关闭WebSocket
2. **错误处理**：连接断开时需要有重连机制
3. **状态同步**：Agent的对话历史需要正确维护
4. **性能优化**：长时间连接可能需要心跳机制

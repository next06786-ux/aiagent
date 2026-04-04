"""
测试流式生成修复
"""
import asyncio
import queue
import threading
import time

def mock_stream_generator():
    """模拟LLM流式生成"""
    for i in range(20):
        time.sleep(0.1)  # 模拟网络延迟
        yield {"type": "answer", "content": f"chunk_{i} "}
    yield {"type": "done"}

async def test_stream_with_queue():
    """测试使用队列的流式处理"""
    print("开始测试流式处理...")
    
    chunk_queue = queue.Queue()
    received_chunks = []
    
    def stream_worker():
        """在独立线程中执行流式生成"""
        try:
            for chunk_data in mock_stream_generator():
                chunk_queue.put(chunk_data)
                print(f"[线程] 放入chunk: {chunk_data}")
            chunk_queue.put(None)  # 结束标记
        except Exception as e:
            print(f"[线程错误] {e}")
            chunk_queue.put(None)
    
    # 启动流式生成线程
    stream_thread = threading.Thread(target=stream_worker, daemon=True)
    stream_thread.start()
    
    # 从队列中读取chunk（使用get_nowait）
    chunk_count = 0
    while True:
        chunk_data = None
        try:
            # 尝试立即获取，不阻塞
            chunk_data = chunk_queue.get_nowait()
        except queue.Empty:
            # 队列为空，短暂休眠后继续
            await asyncio.sleep(0.01)
            continue
        
        if chunk_data is None:
            break
        
        if chunk_data.get("type") == "answer":
            chunk_count += 1
            content = chunk_data.get("content", "")
            received_chunks.append(content)
            print(f"[主协程] 立即收到chunk {chunk_count}: {content}")
            
            # 模拟发送到WebSocket
            await asyncio.sleep(0.001)
    
    print(f"\n测试完成！共收到 {chunk_count} 个chunk")
    print(f"完整内容: {''.join(received_chunks)}")

if __name__ == "__main__":
    asyncio.run(test_stream_with_queue())

"""
HuggingFace模型下载脚本
用于首次部署时下载sentence-transformers模型
"""
import os

# 配置HuggingFace镜像（国内加速）
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_OFFLINE'] = '0'

from huggingface_hub import snapshot_download

model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

print(f"🚀 开始下载模型: {model_name}")
print(f"📦 使用镜像: https://hf-mirror.com")
print(f"💾 缓存目录: /root/.cache/huggingface/")

try:
    snapshot_download(repo_id=model_name, local_dir_use_symlinks=False)
    print("✅ 下载完成！")
    print("📁 模型已保存到Docker卷，重启容器不会丢失")
except Exception as e:
    print(f"❌ 下载失败: {e}")
    print("💡 提示: 请检查网络连接或HuggingFace镜像状态")
    raise

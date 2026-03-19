# pip 国内镜像配置指南

## 🚀 快速配置（3选1）

### 方式 1: 一行命令（最快）
```bash
pip install -r requirements.txt -i https://pypi.tsinghua.edu.cn/simple
```

### 方式 2: 运行配置脚本（推荐）

**Windows:**
```bash
python setup_pip_mirror.py
# 或
setup_pip_mirror.bat
```

**Linux/macOS:**
```bash
python setup_pip_mirror.py
```

### 方式 3: 手动配置

**Windows 用户:**
1. 打开 `%APPDATA%\pip\pip.ini`（如果不存在则创建）
2. 复制以下内容：

```ini
[global]
index-url = https://pypi.tsinghua.edu.cn/simple
extra-index-url = https://mirrors.aliyun.com/pypi/simple/
[install]
trusted-host = pypi.tsinghua.edu.cn
timeout = 120
```

**Linux/macOS 用户:**
1. 编辑 `~/.pip/pip.conf`
2. 复制上面的内容

## 📊 国内镜像源对比

| 镜像源 | 地址 | 速度 | 稳定性 | 推荐度 |
|------|------|------|------|------|
| 清华大学 | https://pypi.tsinghua.edu.cn/simple | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 阿里云 | https://mirrors.aliyun.com/pypi/simple/ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 豆瓣 | https://pypi.douban.com/simple | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| 中科大 | https://pypi.mirrors.ustc.edu.cn/simple | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## 💡 使用技巧

### 临时使用其他镜像
```bash
# 使用阿里云镜像
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 使用豆瓣镜像
pip install -r requirements.txt -i https://pypi.douban.com/simple
```

### 升级 pip
```bash
# 使用清华镜像升级 pip
python -m pip install --upgrade pip -i https://pypi.tsinghua.edu.cn/simple
```

### 查看当前配置
```bash
pip config list
```

### 重置为官方源
```bash
pip config unset global.index-url
```

## 🔧 常见问题

### Q: 安装仍然很慢
**A:** 
1. 检查网络连接
2. 尝试切换镜像源
3. 增加超时时间：`pip install --default-timeout=1000 -r requirements.txt`

### Q: SSL 证书错误
**A:** 
```bash
pip install --trusted-host pypi.tsinghua.edu.cn -r requirements.txt -i https://pypi.tsinghua.edu.cn/simple
```

### Q: 某个包找不到
**A:** 
```bash
# 使用官方源安装该包
pip install package_name -i https://pypi.org/simple/
```

### Q: 配置文件位置
**A:**
- Windows: `%APPDATA%\pip\pip.ini`
- Linux/macOS: `~/.pip/pip.conf`
- 项目级别: `./pip.ini` 或 `./pip.conf`

## 📝 完整配置示例

```ini
[global]
# 主镜像源
index-url = https://pypi.tsinghua.edu.cn/simple

# 备用镜像源（如果主源不可用）
extra-index-url = 
    https://mirrors.aliyun.com/pypi/simple/
    https://pypi.douban.com/simple
    https://pypi.org/simple/

[install]
# 信任的主机
trusted-host = 
    pypi.tsinghua.edu.cn
    mirrors.aliyun.com
    pypi.douban.com
    pypi.org

# 超时时间（秒）
timeout = 120

# 重试次数
retries = 3
```

## 🎯 推荐方案

**最佳实践：**
1. 使用清华大学镜像作为主源（最快最稳定）
2. 配置阿里云作为备用源
3. 设置合理的超时时间（120秒）
4. 定期检查镜像源状态

**配置命令：**
```bash
# 一键配置
python setup_pip_mirror.py

# 然后安装依赖
pip install -r requirements.txt
```

## ✅ 验证配置

```bash
# 查看当前配置
pip config list

# 测试安装速度
pip install requests -i https://pypi.tsinghua.edu.cn/simple
```

---

**提示：** 配置完成后，所有 pip 命令都会自动使用配置的镜像源，无需每次都指定 `-i` 参数。











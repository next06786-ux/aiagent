# HarmonyOS白屏问题修复指南

## 问题原因
应用打开后显示白屏，主要有以下几个原因：

### 1. 页面路径错误 ✅ 已修复
- **问题**: EntryAbility尝试加载 `pages/Login`，但实际页面是 `pages/LoginPage`
- **修复**: 已将所有页面路径更新为正确的名称
  - `pages/Login` → `pages/LoginPage`
  - `pages/AgentHome` → `pages/IndexNew`
  - `pages/Welcome` → `pages/IndexNew`

### 2. 后端连接问题
- **当前配置**: `http://192.168.242.1:6006`
- **可能原因**:
  - 后端服务未启动
  - IP地址不正确
  - 网络连接问题

#### 解决方案：

**方案A: 启动后端服务**
```bash
# 在项目根目录
cd backend
python main.py
```

**方案B: 修改后端地址**

根据你的测试环境修改 `harmonyos/entry/src/main/ets/constants/ApiConstants.ets`:

```typescript
// 模拟器测试
static readonly BASE_URL: string = 'http://10.0.2.2:6006';

// 本机测试
static readonly BASE_URL: string = 'http://localhost:6006';

// 真机测试（需要替换为你的电脑IP）
static readonly BASE_URL: string = 'http://192.168.x.x:6006';
```

查看你的电脑IP:
```bash
# Windows
ipconfig

# 查找 "无线局域网适配器 WLAN" 或 "以太网适配器" 的 IPv4 地址
```

**方案C: 临时禁用后端调用（用于测试UI）**

修改 `harmonyos/entry/src/main/ets/pages/LoginPage.ets`，在登录方法中添加：
```typescript
async handleLogin() {
  // 临时跳过后端验证
  router.replaceUrl({ url: 'pages/IndexNew' });
  return;
  
  // ... 原有的登录代码
}
```

### 3. 编译错误检查

重新编译项目查看是否有错误：
```bash
cd harmonyos
hvigorw clean
hvigorw assembleHap
```

### 4. 查看日志

使用DevEco Studio的日志工具查看运行时错误：
1. 打开 DevEco Studio
2. 点击底部的 "Log" 标签
3. 筛选 "VisionAgent" 标签查看应用日志
4. 查找错误信息

## 快速测试步骤

1. **确认编译成功**
   - 运行 `hvigorw assembleHap`
   - 确保没有ERROR，只有WARN可以忽略

2. **启动后端服务**
   ```bash
   cd backend
   python main.py
   ```
   - 确认看到 "Application startup complete"

3. **修改IP地址**
   - 如果使用真机，确保手机和电脑在同一WiFi
   - 修改 `ApiConstants.ets` 中的 `BASE_URL` 为你的电脑IP

4. **重新安装应用**
   - 在DevEco Studio中点击运行
   - 或使用 `hvigorw assembleHap` 后手动安装HAP

## 当前状态

✅ 编译错误已修复（从155个减少到0个）
✅ 页面路径已修复
⚠️ 需要确认后端服务运行状态
⚠️ 需要确认网络配置正确

## 下一步

1. 启动后端服务
2. 确认IP地址配置
3. 重新运行应用
4. 查看日志输出

如果仍然白屏，请提供：
- DevEco Studio的日志输出
- 后端服务是否正常运行
- 使用的是模拟器还是真机

# 择境 Web

Web 端位于 `E:\ai\web`，与 `E:\ai\harmonyos` 并列，继续连接同一套后端。

## 技术栈

- React 18
- TypeScript
- Vite
- 原生 CSS 主题系统

## 已接入的核心能力

- 登录 / 注册 / 用户中心
- AI 对话 WebSocket 实时输出
- 决策副本增强流程
- 推演展示页
- prediction trace / risk assessment / verifiability report 展示
- 预测后回访校准入口
- 历史推演回放

## 启动

1. 安装依赖
2. 复制 `.env.example` 为 `.env`
3. 执行 `npm run dev`

默认后端地址来自 `.env.example` 里的 `VITE_API_BASE_URL`。

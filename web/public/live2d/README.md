# Live2D 模型文件目录

请将 Live2D 模型文件放置在对应的文件夹中：

## 目录结构

```
live2d/
├── relationship/          # 人际关系 Agent 模型
│   ├── model.json        # 模型配置文件
│   ├── *.moc3            # 模型文件
│   ├── *.physics3.json   # 物理配置
│   ├── *.pose3.json      # 姿势配置
│   └── textures/         # 贴图文件夹
│
├── education/            # 教育升学 Agent 模型
│   ├── model.json
│   └── ...
│
└── career/               # 职业规划 Agent 模型
    ├── model.json
    └── ...
```

## 获取 Live2D 模型

你可以从以下途径获取免费的 Live2D 模型：

1. **Live2D 官方示例模型**
   - https://www.live2d.com/en/download/sample-data/

2. **开源 Live2D 模型**
   - https://github.com/xiazeyu/live2d-widget-models
   - https://github.com/fghrsh/live2d_api

3. **自己制作**
   - 使用 Live2D Cubism Editor 制作

## 模型配置

每个模型文件夹需要包含 `model.json` 或 `model3.json` 配置文件。

示例配置：
```json
{
  "Version": 3,
  "FileReferences": {
    "Moc": "model.moc3",
    "Textures": [
      "textures/texture_00.png"
    ],
    "Physics": "model.physics3.json",
    "Pose": "model.pose3.json",
    "Motions": {
      "idle": [
        {"File": "motions/idle_01.motion3.json"}
      ],
      "tap_body": [
        {"File": "motions/tap_body_01.motion3.json"}
      ]
    }
  }
}
```

## 临时方案

如果暂时没有模型文件，组件会自动显示加载提示。

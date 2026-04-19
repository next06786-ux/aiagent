#ifndef STARMAP_TYPES_H
#define STARMAP_TYPES_H

#include <string>
#include <vector>

// 节点数据
struct StarNode {
    std::string id;
    std::string name;
    std::string category;
    float x, y, z;           // 3D位置
    float vx, vy, vz;        // 速度
    float r, g, b;           // 颜色
    int connections;         // 连接数
};

// 连线数据
struct StarLink {
    int sourceIdx;
    int targetIdx;
    float strength;
};

// 流光粒子
struct FlowParticle {
    int linkIdx;
    float progress;          // 0-1
    float speed;
};

// 背景星星 - 3D版本
struct BackgroundStar {
    float x, y, z;           // 3D位置
    float size;
    float brightness;
    float twinklePhase;
    float twinkleSpeed;
    float r, g, b;           // 星星颜色
};

// 颜色映射
struct CategoryColor {
    float r, g, b;
};

// 屏幕位置（用于文字标签）
struct ScreenPosition {
    float x, y;              // 屏幕坐标
    float scale;             // 缩放（用于透明度）
    float nodeSize;          // 节点在屏幕上的大小
    std::string name;        // 节点名称
    std::string category;    // 节点类别
    int connections;         // 连接数（用于大小和亮度）
    float distFromCenter;    // 距离屏幕中心的距离（归一化）
    float distFromTarget;    // 距离相机目标点的3D距离（归一化，0=在目标点，1=最远）
    float labelX, labelY;    // 标签锚点位置（屏幕坐标）
};

// 文字纹理数据
struct TextLabel {
    int nodeIdx;             // 对应的节点索引
    std::vector<uint8_t> pixels;  // RGBA 像素数据
    int width;
    int height;
    GLuint textureId;        // OpenGL 纹理ID
};

#endif // STARMAP_TYPES_H

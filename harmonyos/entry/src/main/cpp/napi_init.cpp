#include <napi/native_api.h>
#include <hilog/log.h>
#include <ace/xcomponent/native_interface_xcomponent.h>
#include <native_window/external_window.h>
#include <string>
#include <unordered_map>
#include "starmap_renderer.h"

#undef LOG_TAG
#define LOG_TAG "StarMapNAPI"
#define LOGE(...) OH_LOG_ERROR(LOG_APP, __VA_ARGS__)
#define LOGI(...) OH_LOG_INFO(LOG_APP, __VA_ARGS__)

// 全局渲染器实例
static std::unordered_map<std::string, StarMapRenderer*> g_renderers;
static std::string g_currentId;

// XComponent 回调
void OnSurfaceCreatedCB(OH_NativeXComponent* component, void* window) {
    LOGI("OnSurfaceCreated");
    
    char idStr[OH_XCOMPONENT_ID_LEN_MAX + 1] = {0};
    uint64_t idSize = OH_XCOMPONENT_ID_LEN_MAX;
    OH_NativeXComponent_GetXComponentId(component, idStr, &idSize);
    
    uint64_t width, height;
    OH_NativeXComponent_GetXComponentSize(component, window, &width, &height);
    
    LOGI("Surface size: %{public}llu x %{public}llu", width, height);
    
    auto* renderer = new StarMapRenderer();
    if (renderer->init((OHNativeWindow*)window, (int)width, (int)height)) {
        g_renderers[idStr] = renderer;
        g_currentId = idStr;
        LOGI("Renderer created for %{public}s", idStr);
        
        // 立即渲染一帧测试
        renderer->render();
        LOGI("Initial test render completed");
    } else {
        delete renderer;
        LOGE("Failed to create renderer");
    }
}

void OnSurfaceChangedCB(OH_NativeXComponent* component, void* window) {
    LOGI("OnSurfaceChanged");
}

void OnSurfaceDestroyedCB(OH_NativeXComponent* component, void* window) {
    LOGI("OnSurfaceDestroyed");
    
    char idStr[OH_XCOMPONENT_ID_LEN_MAX + 1] = {0};
    uint64_t idSize = OH_XCOMPONENT_ID_LEN_MAX;
    OH_NativeXComponent_GetXComponentId(component, idStr, &idSize);
    
    auto it = g_renderers.find(idStr);
    if (it != g_renderers.end()) {
        delete it->second;
        g_renderers.erase(it);
    }
}

void DispatchTouchEventCB(OH_NativeXComponent* component, void* window) {
    // 触摸事件在ArkTS层处理
}

// 注册XComponent回调
static napi_value RegisterXComponent(napi_env env, napi_callback_info info) {
    size_t argc = 1;
    napi_value args[1];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    if (argc < 1) {
        LOGE("RegisterXComponent: missing xcomponentId");
        return nullptr;
    }
    
    char xcomponentId[64] = {0};
    size_t idLen = 0;
    napi_get_value_string_utf8(env, args[0], xcomponentId, sizeof(xcomponentId), &idLen);
    
    // 获取XComponent实例
    OH_NativeXComponent* nativeXComponent = nullptr;
    napi_value exportInstance = nullptr;
    napi_get_named_property(env, args[0], "__NATIVE_XCOMPONENT_OBJ__", &exportInstance);
    
    // 这里需要通过其他方式获取XComponent，暂时跳过
    LOGI("RegisterXComponent called with id: %{public}s", xcomponentId);
    
    return nullptr;
}

// 设置节点数据
static napi_value SetNodes(napi_env env, napi_callback_info info) {
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        LOGE("SetNodes: no renderer");
        return nullptr;
    }
    
    size_t argc = 1;
    napi_value args[1];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    if (argc < 1) return nullptr;
    
    // 解析节点数组
    bool isArray;
    napi_is_array(env, args[0], &isArray);
    if (!isArray) return nullptr;
    
    uint32_t length;
    napi_get_array_length(env, args[0], &length);
    
    std::vector<StarNode> nodes;
    nodes.reserve(length);
    
    for (uint32_t i = 0; i < length; i++) {
        napi_value item;
        napi_get_element(env, args[0], i, &item);
        
        StarNode node;
        napi_value val;
        
        // id
        napi_get_named_property(env, item, "id", &val);
        char idBuf[128] = {0};
        size_t idLen;
        napi_get_value_string_utf8(env, val, idBuf, sizeof(idBuf), &idLen);
        node.id = idBuf;
        
        // name
        napi_get_named_property(env, item, "name", &val);
        char nameBuf[128] = {0};
        size_t nameLen;
        napi_get_value_string_utf8(env, val, nameBuf, sizeof(nameBuf), &nameLen);
        node.name = nameBuf;
        
        // category
        napi_get_named_property(env, item, "category", &val);
        char catBuf[64] = {0};
        size_t catLen;
        napi_get_value_string_utf8(env, val, catBuf, sizeof(catBuf), &catLen);
        node.category = catBuf;
        
        // x, y, z - 使用 double 临时变量
        double x, y, z;
        napi_get_named_property(env, item, "x", &val);
        napi_get_value_double(env, val, &x);
        node.x = (float)x;
        
        napi_get_named_property(env, item, "y", &val);
        napi_get_value_double(env, val, &y);
        node.y = (float)y;
        
        napi_get_named_property(env, item, "z", &val);
        napi_get_value_double(env, val, &z);
        node.z = (float)z;
        
        // connections
        napi_get_named_property(env, item, "connections", &val);
        int32_t conn;
        napi_get_value_int32(env, val, &conn);
        node.connections = conn;
        
        node.vx = node.vy = node.vz = 0;
        nodes.push_back(node);
    }
    
    g_renderers[g_currentId]->setNodes(nodes);
    LOGI("SetNodes: %{public}zu nodes", nodes.size());
    
    return nullptr;
}

// 设置连线数据
static napi_value SetLinks(napi_env env, napi_callback_info info) {
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        return nullptr;
    }
    
    size_t argc = 1;
    napi_value args[1];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    if (argc < 1) return nullptr;
    
    bool isArray;
    napi_is_array(env, args[0], &isArray);
    if (!isArray) return nullptr;
    
    uint32_t length;
    napi_get_array_length(env, args[0], &length);
    
    std::vector<StarLink> links;
    links.reserve(length);
    
    for (uint32_t i = 0; i < length; i++) {
        napi_value item;
        napi_get_element(env, args[0], i, &item);
        
        StarLink link;
        napi_value val;
        
        napi_get_named_property(env, item, "sourceIdx", &val);
        napi_get_value_int32(env, val, &link.sourceIdx);
        
        napi_get_named_property(env, item, "targetIdx", &val);
        napi_get_value_int32(env, val, &link.targetIdx);
        
        napi_get_named_property(env, item, "strength", &val);
        double strength;
        napi_get_value_double(env, val, &strength);
        link.strength = (float)strength;
        
        links.push_back(link);
    }
    
    g_renderers[g_currentId]->setLinks(links);
    LOGI("SetLinks: %{public}zu links", links.size());
    
    return nullptr;
}

// 设置旋转
static napi_value SetRotation(napi_env env, napi_callback_info info) {
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        return nullptr;
    }
    
    size_t argc = 2;
    napi_value args[2];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    double rotX, rotY;
    napi_get_value_double(env, args[0], &rotX);
    napi_get_value_double(env, args[1], &rotY);
    
    g_renderers[g_currentId]->setRotation((float)rotX, (float)rotY);
    
    return nullptr;
}

// 设置缩放
static napi_value SetZoom(napi_env env, napi_callback_info info) {
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        return nullptr;
    }
    
    size_t argc = 1;
    napi_value args[1];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    double zoom;
    napi_get_value_double(env, args[0], &zoom);
    
    g_renderers[g_currentId]->setZoom((float)zoom);
    
    return nullptr;
}

// 重置相机目标点到原点
static napi_value ResetTarget(napi_env env, napi_callback_info info) {
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        return nullptr;
    }
    
    g_renderers[g_currentId]->resetTarget();
    
    return nullptr;
}

// 渲染一帧
static napi_value RenderFrame(napi_env env, napi_callback_info info) {
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        return nullptr;
    }
    
    g_renderers[g_currentId]->render();
    
    return nullptr;
}

// 纯星空渲染（用于聊天背景）
static napi_value RenderStarfieldOnly(napi_env env, napi_callback_info info) {
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        return nullptr;
    }
    
    g_renderers[g_currentId]->renderStarfieldOnly();
    
    return nullptr;
}

// 更新动画
static napi_value UpdateAnimation(napi_env env, napi_callback_info info) {
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        return nullptr;
    }
    
    size_t argc = 1;
    napi_value args[1];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    double deltaTime;
    napi_get_value_double(env, args[0], &deltaTime);
    
    g_renderers[g_currentId]->updateAnimation((float)deltaTime);
    
    return nullptr;
}

// 更新力导向布局
static napi_value UpdateForceLayout(napi_env env, napi_callback_info info) {
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        return nullptr;
    }
    
    g_renderers[g_currentId]->updateForceLayout();
    
    return nullptr;
}

// 点击测试
static napi_value HitTest(napi_env env, napi_callback_info info) {
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        napi_value result;
        napi_create_int32(env, -1, &result);
        return result;
    }
    
    size_t argc = 2;
    napi_value args[2];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    double x, y;
    napi_get_value_double(env, args[0], &x);
    napi_get_value_double(env, args[1], &y);
    
    int idx = g_renderers[g_currentId]->hitTest((float)x, (float)y);
    
    napi_value result;
    napi_create_int32(env, idx, &result);
    return result;
}

// 获取节点屏幕坐标
static napi_value GetNodeScreenPositions(napi_env env, napi_callback_info info) {
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        napi_value result;
        napi_create_array(env, &result);
        return result;
    }
    
    auto* renderer = g_renderers[g_currentId];
    auto positions = renderer->getNodeScreenPositions();
    
    napi_value result;
    napi_create_array_with_length(env, positions.size(), &result);
    
    for (size_t i = 0; i < positions.size(); i++) {
        napi_value item;
        napi_create_object(env, &item);
        
        napi_value x, y, scale, nodeSize, name, category, connections, distFromCenter, distFromTarget, labelX, labelY;
        napi_create_double(env, positions[i].x, &x);
        napi_create_double(env, positions[i].y, &y);
        napi_create_double(env, positions[i].scale, &scale);
        napi_create_double(env, positions[i].nodeSize, &nodeSize);
        napi_create_string_utf8(env, positions[i].name.c_str(), NAPI_AUTO_LENGTH, &name);
        napi_create_string_utf8(env, positions[i].category.c_str(), NAPI_AUTO_LENGTH, &category);
        napi_create_int32(env, positions[i].connections, &connections);
        napi_create_double(env, positions[i].distFromCenter, &distFromCenter);
        napi_create_double(env, positions[i].distFromTarget, &distFromTarget);
        napi_create_double(env, positions[i].labelX, &labelX);
        napi_create_double(env, positions[i].labelY, &labelY);
        
        napi_set_named_property(env, item, "x", x);
        napi_set_named_property(env, item, "y", y);
        napi_set_named_property(env, item, "scale", scale);
        napi_set_named_property(env, item, "nodeSize", nodeSize);
        napi_set_named_property(env, item, "name", name);
        napi_set_named_property(env, item, "category", category);
        napi_set_named_property(env, item, "connections", connections);
        napi_set_named_property(env, item, "distFromCenter", distFromCenter);
        napi_set_named_property(env, item, "distFromTarget", distFromTarget);
        napi_set_named_property(env, item, "labelX", labelX);
        napi_set_named_property(env, item, "labelY", labelY);
        
        napi_set_element(env, result, i, item);
    }
    
    return result;
}

// 选中节点
static napi_value SelectNode(napi_env env, napi_callback_info info) {
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        return nullptr;
    }
    
    size_t argc = 1;
    napi_value args[1];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    int32_t idx;
    napi_get_value_int32(env, args[0], &idx);
    
    g_renderers[g_currentId]->selectNode(idx);
    
    return nullptr;
}

// 设置文字纹理
static napi_value SetTextTexture(napi_env env, napi_callback_info info) {
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        return nullptr;
    }
    
    size_t argc = 4;
    napi_value args[4];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    if (argc < 4) return nullptr;
    
    int32_t nodeIdx, width, height;
    napi_get_value_int32(env, args[0], &nodeIdx);
    napi_get_value_int32(env, args[2], &width);
    napi_get_value_int32(env, args[3], &height);
    
    // 获取 ArrayBuffer 数据
    void* data = nullptr;
    size_t byteLength = 0;
    bool isArrayBuffer = false;
    napi_is_arraybuffer(env, args[1], &isArrayBuffer);
    
    if (isArrayBuffer) {
        napi_get_arraybuffer_info(env, args[1], &data, &byteLength);
    } else {
        // 可能是 TypedArray
        napi_typedarray_type type;
        size_t length;
        napi_value arrayBuffer;
        size_t offset;
        napi_get_typedarray_info(env, args[1], &type, &length, &data, &arrayBuffer, &offset);
        byteLength = length;
    }
    
    if (data && byteLength > 0) {
        g_renderers[g_currentId]->setTextTexture(nodeIdx, (const uint8_t*)data, width, height);
        LOGI("SetTextTexture: node %{public}d, size %{public}dx%{public}d, bytes %{public}zu", 
             nodeIdx, width, height, byteLength);
    }
    
    return nullptr;
}

// 获取节点关系
static napi_value GetNodeRelations(napi_env env, napi_callback_info info) {
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        napi_value result;
        napi_create_array(env, &result);
        return result;
    }
    
    size_t argc = 1;
    napi_value args[1];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    int32_t nodeIdx;
    napi_get_value_int32(env, args[0], &nodeIdx);
    
    auto* renderer = g_renderers[g_currentId];
    auto relations = renderer->getNodeRelations(nodeIdx);
    
    napi_value result;
    napi_create_array_with_length(env, relations.size(), &result);
    
    for (size_t i = 0; i < relations.size(); i++) {
        napi_value item;
        napi_create_object(env, &item);
        
        napi_value name, category, strength, targetIdx;
        napi_create_string_utf8(env, relations[i].targetName.c_str(), NAPI_AUTO_LENGTH, &name);
        napi_create_string_utf8(env, relations[i].targetCategory.c_str(), NAPI_AUTO_LENGTH, &category);
        napi_create_double(env, relations[i].strength, &strength);
        napi_create_int32(env, relations[i].targetIdx, &targetIdx);
        
        napi_set_named_property(env, item, "name", name);
        napi_set_named_property(env, item, "category", category);
        napi_set_named_property(env, item, "strength", strength);
        napi_set_named_property(env, item, "targetIdx", targetIdx);
        
        napi_set_element(env, result, i, item);
    }
    
    return result;
}

// 聚焦到节点（平滑动画）
static napi_value FocusOnNode(napi_env env, napi_callback_info info) {
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        return nullptr;
    }
    
    size_t argc = 1;
    napi_value args[1];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    int32_t idx;
    napi_get_value_int32(env, args[0], &idx);
    
    g_renderers[g_currentId]->focusOnNode(idx);
    
    return nullptr;
}

// 销毁渲染器
static napi_value DestroyRenderer(napi_env env, napi_callback_info info) {
    LOGI("DestroyRenderer called");
    if (g_currentId.empty() || g_renderers.find(g_currentId) == g_renderers.end()) {
        LOGI("DestroyRenderer: no renderer to destroy");
        napi_value result;
        napi_get_boolean(env, false, &result);
        return result;
    }
    
    auto it = g_renderers.find(g_currentId);
    if (it != g_renderers.end()) {
        it->second->destroy();
        delete it->second;
        g_renderers.erase(it);
        LOGI("DestroyRenderer: renderer destroyed for %s", g_currentId.c_str());
    }
    g_currentId.clear();
    
    napi_value result;
    napi_get_boolean(env, true, &result);
    return result;
}

// XComponent回调结构
static OH_NativeXComponent_Callback g_callback = {
    .OnSurfaceCreated = OnSurfaceCreatedCB,
    .OnSurfaceChanged = OnSurfaceChangedCB,
    .OnSurfaceDestroyed = OnSurfaceDestroyedCB,
    .DispatchTouchEvent = DispatchTouchEventCB,
};

// 导出XComponent回调
EXTERN_C_START
static napi_value Export(napi_env env, napi_value exports) {
    // 注册XComponent回调
    napi_value exportInstance = nullptr;
    napi_get_named_property(env, exports, OH_NATIVE_XCOMPONENT_OBJ, &exportInstance);
    
    OH_NativeXComponent* nativeXComponent = nullptr;
    napi_unwrap(env, exportInstance, reinterpret_cast<void**>(&nativeXComponent));
    
    if (nativeXComponent) {
        OH_NativeXComponent_RegisterCallback(nativeXComponent, &g_callback);
        
        char idStr[OH_XCOMPONENT_ID_LEN_MAX + 1] = {0};
        uint64_t idSize = OH_XCOMPONENT_ID_LEN_MAX;
        OH_NativeXComponent_GetXComponentId(nativeXComponent, idStr, &idSize);
        g_currentId = idStr;
        LOGI("XComponent registered: %{public}s", idStr);
    }
    
    // 导出函数
    napi_property_descriptor desc[] = {
        {"setNodes", nullptr, SetNodes, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"setLinks", nullptr, SetLinks, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"setRotation", nullptr, SetRotation, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"setZoom", nullptr, SetZoom, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"resetTarget", nullptr, ResetTarget, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"renderFrame", nullptr, RenderFrame, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"renderStarfieldOnly", nullptr, RenderStarfieldOnly, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"updateAnimation", nullptr, UpdateAnimation, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"updateForceLayout", nullptr, UpdateForceLayout, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"hitTest", nullptr, HitTest, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"selectNode", nullptr, SelectNode, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"focusOnNode", nullptr, FocusOnNode, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"getNodeScreenPositions", nullptr, GetNodeScreenPositions, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"getNodeRelations", nullptr, GetNodeRelations, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"setTextTexture", nullptr, SetTextTexture, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"destroyRenderer", nullptr, DestroyRenderer, nullptr, nullptr, nullptr, napi_default, nullptr},
    };
    
    napi_define_properties(env, exports, sizeof(desc) / sizeof(desc[0]), desc);
    
    return exports;
}
EXTERN_C_END

// 模块定义
static napi_module starmapModule = {
    .nm_version = 1,
    .nm_flags = 0,
    .nm_filename = nullptr,
    .nm_register_func = Export,
    .nm_modname = "starmap_render",
    .nm_priv = nullptr,
    .reserved = {0},
};

// 模块注册
extern "C" __attribute__((constructor)) void RegisterStarMapModule(void) {
    napi_module_register(&starmapModule);
}

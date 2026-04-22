/**
 * 星云对话 NAPI 接口
 * 使用XComponent回调方式，与starmap_render相同的架构
 */
#include <napi/native_api.h>
#include <hilog/log.h>
#include <ace/xcomponent/native_interface_xcomponent.h>
#include <native_window/external_window.h>
#include <string>
#include <unordered_map>
#include "nebula_chat_renderer.h"

#undef LOG_TAG
#define LOG_TAG "NebulaChatNAPI"
#define LOGE(...) OH_LOG_ERROR(LOG_APP, __VA_ARGS__)
#define LOGI(...) OH_LOG_INFO(LOG_APP, __VA_ARGS__)

// 全局渲染器实例
static std::unordered_map<std::string, nebula::NebulaChatRenderer*> g_nebulaRenderers;
static std::string g_nebulaCurrentId;

// XComponent 回调
void NebulaOnSurfaceCreatedCB(OH_NativeXComponent* component, void* window) {
    LOGI("Nebula: OnSurfaceCreated callback triggered");
    
    if (!component) {
        LOGE("Nebula: component is null!");
        return;
    }
    if (!window) {
        LOGE("Nebula: window is null!");
        return;
    }
    
    char idStr[OH_XCOMPONENT_ID_LEN_MAX + 1] = {0};
    uint64_t idSize = OH_XCOMPONENT_ID_LEN_MAX;
    OH_NativeXComponent_GetXComponentId(component, idStr, &idSize);
    LOGI("Nebula: XComponent ID: %{public}s", idStr);
    
    uint64_t width, height;
    int32_t ret = OH_NativeXComponent_GetXComponentSize(component, window, &width, &height);
    if (ret != 0) {
        LOGE("Nebula: Failed to get XComponent size, ret=%{public}d", ret);
        return;
    }
    
    LOGI("Nebula: Surface size: %{public}llu x %{public}llu", width, height);
    
    auto* renderer = new nebula::NebulaChatRenderer();
    LOGI("Nebula: Renderer instance created, initializing...");
    
    if (renderer->init((OHNativeWindow*)window, (int)width, (int)height)) {
        g_nebulaRenderers[idStr] = renderer;
        g_nebulaCurrentId = idStr;
        LOGI("Nebula: Renderer initialized successfully for %{public}s", idStr);
        
        // 立即渲染一帧测试
        renderer->render();
        LOGI("Nebula: Initial test render completed");
    } else {
        delete renderer;
        LOGE("Nebula: Failed to initialize renderer!");
    }
}

void NebulaOnSurfaceChangedCB(OH_NativeXComponent* component, void* window) {
    LOGI("Nebula: OnSurfaceChanged");
    
    char idStr[OH_XCOMPONENT_ID_LEN_MAX + 1] = {0};
    uint64_t idSize = OH_XCOMPONENT_ID_LEN_MAX;
    OH_NativeXComponent_GetXComponentId(component, idStr, &idSize);
    
    uint64_t width, height;
    OH_NativeXComponent_GetXComponentSize(component, window, &width, &height);
    
    auto it = g_nebulaRenderers.find(idStr);
    if (it != g_nebulaRenderers.end()) {
        it->second->resize((int)width, (int)height);
    }
}

void NebulaOnSurfaceDestroyedCB(OH_NativeXComponent* component, void* window) {
    LOGI("Nebula: OnSurfaceDestroyed");
    
    char idStr[OH_XCOMPONENT_ID_LEN_MAX + 1] = {0};
    uint64_t idSize = OH_XCOMPONENT_ID_LEN_MAX;
    OH_NativeXComponent_GetXComponentId(component, idStr, &idSize);
    
    auto it = g_nebulaRenderers.find(idStr);
    if (it != g_nebulaRenderers.end()) {
        it->second->destroy();
        delete it->second;
        g_nebulaRenderers.erase(it);
    }
}

void NebulaDispatchTouchEventCB(OH_NativeXComponent* component, void* window) {
    // 触摸事件在ArkTS层处理
}

// 渲染一帧
static napi_value NebulaRender(napi_env env, napi_callback_info info) {
    if (g_nebulaCurrentId.empty() || g_nebulaRenderers.find(g_nebulaCurrentId) == g_nebulaRenderers.end()) {
        napi_value result;
        napi_get_boolean(env, false, &result);
        return result;
    }
    
    g_nebulaRenderers[g_nebulaCurrentId]->render();
    
    napi_value result;
    napi_get_boolean(env, true, &result);
    return result;
}

// 添加消息
static napi_value NebulaAddMessage(napi_env env, napi_callback_info info) {
    if (g_nebulaCurrentId.empty() || g_nebulaRenderers.find(g_nebulaCurrentId) == g_nebulaRenderers.end()) {
        napi_value result;
        napi_get_boolean(env, false, &result);
        return result;
    }
    
    size_t argc = 2;
    napi_value args[2];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    if (argc < 2) {
        napi_value result;
        napi_get_boolean(env, false, &result);
        return result;
    }
    
    // 获取消息ID
    char msgId[256] = {0};
    size_t strLen;
    napi_get_value_string_utf8(env, args[0], msgId, sizeof(msgId), &strLen);
    
    // 获取是否是用户消息
    bool isUser;
    napi_get_value_bool(env, args[1], &isUser);
    
    g_nebulaRenderers[g_nebulaCurrentId]->addMessage(std::string(msgId), isUser);
    LOGI("Nebula: Added message %{public}s, isUser=%{public}d", msgId, isUser);
    
    napi_value result;
    napi_get_boolean(env, true, &result);
    return result;
}

// 清除消息
static napi_value NebulaClearMessages(napi_env env, napi_callback_info info) {
    if (g_nebulaCurrentId.empty() || g_nebulaRenderers.find(g_nebulaCurrentId) == g_nebulaRenderers.end()) {
        napi_value result;
        napi_get_boolean(env, false, &result);
        return result;
    }
    
    g_nebulaRenderers[g_nebulaCurrentId]->clearMessages();
    LOGI("Nebula: Cleared all messages");
    
    napi_value result;
    napi_get_boolean(env, true, &result);
    return result;
}

// 滚动
static napi_value NebulaScroll(napi_env env, napi_callback_info info) {
    if (g_nebulaCurrentId.empty() || g_nebulaRenderers.find(g_nebulaCurrentId) == g_nebulaRenderers.end()) {
        return nullptr;
    }
    
    size_t argc = 1;
    napi_value args[1];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    if (argc < 1) return nullptr;
    
    double deltaY;
    napi_get_value_double(env, args[0], &deltaY);
    g_nebulaRenderers[g_nebulaCurrentId]->scroll(static_cast<float>(deltaY));
    
    return nullptr;
}

// 旋转相机
static napi_value NebulaRotateCamera(napi_env env, napi_callback_info info) {
    if (g_nebulaCurrentId.empty() || g_nebulaRenderers.find(g_nebulaCurrentId) == g_nebulaRenderers.end()) {
        return nullptr;
    }
    
    size_t argc = 2;
    napi_value args[2];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    if (argc < 2) return nullptr;
    
    double deltaX, deltaY;
    napi_get_value_double(env, args[0], &deltaX);
    napi_get_value_double(env, args[1], &deltaY);
    g_nebulaRenderers[g_nebulaCurrentId]->rotateCamera(static_cast<float>(deltaX), static_cast<float>(deltaY));
    
    return nullptr;
}

// 缩放
static napi_value NebulaZoom(napi_env env, napi_callback_info info) {
    if (g_nebulaCurrentId.empty() || g_nebulaRenderers.find(g_nebulaCurrentId) == g_nebulaRenderers.end()) {
        return nullptr;
    }
    
    size_t argc = 1;
    napi_value args[1];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    if (argc < 1) return nullptr;
    
    double delta;
    napi_get_value_double(env, args[0], &delta);
    g_nebulaRenderers[g_nebulaCurrentId]->zoom(static_cast<float>(delta));
    
    return nullptr;
}

// 销毁
static napi_value NebulaDestroy(napi_env env, napi_callback_info info) {
    if (g_nebulaCurrentId.empty() || g_nebulaRenderers.find(g_nebulaCurrentId) == g_nebulaRenderers.end()) {
        napi_value result;
        napi_get_boolean(env, false, &result);
        return result;
    }
    
    auto it = g_nebulaRenderers.find(g_nebulaCurrentId);
    if (it != g_nebulaRenderers.end()) {
        it->second->destroy();
        delete it->second;
        g_nebulaRenderers.erase(it);
    }
    
    napi_value result;
    napi_get_boolean(env, true, &result);
    return result;
}

// 点击检测 - 返回点击的消息索引
static napi_value NebulaHitTest(napi_env env, napi_callback_info info) {
    if (g_nebulaCurrentId.empty() || g_nebulaRenderers.find(g_nebulaCurrentId) == g_nebulaRenderers.end()) {
        napi_value result;
        napi_create_int32(env, -1, &result);
        return result;
    }
    
    size_t argc = 2;
    napi_value args[2];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    if (argc < 2) {
        napi_value result;
        napi_create_int32(env, -1, &result);
        return result;
    }
    
    double screenX, screenY;
    napi_get_value_double(env, args[0], &screenX);
    napi_get_value_double(env, args[1], &screenY);
    
    int hitIdx = g_nebulaRenderers[g_nebulaCurrentId]->hitTest(
        static_cast<float>(screenX), static_cast<float>(screenY));
    
    napi_value result;
    napi_create_int32(env, hitIdx, &result);
    return result;
}

// 添加功能球体
static napi_value NebulaAddFeatureOrb(napi_env env, napi_callback_info info) {
    if (g_nebulaCurrentId.empty() || g_nebulaRenderers.find(g_nebulaCurrentId) == g_nebulaRenderers.end()) {
        napi_value result;
        napi_get_boolean(env, false, &result);
        return result;
    }
    
    size_t argc = 4;
    napi_value args[4];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    if (argc < 4) {
        napi_value result;
        napi_get_boolean(env, false, &result);
        return result;
    }
    
    // 获取ID
    char orbId[256] = {0};
    size_t strLen;
    napi_get_value_string_utf8(env, args[0], orbId, sizeof(orbId), &strLen);
    
    // 获取颜色
    double r, g, b;
    napi_get_value_double(env, args[1], &r);
    napi_get_value_double(env, args[2], &g);
    napi_get_value_double(env, args[3], &b);
    
    g_nebulaRenderers[g_nebulaCurrentId]->addFeatureOrb(
        std::string(orbId), static_cast<float>(r), static_cast<float>(g), static_cast<float>(b));
    
    napi_value result;
    napi_get_boolean(env, true, &result);
    return result;
}

// 清除功能球体
static napi_value NebulaClearFeatureOrbs(napi_env env, napi_callback_info info) {
    if (g_nebulaCurrentId.empty() || g_nebulaRenderers.find(g_nebulaCurrentId) == g_nebulaRenderers.end()) {
        napi_value result;
        napi_get_boolean(env, false, &result);
        return result;
    }
    
    g_nebulaRenderers[g_nebulaCurrentId]->clearFeatureOrbs();
    
    napi_value result;
    napi_get_boolean(env, true, &result);
    return result;
}

// 点击检测功能球体
static napi_value NebulaHitTestFeature(napi_env env, napi_callback_info info) {
    if (g_nebulaCurrentId.empty() || g_nebulaRenderers.find(g_nebulaCurrentId) == g_nebulaRenderers.end()) {
        napi_value result;
        napi_create_int32(env, -1, &result);
        return result;
    }
    
    size_t argc = 2;
    napi_value args[2];
    napi_get_cb_info(env, info, &argc, args, nullptr, nullptr);
    
    if (argc < 2) {
        napi_value result;
        napi_create_int32(env, -1, &result);
        return result;
    }
    
    double screenX, screenY;
    napi_get_value_double(env, args[0], &screenX);
    napi_get_value_double(env, args[1], &screenY);
    
    int hitIdx = g_nebulaRenderers[g_nebulaCurrentId]->hitTestFeature(
        static_cast<float>(screenX), static_cast<float>(screenY));
    
    napi_value result;
    napi_create_int32(env, hitIdx, &result);
    return result;
}

// XComponent回调结构
static OH_NativeXComponent_Callback g_nebulaCallback = {
    .OnSurfaceCreated = NebulaOnSurfaceCreatedCB,
    .OnSurfaceChanged = NebulaOnSurfaceChangedCB,
    .OnSurfaceDestroyed = NebulaOnSurfaceDestroyedCB,
    .DispatchTouchEvent = NebulaDispatchTouchEventCB,
};

// 导出
EXTERN_C_START
static napi_value NebulaExport(napi_env env, napi_value exports) {
    LOGI("Nebula: NebulaExport called");
    
    // 注册XComponent回调
    napi_value exportInstance = nullptr;
    napi_status status = napi_get_named_property(env, exports, OH_NATIVE_XCOMPONENT_OBJ, &exportInstance);
    
    if (status != napi_ok) {
        LOGE("Nebula: Failed to get OH_NATIVE_XCOMPONENT_OBJ, status=%{public}d", status);
    }
    
    OH_NativeXComponent* nativeXComponent = nullptr;
    if (exportInstance != nullptr) {
        status = napi_unwrap(env, exportInstance, reinterpret_cast<void**>(&nativeXComponent));
        if (status != napi_ok) {
            LOGE("Nebula: Failed to unwrap XComponent, status=%{public}d", status);
        }
    }
    
    if (nativeXComponent) {
        int32_t ret = OH_NativeXComponent_RegisterCallback(nativeXComponent, &g_nebulaCallback);
        if (ret != 0) {
            LOGE("Nebula: Failed to register callback, ret=%{public}d", ret);
        } else {
            LOGI("Nebula: Callback registered successfully");
        }
        
        char idStr[OH_XCOMPONENT_ID_LEN_MAX + 1] = {0};
        uint64_t idSize = OH_XCOMPONENT_ID_LEN_MAX;
        OH_NativeXComponent_GetXComponentId(nativeXComponent, idStr, &idSize);
        g_nebulaCurrentId = idStr;
        LOGI("Nebula: XComponent registered: %{public}s", idStr);
    } else {
        LOGE("Nebula: nativeXComponent is null, XComponent not available");
    }
    
    // 导出函数
    napi_property_descriptor desc[] = {
        {"nebulaRender", nullptr, NebulaRender, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"nebulaAddMessage", nullptr, NebulaAddMessage, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"nebulaClearMessages", nullptr, NebulaClearMessages, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"nebulaScroll", nullptr, NebulaScroll, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"nebulaRotateCamera", nullptr, NebulaRotateCamera, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"nebulaZoom", nullptr, NebulaZoom, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"nebulaDestroy", nullptr, NebulaDestroy, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"nebulaHitTest", nullptr, NebulaHitTest, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"nebulaAddFeatureOrb", nullptr, NebulaAddFeatureOrb, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"nebulaClearFeatureOrbs", nullptr, NebulaClearFeatureOrbs, nullptr, nullptr, nullptr, napi_default, nullptr},
        {"nebulaHitTestFeature", nullptr, NebulaHitTestFeature, nullptr, nullptr, nullptr, napi_default, nullptr},
    };
    
    napi_define_properties(env, exports, sizeof(desc) / sizeof(desc[0]), desc);
    LOGI("Nebula: Properties defined, export complete");
    
    return exports;
}
EXTERN_C_END

// 模块定义
static napi_module nebulaChatModule = {
    .nm_version = 1,
    .nm_flags = 0,
    .nm_filename = nullptr,
    .nm_register_func = NebulaExport,
    .nm_modname = "nebulachat",
    .nm_priv = nullptr,
    .reserved = {0},
};

// 模块注册
extern "C" __attribute__((constructor)) void RegisterNebulaChatModule(void) {
    LOGI("Nebula: RegisterNebulaChatModule called - registering module 'nebulachat'");
    napi_module_register(&nebulaChatModule);
    LOGI("Nebula: Module 'nebulachat' registered successfully");
}

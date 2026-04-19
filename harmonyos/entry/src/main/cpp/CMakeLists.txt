# CMakeLists.txt for StarMap & Nebula Chat OpenGL ES Renderers
cmake_minimum_required(VERSION 3.5.0)
project(native_renderers)

set(CMAKE_CXX_STANDARD 17)

# ========== StarMap 渲染器 (知识星图) ==========
add_library(starmap_render SHARED
    napi_init.cpp
    starmap_renderer.cpp
    shader_utils.cpp
)

target_link_libraries(starmap_render PUBLIC
    libace_napi.z.so
    libace_ndk.z.so
    libhilog_ndk.z.so
    libEGL.so
    libGLESv3.so
    libnative_window.so
    libnative_drawing.so
)

target_include_directories(starmap_render PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

# ========== Nebula Chat 渲染器 (星云对话) ==========
add_library(nebulachat SHARED
    nebula_napi.cpp
    nebula_chat_renderer.cpp
)

target_link_libraries(nebulachat PUBLIC
    libace_napi.z.so
    libace_ndk.z.so
    libhilog_ndk.z.so
    libEGL.so
    libGLESv3.so
    libnative_window.so
    libnative_drawing.so
)

target_include_directories(nebulachat PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

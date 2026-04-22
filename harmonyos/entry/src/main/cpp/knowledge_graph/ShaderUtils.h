#ifndef SHADER_UTILS_H
#define SHADER_UTILS_H

#include <GLES3/gl3.h>
#include <string>

/**
 * Shader工具类
 */
class ShaderUtils {
public:
    // 编译shader
    static GLuint compileShader(GLenum type, const char* source);
    
    // 创建program
    static GLuint createProgram(const char* vertexSource, const char* fragmentSource);
    
    // 检查GL错误
    static void checkGLError(const char* op);
    
    // 日志输出
    static void logInfo(const char* tag, const char* message);
    static void logError(const char* tag, const char* message);
};

#endif // SHADER_UTILS_H

#ifndef MATRIX_UTILS_H
#define MATRIX_UTILS_H

#include <cmath>

/**
 * 矩阵工具类 - 4x4矩阵运算
 */
class MatrixUtils {
public:
    // 设置单位矩阵
    static void setIdentityM(float* m);
    
    // 矩阵乘法: result = lhs * rhs
    static void multiplyMM(float* result, const float* lhs, const float* rhs);
    
    // 矩阵向量乘法: result = m * v
    static void multiplyMV(float* result, const float* m, const float* v);
    
    // 设置透视投影矩阵
    static void frustumM(float* m, float left, float right, float bottom, float top, float near, float far);
    
    // 设置视图矩阵 (lookAt)
    static void setLookAtM(float* m, 
                          float eyeX, float eyeY, float eyeZ,
                          float centerX, float centerY, float centerZ,
                          float upX, float upY, float upZ);
    
    // 向量归一化
    static void normalize(float* v);
    
    // 向量叉乘
    static void cross(float* result, const float* a, const float* b);
    
    // 向量点乘
    static float dot(const float* a, const float* b);
};

#endif // MATRIX_UTILS_H

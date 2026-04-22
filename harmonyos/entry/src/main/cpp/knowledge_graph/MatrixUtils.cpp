#include "MatrixUtils.h"
#include <cstring>

void MatrixUtils::setIdentityM(float* m) {
    memset(m, 0, 16 * sizeof(float));
    m[0] = m[5] = m[10] = m[15] = 1.0f;
}

void MatrixUtils::multiplyMM(float* result, const float* lhs, const float* rhs) {
    float temp[16];
    for (int i = 0; i < 4; i++) {
        for (int j = 0; j < 4; j++) {
            temp[i * 4 + j] = 0;
            for (int k = 0; k < 4; k++) {
                temp[i * 4 + j] += lhs[i * 4 + k] * rhs[k * 4 + j];
            }
        }
    }
    memcpy(result, temp, 16 * sizeof(float));
}

void MatrixUtils::multiplyMV(float* result, const float* m, const float* v) {
    float temp[4];
    for (int i = 0; i < 4; i++) {
        temp[i] = m[i * 4 + 0] * v[0] +
                  m[i * 4 + 1] * v[1] +
                  m[i * 4 + 2] * v[2] +
                  m[i * 4 + 3] * v[3];
    }
    memcpy(result, temp, 4 * sizeof(float));
}

void MatrixUtils::frustumM(float* m, float left, float right, float bottom, float top, float near, float far) {
    float r_width = 1.0f / (right - left);
    float r_height = 1.0f / (top - bottom);
    float r_depth = 1.0f / (near - far);
    
    m[0] = 2.0f * near * r_width;
    m[1] = 0.0f;
    m[2] = 0.0f;
    m[3] = 0.0f;
    
    m[4] = 0.0f;
    m[5] = 2.0f * near * r_height;
    m[6] = 0.0f;
    m[7] = 0.0f;
    
    m[8] = (right + left) * r_width;
    m[9] = (top + bottom) * r_height;
    m[10] = (far + near) * r_depth;
    m[11] = -1.0f;
    
    m[12] = 0.0f;
    m[13] = 0.0f;
    m[14] = 2.0f * far * near * r_depth;
    m[15] = 0.0f;
}

void MatrixUtils::setLookAtM(float* m,
                             float eyeX, float eyeY, float eyeZ,
                             float centerX, float centerY, float centerZ,
                             float upX, float upY, float upZ) {
    // 计算前向向量
    float fx = centerX - eyeX;
    float fy = centerY - eyeY;
    float fz = centerZ - eyeZ;
    normalize(&fx);
    
    // 计算右向向量
    float up[3] = {upX, upY, upZ};
    float f[3] = {fx, fy, fz};
    float s[3];
    cross(s, f, up);
    normalize(s);
    
    // 计算上向向量
    float u[3];
    cross(u, s, f);
    
    // 构建视图矩阵
    m[0] = s[0];
    m[1] = u[0];
    m[2] = -f[0];
    m[3] = 0.0f;
    
    m[4] = s[1];
    m[5] = u[1];
    m[6] = -f[1];
    m[7] = 0.0f;
    
    m[8] = s[2];
    m[9] = u[2];
    m[10] = -f[2];
    m[11] = 0.0f;
    
    m[12] = -dot(s, &eyeX);
    m[13] = -dot(u, &eyeX);
    m[14] = dot(f, &eyeX);
    m[15] = 1.0f;
}

void MatrixUtils::normalize(float* v) {
    float length = sqrtf(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
    if (length > 0.0f) {
        v[0] /= length;
        v[1] /= length;
        v[2] /= length;
    }
}

void MatrixUtils::cross(float* result, const float* a, const float* b) {
    result[0] = a[1] * b[2] - a[2] * b[1];
    result[1] = a[2] * b[0] - a[0] * b[2];
    result[2] = a[0] * b[1] - a[1] * b[0];
}

float MatrixUtils::dot(const float* a, const float* b) {
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

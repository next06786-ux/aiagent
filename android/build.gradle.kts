// LifeSwarm 根级构建配置
// 对应鸿蒙端: harmonyos/build-profile.json5 + hvigorfile.ts

plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
}

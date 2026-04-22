// LifeSwarm App 模块构建配置
// 对应鸿蒙端: harmonyos/entry/build-profile.json5 + module.json5

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    id("kotlin-parcelize")
}

android {
    namespace = "com.lifeswarm.android"
    // 对应鸿蒙 module.json5 deviceTypes: ["phone","tablet","2in1"]
    compileSdk = 36

    defaultConfig {
        applicationId = "com.lifeswarm.app"
        // Android 8.0+ 对应鸿蒙最低设备要求
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "1.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        // 对应鸿蒙 ApiConfig.ets BASE_URL
        // 云服务器部署地址：82.157.195.238:8000
        // 注意：使用 http 协议（如果后端没有配置 HTTPS）
        buildConfigField(
            "String",
            "API_BASE_URL",
            "\"http://82.157.195.238:8000\""
        )
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
        debug {
            isMinifyEnabled = false
            applicationIdSuffix = ".debug"
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = "11"
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    // AndroidX 核心
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)

    // Jetpack Compose BOM - 统一版本管理
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
    // Material Icons Extended - 对应鸿蒙 IconRenderer.ets 图标库
    implementation(libs.androidx.material.icons.extended)

    // Navigation Compose - 对应鸿蒙 router (pages/Login -> pages/AgentHome)
    implementation(libs.androidx.navigation.compose)

    // ViewModel + Compose - 对应鸿蒙 @State/@Link 状态管理
    implementation(libs.androidx.viewmodel.compose)
    implementation(libs.androidx.lifecycle.viewmodel.ktx)

    // 网络层 - 对应鸿蒙 HttpUtil.ets (@ohos.net.http)
    implementation(libs.retrofit)
    implementation(libs.retrofit.converter.gson)
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging.interceptor)
    // SSE流式 - 对应鸿蒙 HttpUtil.postStream()
    implementation(libs.okhttp.sse)

    // JSON - 对应鸿蒙 JSON.parse() / JSON.stringify()
    implementation(libs.gson)

    // 本地存储 - 对应鸿蒙 @ohos.data.preferences (lifeswarm_auth)
    implementation(libs.androidx.datastore.preferences)

    // 图片加载 - 对应鸿蒙 Image 组件
    implementation(libs.coil.compose)

    // Markdown渲染 - 对应鸿蒙 MarkdownParser.ets
    implementation(libs.markwon.core)

    // CameraX - 对应鸿蒙 EnhancedCameraService.ets (@ohos.multimedia.camera)
    implementation(libs.androidx.camera.core)
    implementation(libs.androidx.camera.camera2)
    implementation(libs.androidx.camera.lifecycle)
    implementation(libs.androidx.camera.view)

    // Google Play Services Location - 对应鸿蒙 @ohos.geoLocationManager
    implementation(libs.play.services.location)

    // 协程 - 对应鸿蒙 async/await/Promise
    implementation(libs.kotlinx.coroutines.android)

    // 测试
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(platform(libs.androidx.compose.bom))
    androidTestImplementation(libs.androidx.ui.test.junit4)
    debugImplementation(libs.androidx.ui.tooling)
    debugImplementation(libs.androidx.ui.test.manifest)
}

# LifeSwarm ProGuard 规则

# Retrofit / OkHttp - 对应鸿蒙 HttpUtil.ets 网络层
-dontwarn retrofit2.**
-keep class retrofit2.** { *; }
-keepattributes Signature
-keepattributes Exceptions

# Gson - 对应鸿蒙 JSON.parse() / JSON.stringify()
-keepattributes *Annotation*
-dontwarn sun.misc.**
-keep class com.google.gson.** { *; }
-keep class * implements com.google.gson.TypeAdapterFactory
-keep class * implements com.google.gson.JsonSerializer
-keep class * implements com.google.gson.JsonDeserializer

# 保留数据模型类（对应鸿蒙 Types.ets / Task.ets 中的 interface/class）
-keep class com.lifeswarm.app.data.model.** { *; }
-keep class com.lifeswarm.app.config.** { *; }

# Compose
-keep class androidx.compose.** { *; }

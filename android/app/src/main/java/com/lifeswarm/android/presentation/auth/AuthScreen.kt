package com.lifeswarm.android.presentation.auth

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.lifeswarm.android.presentation.common.LoadingScreen

/**
 * 认证页面 - 对应 web/src/pages/AuthPage.tsx
 */
@Composable
fun AuthScreen(
    authViewModel: AuthViewModel,
    onNavigateToHome: () -> Unit
) {
    val authState by authViewModel.authState.collectAsState()
    val errorMessage by authViewModel.errorMessage.collectAsState()
    val isAuthenticated by authViewModel.isAuthenticated.collectAsState()
    
    var isLoginMode by remember { mutableStateOf(true) }
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var nickname by remember { mutableStateOf("") }
    
    // 监听认证状态，自动跳转
    LaunchedEffect(isAuthenticated) {
        if (isAuthenticated) {
            onNavigateToHome()
        }
    }
    
    when (authState) {
        is AuthState.Loading -> {
            LoadingScreen(
                title = if (isLoginMode) "正在登录..." else "正在注册...",
                message = "请稍候"
            )
        }
        else -> {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(16.dp),
                contentAlignment = Alignment.Center
            ) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        // 标题
                        Text(
                            text = if (isLoginMode) "登录择境" else "注册择境",
                            style = MaterialTheme.typography.headlineMedium,
                            color = MaterialTheme.colorScheme.primary
                        )
                        
                        // 用户名输入
                        OutlinedTextField(
                            value = username,
                            onValueChange = { username = it },
                            label = { Text("用户名") },
                            modifier = Modifier.fillMaxWidth(),
                            singleLine = true
                        )
                        
                        // 邮箱输入（仅注册时显示）
                        if (!isLoginMode) {
                            OutlinedTextField(
                                value = email,
                                onValueChange = { email = it },
                                label = { Text("邮箱") },
                                modifier = Modifier.fillMaxWidth(),
                                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                                singleLine = true
                            )
                            
                            OutlinedTextField(
                                value = nickname,
                                onValueChange = { nickname = it },
                                label = { Text("昵称（可选）") },
                                modifier = Modifier.fillMaxWidth(),
                                singleLine = true
                            )
                        }
                        
                        // 密码输入
                        OutlinedTextField(
                            value = password,
                            onValueChange = { password = it },
                            label = { Text("密码") },
                            modifier = Modifier.fillMaxWidth(),
                            visualTransformation = PasswordVisualTransformation(),
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                            singleLine = true
                        )
                        
                        // 错误消息
                        if (errorMessage != null) {
                            Text(
                                text = errorMessage!!,
                                color = MaterialTheme.colorScheme.error,
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                        
                        // 提交按钮
                        Button(
                            onClick = {
                                if (isLoginMode) {
                                    authViewModel.login(username, password)
                                } else {
                                    authViewModel.register(username, password, email, nickname.ifEmpty { null })
                                }
                            },
                            modifier = Modifier.fillMaxWidth(),
                            enabled = username.isNotEmpty() && password.isNotEmpty() &&
                                    (isLoginMode || email.isNotEmpty())
                        ) {
                            Text(if (isLoginMode) "登录" else "注册")
                        }
                        
                        // 切换模式
                        TextButton(
                            onClick = {
                                isLoginMode = !isLoginMode
                                authViewModel.clearError()
                            }
                        ) {
                            Text(
                                if (isLoginMode) "还没有账号？立即注册" else "已有账号？立即登录"
                            )
                        }
                    }
                }
            }
        }
    }
}

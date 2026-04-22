package com.lifeswarm.android.presentation.profile

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.lifeswarm.android.data.repository.AuthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * 修改密码页面 - 对应 web/src/pages/ProfilePage.tsx 的修改密码部分
 */

// ViewModel
class ChangePasswordViewModel(
    private val repository: AuthRepository,
    private val userId: String
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(ChangePasswordUiState())
    val uiState: StateFlow<ChangePasswordUiState> = _uiState.asStateFlow()
    
    fun updateOldPassword(value: String) {
        _uiState.value = _uiState.value.copy(oldPassword = value)
    }
    
    fun updateNewPassword(value: String) {
        _uiState.value = _uiState.value.copy(newPassword = value)
    }
    
    fun updateConfirmPassword(value: String) {
        _uiState.value = _uiState.value.copy(confirmPassword = value)
    }
    
    fun toggleOldPasswordVisibility() {
        _uiState.value = _uiState.value.copy(
            oldPasswordVisible = !_uiState.value.oldPasswordVisible
        )
    }
    
    fun toggleNewPasswordVisibility() {
        _uiState.value = _uiState.value.copy(
            newPasswordVisible = !_uiState.value.newPasswordVisible
        )
    }
    
    fun toggleConfirmPasswordVisibility() {
        _uiState.value = _uiState.value.copy(
            confirmPasswordVisible = !_uiState.value.confirmPasswordVisible
        )
    }
    
    fun changePassword() {
        val state = _uiState.value
        
        // 验证
        if (state.oldPassword.isBlank()) {
            _uiState.value = state.copy(error = "请输入旧密码")
            return
        }
        
        if (state.newPassword.isBlank()) {
            _uiState.value = state.copy(error = "请输入新密码")
            return
        }
        
        if (state.newPassword.length < 6) {
            _uiState.value = state.copy(error = "新密码至少需要 6 个字符")
            return
        }
        
        if (state.newPassword != state.confirmPassword) {
            _uiState.value = state.copy(error = "两次密码不一致")
            return
        }
        
        viewModelScope.launch {
            _uiState.value = state.copy(isLoading = true, error = "", success = "")
            
            try {
                val payload = com.lifeswarm.android.data.model.ChangePasswordPayload(
                    oldPassword = state.oldPassword,
                    newPassword = state.newPassword
                )
                
                repository.changePassword(userId, payload)
                
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    success = "密码已修改",
                    oldPassword = "",
                    newPassword = "",
                    confirmPassword = ""
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "修改失败"
                )
            }
        }
    }
}

data class ChangePasswordUiState(
    val oldPassword: String = "",
    val newPassword: String = "",
    val confirmPassword: String = "",
    val oldPasswordVisible: Boolean = false,
    val newPasswordVisible: Boolean = false,
    val confirmPasswordVisible: Boolean = false,
    val isLoading: Boolean = false,
    val error: String = "",
    val success: String = ""
)

// UI
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChangePasswordScreen(
    userId: String,
    onNavigateBack: () -> Unit,
    repository: AuthRepository
) {
    val viewModel: ChangePasswordViewModel = viewModel(
        factory = object : androidx.lifecycle.ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return ChangePasswordViewModel(repository, userId) as T
            }
        }
    )
    
    val uiState by viewModel.uiState.collectAsState()
    
    // 成功后自动返回
    LaunchedEffect(uiState.success) {
        if (uiState.success.isNotEmpty()) {
            kotlinx.coroutines.delay(1500)
            onNavigateBack()
        }
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("修改密码") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, "返回")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // 提示卡片
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                ),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Icon(
                        Icons.Default.Info,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        "密码至少需要 6 个字符，建议包含字母、数字和特殊字符",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            
            // 旧密码
            OutlinedTextField(
                value = uiState.oldPassword,
                onValueChange = { viewModel.updateOldPassword(it) },
                label = { Text("旧密码") },
                placeholder = { Text("请输入旧密码") },
                modifier = Modifier.fillMaxWidth(),
                enabled = !uiState.isLoading,
                visualTransformation = if (uiState.oldPasswordVisible) {
                    VisualTransformation.None
                } else {
                    PasswordVisualTransformation()
                },
                leadingIcon = {
                    Icon(Icons.Default.Lock, contentDescription = null)
                },
                trailingIcon = {
                    IconButton(onClick = { viewModel.toggleOldPasswordVisibility() }) {
                        Icon(
                            if (uiState.oldPasswordVisible) {
                                Icons.Default.VisibilityOff
                            } else {
                                Icons.Default.Visibility
                            },
                            contentDescription = if (uiState.oldPasswordVisible) "隐藏密码" else "显示密码"
                        )
                    }
                },
                singleLine = true
            )
            
            // 新密码
            OutlinedTextField(
                value = uiState.newPassword,
                onValueChange = { viewModel.updateNewPassword(it) },
                label = { Text("新密码") },
                placeholder = { Text("请输入新密码") },
                modifier = Modifier.fillMaxWidth(),
                enabled = !uiState.isLoading,
                visualTransformation = if (uiState.newPasswordVisible) {
                    VisualTransformation.None
                } else {
                    PasswordVisualTransformation()
                },
                leadingIcon = {
                    Icon(Icons.Default.Lock, contentDescription = null)
                },
                trailingIcon = {
                    IconButton(onClick = { viewModel.toggleNewPasswordVisibility() }) {
                        Icon(
                            if (uiState.newPasswordVisible) {
                                Icons.Default.VisibilityOff
                            } else {
                                Icons.Default.Visibility
                            },
                            contentDescription = if (uiState.newPasswordVisible) "隐藏密码" else "显示密码"
                        )
                    }
                },
                singleLine = true
            )
            
            // 确认密码
            OutlinedTextField(
                value = uiState.confirmPassword,
                onValueChange = { viewModel.updateConfirmPassword(it) },
                label = { Text("确认新密码") },
                placeholder = { Text("请再次输入新密码") },
                modifier = Modifier.fillMaxWidth(),
                enabled = !uiState.isLoading,
                visualTransformation = if (uiState.confirmPasswordVisible) {
                    VisualTransformation.None
                } else {
                    PasswordVisualTransformation()
                },
                leadingIcon = {
                    Icon(Icons.Default.Lock, contentDescription = null)
                },
                trailingIcon = {
                    IconButton(onClick = { viewModel.toggleConfirmPasswordVisibility() }) {
                        Icon(
                            if (uiState.confirmPasswordVisible) {
                                Icons.Default.VisibilityOff
                            } else {
                                Icons.Default.Visibility
                            },
                            contentDescription = if (uiState.confirmPasswordVisible) "隐藏密码" else "显示密码"
                        )
                    }
                },
                singleLine = true
            )
            
            // 成功提示
            if (uiState.success.isNotEmpty()) {
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer
                    ),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Icon(
                            Icons.Default.CheckCircle,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary
                        )
                        Text(
                            uiState.success,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                    }
                }
            }
            
            // 错误提示
            if (uiState.error.isNotEmpty()) {
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.errorContainer
                    ),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Icon(
                            Icons.Default.Error,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.error
                        )
                        Text(
                            uiState.error,
                            color = MaterialTheme.colorScheme.onErrorContainer
                        )
                    }
                }
            }
            
            // 提交按钮
            Button(
                onClick = { viewModel.changePassword() },
                modifier = Modifier.fillMaxWidth(),
                enabled = !uiState.isLoading
            ) {
                if (uiState.isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onPrimary
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                }
                Text("修改密码")
            }
        }
    }
}

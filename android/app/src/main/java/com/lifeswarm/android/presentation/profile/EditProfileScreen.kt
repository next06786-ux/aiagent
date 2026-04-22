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
import com.lifeswarm.android.data.model.UpdateProfilePayload
import com.lifeswarm.android.data.model.UserInfo
import com.lifeswarm.android.data.repository.AuthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * 编辑资料页面 - 对应 web/src/pages/ProfilePage.tsx 的编辑资料部分
 */

// ViewModel
class EditProfileViewModel(
    private val repository: AuthRepository,
    private val currentUser: UserInfo
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(EditProfileUiState(
        nickname = currentUser.nickname ?: "",
        phone = currentUser.phone ?: "",
        avatarUrl = currentUser.avatarUrl ?: ""
    ))
    val uiState: StateFlow<EditProfileUiState> = _uiState.asStateFlow()
    
    fun updateNickname(value: String) {
        _uiState.value = _uiState.value.copy(nickname = value)
    }
    
    fun updatePhone(value: String) {
        _uiState.value = _uiState.value.copy(phone = value)
    }
    
    fun updateAvatarUrl(value: String) {
        _uiState.value = _uiState.value.copy(avatarUrl = value)
    }
    
    fun saveProfile() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = "", success = "")
            
            try {
                val payload = UpdateProfilePayload(
                    nickname = _uiState.value.nickname.takeIf { it.isNotBlank() },
                    phone = _uiState.value.phone.takeIf { it.isNotBlank() },
                    avatarUrl = _uiState.value.avatarUrl.takeIf { it.isNotBlank() }
                )
                
                repository.updateUser(currentUser.userId, payload)
                
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    success = "资料已更新"
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.message ?: "更新失败"
                )
            }
        }
    }
}

data class EditProfileUiState(
    val nickname: String = "",
    val phone: String = "",
    val avatarUrl: String = "",
    val isLoading: Boolean = false,
    val error: String = "",
    val success: String = ""
)

// UI
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditProfileScreen(
    user: UserInfo,
    onNavigateBack: () -> Unit,
    repository: AuthRepository
) {
    val viewModel: EditProfileViewModel = viewModel(
        factory = object : androidx.lifecycle.ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return EditProfileViewModel(repository, user) as T
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
                title = { Text("编辑资料") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, "返回")
                    }
                },
                actions = {
                    TextButton(
                        onClick = { viewModel.saveProfile() },
                        enabled = !uiState.isLoading
                    ) {
                        Text("保存")
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
            // 用户名（不可编辑）
            OutlinedTextField(
                value = user.username,
                onValueChange = {},
                label = { Text("用户名") },
                enabled = false,
                modifier = Modifier.fillMaxWidth(),
                leadingIcon = {
                    Icon(Icons.Default.Person, contentDescription = null)
                }
            )
            
            // 昵称
            OutlinedTextField(
                value = uiState.nickname,
                onValueChange = { viewModel.updateNickname(it) },
                label = { Text("昵称") },
                placeholder = { Text("请输入昵称") },
                modifier = Modifier.fillMaxWidth(),
                enabled = !uiState.isLoading,
                leadingIcon = {
                    Icon(Icons.Default.Badge, contentDescription = null)
                }
            )
            
            // 手机号
            OutlinedTextField(
                value = uiState.phone,
                onValueChange = { viewModel.updatePhone(it) },
                label = { Text("手机号") },
                placeholder = { Text("请输入手机号") },
                modifier = Modifier.fillMaxWidth(),
                enabled = !uiState.isLoading,
                leadingIcon = {
                    Icon(Icons.Default.Phone, contentDescription = null)
                }
            )
            
            // 邮箱（不可编辑）
            OutlinedTextField(
                value = user.email,
                onValueChange = {},
                label = { Text("邮箱") },
                enabled = false,
                modifier = Modifier.fillMaxWidth(),
                leadingIcon = {
                    Icon(Icons.Default.Email, contentDescription = null)
                }
            )
            
            // 头像 URL
            OutlinedTextField(
                value = uiState.avatarUrl,
                onValueChange = { viewModel.updateAvatarUrl(it) },
                label = { Text("头像 URL") },
                placeholder = { Text("请输入头像图片地址") },
                modifier = Modifier.fillMaxWidth(),
                enabled = !uiState.isLoading,
                leadingIcon = {
                    Icon(Icons.Default.Image, contentDescription = null)
                },
                minLines = 2
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
            
            // 加载状态
            if (uiState.isLoading) {
                LinearProgressIndicator(
                    modifier = Modifier.fillMaxWidth()
                )
            }
        }
    }
}

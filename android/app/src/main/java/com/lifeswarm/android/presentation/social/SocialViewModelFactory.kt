package com.lifeswarm.android.presentation.social

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider

/**
 * SocialViewModel 工厂类
 */
class SocialViewModelFactory(
    private val userId: String
) : ViewModelProvider.Factory {
    
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(SocialViewModel::class.java)) {
            return SocialViewModel(userId) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class: ${modelClass.name}")
    }
}

package com.lifeswarm.android.presentation.insight

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider

/**
 * InsightsViewModel 工厂类
 */
class InsightsViewModelFactory(
    private val token: String
) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(InsightsViewModel::class.java)) {
            return InsightsViewModel(token) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class: ${modelClass.name}")
    }
}

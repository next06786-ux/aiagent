package com.lifeswarm.android.presentation.parallellife

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider

/**
 * ParallelLifeViewModel 工厂类
 */
class ParallelLifeViewModelFactory(
    private val userId: String
) : ViewModelProvider.Factory {
    
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(ParallelLifeViewModel::class.java)) {
            return ParallelLifeViewModel(userId) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class: ${modelClass.name}")
    }
}

package com.lifeswarm.android.presentation.treehole

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider

/**
 * TreeHoleViewModel 工厂类
 */
class TreeHoleViewModelFactory(
    private val userId: String
) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(TreeHoleViewModel::class.java)) {
            return TreeHoleViewModel(userId) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class: ${modelClass.name}")
    }
}

package com.lifeswarm.android.presentation.treehole

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider

/**
 * TreeHoleDetailViewModel 工厂类
 */
class TreeHoleDetailViewModelFactory(
    private val userId: String,
    private val treeHoleId: String
) : ViewModelProvider.Factory {
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(TreeHoleDetailViewModel::class.java)) {
            return TreeHoleDetailViewModel(userId, treeHoleId) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class: ${modelClass.name}")
    }
}

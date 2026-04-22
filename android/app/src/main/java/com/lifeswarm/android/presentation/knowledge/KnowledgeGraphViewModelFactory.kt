package com.lifeswarm.android.presentation.knowledge

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.lifeswarm.android.data.repository.KnowledgeGraphRepository

/**
 * 知识图谱 ViewModel 工厂
 */
class KnowledgeGraphViewModelFactory(
    private val repository: KnowledgeGraphRepository,
    private val userId: String
) : ViewModelProvider.Factory {
    
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(KnowledgeGraphViewModel::class.java)) {
            return KnowledgeGraphViewModel(repository, userId) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}

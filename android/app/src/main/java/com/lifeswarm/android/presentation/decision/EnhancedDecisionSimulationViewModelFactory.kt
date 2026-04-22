package com.lifeswarm.android.presentation.decision

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.lifeswarm.android.data.model.CollectedInfo
import com.lifeswarm.android.data.model.OptionInput

/**
 * EnhancedDecisionSimulationViewModel 的工厂类
 */
class EnhancedDecisionSimulationViewModelFactory(
    private val sessionId: String,
    private val userId: String,
    private val question: String,
    private val options: List<OptionInput>,
    private val collectedInfo: CollectedInfo?,
    private val decisionType: String
) : ViewModelProvider.Factory {
    
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(EnhancedDecisionSimulationViewModel::class.java)) {
            return EnhancedDecisionSimulationViewModel(
                sessionId = sessionId,
                userId = userId,
                question = question,
                options = options,
                collectedInfo = collectedInfo,
                decisionType = decisionType
            ) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}

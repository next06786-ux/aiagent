package com.lifeswarm.android.presentation.parallellife

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.lifeswarm.android.data.model.DecisionProfile
import com.lifeswarm.android.data.model.TarotCard
import com.lifeswarm.android.data.repository.ParallelLifeRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * 游戏阶段
 */
enum class GamePhase {
    INTRO,      // 介绍
    DRAWING,    // 抽牌中
    CHOOSING,   // 选择中
    RESULT      // 结果
}

/**
 * UI 状态
 */
data class ParallelLifeUiState(
    val phase: GamePhase = GamePhase.INTRO,
    val currentCard: TarotCard? = null,
    val profile: DecisionProfile? = null,
    val progress: Float = 0f,
    val isDrawing: Boolean = false,
    val error: String = ""
)

/**
 * 平行人生 ViewModel
 */
class ParallelLifeViewModel(
    private val userId: String,
    private val repository: ParallelLifeRepository = ParallelLifeRepository()
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(ParallelLifeUiState())
    val uiState: StateFlow<ParallelLifeUiState> = _uiState.asStateFlow()
    
    private val drawnCards = mutableListOf<String>()
    
    companion object {
        private const val TAG = "ParallelLifeViewModel"
        private const val TOTAL_CARDS = 21 // 总共21张牌
    }
    
    /**
     * 开始游戏
     */
    fun startGame() {
        _uiState.value = _uiState.value.copy(
            phase = GamePhase.DRAWING,
            progress = 0f,
            error = ""
        )
        
        // 延迟后开始抽牌
        viewModelScope.launch {
            kotlinx.coroutines.delay(800)
            drawCard()
        }
    }
    
    /**
     * 抽取塔罗牌
     */
    fun drawCard() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isDrawing = true, error = "")
            
            try {
                val result = repository.drawCard(userId, drawnCards)
                
                result.onSuccess { card ->
                    // 记录已抽取的牌
                    drawnCards.add(card.cardKey)
                    
                    // 等待抽牌动画完成
                    kotlinx.coroutines.delay(2500)
                    
                    _uiState.value = _uiState.value.copy(
                        currentCard = card,
                        isDrawing = false,
                        phase = GamePhase.CHOOSING
                    )
                    
                    Log.d(TAG, "抽牌成功: ${card.card} - ${card.dimension}")
                }.onFailure { e ->
                    Log.e(TAG, "抽牌失败", e)
                    _uiState.value = _uiState.value.copy(
                        isDrawing = false,
                        error = e.message ?: "抽牌失败"
                    )
                }
            } catch (e: Exception) {
                Log.e(TAG, "抽牌异常", e)
                _uiState.value = _uiState.value.copy(
                    isDrawing = false,
                    error = e.message ?: "抽牌异常"
                )
            }
        }
    }
    
    /**
     * 提交选择
     */
    fun submitChoice(optionText: String, tendency: String) {
        val card = _uiState.value.currentCard ?: return
        
        viewModelScope.launch {
            try {
                val result = repository.submitChoice(
                    userId = userId,
                    card = card.card,
                    cardKey = card.cardKey,
                    dimension = card.dimension,
                    dimensionKey = card.dimensionKey,
                    scenario = card.scenario,
                    choice = optionText,
                    tendency = tendency
                )
                
                result.onSuccess {
                    // 更新进度
                    val newProgress = _uiState.value.progress + (100f / TOTAL_CARDS)
                    _uiState.value = _uiState.value.copy(progress = newProgress)
                    
                    Log.d(TAG, "提交选择成功，进度: $newProgress")
                    
                    // 检查是否完成
                    if (newProgress >= 100f) {
                        // 游戏完成，获取画像
                        fetchProfile()
                    } else {
                        // 继续抽牌
                        _uiState.value = _uiState.value.copy(phase = GamePhase.DRAWING)
                        kotlinx.coroutines.delay(800)
                        drawCard()
                    }
                }.onFailure { e ->
                    Log.e(TAG, "提交选择失败", e)
                    _uiState.value = _uiState.value.copy(
                        error = e.message ?: "提交失败"
                    )
                }
            } catch (e: Exception) {
                Log.e(TAG, "提交选择异常", e)
                _uiState.value = _uiState.value.copy(
                    error = e.message ?: "提交异常"
                )
            }
        }
    }
    
    /**
     * 提前结束
     */
    fun finishEarly() {
        fetchProfile()
    }
    
    /**
     * 获取决策画像
     */
    private fun fetchProfile() {
        viewModelScope.launch {
            try {
                val result = repository.getDecisionProfile(userId)
                
                result.onSuccess { profile ->
                    _uiState.value = _uiState.value.copy(
                        profile = profile,
                        phase = GamePhase.RESULT
                    )
                    Log.d(TAG, "获取画像成功: ${profile.totalChoices} 次选择")
                }.onFailure { e ->
                    Log.e(TAG, "获取画像失败", e)
                    _uiState.value = _uiState.value.copy(
                        error = e.message ?: "获取画像失败"
                    )
                }
            } catch (e: Exception) {
                Log.e(TAG, "获取画像异常", e)
                _uiState.value = _uiState.value.copy(
                    error = e.message ?: "获取画像异常"
                )
            }
        }
    }
    
    /**
     * 重新开始
     */
    fun restart() {
        drawnCards.clear()
        _uiState.value = ParallelLifeUiState()
    }
}

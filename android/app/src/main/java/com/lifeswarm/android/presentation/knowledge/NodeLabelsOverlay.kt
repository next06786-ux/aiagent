package com.lifeswarm.android.presentation.knowledge

import android.opengl.Matrix
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Paint
import androidx.compose.ui.graphics.PaintingStyle
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import com.lifeswarm.android.presentation.knowledge.opengl.Node

/**
 * 节点标签叠加层
 * 在 OpenGL 视图上方绘制节点名称文字
 */
@Composable
fun NodeLabelsOverlay(
    nodes: List<Node>,
    mvpMatrix: FloatArray,
    viewWidth: Int,
    viewHeight: Int,
    selectedNodeId: String?,
    modifier: Modifier = Modifier
) {
    val density = LocalDensity.current
    val textSize = with(density) { 12.dp.toPx() }
    val selectedTextSize = with(density) { 14.dp.toPx() }
    
    Canvas(modifier = modifier.fillMaxSize()) {
        drawIntoCanvas { canvas ->
            val nativeCanvas = canvas.nativeCanvas
            
            // 创建文字画笔
            val textPaint = android.graphics.Paint().apply {
                isAntiAlias = true
                textAlign = android.graphics.Paint.Align.CENTER
            }
            
            // 创建背景画笔
            val bgPaint = android.graphics.Paint().apply {
                isAntiAlias = true
                style = android.graphics.Paint.Style.FILL
            }
            
            nodes.forEach { node ->
                // 将 3D 坐标投影到屏幕坐标
                val screenPos = projectToScreen(
                    node.x, node.y, node.z,
                    mvpMatrix, viewWidth, viewHeight
                )
                
                if (screenPos != null && screenPos.isValid) {
                    val isSelected = node.id == selectedNodeId
                    
                    // 设置文字大小和颜色
                    textPaint.textSize = if (isSelected) selectedTextSize else textSize
                    textPaint.color = if (isSelected) {
                        android.graphics.Color.WHITE
                    } else {
                        android.graphics.Color.argb(200, 255, 255, 255)
                    }
                    
                    // 计算文字尺寸
                    val textBounds = android.graphics.Rect()
                    textPaint.getTextBounds(node.label, 0, node.label.length, textBounds)
                    
                    // 文字位置（节点下方）
                    val textX = screenPos.x
                    val textY = screenPos.y + 25f
                    
                    // 绘制半透明背景
                    val padding = 8f
                    val bgLeft = textX - textBounds.width() / 2f - padding
                    val bgTop = textY - textBounds.height() - padding
                    val bgRight = textX + textBounds.width() / 2f + padding
                    val bgBottom = textY + padding
                    
                    bgPaint.color = if (isSelected) {
                        android.graphics.Color.argb(180, 100, 80, 200)
                    } else {
                        android.graphics.Color.argb(120, 0, 0, 0)
                    }
                    
                    nativeCanvas.drawRoundRect(
                        bgLeft, bgTop, bgRight, bgBottom,
                        6f, 6f, bgPaint
                    )
                    
                    // 绘制文字
                    nativeCanvas.drawText(
                        node.label,
                        textX,
                        textY,
                        textPaint
                    )
                }
            }
        }
    }
}

/**
 * 投影结果
 */
data class ProjectionResult(
    val x: Float,
    val y: Float,
    val isValid: Boolean
)

/**
 * 将 3D 世界坐标投影到 2D 屏幕坐标
 */
fun projectToScreen(
    x: Float, y: Float, z: Float,
    mvpMatrix: FloatArray,
    viewWidth: Int,
    viewHeight: Int
): ProjectionResult? {
    // 世界坐标
    val pos = FloatArray(4)
    pos[0] = x
    pos[1] = y
    pos[2] = z
    pos[3] = 1f
    
    // 转换到裁剪空间
    val clipPos = FloatArray(4)
    Matrix.multiplyMV(clipPos, 0, mvpMatrix, 0, pos, 0)
    
    // 检查是否在相机后面
    if (clipPos[3] <= 0f) {
        return ProjectionResult(0f, 0f, false)
    }
    
    // 归一化设备坐标 (NDC)
    val ndcX = clipPos[0] / clipPos[3]
    val ndcY = clipPos[1] / clipPos[3]
    val ndcZ = clipPos[2] / clipPos[3]
    
    // 检查是否在视锥体内
    if (ndcX < -1f || ndcX > 1f || ndcY < -1f || ndcY > 1f || ndcZ < -1f || ndcZ > 1f) {
        return ProjectionResult(0f, 0f, false)
    }
    
    // 转换到屏幕坐标
    val screenX = (ndcX + 1f) * 0.5f * viewWidth
    val screenY = (1f - ndcY) * 0.5f * viewHeight
    
    return ProjectionResult(screenX, screenY, true)
}

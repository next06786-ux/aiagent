package com.lifeswarm.android.presentation.home

import android.graphics.BlurMaskFilter
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.zIndex
import kotlinx.coroutines.isActive
import kotlin.math.*

/**
 * 增强版主界面 - 对齐 Web 端五角星布局
 * 
 * 特性：
 * - 中央 AI 核心大球
 * - 5个功能球体环绕布局
 * - 粒子流动动画
 * - 毛玻璃和光晕效果
 * - 底部导航栏
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EnhancedHomeScreen(
    onNavigateToChat: () -> Unit,
    onNavigateToDecision: () -> Unit,
    onNavigateToKnowledgeGraph: () -> Unit,
    onNavigateToInsights: () -> Unit,
    onNavigateToParallelLife: () -> Unit,
    onNavigateToSocial: () -> Unit,
    onNavigateToProfile: () -> Unit
) {
    // 动画状态
    val infiniteTransition = rememberInfiniteTransition(label = "home_animation")
    
    // 粒子动画
    val particleProgress by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(3000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "particle_progress"
    )
    
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.White)  // 白色背景
    ) {
        // 动态浮动光斑背景
        AnimatedBackgroundBlobs()
        
        // 背景粒子和网格
        BackgroundEffects(particleProgress)
        
        // 主内容区域
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(bottom = 80.dp)  // 为底部导航栏留空间
        ) {
            // 顶部品牌文字
            SideText(
                modifier = Modifier
                    .align(Alignment.TopCenter)
                    .padding(top = 32.dp)
            )
            
            // 五角星布局的功能球体
            PentagramLayout(
                onCenterClick = onNavigateToChat,
                onDecisionClick = onNavigateToDecision,
                onKnowledgeClick = onNavigateToKnowledgeGraph,
                onInsightsClick = onNavigateToInsights,
                onParallelLifeClick = onNavigateToParallelLife,
                onSocialClick = onNavigateToSocial,
                particleProgress = particleProgress
            )
            
            // 右上角个人中心按钮
            IconButton(
                onClick = onNavigateToProfile,
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(16.dp)
            ) {
                Icon(
                    Icons.Default.Person,
                    contentDescription = "个人中心",
                    tint = Color(0xFF1a1a1a).copy(alpha = 0.6f)  // 深色图标
                )
            }
        }
        
        // 底部导航栏
        BottomNavigationBar(
            modifier = Modifier.align(Alignment.BottomCenter),
            onNavigateToHome = {},  // 已在主页
            onNavigateToDecision = onNavigateToDecision,
            onNavigateToChat = onNavigateToChat,
            onNavigateToProfile = onNavigateToProfile
        )
    }
}

/**
 * 能量粒子流动动画（连续动画，对齐Web端）
 */
@Composable
fun EnergyParticles(
    nodes: List<NodeData>,
    centerX: Float,
    centerY: Float,
    particleProgress: Float
) {
    // 使用LaunchedEffect创建连续动画
    var animationTime by remember { mutableStateOf(0f) }
    
    LaunchedEffect(Unit) {
        val startTime = System.currentTimeMillis()
        while (true) {
            withFrameMillis { frameTime ->
                animationTime = (frameTime - startTime) / 1000f  // 转换为秒
            }
        }
    }
    
    // 为每个节点创建8个粒子（与Web端一致）
    val particles = remember(nodes) {
        nodes.flatMapIndexed { nodeIdx, _ ->
            (0 until 8).map { i ->
                ParticleData(
                    nodeIdx = nodeIdx,
                    initialT = i / 8f,
                    speed = 0.0018f + (Math.random() * 0.0012f).toFloat(),
                    size = 2.5f + (Math.random() * 2f).toFloat(),
                    opacity = 0.6f + (Math.random() * 0.4f).toFloat()
                )
            }
        }
    }
    
    Canvas(
        modifier = Modifier
            .fillMaxSize()
            .zIndex(2f)
    ) {
        val coreRadius = 100.dp.toPx()  // AI核心半径
        val fadeStart = coreRadius
        val fadeEnd = coreRadius + 50.dp.toPx()
        
        particles.forEach { particle ->
            val node = nodes[particle.nodeIdx]
            
            // 计算粒子当前位置（沿贝塞尔曲线）
            var t = (particle.initialT + animationTime * particle.speed) % 1f
            
            // 贝塞尔曲线控制点
            val mx = (centerX + node.x) / 2 + (node.y - centerY) * 0.18f
            val my = (centerY + node.y) / 2 - (node.x - centerX) * 0.18f
            
            // 二次贝塞尔曲线公式
            val px = (1 - t) * (1 - t) * centerX + 2 * (1 - t) * t * mx + t * t * node.x
            val py = (1 - t) * (1 - t) * centerY + 2 * (1 - t) * t * my + t * t * node.y
            
            // 计算距离中心的距离
            val distToCenter = sqrt((px - centerX).pow(2) + (py - centerY).pow(2))
            
            // 根据距离计算淡出透明度
            val fadeAlpha = when {
                distToCenter < fadeStart -> 0f
                distToCenter < fadeEnd -> (distToCenter - fadeStart) / (fadeEnd - fadeStart)
                else -> 1f
            }
            
            // 只绘制不在避让区域的粒子
            if (fadeAlpha > 0.1f) {
                // 粒子大小随位置变化（接近终点时变大）
                val boost = if (t > 0.8f) (t - 0.8f) / 0.2f else 0f
                val radius = particle.size * (1 + boost * 1.5f)
                
                // 透明度随位置变化，并应用淡出效果
                val alpha = particle.opacity * (0.4f + t * 0.6f) * fadeAlpha
                
                // 绘制粒子（径向渐变）
                drawCircle(
                    brush = Brush.radialGradient(
                        colors = listOf(
                            node.gradient[1].copy(alpha = alpha),
                            node.gradient[1].copy(alpha = 0f)
                        ),
                        center = Offset(px, py),
                        radius = radius * 2.5f
                    ),
                    radius = radius * 2.5f,
                    center = Offset(px, py)
                )
            }
        }
    }
}

/**
 * 粒子数据
 */
data class ParticleData(
    val nodeIdx: Int,
    val initialT: Float,
    val speed: Float,
    val size: Float,
    val opacity: Float
)

/**
 * 动态浮动光斑背景
 */
@Composable
fun AnimatedBackgroundBlobs() {
    val infiniteTransition = rememberInfiniteTransition(label = "blob_animation")
    
    // 光斑1的动画
    val blob1Offset by infiniteTransition.animateValue(
        initialValue = Offset(0f, 0f),
        targetValue = Offset(50f, -80f),
        typeConverter = TwoWayConverter(
            convertToVector = { AnimationVector2D(it.x, it.y) },
            convertFromVector = { Offset(it.v1, it.v2) }
        ),
        animationSpec = infiniteRepeatable(
            animation = keyframes {
                durationMillis = 25000
                Offset(0f, 0f) at 0
                Offset(50f, -80f) at 8333
                Offset(-40f, 50f) at 16666
                Offset(0f, 0f) at 25000
            },
            repeatMode = RepeatMode.Restart
        ),
        label = "blob1"
    )
    
    val blob1Scale by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1.1f,
        animationSpec = infiniteRepeatable(
            animation = keyframes {
                durationMillis = 25000
                1f at 0
                1.1f at 8333
                0.95f at 16666
                1f at 25000
            },
            repeatMode = RepeatMode.Restart
        ),
        label = "blob1_scale"
    )
    
    // 光斑2的动画
    val blob2Offset by infiniteTransition.animateValue(
        initialValue = Offset(0f, 0f),
        targetValue = Offset(50f, -80f),
        typeConverter = TwoWayConverter(
            convertToVector = { AnimationVector2D(it.x, it.y) },
            convertFromVector = { Offset(it.v1, it.v2) }
        ),
        animationSpec = infiniteRepeatable(
            animation = keyframes {
                durationMillis = 25000
                Offset(0f, 0f) at 0
                Offset(50f, -80f) at 8333
                Offset(-40f, 50f) at 16666
                Offset(0f, 0f) at 25000
            },
            repeatMode = RepeatMode.Restart
        ),
        label = "blob2"
    )
    
    val blob2Scale by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1.1f,
        animationSpec = infiniteRepeatable(
            animation = keyframes {
                durationMillis = 25000
                1f at 0
                1.1f at 8333
                0.95f at 16666
                1f at 25000
            },
            repeatMode = RepeatMode.Restart
        ),
        label = "blob2_scale"
    )
    
    // 光斑3的动画
    val blob3Offset by infiniteTransition.animateValue(
        initialValue = Offset(0f, 0f),
        targetValue = Offset(50f, -80f),
        typeConverter = TwoWayConverter(
            convertToVector = { AnimationVector2D(it.x, it.y) },
            convertFromVector = { Offset(it.v1, it.v2) }
        ),
        animationSpec = infiniteRepeatable(
            animation = keyframes {
                durationMillis = 25000
                Offset(0f, 0f) at 0
                Offset(50f, -80f) at 8333
                Offset(-40f, 50f) at 16666
                Offset(0f, 0f) at 25000
            },
            repeatMode = RepeatMode.Restart
        ),
        label = "blob3"
    )
    
    val blob3Scale by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1.1f,
        animationSpec = infiniteRepeatable(
            animation = keyframes {
                durationMillis = 25000
                1f at 0
                1.1f at 8333
                0.95f at 16666
                1f at 25000
            },
            repeatMode = RepeatMode.Restart
        ),
        label = "blob3_scale"
    )
    
    Box(
        modifier = Modifier
            .fillMaxSize()
            .zIndex(0f)
    ) {
        // 光斑1 - 蓝色
        Box(
            modifier = Modifier
                .size(300.dp)
                .offset(x = (-75).dp + blob1Offset.x.dp, y = (-100).dp + blob1Offset.y.dp)
                .scale(blob1Scale)
                .blur(60.dp)
                .background(
                    Brush.radialGradient(
                        colors = listOf(
                            Color(0x140A59F7),  // rgba(10, 89, 247, 0.08)
                            Color.Transparent
                        )
                    ),
                    shape = CircleShape
                )
        )
        
        // 光斑2 - 紫色
        Box(
            modifier = Modifier
                .size(250.dp)
                .align(Alignment.CenterEnd)
                .offset(x = (-75).dp + blob2Offset.x.dp, y = blob2Offset.y.dp)
                .scale(blob2Scale)
                .blur(60.dp)
                .background(
                    Brush.radialGradient(
                        colors = listOf(
                            Color(0x0F6B48FF),  // rgba(107, 72, 255, 0.06)
                            Color.Transparent
                        )
                    ),
                    shape = CircleShape
                )
        )
        
        // 光斑3 - 青色
        Box(
            modifier = Modifier
                .size(200.dp)
                .align(Alignment.BottomStart)
                .offset(x = 150.dp + blob3Offset.x.dp, y = (-50).dp + blob3Offset.y.dp)
                .scale(blob3Scale)
                .blur(60.dp)
                .background(
                    Brush.radialGradient(
                        colors = listOf(
                            Color(0x0A00C8FF),  // rgba(0, 200, 255, 0.04)
                            Color.Transparent
                        )
                    ),
                    shape = CircleShape
                )
        )
    }
}

/**
 * 背景效果：六边形网格和装饰圆环（浅色版本）
 */
@Composable
fun BackgroundEffects(particleProgress: Float) {
    Canvas(
        modifier = Modifier
            .fillMaxSize()
            .zIndex(1f)
    ) {
        val centerX = size.width / 2
        val centerY = size.height / 2
        val maxRadius = min(size.width, size.height) * 0.52f
        
        // 绘制同心圆环（浅色版本）
        listOf(0.44f, 0.72f, 0.96f).forEachIndexed { index, ratio ->
            val radius = maxRadius * ratio
            drawCircle(
                color = Color(0x0A0A59F7),  // 保持浅蓝色
                radius = radius,
                center = Offset(centerX, centerY),
                style = Stroke(
                    width = if (index == 0) 1.5f else 1f,
                    pathEffect = if (index == 1) {
                        PathEffect.dashPathEffect(floatArrayOf(8f, 16f))
                    } else null
                )
            )
        }
        
        // 绘制六边形网格（浅色版本）
        val hexRadius = 40f
        val hexWidth = hexRadius * sqrt(3f)
        val hexHeight = hexRadius * 2
        
        for (row in -2 until (size.height / (hexHeight * 0.75f)).toInt() + 2) {
            for (col in -2 until (size.width / hexWidth).toInt() + 2) {
                val hx = col * hexWidth + (if (row % 2 == 0) 0f else hexWidth / 2)
                val hy = row * hexHeight * 0.75f
                
                val dist = sqrt((hx - centerX).pow(2) + (hy - centerY).pow(2))
                if (dist > maxRadius) continue
                
                val alpha = ((1 - dist / maxRadius) * 0.04f).coerceIn(0f, 1f)  // 降低透明度
                
                // 绘制六边形
                val path = Path().apply {
                    for (i in 0 until 6) {
                        val angle = (PI / 3 * i - PI / 6).toFloat()
                        val px = hx + hexRadius * 0.92f * cos(angle)
                        val py = hy + hexRadius * 0.92f * sin(angle)
                        if (i == 0) moveTo(px, py) else lineTo(px, py)
                    }
                    close()
                }
                
                drawPath(
                    path = path,
                    color = Color(0x0A0A59F7).copy(alpha = alpha),
                    style = Stroke(width = 0.7f)
                )
            }
        }
    }
}

/**
 * 五角星布局的功能球体
 */
@Composable
fun BoxScope.PentagramLayout(
    onCenterClick: () -> Unit,
    onDecisionClick: () -> Unit,
    onKnowledgeClick: () -> Unit,
    onInsightsClick: () -> Unit,
    onParallelLifeClick: () -> Unit,
    onSocialClick: () -> Unit,
    particleProgress: Float
) {
    // 使用 BoxWithConstraints 获取实际尺寸
    BoxWithConstraints(modifier = Modifier.fillMaxSize()) {
        val screenWidth = constraints.maxWidth.toFloat()
        val screenHeight = constraints.maxHeight.toFloat()
        val centerX = screenWidth / 2f
        val centerY = screenHeight / 2f
        
        // 五角星半径（根据屏幕大小调整，增大分散度）
        val radiusX = min(screenWidth, screenHeight) * 0.38f  // 横向半径
        val radiusY = min(screenWidth, screenHeight) * 0.45f  // 纵向半径（拉长）
        
        // 计算五角星的5个顶点位置（从正上方开始，顺时针）
        val angleOffset = -PI / 2  // 从正上方开始
        val angleStep = 2 * PI / 5  // 每个点间隔72度
        
        // 功能节点数据（使用计算出的位置，纵向拉长）
        val nodes = remember(screenWidth, screenHeight) {
            listOf(
                // 顶部：决策副本
                NodeData(
                    id = "decision",
                    title = "决策副本",
                    subtitle = "分析入口",
                    x = (centerX + radiusX * cos(angleOffset + angleStep * 0).toFloat()),
                    y = (centerY + radiusY * sin(angleOffset + angleStep * 0).toFloat()),
                    gradient = listOf(Color(0xFFE8F4FF), Color(0xFFB8DCFF)),
                    onClick = onDecisionClick
                ),
                // 右上：智慧洞察
                NodeData(
                    id = "insights",
                    title = "智慧洞察",
                    subtitle = "决策分析",
                    x = (centerX + radiusX * cos(angleOffset + angleStep * 1).toFloat()),
                    y = (centerY + radiusY * sin(angleOffset + angleStep * 1).toFloat()),
                    gradient = listOf(Color(0xFFD4EBFF), Color(0xFFA8D5FF)),
                    onClick = onInsightsClick
                ),
                // 右下：平行人生
                NodeData(
                    id = "parallel-life",
                    title = "平行人生",
                    subtitle = "塔罗游戏",
                    x = (centerX + radiusX * cos(angleOffset + angleStep * 2).toFloat()),
                    y = (centerY + radiusY * sin(angleOffset + angleStep * 2).toFloat()),
                    gradient = listOf(Color(0xFFC2E3FF), Color(0xFF8FC8FF)),
                    onClick = onParallelLifeClick
                ),
                // 左下：社交
                NodeData(
                    id = "social",
                    title = "社交",
                    subtitle = "好友互动",
                    x = (centerX + radiusX * cos(angleOffset + angleStep * 3).toFloat()),
                    y = (centerY + radiusY * sin(angleOffset + angleStep * 3).toFloat()),
                    gradient = listOf(Color(0xFFB0D9FF), Color(0xFF7DBDFF)),
                    onClick = onSocialClick
                ),
                // 左上：知识星图
                NodeData(
                    id = "knowledge",
                    title = "知识星图",
                    subtitle = "记忆星空",
                    x = (centerX + radiusX * cos(angleOffset + angleStep * 4).toFloat()),
                    y = (centerY + radiusY * sin(angleOffset + angleStep * 4).toFloat()),
                    gradient = listOf(Color(0xFFF0F7FF), Color(0xFFC8E2FF)),
                    onClick = onKnowledgeClick
                )
            )
        }
        
        // 绘制能量通道（从中心到各节点的贝塞尔曲线，靠近中心时虚化）
        Canvas(
            modifier = Modifier
                .fillMaxSize()
                .zIndex(1f)
        ) {
            val coreRadius = 100.dp.toPx()  // AI核心半径
            val fadeStart = coreRadius
            val fadeEnd = coreRadius + 50.dp.toPx()
            
            nodes.forEach { node ->
                // 贝塞尔曲线控制点（与Web端相同的算法）
                val mx = (centerX + node.x) / 2 + (node.y - centerY) * 0.18f
                val my = (centerY + node.y) / 2 - (node.x - centerX) * 0.18f
                
                // 分段绘制，实现渐变和虚化
                val segments = 100
                
                for (i in 0 until segments) {
                    val t1 = i.toFloat() / segments
                    val t2 = (i + 1).toFloat() / segments
                    
                    // 计算起点和终点（二次贝塞尔曲线公式）
                    val x1 = (1 - t1) * (1 - t1) * centerX + 2 * (1 - t1) * t1 * mx + t1 * t1 * node.x
                    val y1 = (1 - t1) * (1 - t1) * centerY + 2 * (1 - t1) * t1 * my + t1 * t1 * node.y
                    val x2 = (1 - t2) * (1 - t2) * centerX + 2 * (1 - t2) * t2 * mx + t2 * t2 * node.x
                    val y2 = (1 - t2) * (1 - t2) * centerY + 2 * (1 - t2) * t2 * my + t2 * t2 * node.y
                    
                    // 计算距离中心的距离
                    val dist1 = sqrt((x1 - centerX).pow(2) + (y1 - centerY).pow(2))
                    val dist2 = sqrt((x2 - centerX).pow(2) + (y2 - centerY).pow(2))
                    
                    // 根据距离计算透明度（靠近中心时淡出）
                    val alpha1 = when {
                        dist1 < fadeStart -> 0f
                        dist1 < fadeEnd -> (dist1 - fadeStart) / (fadeEnd - fadeStart)
                        else -> 1f
                    }
                    
                    val alpha2 = when {
                        dist2 < fadeStart -> 0f
                        dist2 < fadeEnd -> (dist2 - fadeStart) / (fadeEnd - fadeStart)
                        else -> 1f
                    }
                    
                    // 只绘制不在避让区域的线段
                    if (alpha1 > 0.05f || alpha2 > 0.05f) {
                        val avgAlpha = (alpha1 + alpha2) / 2f
                        
                        // 基于位置的颜色渐变（从中心到节点，逐渐增强）
                        val colorAlpha = avgAlpha * (0.2f + t1 * 0.3f)  // 0.2-0.5的范围
                        
                        drawLine(
                            color = node.gradient[1].copy(alpha = colorAlpha),
                            start = Offset(x1, y1),
                            end = Offset(x2, y2),
                            strokeWidth = 2.5f
                        )
                    }
                }
            }
        }
        
        // 流动粒子动画
        EnergyParticles(
            nodes = nodes,
            centerX = centerX,
            centerY = centerY,
            particleProgress = particleProgress
        )
        
        // 中央 AI 核心球体
        CentralCore(
            onClick = onCenterClick,
            modifier = Modifier.align(Alignment.Center)
        )
        
        // 周围功能节点（使用绝对位置）
        nodes.forEach { node ->
            FunctionNode(
                node = node,
                modifier = Modifier
                    .offset {
                        androidx.compose.ui.unit.IntOffset(
                            x = (node.x - 55.dp.toPx()).toInt(),  // 减去球体半径使其居中（110dp / 2 = 55dp）
                            y = (node.y - 55.dp.toPx()).toInt()
                        )
                    }
            )
        }
    }
}

/**
 * 中央 AI 核心球体 - 对齐Web端质感（带装饰环，无脉冲动画）
 */
@Composable
fun CentralCore(
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .size(200.dp)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        // 最外层光晕（柔和的白色光晕）
        Box(
            modifier = Modifier
                .size(280.dp)
                .blur(30.dp)
                .background(
                    Brush.radialGradient(
                        colors = listOf(
                            Color(0x66FFFFFF),  // rgba(255, 255, 255, 0.4)
                            Color(0x40B8DCFF),  // rgba(184, 220, 255, 0.25)
                            Color(0x26F0F7FF),  // rgba(240, 247, 255, 0.15)
                            Color.Transparent
                        )
                    ),
                    shape = CircleShape
                )
        )
        
        // 外层装饰环（大环）
        Box(
            modifier = Modifier
                .size(256.dp)
                .border(
                    width = 2.dp,
                    color = Color(0x66B8DCFF),  // rgba(184, 220, 255, 0.4)
                    shape = CircleShape
                )
        )
        
        // 中层装饰环（虚线环）
        Canvas(modifier = Modifier.size(220.dp)) {
            val radius = size.width / 2
            val dashLength = 8f
            val gapLength = 16f
            val circumference = 2 * PI.toFloat() * radius
            val totalDashLength = dashLength + gapLength
            val dashCount = (circumference / totalDashLength).toInt()
            
            for (i in 0 until dashCount) {
                val startAngle = (i * totalDashLength / circumference) * 360f
                val sweepAngle = (dashLength / circumference) * 360f
                drawArc(
                    color = Color(0x80C8E2FF),  // rgba(200, 226, 255, 0.5)
                    startAngle = startAngle - 90f,
                    sweepAngle = sweepAngle,
                    useCenter = false,
                    style = Stroke(width = 1.5f)
                )
            }
        }
        
        // 主球体 - 白色为主的渐变
        Box(
            modifier = Modifier
                .size(160.dp)
                .border(
                    width = 2.dp,
                    color = Color(0xCCB8DCFF),  // rgba(184, 220, 255, 0.8)
                    shape = CircleShape
                )
                .background(
                    Brush.radialGradient(
                        colors = listOf(
                            Color(0xFFFFFFFF),  // 中心纯白
                            Color(0xFAFFFFFF),  // 接近白色
                            Color(0xF5F8FCFF),  // rgba(248, 252, 255, 0.95)
                            Color(0xF0E8F4FF),  // rgba(232, 244, 255, 0.9)
                            Color(0xD9C8E2FF)   // rgba(200, 226, 255, 0.85)
                        ),
                        center = Offset(0.3f, 0.2f),  // 高光偏左上
                        radius = 1.2f
                    ),
                    shape = CircleShape
                )
                .clip(CircleShape),
            contentAlignment = Alignment.Center
        ) {
            // 顶部高光（强烈的白色高光）
            Box(
                modifier = Modifier
                    .size(88.dp)
                    .offset(x = (-25).dp, y = (-25).dp)
                    .background(
                        Brush.radialGradient(
                            colors = listOf(
                                Color(0xFFFFFFFF),  // 纯白
                                Color(0xE6FFFFFF),  // rgba(255, 255, 255, 0.9)
                                Color(0x80FFFFFF),  // rgba(255, 255, 255, 0.5)
                                Color.Transparent
                            )
                        ),
                        shape = CircleShape
                    )
            )
            
            // 侧面光
            Box(
                modifier = Modifier
                    .size(60.dp)
                    .offset(x = 35.dp, y = 10.dp)
                    .background(
                        Brush.radialGradient(
                            colors = listOf(
                                Color(0xB3FFFFFF),  // rgba(255, 255, 255, 0.7)
                                Color(0x40FFFFFF),
                                Color.Transparent
                            )
                        ),
                        shape = CircleShape
                    )
            )
            
            // 底部环境光
            Box(
                modifier = Modifier
                    .size(70.dp)
                    .offset(y = 40.dp)
                    .background(
                        Brush.radialGradient(
                            colors = listOf(
                                Color(0x99F0F7FF),  // rgba(240, 247, 255, 0.6)
                                Color.Transparent
                            )
                        ),
                        shape = CircleShape
                    )
            )
            
            // 网格纹理（可选）
            Canvas(modifier = Modifier.size(120.dp)) {
                val gridSize = 10.dp.toPx()
                for (i in 0..12) {
                    val pos = i * gridSize
                    drawLine(
                        color = Color(0x14FFFFFF),  // rgba(255, 255, 255, 0.08)
                        start = Offset(pos, 0f),
                        end = Offset(pos, size.height),
                        strokeWidth = 1f
                    )
                    drawLine(
                        color = Color(0x14FFFFFF),
                        start = Offset(0f, pos),
                        end = Offset(size.width, pos),
                        strokeWidth = 1f
                    )
                }
            }
            
            // 文字内容
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
            ) {
                Text(
                    text = "CENTRAL ENGINE",
                    fontSize = 8.sp,
                    fontWeight = FontWeight.Light,
                    color = Color(0x99000000),  // rgba(0, 0, 0, 0.6)
                    letterSpacing = 1.2.sp
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "AI 核心",
                    fontSize = 32.sp,
                    fontWeight = FontWeight.ExtraBold,
                    color = Color(0xE6000000),  // rgba(0, 0, 0, 0.9)
                    style = androidx.compose.ui.text.TextStyle(
                        shadow = androidx.compose.ui.graphics.Shadow(
                            color = Color(0x1A000000),
                            offset = Offset(0f, 2f),
                            blurRadius = 8f
                        )
                    )
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = "感知 / 分析 / 决策",
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Medium,
                    color = Color(0xB3000000)  // rgba(0, 0, 0, 0.7)
                )
            }
        }
    }
}

/**
 * 功能节点球体 - 增强质感（对齐Web端）
 */
@Composable
fun FunctionNode(
    node: NodeData,
    modifier: Modifier = Modifier
) {
    var isPressed by remember { mutableStateOf(false) }
    val scale by animateFloatAsState(
        targetValue = if (isPressed) 0.95f else 1f,
        animationSpec = spring(stiffness = Spring.StiffnessLow),
        label = "node_scale"
    )
    
    // 外层轨道光晕的脉冲动画
    val infiniteTransition = rememberInfiniteTransition(label = "node_pulse")
    val orbitPulse by infiniteTransition.animateFloat(
        initialValue = 1f,
        targetValue = 1.05f,
        animationSpec = infiniteRepeatable(
            animation = tween(4000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "orbit_pulse"
    )
    
    val orbitAlpha by infiniteTransition.animateFloat(
        initialValue = 0.65f,
        targetValue = 0.9f,
        animationSpec = infiniteRepeatable(
            animation = tween(4000, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "orbit_alpha"
    )
    
    Box(
        modifier = modifier
            .size(110.dp)
            .scale(scale)
            .clickable {
                isPressed = true
                node.onClick()
            },
        contentAlignment = Alignment.Center
    ) {
        // 外层轨道光晕（带脉冲动画）
        Box(
            modifier = Modifier
                .size(154.dp)  // 110 + 22*2
                .scale(orbitPulse)
                .border(
                    width = 1.dp,
                    color = Color(0x59B8DCFF).copy(alpha = orbitAlpha),  // rgba(184, 220, 255, 0.35)
                    shape = CircleShape
                )
                .blur(6.dp)
                .background(
                    Brush.radialGradient(
                        colors = listOf(
                            Color(0x80FFFFFF).copy(alpha = orbitAlpha),  // rgba(255, 255, 255, 0.5)
                            Color(0x40B8DCFF).copy(alpha = orbitAlpha * 0.5f),  // rgba(184, 220, 255, 0.25)
                            Color.Transparent
                        )
                    ),
                    shape = CircleShape
                )
        )
        
        // 主球体 - 增强阴影和内发光
        Box(
            modifier = Modifier
                .size(110.dp)
                .border(
                    width = 1.5.dp,
                    color = Color(0x99B8DCFF),  // rgba(184, 220, 255, 0.6)
                    shape = CircleShape
                )
                .background(
                    Brush.radialGradient(
                        colors = listOf(
                            Color(0xFAFFFFFF),  // rgba(255, 255, 255, 0.98) 中心高光
                            Color(0xD9FFFFFF),  // rgba(255, 255, 255, 0.85)
                            Color(0x99FFFFFF),  // rgba(255, 255, 255, 0.6)
                            node.gradient[0],   // 节点主色
                            node.gradient[1]    // 节点深色
                        ),
                        center = Offset(0.5f, 0.3f),  // 高光在顶部中心
                        radius = 1.0f
                    ),
                    shape = CircleShape
                )
                .clip(CircleShape),
            contentAlignment = Alignment.Center
        ) {
            // 顶部强烈高光
            Box(
                modifier = Modifier
                    .size(60.dp)
                    .offset(x = (-8).dp, y = (-12).dp)
                    .background(
                        Brush.radialGradient(
                            colors = listOf(
                                Color(0x8CFFFFFF),  // rgba(255, 255, 255, 0.55)
                                Color(0x33FFFFFF),  // rgba(255, 255, 255, 0.2)
                                Color.Transparent
                            )
                        ),
                        shape = CircleShape
                    )
            )
            
            // 侧面次级高光
            Box(
                modifier = Modifier
                    .size(22.dp)
                    .offset(x = 26.dp, y = 26.dp)
                    .background(
                        Brush.radialGradient(
                            colors = listOf(
                                Color(0x1FFFFFFF),  // rgba(255, 255, 255, 0.12)
                                Color.Transparent
                            )
                        ),
                        shape = CircleShape
                    )
            )
            
            // 噪点纹理层（使用Canvas绘制）
            Canvas(modifier = Modifier.fillMaxSize()) {
                // 绘制细微的噪点纹理
                for (i in 0 until 100) {
                    val x = (Math.random() * size.width).toFloat()
                    val y = (Math.random() * size.height).toFloat()
                    val dist = sqrt((x - size.width/2).pow(2) + (y - size.height/2).pow(2))
                    if (dist < size.width / 2) {
                        drawCircle(
                            color = Color.White.copy(alpha = 0.02f),
                            radius = 0.5f,
                            center = Offset(x, y)
                        )
                    }
                }
            }
            
            // 文字
            Column(
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = node.subtitle,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = Color(0x99000000),  // rgba(0, 0, 0, 0.6)
                    letterSpacing = 0.8.sp,
                    style = androidx.compose.ui.text.TextStyle(
                        brush = Brush.linearGradient(
                            colors = listOf(
                                Color(0x99000000),  // rgba(0, 0, 0, 0.6)
                                Color(0x73000000)   // rgba(0, 0, 0, 0.45)
                            )
                        )
                    )
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = node.title,
                    fontSize = 17.sp,
                    fontWeight = FontWeight.ExtraBold,
                    letterSpacing = (-0.01).sp,
                    style = androidx.compose.ui.text.TextStyle(
                        brush = Brush.linearGradient(
                            colors = listOf(
                                Color(0xE6000000),  // rgba(0, 0, 0, 0.9)
                                Color(0xBF000000)   // rgba(0, 0, 0, 0.75)
                            )
                        ),
                        shadow = androidx.compose.ui.graphics.Shadow(
                            color = Color(0x1A000000),
                            offset = Offset(0f, 2f),
                            blurRadius = 8f
                        )
                    )
                )
            }
        }
    }
    
    LaunchedEffect(isPressed) {
        if (isPressed) {
            kotlinx.coroutines.delay(100)
            isPressed = false
        }
    }
}

/**
 * 顶部品牌文字（居中版本）
 */
@Composable
fun SideText(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        // 品牌名称
        Text(
            text = "择境",
            fontSize = 32.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF1a1a1a),  // 深色文字
            textAlign = TextAlign.Center
        )
        Text(
            text = "CHOICEREALM",
            fontSize = 10.sp,
            fontWeight = FontWeight.Light,
            color = Color(0xFF1a1a1a).copy(alpha = 0.4f),  // 深色文字
            letterSpacing = 1.5.sp,
            textAlign = TextAlign.Center
        )
    }
}

/**
 * 底部导航栏（浅色版本）
 */
@Composable
fun BottomNavigationBar(
    modifier: Modifier = Modifier,
    onNavigateToHome: () -> Unit,
    onNavigateToDecision: () -> Unit,
    onNavigateToChat: () -> Unit,
    onNavigateToProfile: () -> Unit
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .height(80.dp),
        color = Color(0xFFF5F5F5).copy(alpha = 0.95f),  // 浅灰色背景
        shadowElevation = 8.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 24.dp),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically
        ) {
            NavItem("总览", Icons.Default.Home, true, onNavigateToHome)
            NavItem("决策", Icons.Default.AccountTree, false, onNavigateToDecision)
            NavItem("对话", Icons.Default.Chat, false, onNavigateToChat)
            NavItem("能力", Icons.Default.Apps, false) {}
            NavItem("我的", Icons.Default.Person, false, onNavigateToProfile)
        }
    }
}

@Composable
fun NavItem(
    label: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    isActive: Boolean,
    onClick: () -> Unit
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier.clickable(onClick = onClick)
    ) {
        Icon(
            imageVector = icon,
            contentDescription = label,
            tint = if (isActive) Color(0xFF0A59F7) else Color(0xFF1a1a1a).copy(alpha = 0.4f),  // 深色图标
            modifier = Modifier.size(24.dp)
        )
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            text = label,
            fontSize = 11.sp,
            color = if (isActive) Color(0xFF0A59F7) else Color(0xFF1a1a1a).copy(alpha = 0.4f)  // 深色文字
        )
    }
}

/**
 * 节点数据类
 */
data class NodeData(
    val id: String,
    val title: String,
    val subtitle: String,
    val x: Float,  // 绝对X坐标（像素）
    val y: Float,  // 绝对Y坐标（像素）
    val gradient: List<Color>,
    val onClick: () -> Unit
)

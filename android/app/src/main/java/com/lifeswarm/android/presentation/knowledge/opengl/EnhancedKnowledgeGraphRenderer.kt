package com.lifeswarm.android.presentation.knowledge.opengl

import android.opengl.GLES30
import android.opengl.GLSurfaceView
import android.opengl.Matrix
import javax.microedition.khronos.egl.EGLConfig
import javax.microedition.khronos.opengles.GL10
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * 增强版知识图谱渲染器 - OpenGL ES 3.0
 * 移植自 HarmonyOS C++ 实现
 * 
 * 特性：
 * - 多层发光节点
 * - 贝塞尔曲线连线
 * - 流光粒子系统
 * - 3D 球形背景星空
 * - 平滑缓动动画
 */
class EnhancedKnowledgeGraphRenderer : GLSurfaceView.Renderer {
    
    // 视图矩阵
    private val viewMatrix = FloatArray(16)
    private val projectionMatrix = FloatArray(16)
    private val mvpMatrix = FloatArray(16)
    
    // 相机参数
    private var cameraDistance = 220f
    private var cameraAngleX = 0.3f
    private var cameraAngleY = 0f
    
    // 相机目标（用于聚焦节点）
    private var targetX = 0f
    private var targetY = 0f
    private var targetZ = 0f
    
    // 选中的节点
    private var selectedNodeIdx: Int = -1
    
    // 聚焦动画
    private var focusAnimating = false
    private var focusProgress = 0f
    private var focusStartTargetX = 0f
    private var focusStartTargetY = 0f
    private var focusStartTargetZ = 0f
    private var focusEndTargetX = 0f
    private var focusEndTargetY = 0f
    private var focusEndTargetZ = 0f
    private var focusStartRotX = 0f
    private var focusStartRotY = 0f
    private var focusTargetRotX = 0f
    private var focusTargetRotY = 0f
    private var focusStartZoom = 1f
    private var focusTargetZoom = 1f
    
    companion object {
        private const val FOCUS_DURATION = 0.8f
    }
    
    // 节点和连线
    private val nodes = mutableListOf<Node>()
    private val edges = mutableListOf<Edge>()
    
    // 子渲染器
    private var backgroundStarRenderer: BackgroundStarRenderer? = null
    private var enhancedLineRenderer: EnhancedLineRenderer? = null
    private var flowParticleRenderer: FlowParticleRenderer? = null
    private var sphereNodeRenderer: SphereNodeRenderer? = null  // 新的球体渲染器
    private var textLabelRenderer: TextLabelRenderer? = null
    
    // 时间
    private var time = 0f
    private var lastFrameTime = System.currentTimeMillis()
    
    // 自动旋转
    private var autoRotate = true
    
    override fun onSurfaceCreated(gl: GL10?, config: EGLConfig?) {
        // 设置背景色（深色主题）
        GLES30.glClearColor(0.0f, 0.0f, 0.02f, 1.0f)
        
        // 启用深度测试
        GLES30.glEnable(GLES30.GL_DEPTH_TEST)
        
        // 启用混合（用于透明度）
        GLES30.glEnable(GLES30.GL_BLEND)
        GLES30.glBlendFunc(GLES30.GL_SRC_ALPHA, GLES30.GL_ONE_MINUS_SRC_ALPHA)
        
        // 初始化子渲染器
        try {
            backgroundStarRenderer = BackgroundStarRenderer()
            enhancedLineRenderer = EnhancedLineRenderer()
            flowParticleRenderer = FlowParticleRenderer()
            sphereNodeRenderer = SphereNodeRenderer()  // 使用新的球体渲染器
            textLabelRenderer = TextLabelRenderer()
            
            println("[EnhancedKnowledgeGraphRenderer] All renderers initialized")
        } catch (e: Exception) {
            println("[EnhancedKnowledgeGraphRenderer] Failed to initialize renderers: ${e.message}")
            e.printStackTrace()
        }
    }
    
    override fun onSurfaceChanged(gl: GL10?, width: Int, height: Int) {
        GLES30.glViewport(0, 0, width, height)
        
        val ratio = width.toFloat() / height.toFloat()
        
        // 设置投影矩阵（透视投影）
        Matrix.frustumM(projectionMatrix, 0, -ratio, ratio, -1f, 1f, 1f, 2000f)
        
        println("[EnhancedKnowledgeGraphRenderer] Viewport: ${width}x${height}")
    }
    
    override fun onDrawFrame(gl: GL10?) {
        // 更新时间
        val currentTime = System.currentTimeMillis()
        val deltaTime = (currentTime - lastFrameTime) / 1000f
        lastFrameTime = currentTime
        time += deltaTime
        
        // 更新动画
        updateAnimation(deltaTime)
        
        // 清除颜色和深度缓冲
        GLES30.glClear(GLES30.GL_COLOR_BUFFER_BIT or GLES30.GL_DEPTH_BUFFER_BIT)
        
        // 计算 MVP 矩阵
        computeMVPMatrix()
        
        // 渲染顺序：背景 → 连线 → 粒子 → 节点 → 文字标签
        try {
            // 计算相机位置（用于球体渲染）
            val zoom = cameraDistance
            val eyeX = targetX + zoom * sin(cameraAngleY) * cos(cameraAngleX)
            val eyeY = targetY + zoom * sin(cameraAngleX)
            val eyeZ = targetZ + zoom * cos(cameraAngleY) * cos(cameraAngleX)
            val cameraPos = floatArrayOf(eyeX, eyeY, eyeZ)
            
            // 1. 背景星空（最远）
            backgroundStarRenderer?.draw(mvpMatrix, time)
            
            // 2. 连线
            enhancedLineRenderer?.draw(mvpMatrix, edges, nodes)
            
            // 3. 流光粒子
            flowParticleRenderer?.draw(mvpMatrix, edges, nodes, time)
            
            // 4. 3D 球体节点（最近）
            sphereNodeRenderer?.draw(mvpMatrix, viewMatrix, nodes, time, selectedNodeIdx, cameraPos)
            
            // 5. 文字标签（连接线和锚点）
            textLabelRenderer?.draw(mvpMatrix, nodes)
            
        } catch (e: Exception) {
            println("[EnhancedKnowledgeGraphRenderer] Render error: ${e.message}")
        }
    }
    
    /**
     * 计算 MVP 矩阵
     */
    private fun computeMVPMatrix() {
        // 相机位置
        val zoom = cameraDistance
        val eyeX = targetX + zoom * sin(cameraAngleY) * cos(cameraAngleX)
        val eyeY = targetY + zoom * sin(cameraAngleX)
        val eyeZ = targetZ + zoom * cos(cameraAngleY) * cos(cameraAngleX)
        
        // 设置视图矩阵
        Matrix.setLookAtM(
            viewMatrix, 0,
            eyeX, eyeY, eyeZ,           // 相机位置
            targetX, targetY, targetZ,   // 看向目标点
            0f, 1f, 0f                   // 上方向
        )
        
        // 计算 MVP 矩阵
        Matrix.multiplyMM(mvpMatrix, 0, projectionMatrix, 0, viewMatrix, 0)
    }
    
    /**
     * 更新动画
     */
    private fun updateAnimation(deltaTime: Float) {
        // 聚焦动画
        if (focusAnimating) {
            focusProgress += deltaTime / FOCUS_DURATION
            
            if (focusProgress >= 1f) {
                // 动画完成
                focusProgress = 1f
                focusAnimating = false
                cameraAngleX = focusTargetRotX
                cameraAngleY = focusTargetRotY
                cameraDistance = focusTargetZoom
                targetX = focusEndTargetX
                targetY = focusEndTargetY
                targetZ = focusEndTargetZ
            } else {
                // 使用 ease-in-out cubic 缓动
                val t = easeInOutCubic(focusProgress)
                
                // 插值相机目标点
                targetX = focusStartTargetX + (focusEndTargetX - focusStartTargetX) * t
                targetY = focusStartTargetY + (focusEndTargetY - focusStartTargetY) * t
                targetZ = focusStartTargetZ + (focusEndTargetZ - focusStartTargetZ) * t
                
                // 插值旋转角度
                cameraAngleX = focusStartRotX + (focusTargetRotX - focusStartRotX) * t
                
                // 处理 Y 轴旋转的环绕问题
                var deltaY = focusTargetRotY - focusStartRotY
                while (deltaY > Math.PI.toFloat()) deltaY -= (2 * Math.PI).toFloat()
                while (deltaY < -Math.PI.toFloat()) deltaY += (2 * Math.PI).toFloat()
                cameraAngleY = focusStartRotY + deltaY * t
                
                // 缩放动画：先拉远再推近
                val zoomT = if (focusProgress < 0.3f) {
                    val pullBackT = focusProgress / 0.3f
                    val pullEased = 1f - (1f - pullBackT) * (1f - pullBackT)
                    val minZoom = focusStartZoom * 0.5f
                    focusStartZoom + (minZoom - focusStartZoom) * pullEased
                } else {
                    val pushT = (focusProgress - 0.3f) / 0.7f
                    val pushEased = 1f - (1f - pushT) * (1f - pushT) * (1f - pushT)
                    val minZoom = focusStartZoom * 0.5f
                    minZoom + (focusTargetZoom - minZoom) * pushEased
                }
                cameraDistance = zoomT
            }
        }
        // 自动旋转
        else if (autoRotate) {
            cameraAngleY += deltaTime * 0.3f
        }
        
        // 更新粒子
        flowParticleRenderer?.updateParticles(deltaTime)
    }
    
    /**
     * ease-in-out cubic 缓动函数
     */
    private fun easeInOutCubic(t: Float): Float {
        return if (t < 0.5f) {
            4f * t * t * t
        } else {
            val f = 2f * t - 2f
            0.5f * f * f * f + 1f
        }
    }
    
    /**
     * 更新图谱数据
     */
    fun updateGraph(newNodes: List<Node>, newEdges: List<Edge>) {
        nodes.clear()
        nodes.addAll(newNodes)
        edges.clear()
        edges.addAll(newEdges)
        
        // 初始化粒子
        flowParticleRenderer?.initParticles(edges.size)
        
        println("[EnhancedKnowledgeGraphRenderer] Updated: ${nodes.size} nodes, ${edges.size} edges")
    }
    
    /**
     * 获取当前 MVP 矩阵（用于文字标签投影）
     */
    fun getMVPMatrix(): FloatArray {
        return mvpMatrix.copyOf()
    }
    
    /**
     * 获取相机距离
     */
    fun getCameraDistance(): Float {
        return cameraDistance
    }
    
    /**
     * 设置相机距离
     */
    fun setCameraDistance(distance: Float) {
        cameraDistance = distance.coerceIn(100f, 500f)
    }
    
    /**
     * 旋转相机
     */
    fun rotateCamera(deltaX: Float, deltaY: Float) {
        cameraAngleY += deltaX * 0.01f
        cameraAngleX += deltaY * 0.01f
        cameraAngleX = cameraAngleX.coerceIn(-Math.PI.toFloat() / 2f * 0.9f, Math.PI.toFloat() / 2f * 0.9f)
        autoRotate = false
    }
    
    /**
     * 聚焦到节点
     */
    fun focusOnNode(nodeId: String) {
        val nodeIndex = nodes.indexOfFirst { it.id == nodeId }
        if (nodeIndex < 0) return
        
        val node = nodes[nodeIndex]
        
        // 保存动画起始状态
        focusStartRotX = cameraAngleX
        focusStartRotY = cameraAngleY
        focusStartZoom = cameraDistance
        focusStartTargetX = targetX
        focusStartTargetY = targetY
        focusStartTargetZ = targetZ
        
        // 目标点移动到节点位置
        focusEndTargetX = node.x
        focusEndTargetY = node.y
        focusEndTargetZ = node.z
        
        // 保持当前旋转角度
        focusTargetRotX = cameraAngleX
        focusTargetRotY = cameraAngleY
        
        // 目标缩放
        focusTargetZoom = 150f
        
        // 开始动画
        selectedNodeIdx = nodeIndex
        focusProgress = 0f
        focusAnimating = true
        autoRotate = false
        
        println("[EnhancedKnowledgeGraphRenderer] Focusing on node: ${node.label}")
    }
    
    /**
     * 重置相机
     */
    fun resetCamera() {
        // 平滑动画回到原点
        focusStartTargetX = targetX
        focusStartTargetY = targetY
        focusStartTargetZ = targetZ
        focusEndTargetX = 0f
        focusEndTargetY = 0f
        focusEndTargetZ = 0f
        
        focusStartRotX = cameraAngleX
        focusStartRotY = cameraAngleY
        focusTargetRotX = 0.3f
        focusTargetRotY = 0f
        
        focusStartZoom = cameraDistance
        focusTargetZoom = 220f
        
        selectedNodeIdx = -1
        focusProgress = 0f
        focusAnimating = true
        autoRotate = true
        
        println("[EnhancedKnowledgeGraphRenderer] Resetting camera")
    }
    
    /**
     * 检测点击的节点
     */
    fun detectNodeClick(screenX: Float, screenY: Float, screenWidth: Int, screenHeight: Int): Node? {
        // 将屏幕坐标转换为归一化设备坐标
        val ndcX = (2f * screenX) / screenWidth - 1f
        val ndcY = 1f - (2f * screenY) / screenHeight
        
        var closestNode: Node? = null
        var minDistance = Float.MAX_VALUE
        
        for (node in nodes) {
            // 将节点的世界坐标转换到裁剪空间
            val nodePos = FloatArray(4)
            nodePos[0] = node.x
            nodePos[1] = node.y
            nodePos[2] = node.z
            nodePos[3] = 1f
            
            val clipPos = FloatArray(4)
            Matrix.multiplyMV(clipPos, 0, mvpMatrix, 0, nodePos, 0)
            
            if (clipPos[3] > 0f) {
                val screenNodeX = clipPos[0] / clipPos[3]
                val screenNodeY = clipPos[1] / clipPos[3]
                
                // 计算距离
                val dx = screenNodeX - ndcX
                val dy = screenNodeY - ndcY
                val distance = sqrt(dx * dx + dy * dy)
                
                // 检查是否在节点半径内
                val threshold = 0.15f
                if (distance < threshold && distance < minDistance) {
                    minDistance = distance
                    closestNode = node
                }
            }
        }
        
        return closestNode
    }
    
    /**
     * 获取选中的节点
     */
    fun getSelectedNode(): Node? {
        return if (selectedNodeIdx >= 0 && selectedNodeIdx < nodes.size) {
            nodes[selectedNodeIdx]
        } else null
    }
    
    /**
     * 清理资源
     */
    fun cleanup() {
        backgroundStarRenderer?.cleanup()
        enhancedLineRenderer?.cleanup()
        flowParticleRenderer?.cleanup()
        sphereNodeRenderer?.cleanup()
        textLabelRenderer?.cleanup()
    }
}

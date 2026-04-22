package com.lifeswarm.android.data.model

import com.google.gson.annotations.SerializedName

/**
 * 知识图谱数据模型 - 对应 web/src/types/api.ts 的 KnowledgeGraphView
 */

// 知识图谱视图
data class KnowledgeGraphView(
    @SerializedName("nodes") val nodes: List<KnowledgeGraphNode> = emptyList(),
    @SerializedName("links") val links: List<KnowledgeGraphLink> = emptyList(),
    @SerializedName("edges") val edges: List<KnowledgeGraphLink>? = null, // 兼容后端返回 edges
    @SerializedName("view_mode") val viewMode: String? = null,
    @SerializedName("center_node_id") val centerNodeId: String? = null
)

// 知识图谱节点
data class KnowledgeGraphNode(
    @SerializedName("id") val id: String = "",
    @SerializedName("name") val name: String = "",
    @SerializedName("label") val label: String? = null,  // 后端使用label字段
    @SerializedName("type") val type: String = "",
    @SerializedName("category") val category: String? = null,
    @SerializedName("view_role") val viewRole: String? = null,
    @SerializedName("weight") val weight: Double = 0.0,
    @SerializedName("influence_score") val influenceScore: Double = 0.0,
    @SerializedName("connections") val connections: Int = 0,
    @SerializedName("insight_tags") val insightTags: List<String> = emptyList(),
    @SerializedName("is_self") val isSelf: Boolean = false,
    @SerializedName("stories") val stories: List<String>? = null,  // 改为字符串列表
    @SerializedName("description") val description: String? = null,  // 添加description字段
    @SerializedName("metadata") val metadata: Map<String, Any>? = null,
    @SerializedName("position") val position: NodePosition? = null
) {
    // 获取显示名称：优先使用label，其次name，最后从id提取
    val displayName: String
        get() = label?.takeIf { it.isNotEmpty() }
            ?: name.takeIf { it.isNotEmpty() }
            ?: run {
                val id = this.id
                if (id.contains("_")) id.substringAfter("_") else id
            }
}

// 节点故事
data class NodeStory(
    @SerializedName("story_id") val storyId: String,
    @SerializedName("title") val title: String,
    @SerializedName("content") val content: String,
    @SerializedName("timestamp") val timestamp: String,
    @SerializedName("emotion") val emotion: String? = null
)

// 节点位置（职业视图使用）
data class NodePosition(
    @SerializedName("x") val x: Double = 0.0,
    @SerializedName("y") val y: Double = 0.0,
    @SerializedName("z") val z: Double = 0.0
)

// 知识图谱连接
data class KnowledgeGraphLink(
    @SerializedName("source") val source: String = "",
    @SerializedName("target") val target: String = "",
    @SerializedName("type") val type: String = "",
    @SerializedName("strength") val strength: Double = 0.0,
    @SerializedName("weight") val weight: Double = 0.0,
    @SerializedName("description") val description: String? = null
)

// 人际关系图谱请求
data class PeopleGraphRequest(
    @SerializedName("user_id") val userId: String,
    @SerializedName("question") val question: String = "",
    @SerializedName("session_id") val sessionId: String? = null
)

// 职业图谱请求
data class CareerGraphRequest(
    @SerializedName("user_id") val userId: String,
    @SerializedName("mastered_skills") val masteredSkills: List<String> = emptyList(),
    @SerializedName("partial_skills") val partialSkills: List<String> = emptyList(),
    @SerializedName("missing_skills") val missingSkills: List<String> = emptyList(),
    @SerializedName("target_direction") val targetDirection: String = ""
)

// 升学规划图谱请求
data class EducationGraphRequest(
    @SerializedName("user_id") val userId: String,
    @SerializedName("gpa") val gpa: Double,
    @SerializedName("gpa_max") val gpaMax: Double = 4.0,
    @SerializedName("ranking_percent") val rankingPercent: Double,
    @SerializedName("sat_act") val satAct: Int,
    @SerializedName("research_experience") val researchExperience: Double,
    @SerializedName("publications") val publications: Int,
    @SerializedName("target_major") val targetMajor: String,
    @SerializedName("target_level") val targetLevel: String = "master",
    @SerializedName("search_keyword") val searchKeyword: String = "",
    @SerializedName("location") val location: String = ""
)

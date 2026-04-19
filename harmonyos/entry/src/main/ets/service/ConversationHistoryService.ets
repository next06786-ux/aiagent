/**
 * 
 * AI
 */
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'
import preferences from '@ohos.data.preferences'
import { UIContext } from '@kit.ArkUI'
import { BusinessError } from '@kit.BasicServicesKit'

// 处理逻辑
export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  images?: string[]
}

// 处理逻辑
export interface Conversation {
  conversationId: string
  userId: string
  messages: Message[]
  startTime: number
  lastUpdateTime: number
}

// 处理逻辑
export interface ConversationStatistics {
  messageCount: number
  duration: number
  hasImages: boolean
}

// RAG
interface RAGMemoryMetadata {
  conversation_id: string
  role: string
  timestamp: number
  has_images: boolean
}

// RAG
interface RAGMemoryRequest {
  user_id: string
  memory_type: string
  content: string
  metadata: RAGMemoryMetadata
  importance: number
}

export class ConversationHistoryService {
  private static instance: ConversationHistoryService
  private currentConversation: Conversation | null = null
  private autoSaveInterval: number = 30000 // 30
  private saveTimer: number = -1
  private preferences: preferences.Preferences | null = null
  private uiContext: UIContext | null = null // UIContext reference

  private constructor() {
    // Constructor now requires UIContext to be passed externally
  }

  static getInstance(uiContext?: UIContext): ConversationHistoryService {
    if (!ConversationHistoryService.instance) {
      ConversationHistoryService.instance = new ConversationHistoryService()
      ConversationHistoryService.instance.uiContext = uiContext || null
    }
    return ConversationHistoryService.instance
  }

  /**
   * UIContext
   */
  setUIContext(uiContext: UIContext): void {
    this.uiContext = uiContext
    if (uiContext) {
      this.initPreferences()
    }
  }

  /**
 * 服务类
 */
  private async initPreferences() {
    try {
      if (!this.uiContext) {
        console.error('UIContext not set. Cannot initialize preferences.')
        return
      }
      
      // UIContexthost context
      const hostContext = this.uiContext.getHostContext()
      
      // Promisepreferences
      await preferences.getPreferences(hostContext, 'conversation_history')
        .then((data: preferences.Preferences) => {
          this.preferences = data
          console.info('Succeeded in getting preferences')
        })
        .catch((err: BusinessError) => {
          console.error(`Failed to get preferences, Cause: ${err.message}`)
        })
    } catch (error) {
      console.error('Failed to init preferences:', error)
    }
  }

  /**
 * 服务类
 */
  startConversation(userId: string): string {
    const conversationId = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    
    this.currentConversation = {
      conversationId,
      userId,
      messages: [],
      startTime: Date.now(),
      lastUpdateTime: Date.now()
    }

    // 处理逻辑
    this.startAutoSave()

    return conversationId
  }

  /**
 * 服务类
 */
  addMessage(role: 'user' | 'assistant', content: string, images?: string[]) {
    if (!this.currentConversation) {
      this.startConversation('default_user')
    }

    const message: Message = {
      role,
      content,
      timestamp: Date.now(),
      images
    }

    this.currentConversation!.messages.push(message)
    this.currentConversation!.lastUpdateTime = Date.now()

    // 处理逻辑
    this.saveToLocal()
  }

  /**
 * 服务类
 */
  private startAutoSave() {
    if (this.saveTimer !== -1) {
      clearInterval(this.saveTimer)
    }

    this.saveTimer = setInterval(() => {
      this.saveToBackend()
    }, this.autoSaveInterval)
  }

  /**
 * 服务类
 */
  stopAutoSave() {
    if (this.saveTimer !== -1) {
      clearInterval(this.saveTimer)
      this.saveTimer = -1
    }
  }

  /**
 * 服务类
 */
  private async saveToLocal() {
    if (!this.preferences || !this.currentConversation) {
      return
    }

    try {
      await this.preferences.put(
        'current_conversation',
        JSON.stringify(this.currentConversation)
      )
      await this.preferences.flush()
    } catch (error) {
      console.error('Failed to save to local:', error)
    }
  }

  /**
 * 服务类
 */
  async restoreFromLocal(): Promise<Conversation | null> {
    if (!this.preferences) {
      return null
    }

    try {
      const data = await this.preferences.get('current_conversation', '')
      if (data) {
        this.currentConversation = JSON.parse(data as string)
        this.startAutoSave()
        return this.currentConversation
      }
    } catch (error) {
      console.error('Failed to restore from local:', error)
    }

    return null
  }

  /**
   *  + RAG
   */
  async saveToBackend(): Promise<boolean> {
    if (!this.currentConversation || this.currentConversation.messages.length === 0) {
      return false
    }

    try {
      const httpRequest = http.createHttp()

      // 处理逻辑
      const textContent = this.currentConversation.messages
        .map(msg => msg.content)
        .join(' ')

      // 处理逻辑
      const images = this.currentConversation.messages
        .filter(msg => msg.images && msg.images.length > 0)
        .flatMap(msg => msg.images!)

      // 1. 
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/v4/conversation/save`,
        {
          method: http.RequestMethod.POST,
          header: {
            'Content-Type': 'application/json'
          },
          extraData: JSON.stringify({
            conversation_id: this.currentConversation.conversationId,
            user_id: this.currentConversation.userId,
            messages: this.currentConversation.messages,
            text_summary: textContent.substring(0, 1000), // 处理逻辑
            images: images.slice(0, 5), // 5
            start_time: this.currentConversation.startTime,
            last_update: this.currentConversation.lastUpdateTime
          })
        }
      )

      const success = response.responseCode === 200

      // 2. RAG
      if (success) {
        await this.saveToRAG(textContent)
      }

      httpRequest.destroy()

      return success
    } catch (error) {
      console.error('Failed to save to backend:', error)
      return false
    }
  }

  /**
   * RAG
   */
  private async saveToRAG(textContent: string): Promise<void> {
    try {
      const httpRequest = http.createHttp()

      // RAG
      const importantMessages = this.currentConversation!.messages.filter(
        msg => msg.content.length > 10 // 处理逻辑
      )

      for (const msg of importantMessages) {
        // 处理逻辑
        const importance = msg.role === 'user' ? 0.7 : 
                          msg.content.length > 100 ? 0.8 : 0.6

        const metadata: RAGMemoryMetadata = {
          conversation_id: this.currentConversation!.conversationId,
          role: msg.role,
          timestamp: msg.timestamp,
          has_images: msg.images !== undefined && msg.images.length > 0
        }

        const requestData: RAGMemoryRequest = {
          user_id: this.currentConversation!.userId,
          memory_type: 'conversation',
          content: msg.content,
          metadata: metadata,
          importance: importance
        }

        await httpRequest.request(
          `${ApiConfig.getBaseUrl()}/api/v4/rag/add-memory`,
          {
            method: http.RequestMethod.POST,
            header: {
              'Content-Type': 'application/json'
            },
            extraData: JSON.stringify(requestData)
          }
        )
      }

      httpRequest.destroy()
      console.info(`  ${importantMessages.length} RAG`)
    } catch (error) {
      console.error('Failed to save to RAG:', error)
    }
  }

  /**
 * 服务类
 */
  async endConversation(): Promise<boolean> {
    this.stopAutoSave()
    
    // 处理逻辑
    const success = await this.saveToBackend()
    
    // 处理逻辑
    this.currentConversation = null
    
    // 处理逻辑
    if (this.preferences) {
      await this.preferences.delete('current_conversation')
      await this.preferences.flush()
    }

    return success
  }

  /**
 * 服务类
 */
  getCurrentConversation(): Conversation | null {
    return this.currentConversation
  }

  /**
 * 服务类
 */
  getStatistics(): ConversationStatistics {
    if (!this.currentConversation) {
      const emptyStats: ConversationStatistics = {
        messageCount: 0,
        duration: 0,
        hasImages: false
      }
      return emptyStats
    }

    const duration: number = Date.now() - this.currentConversation.startTime
    const hasImages: boolean = this.currentConversation.messages.some(
      msg => msg.images !== undefined && msg.images.length > 0
    )

    const stats: ConversationStatistics = {
      messageCount: this.currentConversation.messages.length,
      duration,
      hasImages
    }
    return stats
  }
}
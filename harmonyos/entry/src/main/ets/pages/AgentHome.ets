/**
 * 智能体主界面 - ParaLife · 平行境
 * HarmonyOS 6 流体设计 · 功能球体环绕AI核心
 */
import { Theme } from '../common/Theme';
import { getAIConversationService, ChatMessage } from '../service/AIConversationService';
import { SimpleIcon } from '../components/IconRenderer';
import http from '@ohos.net.http';
import { ApiConfig } from '../config/ApiConfig';
import { getAuthService, UserInfo } from '../service/AuthService';
import picker from '@ohos.file.picker';
import media from '@ohos.multimedia.media';
import common from '@ohos.app.ability.common';
import fs from '@ohos.file.fs';
import abilityAccessCtrl from '@ohos.abilityAccessCtrl';
import promptAction from '@ohos.promptAction';

interface FeatureCard {
  id: string;
  title: string;
  subtitle: string;
  route: string;
  color: string;
  iconName: string;
}

interface OrbPos {
  x: number;
  y: number;
  title: string;
  icon: string;
  color: string;
  route: string;
}

interface ConversationItem {
  id: string;
  title: string;
  preview: string;
  message_count: number;
  last_message_time: string;
}

@Entry
@Component
struct AgentHome {
  @State messages: ChatMessage[] = [];
  @State inputText: string = '';
  @State isLoading: boolean = false;
  @State showContent: boolean = false;
  @State processingProgress: string = '';
  @State dotAnimation1: number = 1;
  @State dotAnimation2: number = 1;
  @State dotAnimation3: number = 1;
  private animationTimer: number = -1;

  @State showHistoryPanel: boolean = false;
  @State showAiCorePanel: boolean = false;
  @State conversations: ConversationItem[] = [];
  @State currentSessionId: string = '';
  @State isLoadingHistory: boolean = false;
  @State userInfo: UserInfo | null = null;
  @State isRecording: boolean = false;
  @State isVoiceMode: boolean = false;   // true=按住说话模式，false=文本输入模式
  @State showPlusMenu: boolean = false;  // 加号展开菜单
  @State isInCall: boolean = false;      // 通话中
  @State selectedImageUri: string = '';
  private audioRecorder: media.AVRecorder | null = null;
  private recordFilePath: string = '';
  private inputController: TextInputController = new TextInputController();
  private callTimer: number = -1;
  private callDuration: number = 0;
  @State callDurationText: string = '00:00';

  // 布局
  @State screenWidth: number = 360;
  @State screenHeight: number = 780;
  @State centerX: number = 180;
  @State centerY: number = 360;

  // 功能球体漂浮位置
  @State orbPositions: OrbPos[] = [];
  private orbAnimTimer: number = -1;

  // AI核心球体动画
  @State aiCoreBreath: number = 1.0;
  @State aiCoreRing1: number = 0;
  @State aiCoreRing2: number = 0;
  @State aiCoreInnerRotate: number = 0;
  @State runePulse: number = 0;  // 符文脉冲动画 0~1
  private aiCoreAnimTimer: number = -1;

  private aiService = getAIConversationService();
  private authService = getAuthService();

  private features: FeatureCard[] = [
    { id: 'starmap', title: '知识星图', subtitle: '3D知识图谱', route: 'pages/KnowledgeStarMapGL', color: '#0A59F7', iconName: 'network' },
    { id: 'decision', title: '决策副本', subtitle: '探索未来', route: 'pages/QuickDecisionInput', color: '#6B48FF', iconName: 'comparison' },
    { id: 'dashboard', title: '智能洞察', subtitle: '涌现发现', route: 'pages/SmartInsights', color: '#FF9500', iconName: 'analytics' },
    { id: 'profile', title: '我的账号', subtitle: '个人中心', route: 'pages/UserProfile', color: '#00C853', iconName: 'user' },
    { id: 'game', title: '平行人生', subtitle: '决策游戏', route: 'pages/ParallelLifeGame', color: '#FF6B9D', iconName: 'life' },
  ];

  aboutToAppear() {
    this.messages = this.aiService.getConversationHistory();
    if (this.messages.length === 0) this.addWelcomeMessage();
    this.loadUserInfo();
    this.loadConversations().catch(() => {});
    this.initOrbPositions();
    this.startOrbAnimation();
    this.startAiCoreAnimation();
    setTimeout(() => { this.showContent = true; }, 50);
  }

  aboutToDisappear() {
    this.stopLoadingAnimation();
    this.stopOrbAnimation();
    this.stopAiCoreAnimation();
    // 清理通话计时器
    if (this.callTimer !== -1) {
      clearInterval(this.callTimer);
      this.callTimer = -1;
    }
    // 停止录音
    if (this.isRecording) {
      this.stopRecording();
    }
  }

  onPageShow() {
    this.showContent = true;
    this.initOrbPositions();
    this.startOrbAnimation();
    this.startAiCoreAnimation();
  }

  onPageHide() {
    this.stopOrbAnimation();
    this.stopAiCoreAnimation();
  }

  // ===== 球体位置与动画 =====
  private initOrbPositions() {
    const count = this.features.length;
    const radius = 155;
    const cy = this.centerY + 10;
    const positions: OrbPos[] = [];
    for (let i = 0; i < count; i++) {
      const f = this.features[i];
      const angle = (i / count) * Math.PI * 2 - Math.PI / 2;
      positions.push({
        x: this.centerX + Math.cos(angle) * radius,
        y: cy + Math.sin(angle) * radius,
        title: f.title, icon: f.iconName, color: f.color, route: f.route
      });
    }
    this.orbPositions = positions;
  }

  private startOrbAnimation() {
    if (this.orbAnimTimer !== -1) return;
    this.orbAnimTimer = setInterval(() => {
      const time = Date.now() / 1000;
      const count = this.features.length;
      const radius = 155;
      const cy = this.centerY + 10;
      const newPos: OrbPos[] = [];
      for (let i = 0; i < count; i++) {
        const f = this.features[i];
        const angle = (i / count) * Math.PI * 2 - Math.PI / 2;
        const baseX = this.centerX + Math.cos(angle) * radius;
        const baseY = cy + Math.sin(angle) * radius;
        newPos.push({
          x: baseX + Math.cos(time * 0.7 + i * 1.6) * 3,
          y: baseY + Math.sin(time * 0.9 + i * 1.2) * 4,
          title: f.title, icon: f.iconName, color: f.color, route: f.route
        });
      }
      this.orbPositions = newPos;
    }, 50);
  }

  private stopOrbAnimation() {
    if (this.orbAnimTimer !== -1) { clearInterval(this.orbAnimTimer); this.orbAnimTimer = -1; }
  }

  private startAiCoreAnimation() {
    if (this.aiCoreAnimTimer !== -1) return;
    let t = 0;
    this.aiCoreAnimTimer = setInterval(() => {
      t += 0.05;
      animateTo({ duration: 50, curve: Curve.Linear }, () => {
        this.aiCoreBreath = 1.0 + Math.sin(t * 1.2) * 0.05;
        this.aiCoreRing1 = (t * 18) % 360;
        this.aiCoreRing2 = (t * -12 + 120) % 360;
        this.aiCoreInnerRotate = (t * 25) % 360;
        this.runePulse = (Math.sin(t * 0.8) + 1) / 2;  // 0~1 脉冲
      });
    }, 50);
  }

  private stopAiCoreAnimation() {
    if (this.aiCoreAnimTimer !== -1) { clearInterval(this.aiCoreAnimTimer); this.aiCoreAnimTimer = -1; }
  }

  // ===== 业务方法 =====
  private async loadUserInfo() {
    try { this.userInfo = await this.authService.getCurrentUserAsync(); }
    catch (err) { console.error('加载用户信息失败:', err); }
  }

  private async loadConversations() {
    try {
      const userId = this.authService.getCurrentUserId();
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/chat/sessions/${userId}`, { method: http.RequestMethod.GET });
      httpRequest.destroy();
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        const data = result.data as Record<string, Object>;
        const sessions = (data.sessions as Array<Record<string, Object>>) || [];
        this.conversations = sessions.map((item: Record<string, Object>): ConversationItem => ({
          id: item.session_id as string, title: item.title as string || '新对话',
          preview: item.preview as string || '', message_count: item.message_count as number || 0,
          last_message_time: item.last_time as string || ''
        }));
      }
    } catch (err) { console.error('加载历史对话失败:', err); }
  }

  private addWelcomeMessage() {
    this.messages.push(new ChatMessage(Date.now().toString(), 'assistant',
      '欢迎来到 ParaLife · 平行境\n\n我是你的AI助手，可以帮你分析问题、辅助决策。\n\n点击中心AI核心开始对话，或选择周围的功能球体探索更多。',
      Date.now()));
  }

  private startLoadingAnimation() {
    let step = 0;
    this.animationTimer = setInterval(() => {
      step = (step + 1) % 3;
      animateTo({ duration: 300, curve: Curve.EaseInOut }, () => {
        this.dotAnimation1 = step === 0 ? 1.5 : 1;
        this.dotAnimation2 = step === 1 ? 1.5 : 1;
        this.dotAnimation3 = step === 2 ? 1.5 : 1;
      });
    }, 300);
  }

  private stopLoadingAnimation() {
    if (this.animationTimer !== -1) { clearInterval(this.animationTimer); this.animationTimer = -1; }
    this.dotAnimation1 = 1; this.dotAnimation2 = 1; this.dotAnimation3 = 1;
  }

  async sendMessage(overrideText?: string, skipUserPush?: boolean) {
    const msgText = overrideText ?? this.inputText;
    if (!msgText.trim() || this.isLoading) return;
    const userMessage = msgText;
    this.inputText = '';
    this.isLoading = true;
    this.startLoadingAnimation();
    this.showAiCorePanel = true;
    if (!skipUserPush) {
      this.messages.push(new ChatMessage(Date.now().toString(), 'user', userMessage, Date.now()));
    }
    const aiMsgId = (Date.now() + 1).toString();
    this.messages.push(new ChatMessage(aiMsgId, 'assistant', '', Date.now(), ''));
    try {
      await this.aiService.chatStreamWebSocket(userMessage,
        (progress: string) => { this.processingProgress = progress; },
        (thinking: string) => { this.processingProgress = ''; this.updateMessage(aiMsgId, 'thinking', thinking); },
        (answer: string) => { this.updateMessage(aiMsgId, 'content', answer); },
        () => { this.processingProgress = ''; this.stopLoadingAnimation(); this.isLoading = false; this.loadConversations(); },
        (error: string) => {
          this.processingProgress = ''; this.stopLoadingAnimation(); this.isLoading = false;
          const idx = this.messages.findIndex(m => m.id === aiMsgId);
          if (idx >= 0) this.messages.splice(idx, 1);
        },
        null, this.currentSessionId || null,
        (sessionId: string) => { this.currentSessionId = sessionId; }
      );
    } catch (err) {
      const idx = this.messages.findIndex(m => m.id === aiMsgId);
      if (idx >= 0) this.messages.splice(idx, 1);
      this.isLoading = false; this.stopLoadingAnimation();
    }
  }

  private async triggerModelUpdate() {
    if (!this.userInfo) return;
    try {
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/lora/train/${this.userInfo.user_id}`, { method: http.RequestMethod.POST });
      httpRequest.destroy();
      if (response.responseCode === 200) { this.processingProgress = '模型训练已触发'; }
    } catch (err) { console.error('触发模型训练失败:', err); }
  }

  private updateMessage(messageId: string, field: 'thinking' | 'content', value: string): void {
    const idx = this.messages.findIndex(m => m.id === messageId);
    if (idx >= 0) {
      const msg = this.messages[idx];
      const updated = new ChatMessage(msg.id, msg.role,
        field === 'content' ? value : msg.content, msg.timestamp,
        field === 'thinking' ? value : msg.thinking);
      const newMsgs: ChatMessage[] = [];
      for (let i = 0; i < this.messages.length; i++) newMsgs.push(i === idx ? updated : this.messages[i]);
      this.messages = newMsgs;
    }
  }

  async loadConversationMessages(sessionId: string) {
    this.isLoadingHistory = true;
    try {
      const userId = this.authService.getCurrentUserId();
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/chat/session/${userId}/${sessionId}`, { method: http.RequestMethod.GET });
      httpRequest.destroy();
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        const data = result.data as Record<string, Object>;
        const history = (data.messages as Array<Record<string, string>>) || [];
        this.messages = history.map((m: Record<string, string>) => new ChatMessage(
          m.id || Date.now().toString(), m.role as 'user' | 'assistant',
          m.content || '', m.timestamp ? new Date(m.timestamp).getTime() : Date.now(), m.thinking));
        this.currentSessionId = sessionId;
        this.showHistoryPanel = false; this.showAiCorePanel = true;
      }
    } catch (err) { console.error('加载对话消息失败:', err); }
    finally { this.isLoadingHistory = false; }
  }

  async createNewConversation() {
    try {
      const userId = this.authService.getCurrentUserId();
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/chat/session/new/${userId}`, { method: http.RequestMethod.POST });
      httpRequest.destroy();
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, Object>;
        const data = result.data as Record<string, string>;
        if (data?.session_id) {
          this.currentSessionId = data.session_id;
          this.messages = []; this.addWelcomeMessage();
          this.showHistoryPanel = false; this.showAiCorePanel = true;
          this.loadConversations();
        }
      }
    } catch (err) { console.error('创建新对话失败:', err); }
  }

  private navigateTo(route: string): void {
    try { this.getUIContext().getRouter().pushUrl({ url: route }); }
    catch (e) { console.error('导航失败:', e); }
  }

  formatTime(ts: number): string {
    const d = new Date(ts);
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
  }

  async pickImage() {
    try {
      const photoPicker = new picker.PhotoViewPicker();
      const result = await photoPicker.select({
        MIMEType: picker.PhotoViewMIMETypes.IMAGE_TYPE,
        maxSelectNumber: 1
      });
      if (result.photoUris && result.photoUris.length > 0) {
        const uri = result.photoUris[0];
        this.selectedImageUri = uri;
        this.inputText = '图片分析中...';
        try {
          // 读取图片文件内容
          const context = getContext(this) as common.UIAbilityContext;
          const sandboxPath = `${context.cacheDir}/upload_img.jpg`;
          
          // 打开源文件
          const srcFile = await fs.open(uri, fs.OpenMode.READ_ONLY);
          const destFile = await fs.open(sandboxPath, fs.OpenMode.READ_WRITE | fs.OpenMode.CREATE | fs.OpenMode.TRUNC);
          await fs.copyFile(srcFile.fd, destFile.fd);
          await fs.close(srcFile.fd);
          await fs.close(destFile.fd);
          
          const httpRequest = http.createHttp();
          const userId = this.authService.getCurrentUserId();
          const response = await httpRequest.request(
            `${ApiConfig.getBaseUrl()}/api/chat/upload-image?user_id=${userId}`,
            {
              method: http.RequestMethod.POST,
              header: { 'Content-Type': 'multipart/form-data' },
              multiFormDataList: [{
                name: 'file',
                contentType: 'image/jpeg',
                remoteFileName: 'image.jpg',
                filePath: sandboxPath
              }],
              connectTimeout: 30000,
              readTimeout: 30000
            }
          );
          httpRequest.destroy();
          if (response.responseCode === 200) {
            const res = JSON.parse(response.result as string) as Record<string, Object>;
            const data = res.data as Record<string, string>;
            this.inputText = data?.description ? `[图片: ${data.description}]` : '[图片已添加]';
          } else {
            this.inputText = '[图片已添加]';
          }
        } catch (uploadErr) {
          console.error('图片上传失败:', uploadErr);
          this.inputText = '[图片已添加]';
        }
      }
    } catch (err) {
      console.error('选择图片失败:', err);
    }
  }

  toggleVoice() {
    if (this.isRecording) {
      this.stopRecording();
    } else {
      this.startRecording();
    }
  }

  async startRecording() {
    try {
      // 申请麦克风权限
      const atManager = abilityAccessCtrl.createAtManager();
      const context = getContext(this) as common.UIAbilityContext;
      const result = await atManager.requestPermissionsFromUser(context, ['ohos.permission.MICROPHONE']);
      if (result.authResults[0] !== 0) {
        this.inputText = '(需要麦克风权限)';
        return;
      }

      // 准备录音文件路径
      this.recordFilePath = `${context.cacheDir}/voice_${Date.now()}.m4a`;
      const file = await fs.open(this.recordFilePath, fs.OpenMode.READ_WRITE | fs.OpenMode.CREATE);
      await fs.close(file.fd);

      // 创建录音器
      this.audioRecorder = await media.createAVRecorder();
      const config: media.AVRecorderConfig = {
        audioSourceType: media.AudioSourceType.AUDIO_SOURCE_TYPE_MIC,
        profile: {
          audioBitrate: 48000,
          audioChannels: 1,
          audioCodec: media.CodecMimeType.AUDIO_AAC,
          audioSampleRate: 16000,
          fileFormat: media.ContainerFormatType.CFT_MPEG_4A,
        },
        url: `fd://${(await fs.open(this.recordFilePath, fs.OpenMode.READ_WRITE)).fd}`,
      };
      await this.audioRecorder.prepare(config);
      await this.audioRecorder.start();
      this.isRecording = true;
      this.inputText = '录音中，再次点击停止...';
    } catch (err) {
      console.error('录音启动失败:', err);
      this.inputText = '(录音启动失败)';
      this.isRecording = false;
    }
  }

  async stopRecording() {
    try {
      if (this.audioRecorder) {
        await this.audioRecorder.stop();
        await this.audioRecorder.release();
        this.audioRecorder = null;
      }
      this.isRecording = false;
      this.inputText = '';
      // 松手后立刻在对话列表显示"语音识别中"占位气泡
      const placeholderId = `voice_placeholder_${Date.now()}`;
      this.messages.push(new ChatMessage(placeholderId, 'user', '🎤 识别中...', Date.now()));

      // 上传音频到后端转文字
      const httpRequest = http.createHttp();
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/chat/speech-to-text`,
        {
          method: http.RequestMethod.POST,
          header: { 'Content-Type': 'multipart/form-data' },
          multiFormDataList: [{
            name: 'file', contentType: 'audio/mp4',
            remoteFileName: 'voice.m4a', filePath: this.recordFilePath
          }],
          connectTimeout: 30000, readTimeout: 60000
        }
      );
      httpRequest.destroy();
      if (response.responseCode === 200) {
        const res = JSON.parse(response.result as string) as Record<string, Object>;
        const data = res.data as Record<string, string>;
        const recognizedText = data?.text || '';
        if (recognizedText.trim().length > 0) {
          // 替换占位气泡为真实识别内容
          const idx = this.messages.findIndex(m => m.id === placeholderId);
          if (idx >= 0) {
            const updated = new ChatMessage(placeholderId, 'user', recognizedText, Date.now());
            const newMsgs: ChatMessage[] = [];
            for (let i = 0; i < this.messages.length; i++) {
              newMsgs.push(i === idx ? updated : this.messages[i]);
            }
            this.messages = newMsgs;
          }
          this.inputText = recognizedText;
          this.sendMessage(recognizedText, true);
        } else {
          // 识别结果为空，可能是录音太短或环境噪音，给出提示并清空输入框
          this.inputText = '';
          promptAction.showToast({ message: '未识别到语音，请重新录音' });
        }
      } else {
        this.inputText = '';
        promptAction.showToast({ message: '语音识别失败，请重试' });
      }
    } catch (err) {
      console.error('停止录音失败:', err);
      this.inputText = '(录音处理失败)';
      this.isRecording = false;
    }
  }

  // ===== 通话功能 =====
  async startCall() {
    try {
      const atManager = abilityAccessCtrl.createAtManager();
      const context = getContext(this) as common.UIAbilityContext;
      const result = await atManager.requestPermissionsFromUser(context, ['ohos.permission.MICROPHONE']);
      if (result.authResults[0] !== 0) {
        promptAction.showToast({ message: '需要麦克风权限才能通话' });
        return;
      }
      this.isInCall = true;
      this.callDuration = 0;
      this.callDurationText = '00:00';
      // 开始录音（持续录制，每10秒发送一次）
      await this.startRecording();
      // 计时器
      this.callTimer = setInterval(() => {
        this.callDuration++;
        const m = Math.floor(this.callDuration / 60).toString().padStart(2, '0');
        const s = (this.callDuration % 60).toString().padStart(2, '0');
        this.callDurationText = `${m}:${s}`;
        // 每10秒自动发送一次语音
        if (this.callDuration % 10 === 0 && this.isRecording) {
          this.stopRecording();
          setTimeout(() => { if (this.isInCall) { this.startRecording(); } }, 500);
        }
      }, 1000);
      promptAction.showToast({ message: '通话已开始，AI正在聆听' });
    } catch (err) {
      this.isInCall = false;
      promptAction.showToast({ message: '通话启动失败' });
    }
  }

  endCall() {
    if (this.callTimer !== -1) { clearInterval(this.callTimer); this.callTimer = -1; }
    if (this.isRecording) { this.stopRecording(); }
    this.isInCall = false;
    this.callDuration = 0;
    this.callDurationText = '00:00';
    promptAction.showToast({ message: '通话已结束' });
  }

  // ===== UI 构建 =====
  build() {
    Stack() {
      // 浅色背景
      Column().width('100%').height('100%').backgroundColor(Theme.Color.BackgroundPrimary)

      // 装饰光晕 - 跟随AI核心呼吸
      Circle({ width: 320, height: 320 }).fill('#667eea').opacity(0.035).blur(80)
        .position({ x: this.centerX - 160, y: this.centerY - 140 })
        .scale({ x: this.aiCoreBreath, y: this.aiCoreBreath })
      Circle({ width: 200, height: 200 }).fill('#764ba2').opacity(0.025).blur(60)
        .position({ x: this.centerX + 30, y: this.centerY + 60 })

      // 符文法阵连接线 - AI核心向功能球体赋能
      this.buildRuneLines()

      // 功能球体层
      this.buildOrbsLayer()

      // 顶部栏
      this.buildTopBar()

      // 中心AI核心
      this.buildAICore()

      if (this.isLoading && !this.showAiCorePanel) { this.buildLoadingIndicator() }
      // 始终渲染对话面板，关闭时只隐藏不销毁，避免中断WebSocket
      this.buildAICorePanel()
      // 历史面板在对话面板之上
      if (this.showHistoryPanel) { this.buildHistoryPanel() }
    }
    .width('100%').height('100%')
    .onAreaChange((oldArea: Area, newArea: Area) => {
      this.screenWidth = newArea.width as number;
      this.screenHeight = newArea.height as number;
      this.centerX = this.screenWidth / 2;
      this.centerY = this.screenHeight / 2;
      this.initOrbPositions();
    })
  }

  @Builder
  buildTopBar() {
    Row() {
      Row({ space: 10 }) {
        Stack() {
          Circle({ width: 40, height: 40 }).fill(Theme.Color.Primary).opacity(0.12)
          Circle({ width: 32, height: 32 })
            .linearGradient({ angle: 135, colors: [['#667eea', 0], ['#764ba2', 1]] })
          Text('PL').fontSize(13).fontWeight(700).fontColor('#FFFFFF')
        }.width(40).height(40)

        Column({ space: 2 }) {
          Text('ParaLife · 平行境').fontSize(17).fontWeight(700).fontColor(Theme.Color.TextPrimary)
          Text(this.userInfo ? `${this.userInfo.nickname}，你好` : '智能生活助手')
            .fontSize(11).fontColor(Theme.Color.TextTertiary)
        }.alignItems(HorizontalAlign.Start)
      }
      Blank()
      Stack() {
        Circle({ width: 40, height: 40 }).fill(Theme.Color.GlassMedium)
        SimpleIcon({ iconName: 'history', iconSize: 20, color: Theme.Color.TextSecondary })
      }.width(40).height(40)
      .onClick(() => { this.showHistoryPanel = true; })
    }
    .width('100%').height(60)
    .padding({ left: 16, right: 16 })
    .backgroundColor(Theme.Color.GlassHeavy)
    .backdropBlur(Theme.Blur.Medium)
    .border({ width: 0.5, color: Theme.Color.BorderLight })
    .position({ x: 0, y: 0 }).zIndex(10)
  }

  @Builder
  buildAICore() {
    Column({ space: 8 }) {
      Stack() {
        // 最外层脉冲光晕
        Circle({ width: 140, height: 140 })
          .fill(Theme.Color.Primary).opacity(0.04).blur(30)
          .scale({ x: this.aiCoreBreath * 1.15, y: this.aiCoreBreath * 1.15 })

        // 外层呼吸环
        Circle({ width: 118, height: 118 }).fill('transparent')
          .border({ width: 0.8, color: 'rgba(102, 126, 234, 0.12)' })
          .scale({ x: this.aiCoreBreath, y: this.aiCoreBreath })

        // 轨道环1 - 水平椭圆
        Circle({ width: 104, height: 104 }).fill('transparent')
          .border({ width: 1.2, color: 'rgba(10, 89, 247, 0.16)' })
          .rotate({ angle: this.aiCoreRing1 }).scale({ x: 1, y: 0.35 })

        // 轨道环2 - 垂直椭圆
        Circle({ width: 96, height: 96 }).fill('transparent')
          .border({ width: 1, color: 'rgba(107, 72, 255, 0.13)' })
          .rotate({ angle: this.aiCoreRing2 }).scale({ x: 0.35, y: 1 })

        // 轨道环3 - 倾斜
        Circle({ width: 88, height: 88 }).fill('transparent')
          .border({ width: 0.8, color: 'rgba(100, 180, 255, 0.1)' })
          .rotate({ angle: this.aiCoreRing1 * 0.6 + 60 })
          .scale({ x: 0.65, y: 0.45 })

        // 核心发光底 - 加大加深
        Circle({ width: 76, height: 76 })
          .fill(Theme.Color.Primary).opacity(0.1).blur(18)
          .scale({ x: this.aiCoreBreath, y: this.aiCoreBreath })

        // 核心球体 - 用多层线性渐变模拟径向光照，避免方形边界
        Circle({ width: 66, height: 66 })
          .linearGradient({ angle: 150 + this.aiCoreInnerRotate * 0.2,
            colors: [['#8B7CF6', 0], ['#6B5BD4', 0.35], ['#4A3BB0', 0.7], ['#2E1F8A', 1]] })
          .shadow({ radius: 24, color: 'rgba(91, 78, 212, 0.45)', offsetX: 0, offsetY: 8 })

        // 球体上半高光层 - 模拟顶部光照
        Circle({ width: 66, height: 66 })
          .linearGradient({ angle: 170,
            colors: [['rgba(255,255,255,0.25)', 0], ['rgba(255,255,255,0.05)', 0.3], ['rgba(0,0,0,0)', 0.5], ['rgba(0,0,0,0.1)', 1]] })

        // 边缘菲涅尔高光环
        Circle({ width: 64, height: 64 }).fill('transparent')
          .border({ width: 1.5, color: 'rgba(255, 255, 255, 0.12)' })

        // 顶部高光弧 - 更柔和
        Ellipse({ width: 28, height: 11 })
          .fill('rgba(255, 255, 255, 0.25)')
          .blur(4)
          .position({ x: 50, y: 46 })

        // 底部反光
        Ellipse({ width: 18, height: 6 })
          .fill('rgba(180, 170, 255, 0.1)')
          .blur(3)
          .position({ x: 60, y: 92 })

        // AI文字 - 圆形容器融入球体
        Stack() {
          Circle({ width: 36, height: 36 })
            .fill('rgba(255, 255, 255, 0.08)')
          Text('AI').fontSize(16).fontWeight(700)
            .fontColor('rgba(255, 255, 255, 0.75)')
        }
        .width(36)
        .height(36)
        .clip(new Circle({ width: 36, height: 36 }))
      }.width(140).height(140)

      Text('AI核心').fontSize(14).fontWeight(600).fontColor(Theme.Color.TextPrimary)
        .padding({ left: 14, right: 14, top: 5, bottom: 5 })
        .backgroundColor(Theme.Color.GlassHeavy)
        .borderRadius(Theme.Radius.round)
        .border({ width: 0.5, color: Theme.Color.BorderLight })
        .shadow(Theme.Shadow.Soft)

      if (this.isLoading && !this.showAiCorePanel) {
        Text('回复中...').fontSize(11).fontColor(Theme.Color.Primary)
          .padding({ left: 10, right: 10, top: 3, bottom: 3 })
          .backgroundColor('rgba(10, 89, 247, 0.08)')
          .borderRadius(Theme.Radius.round)
      } else {
        Text('点击展开对话').fontSize(11).fontColor(Theme.Color.TextTertiary)
      }
    }
    .position({ x: this.centerX - 70, y: this.centerY - 75 })
    .zIndex(90)
    .onClick(() => { this.showAiCorePanel = true; this.showHistoryPanel = false; })
    .opacity(this.showContent ? 1 : 0)
    .scale({ x: this.showContent ? 1 : 0.85, y: this.showContent ? 1 : 0.85 })
    .animation({ duration: 800, curve: Curve.Smooth, delay: 0 })
  }

  @Builder
  buildRuneLines() {
    // ═══ 符文法阵：AI核心 → 功能球体 赋能连接 ═══

    // 1. 从AI核心到每个球体的能量射线
    ForEach(this.orbPositions, (orb: OrbPos, index: number) => {
      // 主能量线 - 明显的渐变虚线
      Line()
        .width('100%').height('100%')
        .startPoint([this.centerX, this.centerY - 5])
        .endPoint([orb.x, orb.y])
        .stroke(orb.color)
        .strokeWidth(1.5)
        .strokeOpacity(0.15 + this.runePulse * 0.1)
        .strokeDashArray([6, 10])
        .position({ x: 0, y: 0 })
        .hitTestBehavior(HitTestMode.None)

      // 能量线发光层 - 更宽更模糊的底层光
      Line()
        .width('100%').height('100%')
        .startPoint([this.centerX, this.centerY - 5])
        .endPoint([orb.x, orb.y])
        .stroke(orb.color)
        .strokeWidth(4)
        .strokeOpacity(0.04 + this.runePulse * 0.03)
        .position({ x: 0, y: 0 })
        .hitTestBehavior(HitTestMode.None)
        .blur(3)

      // 能量脉冲点 - 沿连接线移动的光点（用 runePulse 驱动位置）
      Circle({ width: 6, height: 6 })
        .fill(orb.color)
        .opacity(0.4 + this.runePulse * 0.3)
        .shadow({ radius: 8, color: orb.color, offsetX: 0, offsetY: 0 })
        .position({
          x: this.centerX + (orb.x - this.centerX) * (0.3 + this.runePulse * 0.4) - 3,
          y: (this.centerY - 5) + (orb.y - (this.centerY - 5)) * (0.3 + this.runePulse * 0.4) - 3
        })
        .hitTestBehavior(HitTestMode.None)

      // 中间能量节点 - 连接线中点的固定光点
      Circle({ width: 5, height: 5 })
        .fill(orb.color)
        .opacity(0.25 + this.runePulse * 0.15)
        .shadow({ radius: 6, color: orb.color, offsetX: 0, offsetY: 0 })
        .position({
          x: (this.centerX + orb.x) / 2 - 2.5,
          y: ((this.centerY - 5) + orb.y) / 2 - 2.5
        })
        .hitTestBehavior(HitTestMode.None)
    })

    // 2. 外层五边形法阵环 - 连接所有球体
    ForEach(this.orbPositions, (orb: OrbPos, index: number) => {
      if (index < this.orbPositions.length - 1) {
        Line()
          .width('100%').height('100%')
          .startPoint([orb.x, orb.y])
          .endPoint([this.orbPositions[index + 1].x, this.orbPositions[index + 1].y])
          .stroke('#6B48FF')
          .strokeWidth(0.8)
          .strokeOpacity(0.1 + this.runePulse * 0.05)
          .strokeDashArray([3, 8])
          .position({ x: 0, y: 0 })
          .hitTestBehavior(HitTestMode.None)
      }
    })
    // 闭合五边形
    if (this.orbPositions.length >= 2) {
      Line()
        .width('100%').height('100%')
        .startPoint([this.orbPositions[this.orbPositions.length - 1].x, this.orbPositions[this.orbPositions.length - 1].y])
        .endPoint([this.orbPositions[0].x, this.orbPositions[0].y])
        .stroke('#6B48FF')
        .strokeWidth(0.8)
        .strokeOpacity(0.1 + this.runePulse * 0.05)
        .strokeDashArray([3, 8])
        .position({ x: 0, y: 0 })
        .hitTestBehavior(HitTestMode.None)
    }

    // 3. 中心法阵光环 - AI核心周围的旋转符文环
    Circle({ width: 200, height: 200 })
      .fill('transparent')
      .border({ width: 0.6, color: `rgba(107, 72, 255, ${0.06 + this.runePulse * 0.04})` })
      .position({ x: this.centerX - 100, y: this.centerY - 105 })
      .rotate({ angle: this.aiCoreRing1 * 0.3 })
      .hitTestBehavior(HitTestMode.None)

    Circle({ width: 240, height: 240 })
      .fill('transparent')
      .border({ width: 0.4, color: `rgba(107, 72, 255, ${0.03 + this.runePulse * 0.02})` })
      .strokeDashArray([12, 20])
      .position({ x: this.centerX - 120, y: this.centerY - 125 })
      .rotate({ angle: -this.aiCoreRing2 * 0.2 })
      .hitTestBehavior(HitTestMode.None)
  }

  @Builder
  buildOrbsLayer() {
    ForEach(this.orbPositions, (orb: OrbPos, index: number) => {
      Column({ space: 8 }) {
        Stack() {
          // 柔和光晕
          Circle({ width: 74, height: 74 }).fill(orb.color).opacity(0.06).blur(18)
          // 外环
          Circle({ width: 64, height: 64 }).fill('transparent')
            .border({ width: 0.8, color: orb.color }).opacity(0.18)
          // 球体底色
          Circle({ width: 54, height: 54 }).fill(orb.color).opacity(0.12)
          // 球体主体渐变
          Circle({ width: 54, height: 54 })
            .linearGradient({ angle: 145, colors: [[orb.color, 0], ['rgba(0,0,0,0.08)', 1]] })
            .shadow({ radius: 14, color: orb.color, offsetX: 0, offsetY: 5 })
          // 高光
          Circle({ width: 46, height: 46 })
            .linearGradient({ angle: 145, colors: [['rgba(255,255,255,0.22)', 0], ['rgba(255,255,255,0.02)', 0.5], ['rgba(0,0,0,0.04)', 1]] })
          // 图标
          SimpleIcon({ iconName: orb.icon, iconSize: 22, color: '#FFFFFF' })
        }.width(74).height(74)

        Text(orb.title)
          .fontSize(12).fontWeight(500).fontColor(Theme.Color.TextPrimary)
          .padding({ left: 10, right: 10, top: 4, bottom: 4 })
          .backgroundColor(Theme.Color.GlassHeavy)
          .borderRadius(Theme.Radius.round)
          .border({ width: 0.5, color: Theme.Color.BorderLight })
          .shadow(Theme.Shadow.Soft)
      }
      .width(92).height(110)
      .justifyContent(FlexAlign.Center)
      .position({ x: orb.x - 46, y: orb.y - 55 })
      .zIndex(100)
      .hitTestBehavior(HitTestMode.Block)
      .onTouch((event: TouchEvent) => {
        if (event.type === TouchType.Up) {
          this.navigateTo(orb.route);
          event.stopPropagation();
        }
      })
      .opacity(this.showContent ? 1 : 0)
      .scale({ x: this.showContent ? 1 : 0.7, y: this.showContent ? 1 : 0.7 })
      .animation({ duration: 700, curve: Curve.Smooth, delay: 150 + index * 100 })
      .stateStyles({
        pressed: {
          .scale({ x: 0.9, y: 0.9 })
          .opacity(0.85)
        },
        normal: {
          .scale({ x: 1, y: 1 })
          .opacity(1)
        }
      })
    })
  }

  @Builder
  buildLoadingIndicator() {
    Column({ space: 10 }) {
      if (this.processingProgress) {
        Text(this.processingProgress).fontSize(12).fontColor(Theme.Color.Primary)
          .padding({ left: 14, right: 14, top: 8, bottom: 8 })
          .backgroundColor('rgba(10, 89, 247, 0.06)').borderRadius(Theme.Radius.round)
      }
      Row({ space: 10 }) {
        Circle({ width: 8, height: 8 }).fill(Theme.Color.Primary).scale({ x: this.dotAnimation1, y: this.dotAnimation1 })
        Circle({ width: 8, height: 8 }).fill(Theme.Color.Secondary).scale({ x: this.dotAnimation2, y: this.dotAnimation2 })
        Circle({ width: 8, height: 8 }).fill(Theme.Color.Accent).scale({ x: this.dotAnimation3, y: this.dotAnimation3 })
      }
    }.position({ x: '50%', y: '60%' }).translate({ x: '-50%' }).zIndex(15)
  }

  @Builder
  buildAICorePanel() {
    Stack() {
      Column().width('100%').height('100%')
        .backgroundColor(Theme.Color.OverlayMedium)
        .onClick(() => { this.showAiCorePanel = false; })

      Column({ space: 0 }) {
        Row() {
          Column({ space: 3 }) {
            Row({ space: 8 }) {
              Stack() {
                Circle({ width: 32, height: 32 })
                  .linearGradient({ angle: 135, colors: [['#667eea', 0], ['#764ba2', 1]] })
                Text('AI').fontSize(12).fontWeight(700).fontColor('#FFFFFF')
              }.width(32).height(32)
              Text('AI核心').fontSize(18).fontWeight(700).fontColor(Theme.Color.TextPrimary)
            }
            Text('对话会沉淀为用户信息，并可触发模型更新')
              .fontSize(11).fontColor(Theme.Color.TextTertiary)
          }.alignItems(HorizontalAlign.Start).layoutWeight(1)

          // 历史消息按钮
          Stack() {
            Circle({ width: 36, height: 36 }).fill('rgba(10, 89, 247, 0.08)')
            Text('H').fontSize(15).fontWeight(600).fontColor(Theme.Color.Primary)
          }.width(36).height(36)
          .onClick(() => {
            this.showHistoryPanel = true;
          })

          Stack() {
            Circle({ width: 36, height: 36 }).fill(Theme.Color.GlassMedium)
            Text('✕').fontSize(16).fontColor(Theme.Color.TextSecondary)
          }.width(36).height(36).margin({ left: 8 })
          .onClick(() => { this.showAiCorePanel = false; })
        }.width('100%').padding({ left: 20, right: 20, top: 18, bottom: 14 })

        Divider().color(Theme.Color.BorderLight).margin({ left: 20, right: 20 })

        Scroll() {
          Column({ space: 10 }) {
            ForEach(this.messages, (msg: ChatMessage) => {
              Column({ space: 6 }) {
                Row() {
                  Row({ space: 6 }) {
                    Circle({ width: 6, height: 6 })
                      .fill(msg.role === 'user' ? Theme.Color.Primary : Theme.Color.Secondary)
                    Text(msg.role === 'user' ? '你' : 'AI').fontSize(12).fontWeight(500)
                      .fontColor(msg.role === 'user' ? Theme.Color.Primary : Theme.Color.Secondary)
                  }
                  Blank()
                  Text(this.formatTime(msg.timestamp)).fontSize(10).fontColor(Theme.Color.TextTertiary)
                }.width('100%')
                if (msg.thinking) {
                  Text(msg.thinking).fontSize(12).fontColor(Theme.Color.Warning)
                    .padding(10).backgroundColor('rgba(255, 149, 0, 0.06)')
                    .borderRadius(Theme.Radius.m)
                    .border({ width: 1, color: 'rgba(255, 149, 0, 0.1)' }).width('100%')
                }
                Text(msg.content).fontSize(14).fontColor(Theme.Color.TextPrimary).lineHeight(22).width('100%')
              }.width('100%').padding(14)
              .backgroundColor(msg.role === 'user' ? 'rgba(10, 89, 247, 0.05)' : Theme.Color.BackgroundTertiary)
              .borderRadius(Theme.Radius.l)
              .border({ width: 1, color: msg.role === 'user' ? 'rgba(10, 89, 247, 0.1)' : Theme.Color.BorderLight })
            })
          }.width('100%').padding({ left: 16, right: 16, top: 12, bottom: 8 })
        }.layoutWeight(1).scrollBar(BarState.Auto)

        // 图片预览
        if (this.selectedImageUri) {
          Row() {
            Image(this.selectedImageUri).width(60).height(60).borderRadius(8).objectFit(ImageFit.Cover)
            Text('取消').fontSize(11).fontColor(Theme.Color.Destructive).margin({ left: 8 })
              .onClick(() => { this.selectedImageUri = '' })
          }.width('100%').padding({ left: 16, right: 16, top: 8 })
        }

        Row({ space: 8 }) {
          // 左：拍照按钮
          Button({ type: ButtonType.Circle }) {
            SimpleIcon({ iconName: 'camera', iconSize: 20, color: Theme.Color.TextSecondary })
          }
          .width(38).height(38)
          .backgroundColor(Theme.Color.BackgroundTertiary)
          .border({ width: 0.5, color: Theme.Color.BorderLight })
          .onClick(() => {
            this.showPlusMenu = false;
            this.getUIContext().getRouter().pushUrl({ url: 'pages/Camera' });
          })

          // 中：输入框 或 按住说话
          if (this.isVoiceMode) {
            Column() {
              SimpleIcon({ iconName: 'mic', iconSize: 16,
                color: this.isRecording ? Theme.Color.Destructive : Theme.Color.TextSecondary })
              Text(this.isRecording ? '松开发送' : '按住说话')
                .fontSize(13).fontWeight(600)
                .fontColor(this.isRecording ? Theme.Color.Destructive : Theme.Color.TextSecondary)
            }
            .layoutWeight(1).height(40)
            .justifyContent(FlexAlign.Center)
            .backgroundColor(this.isRecording ? 'rgba(255,59,48,0.10)' : Theme.Color.BackgroundTertiary)
            .borderRadius(Theme.Radius.round)
            .border({ width: this.isRecording ? 1.5 : 0.5,
              color: this.isRecording ? Theme.Color.Destructive : Theme.Color.BorderLight })
            .onTouch((event: TouchEvent) => {
              if (event.type === TouchType.Down) { this.startRecording(); }
              else if (event.type === TouchType.Up || event.type === TouchType.Cancel) {
                if (this.isRecording) { this.stopRecording(); }
              }
            })
          } else {
            TextInput({ placeholder: '输入消息...', text: this.inputText, controller: this.inputController })
              .layoutWeight(1).height(40).fontSize(14)
              .fontColor(Theme.Color.TextPrimary).placeholderColor(Theme.Color.TextTertiary)
              .backgroundColor(Theme.Color.BackgroundTertiary)
              .borderRadius(Theme.Radius.round)
              .border({ width: 0.5, color: Theme.Color.BorderLight })
              .padding({ left: 14, right: 14 })
              .onChange((v: string) => { this.inputText = v; this.showPlusMenu = false; })
              .onSubmit(() => { this.sendMessage(); })
          }

          // 右1：语音/文本切换按钮
          Button({ type: ButtonType.Circle }) {
            SimpleIcon({ iconName: this.isVoiceMode ? 'keyboard' : 'mic', iconSize: 20,
              color: this.isVoiceMode ? Theme.Color.Primary : Theme.Color.TextSecondary })
          }
          .width(38).height(38)
          .backgroundColor(this.isVoiceMode ? 'rgba(10,89,247,0.08)' : Theme.Color.BackgroundTertiary)
          .border({ width: 0.5, color: this.isVoiceMode ? Theme.Color.Primary : Theme.Color.BorderLight })
          .onClick(() => {
            this.isVoiceMode = !this.isVoiceMode;
            this.showPlusMenu = false;
            if (!this.isVoiceMode) { this.inputText = ''; }
          })

          // 右2：加号按钮 或 发送按钮（文本模式有内容时变发送）
          if (!this.isVoiceMode && this.inputText.trim().length > 0) {
            Button({ type: ButtonType.Circle }) {
              SimpleIcon({ iconName: 'send', iconSize: 18, color: '#FFFFFF' })
            }
            .width(38).height(38)
            .backgroundColor(this.isLoading ? '#CCCCCC' : Theme.Color.Primary)
            .shadow(this.isLoading ? Theme.Shadow.Soft : Theme.Shadow.GlowPrimary)
            .enabled(!this.isLoading)
            .onClick(() => { this.sendMessage(); })
          } else {
            Button({ type: ButtonType.Circle }) {
              Text(this.showPlusMenu ? '×' : '+')
                .fontSize(22).fontWeight(300)
                .fontColor(this.showPlusMenu ? Theme.Color.Destructive : Theme.Color.TextSecondary)
            }
            .width(38).height(38)
            .backgroundColor(this.showPlusMenu ? 'rgba(255,59,48,0.08)' : Theme.Color.BackgroundTertiary)
            .border({ width: 0.5, color: this.showPlusMenu ? Theme.Color.Destructive : Theme.Color.BorderLight })
            .onClick(() => { this.showPlusMenu = !this.showPlusMenu; })
          }
        }
        .width('100%').padding({ left: 12, right: 12, top: 8, bottom: 14 })
        .border({ width: { top: 0.5 }, color: Theme.Color.BorderLight })

        // 加号展开菜单
        if (this.showPlusMenu) {
          Row({ space: 24 }) {
            // 相册
            Column({ space: 6 }) {
              Button({ type: ButtonType.Circle }) {
                SimpleIcon({ iconName: 'image', iconSize: 24, color: Theme.Color.Primary })
              }
              .width(52).height(52)
              .backgroundColor('rgba(10,89,247,0.08)')
              .border({ width: 1, color: 'rgba(10,89,247,0.15)' })
              .onClick(() => { this.showPlusMenu = false; this.pickImage(); })
              Text('相册').fontSize(12).fontColor(Theme.Color.TextSecondary)
            }.alignItems(HorizontalAlign.Center)

            // 通话
            Column({ space: 6 }) {
              Button({ type: ButtonType.Circle }) {
                SimpleIcon({ iconName: this.isInCall ? 'end_call' : 'phone', iconSize: 24,
                  color: this.isInCall ? '#FFFFFF' : '#00C853' })
              }
              .width(52).height(52)
              .backgroundColor(this.isInCall ? '#FF3B30' : 'rgba(0,200,83,0.10)')
              .border({ width: 1, color: this.isInCall ? '#FF3B30' : 'rgba(0,200,83,0.2)' })
              .onClick(() => {
                this.showPlusMenu = false;
                if (this.isInCall) { this.endCall(); } else { this.startCall(); }
              })
              Text(this.isInCall ? this.callDurationText : '通话')
                .fontSize(12)
                .fontColor(this.isInCall ? Theme.Color.Destructive : Theme.Color.TextSecondary)
            }.alignItems(HorizontalAlign.Center)
          }
          .width('100%')
          .padding({ left: 24, right: 24, top: 12, bottom: 16 })
          .backgroundColor(Theme.Color.BackgroundSecondary)
          .border({ width: { top: 0.5 }, color: Theme.Color.BorderLight })
          .justifyContent(FlexAlign.Start)
          .animation({ duration: 200, curve: Curve.EaseOut })
        }
      }
      .width('90%').height('75%')
      .backgroundColor(Theme.Color.BackgroundSecondary)
      .borderRadius(Theme.Radius.xl)
      .border({ width: 1, color: Theme.Color.BorderLight })
      .shadow(Theme.Shadow.Elevated)
      .position({ x: '5%', y: '12.5%' })
    }.width('100%').height('100%').zIndex(180)
    .visibility(this.showAiCorePanel ? Visibility.Visible : Visibility.Hidden)
    .hitTestBehavior(this.showAiCorePanel ? HitTestMode.Default : HitTestMode.None)
  }

  @Builder
  buildHistoryPanel() {
    Stack() {
      Column().width('100%').height('100%').backgroundColor(Theme.Color.OverlayMedium)
        .onClick(() => { this.showHistoryPanel = false; this.showAiCorePanel = true; })
      Column() {
        Row() {
          Text('历史对话').fontSize(17).fontWeight(600).fontColor(Theme.Color.TextPrimary)
          Blank()
          Button('新对话').fontSize(12).fontColor(Theme.Color.Primary)
            .backgroundColor(Theme.Color.GlassMedium).height(32).borderRadius(Theme.Radius.round)
            .padding({ left: 14, right: 14 })
            .onClick(() => { this.createNewConversation(); })
          Stack() {
            Circle({ width: 32, height: 32 }).fill(Theme.Color.GlassMedium)
            Text('✕').fontSize(15).fontColor(Theme.Color.TextSecondary)
          }.width(32).height(32).margin({ left: 10 })
          .onClick(() => { this.showHistoryPanel = false; this.showAiCorePanel = true; })
        }.width('100%').padding({ left: 20, right: 20, top: 18, bottom: 14 })
        Divider().color(Theme.Color.BorderLight).margin({ left: 20, right: 20 })
        if (this.conversations.length === 0) {
          Column({ space: 8 }) {
            SimpleIcon({ iconName: 'chat', iconSize: 36, color: Theme.Color.TextTertiary })
            Text('暂无历史对话').fontSize(14).fontColor(Theme.Color.TextTertiary)
          }.width('100%').height(150).justifyContent(FlexAlign.Center)
        } else {
          List({ space: 8 }) {
            ForEach(this.conversations, (c: ConversationItem) => {
              ListItem() {
                Column({ space: 6 }) {
                  Text(c.title).fontSize(14).fontWeight(600).fontColor(Theme.Color.TextPrimary)
                    .maxLines(1).textOverflow({ overflow: TextOverflow.Ellipsis })
                  Text(c.preview).fontSize(12).fontColor(Theme.Color.TextTertiary)
                    .maxLines(1).textOverflow({ overflow: TextOverflow.Ellipsis })
                }.width('100%').padding(14)
                .backgroundColor(this.currentSessionId === c.id ? 'rgba(10, 89, 247, 0.08)' : Theme.Color.BackgroundTertiary)
                .borderRadius(Theme.Radius.m)
                .border({ width: 1, color: this.currentSessionId === c.id ? 'rgba(10, 89, 247, 0.2)' : Theme.Color.BorderLight })
                .onClick(() => { this.loadConversationMessages(c.id); })
              }
            })
          }.width('100%').layoutWeight(1).padding({ left: 16, right: 16, top: 8 })
        }
      }
      .width('85%').height('60%')
      .backgroundColor(Theme.Color.BackgroundSecondary)
      .borderRadius(Theme.Radius.xl)
      .border({ width: 1, color: Theme.Color.BorderLight })
      .shadow(Theme.Shadow.Elevated)
      .position({ x: '7.5%', y: '20%' })
    }.width('100%').height('100%').zIndex(200)
  }
}

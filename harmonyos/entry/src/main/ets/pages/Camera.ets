/**
 *  - HarmonyOS 6 
 * 
 */
import { BusinessError } from '@ohos.base';
import { router } from '@kit.ArkUI';
import { photoAccessHelper } from '@kit.MediaLibraryKit';
import { fileIo as fs } from '@kit.CoreFileKit';
import { util } from '@kit.ArkTS';
import { abilityAccessCtrl, PermissionRequestResult, Permissions } from '@kit.AbilityKit';
import { HttpUtil } from '../utils/HttpUtil';
import { PhotoAlbumService } from '../service/PhotoAlbumService';
import { SimpleIcon } from '../components/IconRenderer';

interface AnalysisResult {
  scene: string;
  objects: string[];
  suggestion: string;
  confidence?: number;
  emotions?: string[];
  colors?: string[];
}

interface AnalysisHistory {
  timestamp: string;
  scene: string;
  imageUri: string;
}

interface ScanResult {
  scanned: number;
  synced: boolean;
}

@Entry
@Component
struct CameraPage {
  @State isProcessing: boolean = false;
  @State statusMessage: string = '';
  @State progress: number = 0;
  @State showContent: boolean = false;
  @State selectedImageUri: string = '';
  @State analysisMode: string = 'comprehensive'; // comprehensive, quick, detailed
  @State historyList: AnalysisHistory[] = [];
  @State showHistory: boolean = false;
  @State isScanning: boolean = false;
  @State scanProgress: string = '';
  @State hasAlbumPermission: boolean = false;
  
  private photoAlbumService: PhotoAlbumService = PhotoAlbumService.getInstance();

  aboutToAppear(): void {
    console.info('VisionAgent', 'Camera page loaded');
    this.loadHistory();
    // UIContext
    this.photoAlbumService.setUIContext(this.getUIContext());
    // 处理逻辑
    this.checkAlbumPermission();
  }
  
  onPageShow(): void {
    this.triggerPageAnimation();
  }
  
  /**
 * 页面组件
 */
  private triggerPageAnimation(): void {
    this.showContent = false;
    setTimeout(() => {
      this.showContent = true;
    }, 50);
  }
  
  /**
 * 页面组件
 */
  private async checkAlbumPermission(): Promise<void> {
    try {
      const atManager = abilityAccessCtrl.createAtManager();
      const permissions: Permissions[] = ['ohos.permission.READ_MEDIA'];
      
      const hostContext = this.getUIContext().getHostContext();
      if (!hostContext || !hostContext.applicationInfo) {
        console.error('Cannot get host context or application info');
        this.hasAlbumPermission = false;
        return;
      }
      
      const grantStatus = await atManager.checkAccessToken(
        hostContext.applicationInfo.accessTokenId,
        permissions[0]
      );
      
      this.hasAlbumPermission = (grantStatus === abilityAccessCtrl.GrantStatus.PERMISSION_GRANTED);
      console.info(`Album permission status: ${this.hasAlbumPermission}`);
    } catch (error) {
      console.error('Check album permission failed:', error);
      this.hasAlbumPermission = false;
    }
  }
  
  /**
 * 页面组件
 */
  private async requestAlbumPermission(): Promise<boolean> {
    try {
      const atManager = abilityAccessCtrl.createAtManager();
      const permissions: Permissions[] = ['ohos.permission.READ_MEDIA'];
      
      const hostContext = this.getUIContext().getHostContext();
      if (!hostContext) {
        console.error('Cannot get host context');
        return false;
      }
      
      const result = await atManager.requestPermissionsFromUser(
        hostContext,
        permissions
      ) as PermissionRequestResult;
      
      if (result && result.authResults && result.authResults[0] === abilityAccessCtrl.GrantStatus.PERMISSION_GRANTED) {
        this.hasAlbumPermission = true;
        console.info('Album permission granted');
        return true;
      } else {
        this.hasAlbumPermission = false;
        console.warn('Album permission denied');
        return false;
      }
    } catch (error) {
      console.error('Request album permission failed:', error);
      this.hasAlbumPermission = false;
      return false;
    }
  }
  
  /**
 * 页面组件
 */
  private loadHistory(): void {
    // TODO: 
    this.historyList = [];
  }
  
  /**
   * 7
   */
  async scanAlbum(): Promise<void> {
    if (this.isScanning) {
      return;
    }
    
    // 处理逻辑
    if (!this.hasAlbumPermission) {
      this.scanProgress = '...';
      const granted = await this.requestAlbumPermission();
      if (!granted) {
        this.scanProgress = '';
        setTimeout(() => {
          this.scanProgress = '';
        }, 2000);
        return;
      }
    }
    
    try {
      this.isScanning = true;
      this.scanProgress = '...';
      
      console.info('[Camera] Starting album scan...');
      console.info('[Camera] PhotoAlbumService instance:', this.photoAlbumService ? 'valid' : 'null');
      
      // 处理逻辑
      let timeoutId: number = -1;
      const timeoutPromise = new Promise<never>((_, reject) => {
        timeoutId = setTimeout(() => {
          console.error('[Camera] Scan timeout after 60 seconds');
          reject(new Error(''));
        }, 60000); // 60
      });
      
      console.info('[Camera] Calling scanAndSync...');
      
      // 7
      let result: ScanResult;
      try {
        result = await Promise.race([
          this.photoAlbumService.scanAndSync('default_user', 7),
          timeoutPromise
        ]) as ScanResult;
        // 处理逻辑
        if (timeoutId !== -1) {
          clearTimeout(timeoutId);
        }
      } catch (error) {
        // 处理逻辑
        if (timeoutId !== -1) {
          clearTimeout(timeoutId);
        }
        // Error
        if (error instanceof Error) {
          throw error;
        } else {
          throw new Error(String(error));
        }
      }
      
      console.info('[Camera] scanAndSync completed');
      
      console.info(`Scan result: scanned=${result.scanned}, synced=${result.synced}`);
      
      this.scanProgress = ` ${result.scanned} `;
      
      if (result.scanned > 0 && result.synced) {
        this.scanProgress += '';
        
        // 处理逻辑
        setTimeout(() => {
          this.scanProgress = '';
          this.isScanning = false;
          this.statusMessage = ` ${result.scanned} `;
        }, 2000);
      } else if (result.scanned === 0) {
        this.scanProgress = '7';
        setTimeout(() => {
          this.scanProgress = '';
          this.isScanning = false;
        }, 2000);
      } else {
        this.scanProgress += '';
        setTimeout(() => {
          this.scanProgress = '';
          this.isScanning = false;
        }, 2000);
      }
      
    } catch (error) {
      console.error(':', JSON.stringify(error));
      const errorMsg = error instanceof Error ? error.message : '';
      this.scanProgress = `: ${errorMsg}`;
      setTimeout(() => {
        this.scanProgress = '';
        this.isScanning = false;
      }, 3000);
    }
  }

  async openPhotoPicker(): Promise<void> {
    try {
      this.statusMessage = '...';
      
      const photoSelectOptions: photoAccessHelper.PhotoSelectOptions = 
        new photoAccessHelper.PhotoSelectOptions();
      photoSelectOptions.maxSelectNumber = 1;
      photoSelectOptions.MIMEType = photoAccessHelper.PhotoViewMIMETypes.IMAGE_TYPE;
      
      const photoViewPicker: photoAccessHelper.PhotoViewPicker = 
        new photoAccessHelper.PhotoViewPicker();
      const photoSelectResult: photoAccessHelper.PhotoSelectResult = 
        await photoViewPicker.select(photoSelectOptions);
      
      if (photoSelectResult.photoUris.length > 0) {
        const photoUri: string = photoSelectResult.photoUris[0];
        this.selectedImageUri = photoUri;
        await this.handleSelectedPhoto(photoUri);
      } else {
        this.statusMessage = '';
      }
      
    } catch (error) {
      const err = error as BusinessError;
      if (err.code === 13900042) {
        this.statusMessage = '';
      } else {
        this.statusMessage = '';
      }
    }
  }

  async handleSelectedPhoto(photoUri: string): Promise<void> {
    try {
      this.isProcessing = true;
      this.progress = 0;
      this.statusMessage = '...';
      
      const file = fs.openSync(photoUri, fs.OpenMode.READ_ONLY);
      const stat = fs.statSync(photoUri);
      const buffer: ArrayBuffer = new ArrayBuffer(stat.size);
      fs.readSync(file.fd, buffer);
      fs.closeSync(file);
      
      this.progress = 20;
      this.statusMessage = '...';
      
      await new Promise<void>((resolve: (value: void) => void) => setTimeout(resolve, 300));
      
      this.progress = 40;
      this.statusMessage = 'AI ...';
      
      const result: AnalysisResult = await this.uploadAndAnalyze(buffer, photoUri);
      
      this.progress = 80;
      this.statusMessage = '...';
      
      await new Promise<void>((resolve: (value: void) => void) => setTimeout(resolve, 300));
      
      this.progress = 100;
      this.statusMessage = '';
      
      // 处理逻辑
      this.saveToHistory(result.scene, photoUri);
      
      setTimeout(() => {
        const resultText: string = this.formatResult(result);
        try {
          router.pushUrl({
            url: 'pages/Result',
            params: {
              imageUri: photoUri,
              result: resultText,
              analysisMode: this.analysisMode
            }
          });
        } catch (error) {
          console.error(':', error);
        }
      }, 500);
      
    } catch (error) {
      const err = error as BusinessError;
      console.error('VisionAgent', `Handle photo error: ${err.message}`);
      this.statusMessage = '';
    } finally {
      this.isProcessing = false;
      this.progress = 0;
    }
  }
  
  /**
 * 页面组件
 */
  private formatResult(result: AnalysisResult): string {
    let text = `${result.scene}\n`;
    
    if (result.objects && result.objects.length > 0) {
      text += `${result.objects.join('')}\n`;
    }
    
    if (result.confidence) {
      text += `${(result.confidence * 100).toFixed(1)}%\n`;
    }
    
    if (result.emotions && result.emotions.length > 0) {
      text += `${result.emotions.join('')}\n`;
    }
    
    if (result.colors && result.colors.length > 0) {
      text += `${result.colors.join('')}\n`;
    }
    
    text += `\n${result.suggestion}`;
    
    return text;
  }
  
  /**
 * 页面组件
 */
  private saveToHistory(scene: string, imageUri: string): void {
    const history: AnalysisHistory = {
      timestamp: new Date().toISOString(),
      scene: scene,
      imageUri: imageUri
    };
    
    this.historyList.unshift(history);
    if (this.historyList.length > 10) {
      this.historyList.pop();
    }
    
    // TODO: 
  }

  async uploadAndAnalyze(imageData: ArrayBuffer, fileName: string): Promise<AnalysisResult> {
    try {
      const uint8Array = new Uint8Array(imageData);
      const base64Helper = new util.Base64Helper();
      const base64 = base64Helper.encodeToStringSync(uint8Array);
      
      class ImageRequest {
        user_id: string = '';
        image: string = '';
        timestamp: string = '';
        analysis_mode: string = '';
      }
      
      const requestData = new ImageRequest();
      requestData.user_id = 'default_user';
      requestData.image = base64;
      requestData.timestamp = new Date().toISOString();
      requestData.analysis_mode = this.analysisMode;
      
      const response = await HttpUtil.post('/api/image/analyze', requestData);
      
      if (response.responseCode === 200) {
        const result = JSON.parse(response.result as string) as Record<string, ESObject>;
        
        // 处理逻辑
        let scene = '';
        let objects: string[] = [];
        
        if (result.data) {
          const dataObj = result.data as Record<string, ESObject>;
          if (dataObj.perception) {
            const perceptionObj = dataObj.perception as Record<string, ESObject>;
            if (perceptionObj.modalities) {
              const modalitiesObj = perceptionObj.modalities as Record<string, ESObject>;
              if (modalitiesObj.image_result) {
                const imageResultObj = modalitiesObj.image_result as Record<string, ESObject>;
                if (imageResultObj.scene) {
                  scene = imageResultObj.scene as string;
                }
                if (imageResultObj.objects) {
                  objects = imageResultObj.objects as string[];
                }
              }
            }
          }
        }
        
        return {
          scene: scene,
          objects: objects,
          suggestion: '',
          confidence: 0.85,
          emotions: ['', ''],
          colors: ['', '']
        };
      } else {
        throw new Error('');
      }
      
    } catch (error) {
      console.error(':', error);
      return {
        scene: '',
        objects: [],
        suggestion: ''
      };
    }
  }

  build() {
    Stack() {
      // 1. 
      Column()
        .width('100%')
        .height('100%')
        .backgroundColor('#F1F3F5')
        
      // 处理逻辑
      Circle({ width: 400, height: 400 })
        .fill('rgba(0, 122, 255, 0.05)')
        .blur(80)
        .position({ x: '50%', y: -100 })
        .translate({ x: '-50%' })

      Column() {
        // 2. 
        Row() {
          Row({ space: 12 }) {
            Button({ type: ButtonType.Circle, stateEffect: true }) {
              SimpleIcon({
                iconName: 'back',
                iconSize: 20,
                color: '#1A1A1A'
              })
            }
            .width(40)
            .height(40)
            .backgroundColor('rgba(255, 255, 255, 0.0)')
            .onClick(() => {
              try {
                router.back();
              } catch (error) {
                console.error(':', error);
              }
            })

            Column({ space: 2 }) {
              Text('')
                .fontSize(20)
                .fontWeight(700)
                .fontColor('#1A1A1A')
              
              Text('AI ')
                .fontSize(12)
                .fontColor('#666666')
            }
            .alignItems(HorizontalAlign.Start)
          }

          Blank()
          
          Button({ type: ButtonType.Circle, stateEffect: true }) {
            SimpleIcon({
              iconName: 'calendar',
              iconSize: 20,
              color: '#007AFF'
            })
          }
          .width(40)
          .height(40)
          .backgroundColor('rgba(255, 255, 255, 0.0)')
          .onClick(() => {
            this.showHistory = !this.showHistory;
          })
        }
        .width('100%')
        .height(56)
        .padding({ left: 16, right: 16 })
        .backgroundColor('rgba(255, 255, 255, 0.6)')
        .backdropBlur(20)
        .zIndex(100)
        .opacity(this.showContent ? 1 : 0)
        .translate({ y: this.showContent ? 0 : -20 })
        .animation({
          duration: 600,
          curve: Curve.Friction
        })

        // 3. 
        if (!this.showHistory) {
          Column({ space: 24 }) {
            // Hero
            Column({ space: 24 }) {
              // 处理逻辑
              Stack({ alignContent: Alignment.Center }) {
                Circle({ width: 160, height: 160 })
                  .fill('rgba(255, 255, 255, 0.8)')
                  .backdropBlur(20)
                  .shadow({ radius: 20, color: 'rgba(0,0,0,0.05)', offsetY: 8 })
                
                if (this.isProcessing) {
                  // 处理逻辑
                  Circle({ width: 160, height: 160 })
                    .fill('rgba(0, 122, 255, 0.1)')
                    .scale({ x: 1.1, y: 1.1 })
                    .animation({
                      duration: 1000,
                      iterations: -1,
                      curve: Curve.EaseInOut,
                      playMode: PlayMode.Alternate
                    })
                }
                
                SimpleIcon({
                  iconName: 'camera',
                  iconSize: 64,
                  color: '#007AFF'
                })
                .opacity(this.isProcessing ? 0.5 : 1.0)
              }
              .margin({ top: 40 })
              .opacity(this.showContent ? 1 : 0)
              .scale({ x: this.showContent ? 1 : 0.8, y: this.showContent ? 1 : 0.8 })
              .animation({
                duration: 600,
                curve: Curve.Friction,
                delay: 100
              })
              
              // 处理逻辑
              Text(this.statusMessage)
                .fontSize(18)
                .fontColor('#1A1A1A')
                .fontWeight(600)
                .textAlign(TextAlign.Center)
                .width('80%')
                .opacity(this.showContent ? 1 : 0)
                .translate({ y: this.showContent ? 0 : 20 })
                .animation({
                  duration: 600,
                  curve: Curve.Friction,
                  delay: 200
                })
              
              // 处理逻辑
              if (this.isProcessing) {
                Column({ space: 8 }) {
                  Progress({ value: this.progress, total: 100, type: ProgressType.Linear })
                    .width('60%')
                    .color('#007AFF')
                    .backgroundColor('rgba(0, 0, 0, 0.05)')
                    .style({ strokeWidth: 4 })
                  
                  Text(`${this.progress}%`)
                    .fontSize(12)
                    .fontColor('#999')
                }
                .width('100%')
                .alignItems(HorizontalAlign.Center)
              }
            }
            .width('100%')
            .alignItems(HorizontalAlign.Center)
            
            // 处理逻辑
            if (!this.isProcessing) {
              Column({ space: 16 }) {
                Text('')
                  .fontSize(16)
                  .fontWeight(600)
                  .fontColor('#1A1A1A')
                  .width('100%')
                  .padding({ left: 8 })
                
                Row({ space: 12 }) {
                  this.ModeButton('快速', 'quick', 'learning')
                  this.ModeButton('全面', 'comprehensive', 'analytics')
                  this.ModeButton('详细', 'detailed', 'insight')
                }
                .width('100%')
              }
              .width('100%')
              .padding({ left: 16, right: 16 })
              .opacity(this.showContent ? 1 : 0)
              .translate({ y: this.showContent ? 0 : 25 })
              .animation({
                duration: 600,
                curve: Curve.Friction,
                delay: 250
              })
            }
            
            // 处理逻辑
            if (!this.isProcessing) {
              Column({ space: 16 }) {
                Text('')
                  .fontSize(16)
                  .fontWeight(600)
                  .fontColor('#1A1A1A')
                  .width('100%')
                  .padding({ left: 8 })
                
                Column({ space: 1 }) {
                  this.FeatureItem('实时分析', 'AI 智能场景识别', true)
                  this.FeatureItem('多模态融合', '图像+文本+语音', true)
                  this.FeatureItem('智能建议', '个性化推荐方案', true)
                  this.FeatureItem('历史记录', '查看分析历史', false)
                }
                .width('100%')
                .backgroundColor('rgba(255, 255, 255, 0.6)')
                .backdropBlur(20)
                .borderRadius(20)
                .clip(true)
              }
              .width('100%')
              .padding({ left: 16, right: 16 })
              .opacity(this.showContent ? 1 : 0)
              .translate({ y: this.showContent ? 0 : 30 })
              .animation({
                duration: 600,
                curve: Curve.Friction,
                delay: 300
              })
            }
          }
          .layoutWeight(1)
          .width('100%')
          .justifyContent(this.isProcessing ? FlexAlign.Center : FlexAlign.Start)
        } else {
          // 处理逻辑
          this.HistoryView()
        }

        // 4. 
        Column({ space: 16 }) {
          // 处理逻辑
          Button() {
            Row({ space: 12 }) {
              SimpleIcon({
                iconName: 'learning',
                iconSize: 20,
                color: '#FFFFFF'
              })
              Text(this.isScanning ? '扫描中...' : '扫描相册')
                .fontSize(16)
                .fontWeight(600)
                .fontColor('#FFFFFF')
            }
          }
          .width('90%')
          .height(56)
          .backgroundColor(this.isScanning ? '#CCCCCC' : '#34C759')
          .borderRadius(28)
          .shadow({ radius: 10, color: this.isScanning ? 'transparent' : 'rgba(52, 199, 89, 0.3)', offsetY: 4 })
          .enabled(!this.isScanning && !this.isProcessing)
          .onClick(() => {
            this.scanAlbum();
          })
          
          // 处理逻辑
          Button() {
            Row({ space: 12 }) {
              SimpleIcon({
                iconName: 'camera',
                iconSize: 20,
                color: '#FFFFFF'
              })
              Text('选择照片')
                .fontSize(16)
                .fontWeight(600)
                .fontColor('#FFFFFF')
            }
          }
          .width('90%')
          .height(56)
          .backgroundColor(this.isProcessing ? '#CCCCCC' : '#007AFF')
          .borderRadius(28)
          .shadow({ radius: 10, color: this.isProcessing ? 'transparent' : 'rgba(0, 122, 255, 0.3)', offsetY: 4 })
          .enabled(!this.isProcessing && !this.isScanning)
          .onClick(() => {
            this.openPhotoPicker();
          })
          
          // 处理逻辑
          if (this.scanProgress) {
            Text(this.scanProgress)
              .fontSize(13)
              .fontColor('#34C759')
              .fontWeight(500)
          } else {
            Text(' AI ')
              .fontSize(12)
              .fontColor('#999999')
          }
        }
        .width('100%')
        .padding({ bottom: 30, top: 20 })
        .alignItems(HorizontalAlign.Center)
        .backgroundColor('rgba(255, 255, 255, 0.8)')
        .backdropBlur(30)
        .borderRadius({ topLeft: 30, topRight: 30 })
        .shadow({ radius: 20, color: 'rgba(0,0,0,0.05)', offsetY: -4 })
      }
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F1F3F5')
  }
  
  @Builder
  ModeButton(label: string, mode: string, iconName: string) {
    Column({ space: 8 }) {
      SimpleIcon({
        iconName: iconName,
        iconSize: 24,
        color: this.analysisMode === mode ? '#007AFF' : '#666666'
      })
      
      Text(label)
        .fontSize(14)
        .fontWeight(this.analysisMode === mode ? 600 : 400)
        .fontColor(this.analysisMode === mode ? '#007AFF' : '#666666')
    }
    .layoutWeight(1)
    .height(90)
    .backgroundColor(this.analysisMode === mode ? 'rgba(0, 122, 255, 0.1)' : 'rgba(255, 255, 255, 0.6)')
    .backdropBlur(10)
    .borderRadius(16)
    .border({
      width: this.analysisMode === mode ? 2 : 0,
      color: '#007AFF'
    })
    .justifyContent(FlexAlign.Center)
    .onClick(() => {
      this.analysisMode = mode;
    })
    .animation({
      duration: 300,
      curve: Curve.EaseInOut
    })
  }
  
  @Builder
  FeatureItem(title: string, desc: string, showDivider: boolean) {
    Column() {
      Row({ space: 12 }) {
        Circle({ width: 8, height: 8 })
          .fill('#007AFF')
          .opacity(0.6)
        
        Column({ space: 4 }) {
          Text(title)
            .fontSize(15)
            .fontWeight(600)
            .fontColor('#1A1A1A')
          
          Text(desc)
            .fontSize(13)
            .fontColor('#666666')
        }
        .alignItems(HorizontalAlign.Start)
        .layoutWeight(1)
      }
      .width('100%')
      .padding(16)
      .alignItems(VerticalAlign.Top)
      
      if (showDivider) {
        Divider()
          .color('rgba(0,0,0,0.05)')
          .padding({ left: 36 })
      }
    }
  }
  
  @Builder
  HistoryView() {
    Column({ space: 16 }) {
      Text('分析历史')
        .fontSize(18)
        .fontWeight(700)
        .fontColor('#1A1A1A')
        .width('100%')
        .padding({ left: 20, right: 20, top: 20 })
      
      if (this.historyList.length === 0) {
        Column({ space: 16 }) {
          SimpleIcon({
            iconName: 'camera',
            iconSize: 48,
            color: '#CCCCCC'
          })
          
          Text('暂无分析记录')
            .fontSize(16)
            .fontColor('#999999')
        }
        .width('100%')
        .height(300)
        .justifyContent(FlexAlign.Center)
      } else {
        List({ space: 12 }) {
          ForEach(this.historyList, (item: AnalysisHistory) => {
            ListItem() {
              Row({ space: 16 }) {
                // 处理逻辑
                Stack() {
                  Rect()
                    .width(60)
                    .height(60)
                    .fill('#F0F0F0')
                    .borderRadius(12)
                  SimpleIcon({
                    iconName: 'camera',
                    iconSize: 24,
                    color: '#007AFF'
                  })
                }
                
                Column({ space: 6 }) {
                  Text(item.scene)
                    .fontSize(16)
                    .fontWeight(600)
                    .fontColor('#1A1A1A')
                  
                  Text(new Date(item.timestamp).toLocaleString())
                    .fontSize(12)
                    .fontColor('#999999')
                }
                .alignItems(HorizontalAlign.Start)
                .layoutWeight(1)
                
                Text('→')
                  .fontSize(20)
                  .fontColor('#CCCCCC')
              }
              .width('100%')
              .padding(16)
              .backgroundColor('rgba(255, 255, 255, 0.8)')
              .backdropBlur(20)
              .borderRadius(16)
              .shadow({ radius: 8, color: 'rgba(0,0,0,0.03)', offsetY: 2 })
            }
          })
        }
        .width('100%')
        .layoutWeight(1)
        .padding({ left: 16, right: 16 })
      }
    }
    .width('100%')
    .layoutWeight(1)
  }
}

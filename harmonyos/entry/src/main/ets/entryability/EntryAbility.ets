import { UIAbility } from '@kit.AbilityKit';
import { hilog } from '@kit.PerformanceAnalysisKit';
import { window } from '@kit.ArkUI';
import { Want } from '@kit.AbilityKit';
import { AbilityConstant } from '@kit.AbilityKit';
import { abilityAccessCtrl, Permissions, PermissionRequestResult } from '@kit.AbilityKit';
import { BusinessError } from '@kit.BasicServicesKit';
// import { SmartVisionService, SamplingStrategy } from '../service/SmartVisionService'; // 
import preferences from '@ohos.data.preferences';
import { getUserSessionManager } from '../service/UserSessionManager';

export default class EntryAbility extends UIAbility {
  // private smartVisionService: SmartVisionService | null = null; // 
  
  onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
    hilog.info(0x0000, 'VisionAgent', '%{public}s', 'Ability onCreate');
    
    // 初始化用户会话管理器
    this.initializeUserSession();
    
    // 
    this.initializeSmartVision();
  }
  
  /**
   * 初始化用户会话管理器
   */
  private async initializeUserSession(): Promise<void> {
    try {
      hilog.info(0x0000, 'VisionAgent', '初始化用户会话管理器...');
      const sessionManager = getUserSessionManager();
      await sessionManager.initialize();
      hilog.info(0x0000, 'VisionAgent', '用户会话管理器初始化完成');
    } catch (err) {
      hilog.error(0x0000, 'VisionAgent', '用户会话管理器初始化失败: %{public}s', JSON.stringify(err));
    }
  }

  onDestroy(): void {
    hilog.info(0x0000, 'VisionAgent', '%{public}s', 'Ability onDestroy');
  }

  onWindowStageCreate(windowStage: window.WindowStage): void {
    hilog.info(0x0000, 'VisionAgent', '%{public}s', 'Ability onWindowStageCreate');

    // 
    this.requestPermissions();

    // 
    this.checkFirstLaunchAndLoadPage(windowStage);
  }

  /**
   * 
   */
  private async checkFirstLaunchAndLoadPage(windowStage: window.WindowStage): Promise<void> {
    try {
      // 检查登录状态
      const authPrefs = await preferences.getPreferences(this.context, 'lifeswarm_auth');
      const token = await authPrefs.get('token', '') as string;
      
      let targetPage = 'pages/Login'; // 默认进入登录页
      
      if (token) {
        // 已登录，检查是否首次启动
        const prefs = await preferences.getPreferences(this.context, 'lifeswarm_config');
        const firstLaunch = await prefs.get('first_launch', true);
        
        if (!firstLaunch) {
          // 非首次启动，直接进入主页
          targetPage = 'pages/Index';
          hilog.info(0x0000, 'VisionAgent', 'User logged in, loading Index');
        } else {
          // 首次启动，进入欢迎页
          targetPage = 'pages/Welcome';
          hilog.info(0x0000, 'VisionAgent', 'First launch with login, loading Welcome page');
        }
      } else {
        // 未登录，进入登录页
        hilog.info(0x0000, 'VisionAgent', 'User not logged in, loading Login page');
      }
      
      windowStage.loadContent(targetPage, (err: BusinessError) => {
        if (err.code) {
          hilog.error(0x0000, 'VisionAgent', 'Failed to load the content. Cause: %{public}s', 
            JSON.stringify(err) ?? '');
          return;
        }
        hilog.info(0x0000, 'VisionAgent', `Succeeded in loading ${targetPage}`);
      });
      
    } catch (error) {
      const err = error as BusinessError;
      hilog.error(0x0000, 'VisionAgent', `Check first launch failed: ${err.message}`);
      
      // 出错时默认进入登录页
      windowStage.loadContent('pages/Login', (err: BusinessError) => {
        if (err.code) {
          hilog.error(0x0000, 'VisionAgent', 'Failed to load Login page. Cause: %{public}s', 
            JSON.stringify(err) ?? '');
        }
      });
    }
  }

  /**
   * 
   */
  private async requestPermissions(): Promise<void> {
    try {
      hilog.info(0x0000, 'VisionAgent', 'Requesting permissions...');
      
      const permissions: Array<Permissions> = [
        'ohos.permission.CAMERA'
      ];
      
      const atManager: abilityAccessCtrl.AtManager = abilityAccessCtrl.createAtManager();
      const result: PermissionRequestResult = await atManager.requestPermissionsFromUser(
        this.context, 
        permissions
      );
      
      // 
      for (let i = 0; i < result.authResults.length; i++) {
        if (result.authResults[i] === 0) {
          hilog.info(0x0000, 'VisionAgent', `Permission granted: ${permissions[i]}`);
        } else {
          hilog.warn(0x0000, 'VisionAgent', `Permission denied: ${permissions[i]}`);
        }
      }
      
    } catch (error) {
      const err = error as BusinessError;
      hilog.error(0x0000, 'VisionAgent', `Request permissions failed: ${err.code}, ${err.message}`);
    }
  }

  onWindowStageDestroy(): void {
    hilog.info(0x0000, 'VisionAgent', '%{public}s', 'Ability onWindowStageDestroy');
  }

  onForeground(): void {
    hilog.info(0x0000, 'VisionAgent', '%{public}s', 'Ability onForeground');
  }

  onBackground(): void {
    hilog.info(0x0000, 'VisionAgent', '%{public}s', 'Ability onBackground');
  }
  
  /**
   * 
   */
  private async initializeSmartVision(): Promise<void> {
    // 
    /*
    try {
      hilog.info(0x0000, 'VisionAgent', 'Initializing smart vision service...');
      
      this.smartVisionService = SmartVisionService.getInstance();
      await this.smartVisionService.initialize(this.context);
      
      // 
      this.smartVisionService.configure({
        strategy: SamplingStrategy.SPARSE,      // 5/
        interval: 5 * 60 * 1000,                // 5
        enableAutoTrigger: true,                // 
        enableBackgroundCapture: false,         // 
        privacyMode: true,                      // 
        localProcessOnly: true,                 // 
        autoDeleteRaw: true                     // 
      });
      
      // 
      this.smartVisionService.addListener((result) => {
        hilog.info(0x0000, 'VisionAgent', 
          `Vision captured: ${result.scene} at ${new Date(result.timestamp).toLocaleString()}`);
      });
      
      // 
      // await this.smartVisionService.startSampling();
      
      hilog.info(0x0000, 'VisionAgent', 'Smart vision service initialized');
      
    } catch (error) {
      const err = error as BusinessError;
      hilog.error(0x0000, 'VisionAgent', `Initialize smart vision failed: ${err.message}`);
    }
    */
    hilog.info(0x0000, 'VisionAgent', 'Smart vision service disabled for testing');
  }
}

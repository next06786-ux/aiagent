import { UIAbility } from '@kit.AbilityKit';
import { hilog } from '@kit.PerformanceAnalysisKit';
import { window } from '@kit.ArkUI';
import { Want } from '@kit.AbilityKit';
import { AbilityConstant } from '@kit.AbilityKit';
import { abilityAccessCtrl, Permissions, PermissionRequestResult } from '@kit.AbilityKit';
import { BusinessError } from '@kit.BasicServicesKit';
import preferences from '@ohos.data.preferences';

export default class EntryAbility extends UIAbility {
  
  onCreate(want: Want, launchParam: AbilityConstant.LaunchParam): void {
    hilog.info(0x0000, 'VisionAgent', '%{public}s', 'Ability onCreate');
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
          targetPage = 'pages/AgentHome';
          hilog.info(0x0000, 'VisionAgent', 'User logged in, loading AgentHome');
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
}

import * as PIXI from 'pixi.js';
import { Live2DModel } from 'pixi-live2d-display/cubism4';

// 简单的Live2D管理器 - 每个模型完全独立
class Live2DManager {
  private static instance: Live2DManager;
  private models: Map<string, any> = new Map();
  private containers: Map<string, HTMLDivElement> = new Map();
  private tickerRegistered: boolean = false;
  private loadingQueue: Promise<void> = Promise.resolve();

  private constructor() {
    // 延迟注册Ticker
  }

  static getInstance(): Live2DManager {
    if (!Live2DManager.instance) {
      Live2DManager.instance = new Live2DManager();
    }
    return Live2DManager.instance;
  }

  private ensureTickerRegistered(): void {
    if (!this.tickerRegistered && typeof window !== 'undefined') {
      (window as any).PIXI = PIXI;
      Live2DModel.registerTicker(PIXI.Ticker);
      this.tickerRegistered = true;
      console.log('[Live2DManager] Ticker registered');
    }
  }

  async loadModel(
    id: string,
    container: HTMLDivElement,
    modelPath: string
  ): Promise<void> {
    // 串行加载，避免并发创建WebGL上下文
    this.loadingQueue = this.loadingQueue.then(() => 
      this._loadModelInternal(id, container, modelPath)
    );
    return this.loadingQueue;
  }

  private async _loadModelInternal(
    id: string,
    container: HTMLDivElement,
    modelPath: string
  ): Promise<void> {
    try {
      console.log(`[Live2DManager] Loading model ${id} from ${modelPath}`);

      // 确保Ticker已注册
      this.ensureTickerRegistered();

      // 如果已经有这个模型，先销毁
      if (this.models.has(id)) {
        await this.destroyModel(id);
      }

      // 创建独立的 canvas
      const canvas = document.createElement('canvas');
      canvas.className = 'live2d-canvas';
      canvas.width = 200;
      canvas.height = 250;
      container.appendChild(canvas);

      // 为每个模型创建独立的 PIXI Application
      const app = new PIXI.Application({
        view: canvas,
        width: 200,
        height: 250,
        backgroundColor: 0xffffff,
        backgroundAlpha: 0,
        antialias: true,
        resolution: window.devicePixelRatio || 1,
        autoDensity: true,
        powerPreference: 'high-performance',
        // 关键：使用独立的WebGL上下文
        context: null, // 让PIXI创建新的上下文
      });

      // 等待一帧，确保WebGL上下文完全初始化
      await new Promise(resolve => requestAnimationFrame(resolve));

      // 加载模型
      const model = await Live2DModel.from(modelPath, {
        autoInteract: false,
        autoUpdate: false,
      });

      // 设置模型
      const scale = Math.min(app.screen.width / model.width, app.screen.height / model.height) * 0.8;
      model.scale.set(scale);
      model.anchor.set(0.5, 0.5);
      model.x = app.screen.width / 2;
      model.y = app.screen.height / 2 + 20;

      app.stage.addChild(model as any);

      // 手动更新循环
      app.ticker.add(() => {
        model.update(app.ticker.deltaMS);
      });

      // 保存引用
      this.models.set(id, { app, model, canvas });
      this.containers.set(id, container);

      console.log(`[Live2DManager] Model ${id} loaded successfully`);

      // 播放待机动画
      this.playIdleMotion(id);

      // 再等待一帧，确保渲染完成
      await new Promise(resolve => requestAnimationFrame(resolve));
    } catch (error) {
      console.error(`[Live2DManager] Failed to load model ${id}:`, error);
      throw error;
    }
  }

  playIdleMotion(id: string): void {
    const modelData = this.models.get(id);
    if (modelData?.model?.internalModel?.motionManager) {
      try {
        modelData.model.motion('idle');
      } catch (e) {
        console.log(`[Live2DManager] Idle motion failed for ${id}:`, e);
      }
    }
  }

  playMotion(id: string, motionName: string): void {
    const modelData = this.models.get(id);
    if (modelData?.model?.internalModel?.motionManager) {
      try {
        modelData.model.motion(motionName);
      } catch (e) {
        console.log(`[Live2DManager] Motion ${motionName} failed for ${id}:`, e);
      }
    }
  }

  async destroyModel(id: string): Promise<void> {
    const modelData = this.models.get(id);
    if (modelData) {
      try {
        if (modelData.model) {
          modelData.model.destroy({ children: true });
        }
        if (modelData.app) {
          modelData.app.destroy(true, { children: true, texture: true, baseTexture: true });
        }
        if (modelData.canvas && modelData.canvas.parentNode) {
          modelData.canvas.parentNode.removeChild(modelData.canvas);
        }
      } catch (e) {
        console.error(`[Live2DManager] Error destroying model ${id}:`, e);
      }
      this.models.delete(id);
      this.containers.delete(id);
    }
  }
}

export default Live2DManager;

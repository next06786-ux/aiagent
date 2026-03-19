/**
 * 多模态数据收集服务
 * 整合传感器、上下文和图像数据
 */
import { SensorService, SensorData, HealthData } from './SensorService';
import { ContextService, ContextData } from './ContextService';
import { EnhancedCameraService, CaptureResult } from './EnhancedCameraService';
import { HttpUtil } from '../utils/HttpUtil';

/**
 * 图像数据接口
 */
export interface ImageData {
  uri: string;
  data: ArrayBuffer;
  scene: string;
}

/**
 * 数据元信息接口
 */
export interface DataMetadata {
  dataQuality: number;
  completeness: number;
  availableModalities: string[];
}

/**
 * 服务类
 */
export interface MultimodalDataPackage {
  timestamp: number;
  userId: string;
  sensor?: SensorData;
  health?: HealthData;
  context?: ContextData;
  image?: ImageData;
  text?: string;
  metadata: DataMetadata;
}

/**
 * 服务类
 */
export interface CollectionConfig {
  enableSensor: boolean;
  enableHealth: boolean;
  enableContext: boolean;
  enableImage: boolean;
  sensorInterval: number; // 处理逻辑
  contextInterval: number;
}

/**
 * 服务类
 */
export interface CollectionStats {
  isCollecting: boolean;
  config: CollectionConfig;
  lastCollection?: number;
}

/**
 * 服务类
 */
interface SendLogData {
  timestamp: number;
  modalities: string[];
  quality: number;
}

/**
 * 服务类
 */
export class MultimodalDataCollector {
  private static instance: MultimodalDataCollector;
  
  private sensorService: SensorService;
  private contextService: ContextService;
  private cameraService: EnhancedCameraService;
  
  private config: CollectionConfig = {
    enableSensor: true,
    enableHealth: true,
    enableContext: true,
    enableImage: false,
    sensorInterval: 5000,
    contextInterval: 60000
  };
  
  private isCollecting: boolean = false;
  private collectionTimer: number = -1;
  
  private constructor() {
    this.sensorService = SensorService.getInstance();
    this.contextService = ContextService.getInstance();
    this.cameraService = EnhancedCameraService.getInstance();
  }
  
  /**
 * 服务类
 */
  public static getInstance(): MultimodalDataCollector {
    if (!MultimodalDataCollector.instance) {
      MultimodalDataCollector.instance = new MultimodalDataCollector();
    }
    return MultimodalDataCollector.instance;
  }
  
  /**
 * 服务类
 */
  public configure(config: Partial<CollectionConfig>): void {
    if (config.enableSensor !== undefined) this.config.enableSensor = config.enableSensor;
    if (config.enableHealth !== undefined) this.config.enableHealth = config.enableHealth;
    if (config.enableContext !== undefined) this.config.enableContext = config.enableContext;
    if (config.enableImage !== undefined) this.config.enableImage = config.enableImage;
    if (config.sensorInterval !== undefined) this.config.sensorInterval = config.sensorInterval;
    if (config.contextInterval !== undefined) this.config.contextInterval = config.contextInterval;
    console.info('MultimodalCollector', 'Configuration updated');
  }
  
  /**
 * 服务类
 */
  public startCollection(userId: string): void {
    if (this.isCollecting) {
      console.warn('MultimodalCollector', 'Already collecting');
      return;
    }
    
    console.info('MultimodalCollector', 'Starting data collection...');
    
    // 处理逻辑
    if (this.config.enableSensor) {
      this.sensorService.startSensorMonitoring();
    }
    
    this.isCollecting = true;
    
    // 处理逻辑
    this.collectionTimer = setInterval(() => {
      this.collectAndSend(userId);
    }, this.config.sensorInterval);
    
    console.info('MultimodalCollector', 'Data collection started');
  }
  
  /**
 * 服务类
 */
  public stopCollection(): void {
    if (!this.isCollecting) {
      return;
    }
    
    console.info('MultimodalCollector', 'Stopping data collection...');
    
    // 处理逻辑
    this.sensorService.stopSensorMonitoring();
    
    // 处理逻辑
    if (this.collectionTimer !== -1) {
      clearInterval(this.collectionTimer);
      this.collectionTimer = -1;
    }
    
    this.isCollecting = false;
    console.info('MultimodalCollector', 'Data collection stopped');
  }
  
  /**
 * 服务类
 */
  private async collectAndSend(userId: string): Promise<void> {
    try {
      const dataPackage = await this.collectData(userId);
      
      // 处理逻辑
      await this.sendToBackend(dataPackage);
      
      console.info('MultimodalCollector', 'Data collected and sent');
    } catch (error) {
      console.error('MultimodalCollector', 'Collection failed:', error);
    }
  }
  
  /**
 * 服务类
 */
  public async collectData(userId: string): Promise<MultimodalDataPackage> {
    const availableModalities: string[] = [];
    
    // 处理逻辑
    let sensorData: SensorData | undefined = undefined;
    if (this.config.enableSensor) {
      sensorData = this.sensorService.getCurrentSensorData();
      availableModalities.push('sensor');
    }
    
    // 处理逻辑
    let healthData: HealthData | undefined = undefined;
    if (this.config.enableHealth) {
      healthData = this.sensorService.getHealthData();
      availableModalities.push('health');
    }
    
    // 处理逻辑
    let contextData: ContextData | undefined = undefined;
    if (this.config.enableContext) {
      contextData = await this.contextService.getCurrentContext();
      availableModalities.push('context');
    }
    
    // 处理逻辑
    const quality = this.calculateDataQuality(sensorData, healthData, contextData);
    const completeness = availableModalities.length / 4; // 4
    
    const dataPackage: MultimodalDataPackage = {
      timestamp: Date.now(),
      userId: userId,
      sensor: sensorData,
      health: healthData,
      context: contextData,
      metadata: {
        dataQuality: quality,
        completeness: completeness,
        availableModalities: availableModalities
      }
    };
    
    return dataPackage;
  }
  
  /**
 * 服务类
 */
  public async collectImageData(userId: string): Promise<MultimodalDataPackage> {
    const baseData = await this.collectData(userId);
    
    // 处理逻辑
    const captureResult = await this.cameraService.capturePhoto();
    
    if (captureResult) {
      const imageData: ImageData = {
        uri: captureResult.imageUri,
        data: captureResult.imageData,
        scene: captureResult.scene
      };
      baseData.image = imageData;
      const modalities = baseData.metadata.availableModalities;
      modalities.push('image');
      baseData.metadata.completeness = modalities.length / 4;
    }
    
    return baseData;
  }
  
  /**
 * 服务类
 */
  public async collectWithText(userId: string, text: string): Promise<MultimodalDataPackage> {
    const baseData = await this.collectData(userId);
    
    baseData.text = text;
    const modalities = baseData.metadata.availableModalities;
    modalities.push('text');
    baseData.metadata.completeness = modalities.length / 4;
    
    return baseData;
  }
  
  /**
 * 服务类
 */
  private calculateDataQuality(
    sensor?: SensorData,
    health?: HealthData,
    context?: ContextData
  ): number {
    let quality = 0;
    let count = 0;
    
    // 处理逻辑
    if (sensor) {
      let sensorQuality = 0;
      if (sensor.heartRate) sensorQuality += 0.25;
      if (sensor.steps) sensorQuality += 0.25;
      if (sensor.accelerometer) sensorQuality += 0.25;
      if (sensor.gyroscope) sensorQuality += 0.25;
      quality += sensorQuality;
      count++;
    }
    
    // 处理逻辑
    if (health) {
      let healthQuality = 0;
      if (health.sleepHours) healthQuality += 0.33;
      if (health.exerciseMinutes) healthQuality += 0.33;
      if (health.mood) healthQuality += 0.34;
      quality += healthQuality;
      count++;
    }
    
    // 处理逻辑
    if (context) {
      let contextQuality = 0.5; // 处理逻辑
      if (context.latitude && context.longitude) contextQuality += 0.25;
      if (context.weather) contextQuality += 0.25;
      quality += contextQuality;
      count++;
    }
    
    return count > 0 ? quality / count : 0;
  }
  
  /**
 * 服务类
 */
  private async sendToBackend(dataPackage: MultimodalDataPackage): Promise<void> {
    try {
      // 处理逻辑
      class MultimodalRequest {
        user_id: string = '';
        timestamp: number = 0;
        sensor: Object | null = null;
        health: Object | null = null;
        context: Object | null = null;
        image: Object | null = null;
        text: string = '';
        metadata: Object | null = null;
      }
      
      const requestData = new MultimodalRequest();
      requestData.user_id = dataPackage.userId;
      requestData.timestamp = dataPackage.timestamp;
      requestData.sensor = dataPackage.sensor as Object || null;
      requestData.health = dataPackage.health as Object || null;
      requestData.context = dataPackage.context as Object || null;
      requestData.image = dataPackage.image as Object || null;
      requestData.text = dataPackage.text || '';
      requestData.metadata = dataPackage.metadata as Object;
      
      // 发送到后端 API
      const response = await HttpUtil.post('/api/v4/multimodal/data', requestData);
      
      if (response.responseCode === 200) {
        console.info('MultimodalCollector', '数据上传成功');
      } else {
        console.warn('MultimodalCollector', `上传失败: ${response.responseCode}`);
      }
    } catch (error) {
      console.error('MultimodalCollector', ':', error);
      // 处理逻辑
    }
  }
  
  /**
 * 服务类
 */
  public getCollectionStats(): CollectionStats {
    const stats: CollectionStats = {
      isCollecting: this.isCollecting,
      config: this.config
    };
    return stats;
  }
  
  /**
 * 服务类
 */
  public async triggerCollection(userId: string): Promise<MultimodalDataPackage> {
    console.info('MultimodalCollector', 'Manual collection triggered');
    const dataPackage = await this.collectData(userId);
    await this.sendToBackend(dataPackage);
    return dataPackage;
  }
}

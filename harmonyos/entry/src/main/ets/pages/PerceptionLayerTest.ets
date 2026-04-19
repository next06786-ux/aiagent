/**
 * 
 * 
 */
import { HttpUtil } from '../utils/HttpUtil';
import { MultimodalDataCollector } from '../service/MultimodalDataCollector';
import { SensorService } from '../service/SensorService';
import { ContextService } from '../service/ContextService';

/**
 * 页面组件
 */
interface TestResult {
  name: string;
  success: boolean;
  duration: string;
  details?: string;
  error?: string;
}

/**
 * 页面组件
 */
class PerceptionAnalysis {
  perception_quality: number = 0;
  modalities_used: string[] = [];
  fused_representation: Record<string, Object> = {};
}

/**
 * API 
 */
class ApiResponse {
  success: boolean = false;
  user_id: string = '';
  analysis: PerceptionAnalysis = new PerceptionAnalysis();
  recommendations: string[] = [];
  timestamp: string = '';
}

/**
 * 页面组件
 */
class RequestMetadata {
  dataQuality: number = 0;
  completeness: number = 0;
  availableModalities: string[] = [];
}

/**
 * 页面组件
 */
class SensorDataRequest {
  steps: number = 0;
  heartRate: number = 0;
  accelerometer: Record<string, number> = {};
  gyroscope: Record<string, number> = {};
}

/**
 * 页面组件
 */
class HealthDataRequest {
  sleepHours: number = 0;
  exerciseMinutes: number = 0;
  mood: number = 0;
}

/**
 * 页面组件
 */
class ContextDataRequest {
  location: string = '';
  latitude: number = 0;
  longitude: number = 0;
}

/**
 * 页面组件
 */
class MultimodalRequest {
  user_id: string = '';
  timestamp: number = 0;
  text?: string;
  sensor?: SensorDataRequest;
  health?: HealthDataRequest;
  context?: ContextDataRequest;
  metadata: RequestMetadata = new RequestMetadata();
}

@Entry
@Component
struct PerceptionLayerTest {
  @State testResults: TestResult[] = [];
  @State isRunning: boolean = false;
  @State currentTest: string = '';
  @State overallStatus: string = '';
  @State userInputText: string = '';
  @State realSensorData: string = '...';
  @State realLocationData: string = '...';
  @State currentLatitude: number = 0;
  @State currentLongitude: number = 0;
  @State currentIPAddress: string = '...';
  @State useRealData: boolean = true;
  
  private collector: MultimodalDataCollector = MultimodalDataCollector.getInstance();
  private sensorService: SensorService = SensorService.getInstance();
  private contextService: ContextService = ContextService.getInstance();
  private userId: string = 'test_user_001';
  
  aboutToAppear() {
    console.info('PerceptionLayerTest', '页面初始化');
    // 请求位置权限
    this.requestLocationPermission();
    // 启动传感器监控
    this.sensorService.startSensorMonitoring();
    // 延迟收集数据
    setTimeout(() => {
      this.collectRealData();
    }, 500); // 等待传感器初始化
  }
  
  /**
 * 页面组件
 */
  private async requestLocationPermission() {
    try {
      console.info('PerceptionLayerTest', ' module.json5 ');
      // 处理逻辑
      this.contextService.setHomeLocation(39.9042, 116.4074); // 处理逻辑
      this.contextService.setOfficeLocation(31.2304, 121.4737); // 处理逻辑
    } catch (error) {
      console.error('PerceptionLayerTest', '', JSON.stringify(error));
    }
  }
  
  aboutToDisappear() {
    // 处理逻辑
    this.sensorService.stopSensorMonitoring();
  }
  
  build() {
    Column() {
      // 处理逻辑
      Row() {
        Text(' ')
          .fontSize(24)
          .fontWeight(FontWeight.Bold)
          .fontColor(Color.White)
      }
      .width('100%')
      .height(60)
      .backgroundColor('#1E88E5')
      .padding({ left: 20 })
      .justifyContent(FlexAlign.Start)
      
      Scroll() {
        Column({ space: 16 }) {
          // 处理逻辑
          this.StatusCard()
          
          // 处理逻辑
          this.DataInputSection()
          
          // 处理逻辑
          this.RealDataDisplay()
          
          // 处理逻辑
          this.TestButtons()
          
          // 处理逻辑
          this.TestResults()
        }
        .width('100%')
        .padding(16)
      }
      .layoutWeight(1)
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#F5F5F5')
  }
  
  @Builder
  StatusCard() {
    Column({ space: 12 }) {
      Row() {
        Text(' ')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
      }
      .width('100%')
      
      Row() {
        Text(': ')
          .fontSize(14)
          .fontColor('#666')
        Text(this.overallStatus)
          .fontSize(14)
          .fontColor(this.isRunning ? '#FF9800' : '#4CAF50')
          .fontWeight(FontWeight.Medium)
      }
      .width('100%')
      
      if (this.currentTest) {
        Row() {
          Text(': ')
            .fontSize(14)
            .fontColor('#666')
          Text(this.currentTest)
            .fontSize(14)
            .fontColor('#1E88E5')
        }
        .width('100%')
      }
      
      Row() {
        Text(`: ${this.testResults.length} `)
          .fontSize(14)
          .fontColor('#666')
      }
      .width('100%')
    }
    .width('100%')
    .padding(16)
    .backgroundColor(Color.White)
    .borderRadius(12)
    .shadow({ radius: 4, color: '#00000010' })
  }
  
  @Builder
  DataInputSection() {
    Column({ space: 12 }) {
      Row() {
        Text(' ')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
      }
      .width('100%')
      
      Column({ space: 8 }) {
        Text('')
          .fontSize(14)
          .fontColor('#666')
          .width('100%')
        
        TextArea({ placeholder: '请输入' })
          .width('100%')
          .height(80)
          .fontSize(14)
          .onChange((value: string) => {
            this.userInputText = value;
          })
      }
      .width('100%')
      .padding(12)
      .backgroundColor(Color.White)
      .borderRadius(8)
    }
    .width('100%')
  }
  
  @Builder
  RealDataDisplay() {
    Column({ space: 12 }) {
      Row() {
        Text(' ')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
      }
      .width('100%')
        
      Column({ space: 8 }) {
        Text('')
          .fontSize(14)
          .fontWeight(FontWeight.Medium)
          .width('100%')
        
        Text(this.realSensorData)
          .fontSize(12)
          .fontColor('#666')
          .width('100%')
        
        Text('')
          .fontSize(14)
          .fontWeight(FontWeight.Medium)
          .width('100%')
          .margin({ top: 8 })
        
        Text(this.realLocationData)
          .fontSize(12)
          .fontColor('#666')
          .width('100%')
        
        Text('IP')
          .fontSize(14)
          .fontWeight(FontWeight.Medium)
          .width('100%')
          .margin({ top: 8 })
        
        Text(this.currentIPAddress)
          .fontSize(12)
          .fontColor('#666')
          .width('100%')
        
        Button('')
          .width('100%')
          .height(35)
          .fontSize(12)
          .backgroundColor('#2196F3')
          .margin({ top: 8 })
          .onClick(() => {
            this.collectRealData();
          })
        
        Button('')
          .width('100%')
          .height(35)
          .fontSize(12)
          .backgroundColor('#FF9800')
          .margin({ top: 8 })
          .onClick(() => {
            this.testLocationPermission();
          })
      }
      .width('100%')
      .padding(12)
      .backgroundColor('#E3F2FD')
      .borderRadius(8)
    }
  }
  
  @Builder
  TestButtons() {
    Column({ space: 12 }) {
      Button('')
        .width('100%')
        .height(50)
        .fontSize(16)
        .backgroundColor('#1E88E5')
        .enabled(!this.isRunning)
        .onClick(() => {
          this.runAllTests();
        })
      
      Row({ space: 12 }) {
        Button('1: ')
          .layoutWeight(1)
          .height(45)
          .fontSize(14)
          .backgroundColor('#4CAF50')
          .enabled(!this.isRunning)
          .onClick(() => {
            this.testTextOnly();
          })
        
        Button('2: ')
          .layoutWeight(1)
          .height(45)
          .fontSize(14)
          .backgroundColor('#FF9800')
          .enabled(!this.isRunning)
          .onClick(() => {
            this.testSensorOnly();
          })
      }
      .width('100%')
      
      Row({ space: 12 }) {
        Button('3: ')
          .layoutWeight(1)
          .height(45)
          .fontSize(14)
          .backgroundColor('#9C27B0')
          .enabled(!this.isRunning)
          .onClick(() => {
            this.testMultimodal();
          })
        
        Button('')
          .layoutWeight(1)
          .height(45)
          .fontSize(14)
          .backgroundColor('#F44336')
          .enabled(!this.isRunning)
          .onClick(() => {
            this.testResults = [];
            this.overallStatus = '';
          })
      }
      .width('100%')
    }
    .width('100%')
  }
  
  @Builder
  TestResults() {
    if (this.testResults.length > 0) {
      Column({ space: 12 }) {
        Text(' ')
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
          .width('100%')
        
        ForEach(this.testResults, (result: TestResult, index: number) => {
          this.TestResultItem(result, index)
        })
      }
      .width('100%')
    }
  }
  
  @Builder
  TestResultItem(result: TestResult, index: number) {
    Column({ space: 8 }) {
      Row() {
        Text(result.success ? '' : '')
          .fontSize(20)
          .fontColor(result.success ? '#4CAF50' : '#F44336')
          .margin({ right: 8 })
        
        Text(`${index + 1}. ${result.name}`)
          .fontSize(16)
          .fontWeight(FontWeight.Medium)
          .layoutWeight(1)
        
        Text(result.duration)
          .fontSize(12)
          .fontColor('#999')
      }
      .width('100%')
      
      if (result.details) {
        Text(result.details)
          .fontSize(14)
          .fontColor('#666')
          .width('100%')
          .margin({ top: 4 })
      }
      
      if (result.error) {
        Text(`: ${result.error}`)
          .fontSize(12)
          .fontColor('#F44336')
          .width('100%')
          .margin({ top: 4 })
      }
    }
    .width('100%')
    .padding(12)
    .backgroundColor(Color.White)
    .borderRadius(8)
    .border({
      width: 1,
      color: result.success ? '#4CAF5020' : '#F4433620'
    })
  }
  
  /**
 * 页面组件
 */
  private async runAllTests(): Promise<void> {
    this.isRunning = true;
    this.overallStatus = '...';
    this.testResults = [];
    
    await this.testTextOnly();
    await this.delay(1000);
    
    await this.testSensorOnly();
    await this.delay(1000);
    
    await this.testMultimodal();
    
    this.isRunning = false;
    
    const passed = this.testResults.filter(r => r.success).length;
    const total = this.testResults.length;
    this.overallStatus = `: ${passed}/${total} `;
    this.currentTest = '';
  }
  
  /**
 * 页面组件
 */
  private async collectRealData(): Promise<void> {
    try {
      // 处理逻辑
      const sensorData = this.sensorService.getCurrentSensorData();
      
      let dataText = '';
      
      // 处理逻辑
      if (sensorData.steps !== undefined) {
        dataText += `: ${sensorData.steps}\n`;
      } else {
        dataText += `: \n`;
      }
      
      // 处理逻辑
      if (sensorData.accelerometer) {
        dataText += `:\n`;
        dataText += `  x=${sensorData.accelerometer.x.toFixed(3)}\n`;
        dataText += `  y=${sensorData.accelerometer.y.toFixed(3)}\n`;
        dataText += `  z=${sensorData.accelerometer.z.toFixed(3)}\n`;
      } else {
        dataText += `: \n`;
      }
      
      // 处理逻辑
      if (sensorData.gyroscope) {
        dataText += `:\n`;
        dataText += `  x=${sensorData.gyroscope.x.toFixed(3)}\n`;
        dataText += `  y=${sensorData.gyroscope.y.toFixed(3)}\n`;
        dataText += `  z=${sensorData.gyroscope.z.toFixed(3)}`;
      } else {
        dataText += `: `;
      }
      
      this.realSensorData = dataText;
      
      //  GPS IP
      const context = await this.contextService.getCurrentContext();
      if (context.latitude && context.longitude) {
        this.currentLatitude = context.latitude;
        this.currentLongitude = context.longitude;
        
        const locationName = this.getLocationName(context.location);
        this.realLocationData = `: ${context.latitude.toFixed(6)}°\n` +
          `: ${context.longitude.toFixed(6)}°\n` +
          `: ${locationName}`;
      } else {
        this.realLocationData = 'GPS\n';
      }
      
      // IP
      if (context.ipAddress) {
        this.currentIPAddress = context.ipAddress;
      } else {
        this.currentIPAddress = 'IP\n';
      }
      
    } catch (error) {
      console.error('PerceptionLayerTest', '', JSON.stringify(error));
      this.realSensorData = '';
      this.realLocationData = 'GPS\n';
    }
  }
  
  /**
 * 页面组件
 */
  private getLocationName(locationType: string): string {
    switch (locationType) {
      case 'home':
        return '';
      case 'office':
        return '';
      case 'outdoor':
        return '';
      default:
        return '';
    }
  }
  
  /**
   * 1: 
   */
  private async testTextOnly(): Promise<void> {
    this.currentTest = '1: ';
    const startTime = Date.now();
    
    try {
      // 处理逻辑
      const textInput = this.userInputText.trim() || '';
      
      const metadata = new RequestMetadata();
      metadata.dataQuality = 0.8;
      metadata.completeness = 0.25;
      metadata.availableModalities = ['text'];
      
      const data = new MultimodalRequest();
      data.user_id = this.userId;
      data.timestamp = Date.now();
      data.text = textInput;
      data.metadata = metadata;
      
      const response = await HttpUtil.post('/api/v4/multimodal/data', data);
      const duration = `${Date.now() - startTime}ms`;
      
      if (response.responseCode === 200) {
        const resultStr = response.result as string;
        const apiResp: ApiResponse = JSON.parse(resultStr) as ApiResponse;
        const quality = apiResp.analysis.perception_quality;
        
        const testResult: TestResult = {
          name: '',
          success: true,
          duration: duration,
          details: `: ${(quality * 100).toFixed(0)}%`
        };
        this.testResults.push(testResult);
      } else {
        throw new Error(`HTTP ${response.responseCode}`);
      }
    } catch (error) {
      const duration = `${Date.now() - startTime}ms`;
      const err = error as Error;
      const testResult: TestResult = {
        name: '',
        success: false,
        duration: duration,
        error: err.message || ''
      };
      this.testResults.push(testResult);
    }
  }
  
  /**
   * 2: 
   */
  private async testSensorOnly(): Promise<void> {
    this.currentTest = '2: ';
    const startTime = Date.now();
    
    try {
      const metadata = new RequestMetadata();
      metadata.dataQuality = 0.9;
      metadata.completeness = 0.5;
      metadata.availableModalities = ['sensor', 'health'];
      
      const sensor = new SensorDataRequest();
      const health = new HealthDataRequest();
      
      // 处理逻辑
      const realData = this.sensorService.getCurrentSensorData();
      
      // 处理逻辑
      sensor.steps = realData.steps || 0;
      
      // 0
      sensor.heartRate = 0;
      
      // 处理逻辑
      sensor.accelerometer = {
        'x': realData.accelerometer?.x || 0,
        'y': realData.accelerometer?.y || 0,
        'z': realData.accelerometer?.z || 9.8
      };
      sensor.gyroscope = {
        'x': realData.gyroscope?.x || 0,
        'y': realData.gyroscope?.y || 0,
        'z': realData.gyroscope?.z || 0
      };
      
      health.sleepHours = 7;
      health.exerciseMinutes = 30;
      health.mood = 7;
      
      const data = new MultimodalRequest();
      data.user_id = this.userId;
      data.timestamp = Date.now();
      data.sensor = sensor;
      data.health = health;
      data.metadata = metadata;
      
      const response = await HttpUtil.post('/api/v4/multimodal/data', data);
      const duration = `${Date.now() - startTime}ms`;
      
      if (response.responseCode === 200) {
        const resultStr = response.result as string;
        const apiResp: ApiResponse = JSON.parse(resultStr) as ApiResponse;
        const quality = apiResp.analysis.perception_quality;
        
        const testResult: TestResult = {
          name: '',
          success: true,
          duration: duration,
          details: `: ${(quality * 100).toFixed(0)}%`
        };
        this.testResults.push(testResult);
      } else {
        throw new Error(`HTTP ${response.responseCode}`);
      }
    } catch (error) {
      const duration = `${Date.now() - startTime}ms`;
      const err = error as Error;
      const testResult: TestResult = {
        name: '',
        success: false,
        duration: duration,
        error: err.message || ''
      };
      this.testResults.push(testResult);
    }
  }
  
  /**
   * 3: 
   */
  private async testMultimodal(): Promise<void> {
    this.currentTest = '3: ';
    const startTime = Date.now();
    
    try {
      const metadata = new RequestMetadata();
      metadata.dataQuality = 0.95;
      metadata.completeness = 0.75;
      metadata.availableModalities = ['text', 'sensor', 'health', 'context'];
      
      const sensor = new SensorDataRequest();
      const health = new HealthDataRequest();
      const context = new ContextDataRequest();
      
      // 处理逻辑
      const textInput = this.userInputText.trim() || '';
      
      if (this.useRealData) {
        // 处理逻辑
        const realData = this.sensorService.getCurrentSensorData();
        sensor.steps = realData.steps || 0;
        sensor.heartRate = realData.heartRate || 0;
        sensor.accelerometer = {
          'x': realData.accelerometer?.x || 0,
          'y': realData.accelerometer?.y || 0,
          'z': realData.accelerometer?.z || 9.8
        };
        sensor.gyroscope = {
          'x': realData.gyroscope?.x || 0,
          'y': realData.gyroscope?.y || 0,
          'z': realData.gyroscope?.z || 0
        };
        
        health.sleepHours = 7;
        health.exerciseMinutes = 20;
        health.mood = 7;
        
        //  GPS 
        if (this.currentLatitude !== 0 && this.currentLongitude !== 0) {
          context.location = 'real_location';
          context.latitude = this.currentLatitude;
          context.longitude = this.currentLongitude;
        } else {
          // GPS
          context.location = 'unknown';
          context.latitude = 0;
          context.longitude = 0;
        }
      } else {
        // 处理逻辑
        sensor.steps = 2000;
        sensor.heartRate = 78;
        sensor.accelerometer = { 'x': 0.05, 'y': 0.1, 'z': 9.8 };
        sensor.gyroscope = { 'x': 0.01, 'y': 0.02, 'z': 0.01 };
        
        health.sleepHours = 6;
        health.exerciseMinutes = 10;
        health.mood = 6;
        
        context.location = 'office';
        context.latitude = 0;
        context.longitude = 0;
      }
      
      const data = new MultimodalRequest();
      data.user_id = this.userId;
      data.timestamp = Date.now();
      data.text = textInput;
      data.sensor = sensor;
      data.health = health;
      data.context = context;
      data.metadata = metadata;
      
      const response = await HttpUtil.post('/api/v4/multimodal/data', data);
      const duration = `${Date.now() - startTime}ms`;
      
      if (response.responseCode === 200) {
        const resultStr = response.result as string;
        const apiResp: ApiResponse = JSON.parse(resultStr) as ApiResponse;
        const quality = apiResp.analysis.perception_quality;
        const modalityCount = apiResp.analysis.modalities_used.length;
        const recommendCount = apiResp.recommendations.length;
        
        const testResult: TestResult = {
          name: '',
          success: true,
          duration: duration,
          details: `: ${(quality * 100).toFixed(0)}%, : ${modalityCount}, : ${recommendCount}`
        };
        this.testResults.push(testResult);
      } else {
        throw new Error(`HTTP ${response.responseCode}`);
      }
    } catch (error) {
      const duration = `${Date.now() - startTime}ms`;
      const err = error as Error;
      const testResult: TestResult = {
        name: '',
        success: false,
        duration: duration,
        error: err.message || ''
      };
      this.testResults.push(testResult);
    }
  }
  
  /**
 * 页面组件
 */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  /**
 * 页面组件
 */
  private async testLocationPermission(): Promise<void> {
    try {
      this.realLocationData = '...';
      
      // 处理逻辑
      const context = await this.contextService.getCurrentContext();
      
      if (context.latitude && context.longitude) {
        this.currentLatitude = context.latitude;
        this.currentLongitude = context.longitude;
        
        const locationName = this.getLocationName(context.location);
        this.realLocationData = `: ${context.latitude.toFixed(6)}°\n` +
          `: ${context.longitude.toFixed(6)}°\n` +
          `: ${locationName}\n` +
          `: `;
        
        console.info('PerceptionLayerTest', `位置信息: ${context.latitude}, ${context.longitude}`);
      } else {
        this.realLocationData = 'GPS数据不可用\n\n请检查:\n1. 是否授予位置权限\n2. 是否开启GPS\n3. 是否在室外GPS信号良好的地方\n4. 重启应用重试';
        console.warn('PerceptionLayerTest', 'GPS数据不可用');
      }
      
    } catch (error) {
      console.error('PerceptionLayerTest', '获取位置失败', JSON.stringify(error));
      this.realLocationData = '位置获取失败\n' + JSON.stringify(error);
    }
  }
}
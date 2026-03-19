/**
 * 24
 * 
 */
import backgroundTaskManager from '@ohos.resourceschedule.backgroundTaskManager'
import { sensor } from '@kit.SensorServiceKit'
import geoLocationManager from '@ohos.geoLocationManager'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'
import { UIContext } from '@kit.ArkUI'

// 处理逻辑
export interface SensorData {
  timestamp: number
  steps: number
  heart_rate?: number
  accelerometer?: AccelerometerData
  gyroscope?: GyroscopeData
  location?: LocationData
  activity?: string
}

// 处理逻辑
interface AccelerometerData {
  x: number
  y: number
  z: number
}

// 处理逻辑
interface GyroscopeData {
  x: number
  y: number
  z: number
}

// 处理逻辑
interface LocationData {
  latitude: number
  longitude: number
}

// 处理逻辑
export interface BackgroundServiceStatus {
  isRunning: boolean
  batchSize: number
  userId: string
}

export class BackgroundSensorService {
  private static instance: BackgroundSensorService
  private isRunning: boolean = false
  private collectInterval: number = 300000 // 5
  private uploadInterval: number = 1800000 // 30
  private collectTimer: number = -1
  private uploadTimer: number = -1
  private sensorDataBatch: SensorData[] = []
  private userId: string = 'default_user'
  
  // 处理逻辑
  private isUserActive: boolean = true // 处理逻辑
  private lastActivityTime: number = Date.now()
  private activeCollectInterval: number = 300000 // 5
  private inactiveCollectInterval: number = 900000 // 15

  private uiContext: UIContext | null = null // UIContext reference

  private constructor() {}

  static getInstance(uiContext?: UIContext): BackgroundSensorService {
    if (!BackgroundSensorService.instance) {
      BackgroundSensorService.instance = new BackgroundSensorService()
      BackgroundSensorService.instance.uiContext = uiContext || null
    }
    return BackgroundSensorService.instance
  }

  /**
   * UIContext
   */
  setUIContext(uiContext: UIContext): void {
    this.uiContext = uiContext
  }

  /**
 * 服务类
 */
  async startBackgroundCollection(userId: string) {
    if (this.isRunning) {
      console.info('Background collection already running')
      return
    }

    this.userId = userId
    this.isRunning = true

    try {
      // 处理逻辑
      await this.requestContinuousTask()

      // 处理逻辑
      this.startCollectionTimer()

      // 处理逻辑
      this.startUploadTimer()

      console.info('Background sensor collection started')
    } catch (error) {
      console.error('Failed to start background collection:', error)
      this.isRunning = false
    }
  }

  /**
 * 服务类
 */
  async stopBackgroundCollection() {
    if (!this.isRunning) {
      return
    }

    // 处理逻辑
    if (this.collectTimer !== -1) {
      clearInterval(this.collectTimer)
      this.collectTimer = -1
    }

    if (this.uploadTimer !== -1) {
      clearInterval(this.uploadTimer)
      this.uploadTimer = -1
    }

    // 处理逻辑
    if (this.sensorDataBatch.length > 0) {
      await this.uploadSensorData()
    }

    // 处理逻辑
    await this.cancelContinuousTask()

    this.isRunning = false
    console.info('Background sensor collection stopped')
  }

  /**
 * 服务类
 */
  private async requestContinuousTask() {
    try {
      if (!this.uiContext) {
        throw new Error('UIContext not set. Cannot start background task.')
      }
      const hostContext = this.uiContext.getHostContext()
      await backgroundTaskManager.startBackgroundRunning(
        hostContext,
        backgroundTaskManager.BackgroundMode.DATA_TRANSFER,
        {
          title: 'LifeSwarm',
          description: ''
        }
      )
    } catch (error) {
      console.error('Failed to request continuous task:', error)
      throw new Error(`Failed to request continuous task: ${error.message || error}`)
    }
  }

  /**
 * 服务类
 */
  private async cancelContinuousTask() {
    try {
      if (!this.uiContext) {
        throw new Error('UIContext not set. Cannot stop background task.')
      }
      const hostContext = this.uiContext.getHostContext()
      await backgroundTaskManager.stopBackgroundRunning(hostContext)
    } catch (error) {
      console.error('Failed to cancel continuous task:', error)
    }
  }

  /**
 * 服务类
 */
  private startCollectionTimer() {
    this.collectTimer = setInterval(() => {
      this.collectSensorData()
    }, this.collectInterval)

    // 处理逻辑
    this.collectSensorData()
  }

  /**
 * 服务类
 */
  private startUploadTimer() {
    this.uploadTimer = setInterval(() => {
      this.uploadSensorData()
    }, this.uploadInterval)
  }

  /**
 * 服务类
 */
  private async collectSensorData() {
    try {
      const data: SensorData = {
        timestamp: Date.now(),
        steps: 0
      }

      // 处理逻辑
      try {
        sensor.once(sensor.SensorId.PEDOMETER, (sensorData: sensor.PedometerResponse) => {
          data.steps = sensorData.steps
          
          // 处理逻辑
          this.updateUserActivity(sensorData.steps)
        })
      } catch (error) {
        console.error('Failed to collect steps:', error)
      }

      // 处理逻辑
      try {
        sensor.once(sensor.SensorId.ACCELEROMETER, (sensorData: sensor.AccelerometerResponse) => {
          data.accelerometer = {
            x: sensorData.x,
            y: sensorData.y,
            z: sensorData.z
          }
          
          // 处理逻辑
          const magnitude = Math.sqrt(
            sensorData.x * sensorData.x +
            sensorData.y * sensorData.y +
            sensorData.z * sensorData.z
          )
          
          // 处理逻辑
          if (magnitude > 15) {
            this.isUserActive = true
            this.lastActivityTime = Date.now()
          }
        })
      } catch (error) {
        console.error('Failed to collect accelerometer:', error)
      }

      // 处理逻辑
      if (this.isUserActive) {
        try {
          sensor.once(sensor.SensorId.GYROSCOPE, (sensorData: sensor.GyroscopeResponse) => {
            data.gyroscope = {
              x: sensorData.x,
              y: sensorData.y,
              z: sensorData.z
            }
          })
        } catch (error) {
          console.error('Failed to collect gyroscope:', error)
        }
      }

      // 处理逻辑
      if (this.isUserActive && this.sensorDataBatch.length % 3 === 0) {
        try {
          const location = await geoLocationManager.getCurrentLocation()
          data.location = {
            latitude: location.latitude,
            longitude: location.longitude
          }
        } catch (error) {
          console.error('Failed to collect location:', error)
        }
      }

      // 处理逻辑
      data.activity = this.inferActivity(data)

      // 处理逻辑
      this.sensorDataBatch.push(data)

      console.info(`Collected sensor data, batch size: ${this.sensorDataBatch.length}, active: ${this.isUserActive}`)

      // 处理逻辑
      if (this.sensorDataBatch.length >= 20) {
        await this.uploadSensorData()
      }
      
      // 处理逻辑
      this.adjustCollectInterval()
    } catch (error) {
      console.error('Failed to collect sensor data:', error)
    }
  }
  
  /**
 * 服务类
 */
  private updateUserActivity(steps: number) {
    const now = Date.now()
    const timeSinceLastActivity = now - this.lastActivityTime
    
    // 30
    if (timeSinceLastActivity > 1800000) {
      this.isUserActive = false
    }
    
    // 处理逻辑
    if (steps > 0) {
      this.isUserActive = true
      this.lastActivityTime = now
    }
  }
  
  /**
 * 服务类
 */
  private inferActivity(data: SensorData): string {
    if (!data.accelerometer) {
      return 'unknown'
    }
    
    const magnitude = Math.sqrt(
      data.accelerometer.x * data.accelerometer.x +
      data.accelerometer.y * data.accelerometer.y +
      data.accelerometer.z * data.accelerometer.z
    )
    
    if (magnitude < 10) {
      return 'sedentary' // 处理逻辑
    } else if (magnitude < 15) {
      return 'walking' // 处理逻辑
    } else {
      return 'exercising' // 处理逻辑
    }
  }
  
  /**
 * 服务类
 */
  private adjustCollectInterval() {
    const newInterval = this.isUserActive ? 
      this.activeCollectInterval : 
      this.inactiveCollectInterval
    
    if (newInterval !== this.collectInterval) {
      console.info(`Adjusting collect interval: ${this.collectInterval}ms -> ${newInterval}ms`)
      this.collectInterval = newInterval
      
      // 处理逻辑
      if (this.collectTimer !== -1) {
        clearInterval(this.collectTimer)
        this.startCollectionTimer()
      }
    }
  }

  /**
 * 服务类
 */
  private async uploadSensorData(): Promise<boolean> {
    if (this.sensorDataBatch.length === 0) {
      return true
    }

    try {
      const httpRequest = http.createHttp()

      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/v4/sensor/background`,
        {
          method: http.RequestMethod.POST,
          header: {
            'Content-Type': 'application/json'
          },
          extraData: JSON.stringify({
            user_id: this.userId,
            sensor_batch: this.sensorDataBatch
          })
        }
      )

      httpRequest.destroy()

      if (response.responseCode === 200) {
        console.info(`Uploaded ${this.sensorDataBatch.length} sensor records`)
        this.sensorDataBatch = [] // 处理逻辑
        return true
      } else {
        console.error('Failed to upload sensor data:', response.responseCode)
        return false
      }
    } catch (error) {
      console.error('Failed to upload sensor data:', error)
      return false
    }
  }

  /**
 * 服务类
 */
  getStatus(): BackgroundServiceStatus {
    return {
      isRunning: this.isRunning,
      batchSize: this.sensorDataBatch.length,
      userId: this.userId
    } as BackgroundServiceStatus
  }

  /**
 * 服务类
 */
  setCollectInterval(intervalMs: number) {
    this.collectInterval = intervalMs

    if (this.isRunning) {
      // 处理逻辑
      if (this.collectTimer !== -1) {
        clearInterval(this.collectTimer)
      }
      this.startCollectionTimer()
    }
  }

  /**
 * 服务类
 */
  setUploadInterval(intervalMs: number) {
    this.uploadInterval = intervalMs

    if (this.isRunning) {
      // 处理逻辑
      if (this.uploadTimer !== -1) {
        clearInterval(this.uploadTimer)
      }
      this.startUploadTimer()
    }
  }
}

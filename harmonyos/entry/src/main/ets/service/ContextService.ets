/**
 * 
 * 
 */
import { geoLocationManager } from '@kit.LocationKit';
import { BusinessError } from '@kit.BasicServicesKit';
import { connection } from '@kit.NetworkKit';

/**
 * 服务类
 */
export enum TimeSlot {
  EARLY_MORNING = 'early_morning',  //  0-6
  MORNING = 'morning',              //  6-9
  FORENOON = 'forenoon',            //  9-12
  NOON = 'noon',                    //  12-14
  AFTERNOON = 'afternoon',          //  14-18
  EVENING = 'evening',              //  18-20
  NIGHT = 'night'                   //  20-24
}

/**
 * 服务类
 */
export enum LocationType {
  HOME = 'home',
  OFFICE = 'office',
  OUTDOOR = 'outdoor',
  UNKNOWN = 'unknown'
}

/**
 * 服务类
 */
export interface WeatherInfo {
  temperature: number;
  condition: string;
  humidity: number;
  rain: boolean;
}

/**
 * 服务类
 */
export interface ContextData {
  timestamp: number;
  timeSlot: TimeSlot;
  dayOfWeek: number;
  isWeekend: boolean;
  location: LocationType;
  latitude?: number;
  longitude?: number;
  weather?: WeatherInfo;
  ipAddress?: string;
}

// 处理逻辑
interface LocationCoords {
  lat: number;
  lon: number;
}

/**
 * 服务类
 */
export class ContextService {
  private static instance: ContextService;
  
  private currentLocation: geoLocationManager.Location | null = null;
  private homeLocation: LocationCoords | null = null;
  private officeLocation: LocationCoords | null = null;
  
  private constructor() {}
  
  /**
 * 服务类
 */
  public static getInstance(): ContextService {
    if (!ContextService.instance) {
      ContextService.instance = new ContextService();
    }
    return ContextService.instance;
  }
  
  /**
 * 服务类
 */
  public setHomeLocation(lat: number, lon: number): void {
    this.homeLocation = { lat: lat, lon: lon };
    console.info('ContextService', `Home location set: ${lat}, ${lon}`);
  }
  
  /**
 * 服务类
 */
  public setOfficeLocation(lat: number, lon: number): void {
    this.officeLocation = { lat: lat, lon: lon };
    console.info('ContextService', `Office location set: ${lat}, ${lon}`);
  }
  
  /**
 * 服务类
 */
  public async getCurrentContext(): Promise<ContextData> {
    const now = new Date();
    const timeSlot = this.getTimeSlot(now.getHours());
    const dayOfWeek = now.getDay();
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
    
    // 处理逻辑
    let locationType = LocationType.UNKNOWN;
    let latitude: number | undefined = undefined;
    let longitude: number | undefined = undefined;
    
    try {
      const location = await this.getCurrentLocation();
      if (location) {
        latitude = location.latitude;
        longitude = location.longitude;
        locationType = this.inferLocationType(latitude, longitude);
        console.info('ContextService', `Got location: ${latitude}, ${longitude}`);
      } else {
        console.warn('ContextService', 'Location is null');
      }
    } catch (error) {
      const err = error as BusinessError;
      console.error('ContextService', `Failed to get location: ${err.code} - ${err.message}`);
    }
    
    // 处理逻辑
    let weather: WeatherInfo | undefined = undefined;
    if (latitude && longitude) {
      try {
        weather = await this.getWeather(latitude, longitude);
      } catch (error) {
        console.warn('ContextService', 'Failed to get weather');
      }
    }
    
    // IP
    let ipAddress: string | undefined = undefined;
    try {
      ipAddress = await this.getCurrentIPAddress();
    } catch (error) {
      console.warn('ContextService', 'Failed to get IP address');
    }
    
    return {
      timestamp: now.getTime(),
      timeSlot: timeSlot,
      dayOfWeek: dayOfWeek,
      isWeekend: isWeekend,
      location: locationType,
      latitude: latitude,
      longitude: longitude,
      weather: weather,
      ipAddress: ipAddress
    };
  }
  
  /**
 * 服务类
 */
  private async getCurrentLocation(): Promise<geoLocationManager.Location | null> {
    try {
      // 处理逻辑
      const isLocationEnabled = await geoLocationManager.isLocationEnabled();
      if (!isLocationEnabled) {
        console.warn('ContextService', 'Location service is disabled');
        return null;
      }
      
      const requestInfo: geoLocationManager.LocationRequest = {
        'priority': geoLocationManager.LocationRequestPriority.ACCURACY,
        'scenario': geoLocationManager.LocationRequestScenario.UNSET,
        'timeInterval': 1,
        'distanceInterval': 0,
        'maxAccuracy': 100
      };
      
      const location = await geoLocationManager.getCurrentLocation(requestInfo);
      this.currentLocation = location;
      console.info('ContextService', `Location obtained: ${location.latitude}, ${location.longitude}`);
      return location;
    } catch (error) {
      const err = error as BusinessError;
      console.error('ContextService', `Location error: ${err.code} - ${err.message}`);
      
      // 处理逻辑
      console.info('ContextService', 'Using simulated location data');
      return this.getSimulatedLocation();
    }
  }
  
  /**
 * 服务类
 */
  private getSimulatedLocation(): geoLocationManager.Location | null {
    // 处理逻辑
    const simulatedLocation: geoLocationManager.Location = {
      latitude: 39.9042,
      longitude: 116.4074,
      altitude: 0,
      accuracy: 50,
      speed: 0,
      timeStamp: Date.now(),
      direction: 0,
      timeSinceBoot: 0,
      additions: []
    };
    
    console.info('ContextService', 'Using simulated location: 39.9042, 116.4074');
    return simulatedLocation;
  }
  
  /**
 * 服务类
 */
  private inferLocationType(lat: number, lon: number): LocationType {
    // 处理逻辑
    if (this.homeLocation) {
      const distanceToHome = this.calculateDistance(
        lat, lon,
        this.homeLocation.lat, this.homeLocation.lon
      );
      if (distanceToHome < 0.1) { // 100
        return LocationType.HOME;
      }
    }
    
    // 处理逻辑
    if (this.officeLocation) {
      const distanceToOffice = this.calculateDistance(
        lat, lon,
        this.officeLocation.lat, this.officeLocation.lon
      );
      if (distanceToOffice < 0.1) {
        return LocationType.OFFICE;
      }
    }
    
    return LocationType.OUTDOOR;
  }
  
  /**
 * 服务类
 */
  private calculateDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const R = 6371; // 处理逻辑
    const dLat = this.toRadians(lat2 - lat1);
    const dLon = this.toRadians(lon2 - lon1);
    
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(this.toRadians(lat1)) * Math.cos(this.toRadians(lat2)) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }
  
  /**
 * 服务类
 */
  private toRadians(degrees: number): number {
    return degrees * Math.PI / 180;
  }
  
  /**
 * 服务类
 */
  private getTimeSlot(hour: number): TimeSlot {
    if (hour >= 0 && hour < 6) {
      return TimeSlot.EARLY_MORNING;
    } else if (hour >= 6 && hour < 9) {
      return TimeSlot.MORNING;
    } else if (hour >= 9 && hour < 12) {
      return TimeSlot.FORENOON;
    } else if (hour >= 12 && hour < 14) {
      return TimeSlot.NOON;
    } else if (hour >= 14 && hour < 18) {
      return TimeSlot.AFTERNOON;
    } else if (hour >= 18 && hour < 20) {
      return TimeSlot.EVENING;
    } else {
      return TimeSlot.NIGHT;
    }
  }
  
  /**
   * IP
   */
  private async getCurrentIPAddress(): Promise<string | undefined> {
    try {
      const netHandle = await connection.getDefaultNet();
      if (!netHandle) {
        console.warn('ContextService', 'No active network connection');
        return undefined;
      }
      
      return new Promise((resolve, reject) => {
        connection.getConnectionProperties(netHandle, (error, data) => {
          if (error) {
            console.error('ContextService', `Failed to get connection properties: ${error.code} - ${error.message}`);
            reject(error);
            return;
          }
          
          try {
            const linkAddresses = data.linkAddresses;
            if (linkAddresses && linkAddresses.length > 0) {
              const firstAddress = linkAddresses[0];
              if (firstAddress.address && firstAddress.address.address) {
                const ip = firstAddress.address.address;
                console.info('ContextService', `Got IP address: ${ip}`);
                resolve(ip);
                return;
              }
            }
            
            console.warn('ContextService', 'No valid IP address found');
            resolve(undefined);
          } catch (parseError) {
            console.error('ContextService', 'Error parsing IP address data');
            reject(parseError);
          }
        });
      });
    } catch (error) {
      const err = error as BusinessError;
      console.error('ContextService', `Failed to get IP address: ${err.code} - ${err.message}`);
      return undefined;
    }
  }
  
  /**
 * 服务类
 */
  private async getWeather(lat: number, lon: number): Promise<WeatherInfo> {
    // TODO: API
    // 处理逻辑
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          temperature: 20,
          condition: '',
          humidity: 60,
          rain: false
        });
      }, 100);
    });
  }
  
  /**
 * 服务类
 */
  public generateSceneDescription(context: ContextData): string {
    const timeDesc = this.getTimeDescription(context.timeSlot);
    const locationDesc = this.getLocationDescription(context.location);
    const dayDesc = context.isWeekend ? '' : '';
    
    let description = `${timeDesc}${dayDesc}`;
    if (locationDesc) {
      description += `${locationDesc}`;
    }
    
    if (context.weather) {
      description += `${context.weather.condition}${context.weather.temperature}°C`;
    }
    
    return description;
  }
  
  /**
 * 服务类
 */
  private getTimeDescription(timeSlot: TimeSlot): string {
    switch (timeSlot) {
      case TimeSlot.EARLY_MORNING:
        return '';
      case TimeSlot.MORNING:
        return '';
      case TimeSlot.FORENOON:
        return '';
      case TimeSlot.NOON:
        return '';
      case TimeSlot.AFTERNOON:
        return '';
      case TimeSlot.EVENING:
        return '';
      case TimeSlot.NIGHT:
        return '';
      default:
        return '';
    }
  }
  
  /**
 * 服务类
 */
  private getLocationDescription(location: LocationType): string {
    switch (location) {
      case LocationType.HOME:
        return '';
      case LocationType.OFFICE:
        return '';
      case LocationType.OUTDOOR:
        return '';
      default:
        return '';
    }
  }
}
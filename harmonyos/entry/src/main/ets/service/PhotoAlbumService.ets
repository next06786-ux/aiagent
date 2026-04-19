/**
 * 
 * 7
 */
import photoAccessHelper from '@ohos.file.photoAccessHelper'
import http from '@ohos.net.http'
import { ApiConfig } from '../config/ApiConfig'
import fs from '@ohos.file.fs'
import image from '@ohos.multimedia.image'
import { UIContext } from '@kit.ArkUI'
import dataSharePredicates from '@ohos.data.dataSharePredicates'

interface LocationData {
  latitude: number
  longitude: number
}

interface PhotoMetadata {
  uri: string
  displayName: string
  timestamp: number
  location?: LocationData
  base64?: string
}

interface PhotoSyncData {
  uri: string
  display_name: string
  timestamp: number
  location?: LocationData
  base64?: string
}

interface PhotoSyncRequest {
  user_id: string
  photos: PhotoSyncData[]
}

interface ScanStatus {
  isScanning: boolean
  lastScanTime: number
  lastScanCount: number
  lastSyncSuccess: boolean
  autoScanEnabled: boolean
  nextScanTime: number
}

interface ScanResult {
  scanned: number
  synced: boolean
}

interface SmartSyncResult {
  scanned: number
  newPhotos: number
  synced: boolean
}

export class PhotoAlbumService {
  private static instance: PhotoAlbumService
  private phAccessHelper: photoAccessHelper.PhotoAccessHelper | null = null
  private userId: string = 'default_user'
  private scanStatus: ScanStatus = {
    isScanning: false,
    lastScanTime: 0,
    lastScanCount: 0,
    lastSyncSuccess: false,
    autoScanEnabled: false,
    nextScanTime: 0
  }
  private autoScanTimer: number = -1
  private autoScanInterval: number = 86400000 // 24

  private uiContext: UIContext | undefined = undefined // UIContext reference

  private constructor() {}

  static getInstance(uiContext?: UIContext): PhotoAlbumService {
    if (!PhotoAlbumService.instance) {
      PhotoAlbumService.instance = new PhotoAlbumService()
      if (uiContext) {
        PhotoAlbumService.instance.uiContext = uiContext
      }
    }
    return PhotoAlbumService.instance
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
  private async initPhotoAccess() {
    if (!this.phAccessHelper) {
      if (!this.uiContext) {
        throw new Error('UIContext not set. Cannot initialize photo access helper.')
      }
      const hostContext = this.uiContext.getHostContext()
      this.phAccessHelper = photoAccessHelper.getPhotoAccessHelper(hostContext)
    }
  }

  /**
   * 7
   */
  async scanRecentPhotos(userId: string, days: number = 7): Promise<PhotoMetadata[]> {
    this.userId = userId
    this.scanStatus.isScanning = true
    
    console.info('[PhotoAlbum] === START SCAN ===')

    try {
      console.info('[PhotoAlbum] Step 1: Initialize PhotoAccessHelper')
      if (!this.uiContext) {
        console.error('[PhotoAlbum] ERROR: UIContext not set!')
        this.scanStatus.isScanning = false
        return []
      }
      
      const hostContext = this.uiContext.getHostContext()
      if (!hostContext) {
        console.error('[PhotoAlbum] ERROR: Cannot get host context')
        this.scanStatus.isScanning = false
        return []
      }
      
      if (!this.phAccessHelper) {
        this.phAccessHelper = photoAccessHelper.getPhotoAccessHelper(hostContext)
      }

      // 7
      const timeThresholdMs = Date.now() - (days * 24 * 60 * 60 * 1000)
      const timeThresholdSec = Math.floor(timeThresholdMs / 1000)
      console.info(`[PhotoAlbum] Step 2: Time threshold = ${new Date(timeThresholdMs).toISOString()}`)
      console.info(`[PhotoAlbum] Step 2.1: Threshold in seconds = ${timeThresholdSec}`)

      // greaterThanOrEqualTo
      const predicates = new dataSharePredicates.DataSharePredicates()
      predicates.orderByDesc(photoAccessHelper.PhotoKeys.DATE_ADDED)
      
      const fetchOptions: photoAccessHelper.FetchOptions = {
        fetchColumns: [
          photoAccessHelper.PhotoKeys.URI,
          photoAccessHelper.PhotoKeys.DISPLAY_NAME,
          photoAccessHelper.PhotoKeys.DATE_ADDED
        ],
        predicates: predicates
      }

      console.info('[PhotoAlbum] Step 3: Fetching assets...')
      console.info('[PhotoAlbum] FetchOptions:', JSON.stringify({
        fetchColumns: fetchOptions.fetchColumns,
        predicatesExists: !!fetchOptions.predicates
      }))
      
      const fetchResult = await this.phAccessHelper.getAssets(fetchOptions)
      console.info('[PhotoAlbum] Step 3.5: FetchResult obtained')
      
      const totalCount = fetchResult.getCount()
      console.info(`[PhotoAlbum] Step 4: Total ${totalCount} photos in album`)

      const photos: PhotoMetadata[] = []
      
      if (totalCount === 0) {
        fetchResult.close()
        this.scanStatus.lastScanTime = Date.now()
        this.scanStatus.lastScanCount = 0
        this.scanStatus.isScanning = false
        console.info('[PhotoAlbum] No photos in album')
        return []
      }

      // 7
      console.info('[PhotoAlbum] Step 5: Processing photos...')
      console.info('[PhotoAlbum] About to call getFirstObject()')
      
      let photoAsset = await fetchResult.getFirstObject()
      console.info('[PhotoAlbum] getFirstObject() returned:', photoAsset ? 'valid asset' : 'null')
      
      let processedCount = 0
      const maxProcess = Math.min(totalCount, 2000) // 2000
      console.info(`[PhotoAlbum] Will process max ${maxProcess} photos (or until 7 days threshold)`)
      
      while (photoAsset && processedCount < maxProcess) {
        processedCount++
        
        if (processedCount === 1) {
          console.info('[PhotoAlbum] Processing first photo...')
        }
        
        try {
          const dateAdded = photoAsset.get(photoAccessHelper.PhotoKeys.DATE_ADDED) as number
          
          // 处理逻辑
          let timestampMs: number
          if (dateAdded > 10000000000) {
            timestampMs = dateAdded
          } else {
            timestampMs = dateAdded * 1000
          }
          
          // 7
          if (timestampMs >= timeThresholdMs) {
            photos.push({
              uri: photoAsset.uri,
              displayName: photoAsset.displayName,
              timestamp: timestampMs
            })
            
            if (processedCount === 1) {
              console.info(`[PhotoAlbum] First photo: ${photoAsset.displayName}, date: ${new Date(timestampMs).toISOString()}`)
            }
          } else {
            // 7
            console.info(`[PhotoAlbum] Reached photos older than ${days} days, stopping scan`)
            break
          }
        } catch (err) {
          console.error(`[PhotoAlbum] Error processing photo ${processedCount}:`, err)
        }

        // 50
        if (processedCount % 50 === 0) {
          console.info(`[PhotoAlbum] Progress: ${processedCount}/${maxProcess}, found ${photos.length} recent photos`)
        }

        if (await fetchResult.isAfterLast()) {
          console.info('[PhotoAlbum] Reached last photo')
          break
        }
        
        if (processedCount === 1) {
          console.info('[PhotoAlbum] Getting next object...')
        }
        photoAsset = await fetchResult.getNextObject()
        
        if (processedCount === 1) {
          console.info('[PhotoAlbum] Got next object:', photoAsset ? 'valid' : 'null')
        }
      }

      fetchResult.close()

      // 处理逻辑
      this.scanStatus.lastScanTime = Date.now()
      this.scanStatus.lastScanCount = photos.length
      this.scanStatus.isScanning = false

      console.info(`[PhotoAlbum] === SCAN COMPLETE ===`)
      console.info(`[PhotoAlbum] Processed ${processedCount} photos, found ${photos.length} within ${days} days`)
      return photos
    } catch (error) {
      console.error('[PhotoAlbum] === SCAN FAILED ===')
      console.error('[PhotoAlbum] Error:', JSON.stringify(error))
      this.scanStatus.isScanning = false
      return []
    }
  }

  /**
   * base64
   */
  private async photoToBase64(uri: string): Promise<string | null> {
    try {
      if (!this.phAccessHelper) {
        return null
      }

      // 处理逻辑
      const file = await fs.open(uri, fs.OpenMode.READ_ONLY)
      
      // 处理逻辑
      const buffer = new ArrayBuffer(1024 * 1024) // 1MB buffer
      const readLen = await fs.read(file.fd, buffer)
      
      // 处理逻辑
      fs.close(file)

      // base64
      const uint8Array = new Uint8Array(buffer, 0, readLen)
      const base64 = this.arrayBufferToBase64(uint8Array)
      
      return base64
    } catch (error) {
      console.error('Failed to convert photo to base64:', error)
      return null
    }
  }

  /**
   * ArrayBufferbase64
   */
  private arrayBufferToBase64(buffer: Uint8Array): string {
    let binary = ''
    const len = buffer.byteLength
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(buffer[i])
    }
    // btoa is deprecated, use TextEncoder or other methods
    // For now, we'll use a simple implementation
    const base64Chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    let result = ''
    let i = 0
    while (i < binary.length) {
      const a = binary.charCodeAt(i++)
      const b = binary.charCodeAt(i++)
      const c = binary.charCodeAt(i++)
      
      const index1 = a >> 2
      const index2 = ((a & 3) << 4) | (b >> 4)
      const index3 = isNaN(b) ? 64 : ((b & 15) << 2) | (c >> 6)
      const index4 = isNaN(c) ? 64 : (c & 63)
      
      result += base64Chars.charAt(index1) + base64Chars.charAt(index2) +
                (isNaN(b) ? '==' : (isNaN(c) ? '=' : base64Chars.charAt(index3) + base64Chars.charAt(index4)))
    }
    return result
  }

  /**
 * 服务类
 */
  async syncPhotosToBackend(
    photos: PhotoMetadata[],
    includeBase64: boolean = false
  ): Promise<boolean> {
    if (photos.length === 0) {
      console.info('[PhotoAlbum] No photos to sync')
      return true
    }

    console.info(`[PhotoAlbum] Starting sync of ${photos.length} photos (includeBase64: ${includeBase64})`)

    try {
      // base64
      if (includeBase64) {
        for (const photo of photos) {
          photo.base64 = await this.photoToBase64(photo.uri) || undefined
        }
      }

      // 10
      const batchSize = 10
      let successCount = 0
      let failCount = 0
      
      for (let i = 0; i < photos.length; i += batchSize) {
        const batch = photos.slice(i, i + batchSize)
        const success = await this.uploadPhotoBatch(batch)
        if (success) {
          successCount += batch.length
        } else {
          failCount += batch.length
        }
      }

      console.info(`[PhotoAlbum] Sync complete: ${successCount} success, ${failCount} failed`)
      return failCount === 0
    } catch (error) {
      console.error('[PhotoAlbum] Failed to sync photos:', JSON.stringify(error))
      return false
    }
  }

  /**
 * 服务类
 */
  private async uploadPhotoBatch(photos: PhotoMetadata[]): Promise<boolean> {
    try {
      console.info(`[PhotoAlbum] Uploading batch of ${photos.length} photos...`)
      
      const httpRequest = http.createHttp()
      
      // 处理逻辑
      const response = await httpRequest.request(
        `${ApiConfig.getBaseUrl()}/api/v4/photos/sync`,
        {
          method: http.RequestMethod.POST,
          header: {
            'Content-Type': 'application/json'
          },
          extraData: JSON.stringify({
            user_id: this.userId,
            photos: photos.map((p: PhotoMetadata): PhotoSyncData => ({
              uri: p.uri,
              display_name: p.displayName,
              timestamp: p.timestamp,
              location: p.location,
              base64: p.base64
            }))
          } as PhotoSyncRequest),
          connectTimeout: 5000,  // 5
          readTimeout: 10000     // 10
        }
      )

      httpRequest.destroy()

      if (response.responseCode === 200) {
        console.info(`[PhotoAlbum] Successfully uploaded ${photos.length} photos`)
        return true
      } else {
        console.error(`[PhotoAlbum] Upload failed with code: ${response.responseCode}`)
        return false
      }
    } catch (error) {
      console.error('[PhotoAlbum] Failed to upload photo batch:', JSON.stringify(error))
      // 处理逻辑
      return false
    }
  }

  /**
 * 服务类
 */
  async scanAndSync(userId: string, days: number = 7): Promise<ScanResult> {
    const photos = await this.scanRecentPhotos(userId, days)
    const synced = await this.syncPhotosToBackend(photos, false) // base64

    this.scanStatus.lastSyncSuccess = synced

    const syncResult: ScanResult = {
      scanned: photos.length,
      synced
    }
    return syncResult
  }

  /**
 * 服务类
 */
  async scanAndSyncWithThumbnails(userId: string, days: number = 7): Promise<ScanResult> {
    const photos = await this.scanRecentPhotos(userId, days)
    
    // 处理逻辑
    const recentPhotos = photos.slice(0, 20)
    const synced = await this.syncPhotosToBackend(recentPhotos, true)

    this.scanStatus.lastSyncSuccess = synced

    const syncResult: ScanResult = {
      scanned: photos.length,
      synced
    }
    return syncResult
  }

  /**
 * 服务类
 */
  getScanStatus(): ScanStatus {
    return this.scanStatus
  }
  
  /**
 * 服务类
 */
  startAutoScan(userId: string, intervalHours: number = 24) {
    if (this.scanStatus.autoScanEnabled) {
      console.info('Auto scan already enabled')
      return
    }
    
    this.userId = userId
    this.autoScanInterval = intervalHours * 60 * 60 * 1000
    this.scanStatus.autoScanEnabled = true
    
    // 处理逻辑
    this.scanAndSync(userId, 7)
    
    // 处理逻辑
    this.autoScanTimer = setInterval(() => {
      this.scanAndSync(userId, 7)
    }, this.autoScanInterval)
    
    this.scanStatus.nextScanTime = Date.now() + this.autoScanInterval
    
    console.info(`Auto scan started, interval: ${intervalHours} hours`)
  }
  
  /**
 * 服务类
 */
  stopAutoScan() {
    if (this.autoScanTimer !== -1) {
      clearInterval(this.autoScanTimer)
      this.autoScanTimer = -1
    }
    
    this.scanStatus.autoScanEnabled = false
    this.scanStatus.nextScanTime = 0
    
    console.info('Auto scan stopped')
  }
  
  /**
 * 服务类
 */
  async smartSync(userId: string): Promise<SmartSyncResult> {
    const photos = await this.scanRecentPhotos(userId, 7)
    
    // 处理逻辑
    const newPhotos = photos.filter((p: PhotoMetadata) => p.timestamp > this.scanStatus.lastScanTime)
    
    if (newPhotos.length === 0) {
      console.info('No new photos to sync')
      const noNewPhotosResult: SmartSyncResult = {
        scanned: photos.length,
        newPhotos: 0,
        synced: true
      }
      return noNewPhotosResult
    }
    
    // 处理逻辑
    const synced = await this.syncPhotosToBackend(newPhotos, false)
    
    this.scanStatus.lastSyncSuccess = synced
    
    const smartSyncResult: SmartSyncResult = {
      scanned: photos.length,
      newPhotos: newPhotos.length,
      synced
    }
    return smartSyncResult
  }
}

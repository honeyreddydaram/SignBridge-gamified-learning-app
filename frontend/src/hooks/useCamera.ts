import { useCallback, useEffect, useRef, useState } from 'react'

export type CameraPermissionState = 'idle' | 'requesting' | 'granted' | 'denied' | 'unavailable'

/**
 * Owns getUserMedia lifecycle + frame capture. Kept separate from prediction
 * logic (useStablePrediction) so both the standalone Recognition page and
 * Learning-module camera challenges can share it without duplicating camera
 * permission/error handling.
 */
export function useCamera() {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [permission, setPermission] = useState<CameraPermissionState>('idle')
  const [error, setError] = useState<string | null>(null)

  const start = useCallback(async () => {
    setError(null)
    if (!navigator.mediaDevices?.getUserMedia) {
      setPermission('unavailable')
      setError('This browser does not support camera access.')
      return
    }
    setPermission('requesting')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }
      setPermission('granted')
    } catch (err) {
      setPermission('denied')
      if (err instanceof DOMException && err.name === 'NotAllowedError') {
        setError('Camera permission was denied. Allow camera access in your browser settings to continue.')
      } else if (err instanceof DOMException && err.name === 'NotFoundError') {
        setError('No camera was found on this device.')
      } else {
        setError('Could not access the camera.')
      }
    }
  }, [])

  const stop = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
    setPermission('idle')
  }, [])

  useEffect(() => stop, [stop])

  const captureFrameBase64 = useCallback((): string | null => {
    const video = videoRef.current
    if (!video || video.readyState < 2) return null

    if (!canvasRef.current) canvasRef.current = document.createElement('canvas')
    const canvas = canvasRef.current
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return null
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    return canvas.toDataURL('image/jpeg', 0.8)
  }, [])

  return { videoRef, permission, error, start, stop, captureFrameBase64 }
}

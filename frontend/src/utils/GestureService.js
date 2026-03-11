/**
 * GestureService - Hand gesture recognition service
 * Real-time gesture detection using MediaPipe Gesture Recognizer
 * 
 * Supported gestures:
 * - Closed_Fist: Fist (pan/grab)
 * - Open_Palm: Open palm (reset/select)
 * - Pointing_Up: Pointing up (select)
 * - Thumb_Down: Thumb down (zoom out)
 * - Thumb_Up: Thumb up (zoom in)
 * - Victory: V sign (rotate mode)
 * - ILoveYou: I love you gesture
 */

import { FilesetResolver, GestureRecognizer } from '@mediapipe/tasks-vision';

// Gesture types
export const GestureType = {
  NONE: 'None',
  CLOSED_FIST: 'Closed_Fist',
  OPEN_PALM: 'Open_Palm',
  POINTING_UP: 'Pointing_Up',
  THUMB_DOWN: 'Thumb_Down',
  THUMB_UP: 'Thumb_Up',
  VICTORY: 'Victory',
  ILOVEYOU: 'ILoveYou',
};

// Gesture action types
export const GestureAction = {
  NONE: 'none',
  ZOOM_IN: 'zoom_in',
  ZOOM_OUT: 'zoom_out',
  PAN: 'pan',
  RESET: 'reset',
  SELECT: 'select',
  ROTATE: 'rotate',
  PINCH: 'pinch',
};

class GestureService {
  constructor() {
    this.gestureRecognizer = null;
    this.videoElement = null;
    this.isInitialized = false;
    this.isRunning = false;
    this.animationFrameId = null;
    this.lastVideoTime = -1;
    
    // Callbacks
    this.onGestureCallback = null;
    this.onHandPositionCallback = null;
    this.onTwoHandsCallback = null;
    this.onStatusChangeCallback = null;
    
    // State tracking
    this.currentGesture = GestureType.NONE;
    this.lastGesture = GestureType.NONE;
    this.gestureStartTime = 0;
    this.gestureHoldTime = 0;
    
    // Two hands tracking (for pinch zoom)
    this.previousHandDistance = null;
    this.previousHandCenter = null;
    
    // Hand positions
    this.handPositions = {
      left: null,
      right: null,
    };
    
    // Smoothing
    this.smoothingFactor = 0.3;
    this.smoothedPosition = null;
  }

  /**
   * Initialize gesture recognizer
   */
  async initialize() {
    if (this.isInitialized) return true;
    
    try {
      this.notifyStatus('loading', 'Loading gesture recognition model...');
      
      // Create Vision FilesetResolver
      const vision = await FilesetResolver.forVisionTasks(
        'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
      );
      
      // Create GestureRecognizer
      this.gestureRecognizer = await GestureRecognizer.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath: 'https://storage.googleapis.com/mediapipe-tasks/gesture_recognizer/gesture_recognizer.task',
          delegate: 'GPU',
        },
        runningMode: 'VIDEO',
        numHands: 2,
        minHandDetectionConfidence: 0.5,
        minHandPresenceConfidence: 0.5,
        minTrackingConfidence: 0.5,
      });
      
      this.isInitialized = true;
      this.notifyStatus('ready', 'Gesture recognition ready');
      return true;
    } catch (error) {
      console.error('Failed to initialize GestureRecognizer:', error);
      this.notifyStatus('error', `Failed to load: ${error.message}`);
      return false;
    }
  }

  /**
   * Start camera and gesture recognition
   */
  async start(videoElement) {
    if (!this.isInitialized) {
      const success = await this.initialize();
      if (!success) return false;
    }
    
    if (this.isRunning) return true;
    
    try {
      this.videoElement = videoElement;
      
      // Get camera stream
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user',
        },
      });
      
      videoElement.srcObject = stream;
      await videoElement.play();
      
      this.isRunning = true;
      this.lastVideoTime = -1;
      
      // Start detection loop
      this.detectLoop();
      
      this.notifyStatus('running', 'Gesture control active');
      return true;
    } catch (error) {
      console.error('Failed to start camera:', error);
      this.notifyStatus('error', `Camera error: ${error.message}`);
      return false;
    }
  }

  /**
   * Stop gesture recognition
   */
  stop() {
    this.isRunning = false;
    
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    
    if (this.videoElement && this.videoElement.srcObject) {
      const tracks = this.videoElement.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      this.videoElement.srcObject = null;
    }
    
    this.currentGesture = GestureType.NONE;
    this.lastGesture = GestureType.NONE;
    this.previousHandDistance = null;
    this.previousHandCenter = null;
    this.handPositions = { left: null, right: null };
    
    this.notifyStatus('stopped', 'Gesture control stopped');
  }

  /**
   * Detection loop
   */
  detectLoop() {
    if (!this.isRunning || !this.videoElement || !this.gestureRecognizer) {
      return;
    }
    
    const video = this.videoElement;
    
    // Process only when video frame updates
    if (video.currentTime !== this.lastVideoTime) {
      this.lastVideoTime = video.currentTime;
      
      try {
        const results = this.gestureRecognizer.recognizeForVideo(video, performance.now());
        this.processResults(results);
      } catch (error) {
        console.error('Gesture recognition error:', error);
      }
    }
    
    this.animationFrameId = requestAnimationFrame(() => this.detectLoop());
  }

  /**
   * Process recognition results
   */
  processResults(results) {
    const { gestures, landmarks, handedness } = results;
    
    // Reset hand positions
    this.handPositions = { left: null, right: null };
    
    // No hand detected
    if (!gestures || gestures.length === 0) {
      this.currentGesture = GestureType.NONE;
      this.previousHandDistance = null;
      this.previousHandCenter = null;
      
      if (this.onGestureCallback) {
        this.onGestureCallback({
          gesture: GestureType.NONE,
          action: GestureAction.NONE,
          holdTime: 0,
        });
      }
      return;
    }
    
    // Process each hand
    for (let i = 0; i < gestures.length; i++) {
      const gesture = gestures[i][0]; // Get highest confidence gesture
      const handLandmarks = landmarks[i];
      const hand = handedness[i][0];
      
      if (!gesture || !handLandmarks || !hand) continue;
      
      // Get palm center position (using wrist and middle finger base)
      const wrist = handLandmarks[0];
      const middleMcp = handLandmarks[9];
      const palmCenter = {
        x: (wrist.x + middleMcp.x) / 2,
        y: (wrist.y + middleMcp.y) / 2,
        z: (wrist.z + middleMcp.z) / 2,
      };
      
      // Apply smoothing
      if (!this.smoothedPosition) {
        this.smoothedPosition = { ...palmCenter };
      } else {
        this.smoothedPosition.x += (palmCenter.x - this.smoothedPosition.x) * this.smoothingFactor;
        this.smoothedPosition.y += (palmCenter.y - this.smoothedPosition.y) * this.smoothingFactor;
        this.smoothedPosition.z += (palmCenter.z - this.smoothedPosition.z) * this.smoothingFactor;
      }
      
      // Record hand position
      const handLabel = hand.categoryName.toLowerCase(); // 'left' or 'right'
      this.handPositions[handLabel] = {
        landmarks: handLandmarks,
        center: { ...this.smoothedPosition },
        gesture: gesture.categoryName,
      };
    }
    
    // Two hands gesture handling
    if (this.handPositions.left && this.handPositions.right) {
      this.handleTwoHands();
      return;
    }
    
    // Single hand gesture handling
    const activeHand = this.handPositions.left || this.handPositions.right;
    if (activeHand) {
      this.handleSingleHand(activeHand);
      
      // Call position callback
      if (this.onHandPositionCallback) {
        this.onHandPositionCallback(activeHand.center, activeHand.landmarks);
      }
    }
  }

  /**
   * Handle single hand gesture
   */
  handleSingleHand(handData) {
    const gestureName = handData.gesture;
    const now = Date.now();
    
    // Gesture change
    if (gestureName !== this.lastGesture) {
      this.lastGesture = gestureName;
      this.gestureStartTime = now;
      this.gestureHoldTime = 0;
    } else {
      this.gestureHoldTime = now - this.gestureStartTime;
    }
    
    this.currentGesture = gestureName;
    
    // Map gesture to action
    const action = this.gestureToAction(gestureName, this.gestureHoldTime);
    
    if (this.onGestureCallback) {
      this.onGestureCallback({
        gesture: gestureName,
        action,
        holdTime: this.gestureHoldTime,
        position: handData.center,
      });
    }
  }

  /**
   * Handle two hands gesture (zoom)
   */
  handleTwoHands() {
    const left = this.handPositions.left;
    const right = this.handPositions.right;
    
    if (!left || !right) return;
    
    // Calculate distance between hands
    const dx = right.center.x - left.center.x;
    const dy = right.center.y - left.center.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    // Calculate center point
    const centerX = (left.center.x + right.center.x) / 2;
    const centerY = (left.center.y + right.center.y) / 2;
    const center = { x: centerX, y: centerY };
    
    // Calculate zoom and pan
    let pinchScale = 0;
    let panDelta = { x: 0, y: 0 };
    
    if (this.previousHandDistance !== null && this.previousHandCenter !== null) {
      // Zoom - based on distance change
      const distanceDelta = distance - this.previousHandDistance;
      pinchScale = distanceDelta * 5; // Scale factor
      
      // Pan - based on center point movement
      panDelta = {
        x: (centerX - this.previousHandCenter.x) * 500, // Convert to pixels
        y: (centerY - this.previousHandCenter.y) * 500,
      };
    }
    
    // Update state
    this.previousHandDistance = distance;
    this.previousHandCenter = center;
    this.currentGesture = 'PINCH';
    
    // Call callbacks
    if (this.onTwoHandsCallback) {
      this.onTwoHandsCallback({
        pinchScale,
        panDelta,
        distance,
        center,
        leftGesture: left.gesture,
        rightGesture: right.gesture,
      });
    }
    
    if (this.onGestureCallback) {
      this.onGestureCallback({
        gesture: 'PINCH',
        action: pinchScale > 0.01 ? GestureAction.ZOOM_IN : 
                pinchScale < -0.01 ? GestureAction.ZOOM_OUT : 
                GestureAction.PAN,
        holdTime: 0,
        pinchScale,
        panDelta,
      });
    }
  }

  /**
   * Map gesture to action
   */
  gestureToAction(gesture, holdTime) {
    // Long press threshold (500ms)
    const isLongPress = holdTime > 500;
    
    switch (gesture) {
      case GestureType.THUMB_UP:
        return GestureAction.ZOOM_IN;
      
      case GestureType.THUMB_DOWN:
        return GestureAction.ZOOM_OUT;
      
      case GestureType.CLOSED_FIST:
        return GestureAction.PAN;
      
      case GestureType.OPEN_PALM:
        return isLongPress ? GestureAction.RESET : GestureAction.SELECT;
      
      case GestureType.POINTING_UP:
        return GestureAction.SELECT;
      
      case GestureType.VICTORY:
        return GestureAction.ROTATE;
      
      default:
        return GestureAction.NONE;
    }
  }

  /**
   * Set callbacks
   */
  onGesture(callback) {
    this.onGestureCallback = callback;
  }

  onHandPosition(callback) {
    this.onHandPositionCallback = callback;
  }

  onTwoHands(callback) {
    this.onTwoHandsCallback = callback;
  }

  onStatusChange(callback) {
    this.onStatusChangeCallback = callback;
  }

  /**
   * Notify status change
   */
  notifyStatus(status, message) {
    if (this.onStatusChangeCallback) {
      this.onStatusChangeCallback({ status, message });
    }
  }

  /**
   * Get current status
   */
  getStatus() {
    return {
      isInitialized: this.isInitialized,
      isRunning: this.isRunning,
      currentGesture: this.currentGesture,
    };
  }

  /**
   * Destroy
   */
  destroy() {
    this.stop();
    this.gestureRecognizer = null;
    this.isInitialized = false;
  }
}

// Export singleton
export const gestureService = new GestureService();
export default gestureService;
export class LipSyncController {
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private dataArray: Uint8Array | null = null;
  private audioBuffer: AudioBuffer | null = null;
  private phonemeMap: Map<number, number> = new Map();
  private isAnalyzing: boolean = false;
  private lastUpdateTime: number = 0;
  private smoothingFactor: number = 0.8; // 平滑系数
  private lastMouthValue: number = 0;
  private isDestroyed: boolean = false;  // 添加销毁标记
  
  constructor() {
    if (typeof window !== 'undefined' && window.AudioContext) {
      this.audioContext = new AudioContext();
    }
  }

  /**
   * Analyze audio and prepare lip sync data
   */
  async analyzeAudio(audioUrl: string | ArrayBuffer): Promise<void> {
    if (this.checkDestroyed()) return;

    this.isAnalyzing = true;
    try {
      let audioData: ArrayBuffer;
      
      if (typeof audioUrl === 'string') {
        const response = await fetch(audioUrl);
        if (!response.ok) {
          throw new Error(`Failed to fetch audio: ${response.status}`);
        }
        audioData = await response.arrayBuffer();
      } else {
        audioData = audioUrl;
      }

      if (audioData.byteLength === 0) {
        throw new Error('Empty audio data');
      }

      this.audioBuffer = await this.audioContext.decodeAudioData(audioData);
      this.generatePhonemeMap();
      console.log(`Lip sync analysis completed: ${this.phonemeMap.size} phonemes mapped`);
    } catch (error) {
      console.error('Error analyzing audio:', error);
      // 生成默认的口型映射作为回退
      this.generateFallbackPhonemeMap();
    } finally {
      this.isAnalyzing = false;
    }
  }

  /**
   * Generate a simple phoneme map based on audio amplitude
   * In production, this would use more sophisticated speech analysis
   */
  private generatePhonemeMap(): void {
    if (!this.audioBuffer || !this.audioContext) return;

    const sampleRate = this.audioBuffer.sampleRate;
    const channelData = this.audioBuffer.getChannelData(0);
    const windowSize = Math.floor(sampleRate * 0.01); // 10ms windows for better precision
    const hopSize = Math.floor(windowSize * 0.5); // 50% overlap
    
    this.phonemeMap.clear();
    
    for (let i = 0; i < channelData.length; i += hopSize) {
      let sum = 0;
      let peak = 0;
      for (let j = 0; j < windowSize && i + j < channelData.length; j++) {
        const sample = Math.abs(channelData[i + j]);
        sum += sample;
        peak = Math.max(peak, sample);
      }
      const amplitude = sum / windowSize;
      const time = i / sampleRate;
      
      // 改进的口型映射算法
      // 结合平均振幅和峰值，增加对语音特征的敏感度
      const normalizedAmplitude = Math.min(amplitude * 8, 1);
      const normalizedPeak = Math.min(peak * 4, 1);
      const mouthShape = Math.min((normalizedAmplitude * 0.7 + normalizedPeak * 0.3), 1);
      
      this.phonemeMap.set(Math.floor(time * 1000), mouthShape);
    }
  }

  /**
   * Generate fallback phoneme map when analysis fails
   */
  private generateFallbackPhonemeMap(): void {
    this.phonemeMap.clear();
    // 生成一个简单的默认动画模式
    for (let i = 0; i < 5000; i += 100) { // 5秒的默认动画
      const t = i / 1000;
      const mouthShape = (Math.sin(t * 4) + 1) * 0.3; // 简单的正弦波动画
      this.phonemeMap.set(i, mouthShape);
    }
  }

  /**
   * Get mouth shape for a given time
   */
  getMouthShape(currentTime: number): number {
    if (this.checkDestroyed()) return 0;
    
    const timeMs = Math.floor(currentTime * 1000);
    
    // 使用线性插值来平滑口型变化
    const currentValue = this.phonemeMap.get(timeMs) || 0;
    const nextTimeMs = timeMs + 10;
    const nextValue = this.phonemeMap.get(nextTimeMs) || currentValue;
    
    // 时间内插值
    const fraction = (currentTime * 1000 - timeMs) / 10;
    const interpolatedValue = currentValue + (nextValue - currentValue) * fraction;
    
    // 应用平滑滤波
    const now = performance.now();
    if (now - this.lastUpdateTime > 16) { // 限制更新频率到60FPS
      this.lastMouthValue = this.lastMouthValue * this.smoothingFactor + 
                           interpolatedValue * (1 - this.smoothingFactor);
      this.lastUpdateTime = now;
    }
     
    return Math.max(0, Math.min(1, this.lastMouthValue));
  }

  /**
   * Real-time audio analysis for live speech
   */
  async connectToAudioElement(audioElement: HTMLAudioElement): Promise<void> {
    if (!this.audioContext) return;

    try {
      const source = this.audioContext.createMediaElementSource(audioElement);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      
      source.connect(this.analyser);
      this.analyser.connect(this.audioContext.destination);
      
      this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
    } catch (error) {
      console.error('Error connecting to audio element:', error);
    }
  }

  /**
   * Get real-time mouth shape from live audio
   */
  getRealTimeMouthShape(): number {
    if (this.checkDestroyed() || !this.analyser || !this.dataArray) return 0;

    this.analyser.getByteFrequencyData(this.dataArray);
    
    // Calculate average amplitude in speech frequency range (100-1000 Hz)
    const speechRange = this.dataArray.slice(2, 20);
    const average = speechRange.reduce((a, b) => a + b, 0) / speechRange.length;
    
    // Normalize to 0-1 range
    return Math.min(average / 128, 1);
  }

  /**
   * Cleanup resources
   */
  dispose(): void {
    if (this.audioContext) {
      this.audioContext.close();
    }
    this.phonemeMap.clear();
  }

  /**
   * 销毁控制器，清理所有资源
   */
  destroy(): void {
    this.isDestroyed = true;
    
    // 清理音频上下文
    if (this.audioContext && this.audioContext.state !== 'closed') {
      try {
        this.audioContext.close();
      } catch (error) {
        console.warn('Audio context cleanup failed:', error);
      }
      this.audioContext = null;
    }
    
    // 清理分析器
    this.analyser = null;
    this.dataArray = null;
    
    // 清理映射数据
    this.phonemeMap.clear();
    
    console.log('🧹 LipSyncController resources cleaned up');
  }

  /**
   * 检查控制器是否已被销毁
   */
  private checkDestroyed(): boolean {
    if (this.isDestroyed) {
      console.warn('⚠️ LipSyncController已被销毁，操作被忽略');
      return true;
    }
    return false;
  }
} 
import React, { useState, useRef, useCallback } from 'react';
import { Mic, MicOff, Send, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { logger } from '@/utils/logger';

interface ControlBarProps {
  onSendMessage: (message: string) => void;
  onAudioData: (audioBlob: Blob) => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export const ControlBar: React.FC<ControlBarProps> = ({
  onSendMessage,
  onAudioData,
  isLoading = false,
  disabled = false,
  placeholder = "Type your message or use voice...",
  className = '',
}) => {
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Start recording
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        onAudioData(audioBlob);
        
        // Clean up
        stream.getTracks().forEach(track => track.stop());
        audioChunksRef.current = [];
        logger.info('Audio recording completed', { size: audioBlob.size });
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

      logger.info('Started audio recording');
    } catch (error) {
      logger.error('Failed to start recording', error as Error);
      alert('Failed to access microphone. Please check your permissions.');
    }
  }, [onAudioData]);

  // Stop recording
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      
      setRecordingTime(0);
      logger.info('Stopped audio recording');
    }
  }, [isRecording]);

  // Handle text message submit
  const handleSubmit = useCallback((e?: React.FormEvent) => {
    e?.preventDefault();
    
    if (message.trim() && !disabled && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
      logger.info('Sent text message', { length: message.length });
    }
  }, [message, disabled, isLoading, onSendMessage]);

  // Format recording time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className={`flex items-center gap-2 p-4 bg-white dark:bg-gray-800 border-t ${className}`}>
      {/* Audio recording button */}
      <Button
        type="button"
        variant={isRecording ? 'destructive' : 'outline'}
        size="icon"
        onClick={isRecording ? stopRecording : startRecording}
        disabled={disabled || isLoading}
        className="flex-shrink-0"
      >
        {isRecording ? (
          <MicOff className="w-4 h-4" />
        ) : (
          <Mic className="w-4 h-4" />
        )}
      </Button>

      {/* Recording indicator */}
      {isRecording && (
        <div className="flex items-center gap-2 text-red-500">
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
          <span className="text-sm font-medium">{formatTime(recordingTime)}</span>
        </div>
      )}

      {/* Text input form */}
      <form onSubmit={handleSubmit} className="flex-1 flex gap-2">
        <Input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={placeholder}
          disabled={disabled || isLoading || isRecording}
          className="flex-1"
        />
        
        {/* Send button */}
        <Button
          type="submit"
          disabled={!message.trim() || disabled || isLoading || isRecording}
          className="flex-shrink-0"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Sending...
            </>
          ) : (
            <>
              <Send className="w-4 h-4 mr-2" />
              Send
            </>
          )}
        </Button>
      </form>
    </div>
  );
};

export default React.memo(ControlBar); 
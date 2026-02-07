import React, { useState, useRef } from 'react';
import { Mic, Square, Loader2 } from 'lucide-react';
import { GoogleGenerativeAI } from '@google/generative-ai';

interface VoiceInputProps {
    onTranscriptionComplete: (text: string) => void;
}

const VoiceInput: React.FC<VoiceInputProps> = ({ onTranscriptionComplete }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const animationFrameRef = useRef<number | null>(null);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);

    const cleanupAudio = () => {
        if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
            silenceTimerRef.current = null;
        }
        if (animationFrameRef.current) {
            cancelAnimationFrame(animationFrameRef.current);
            animationFrameRef.current = null;
        }
        if (audioContextRef.current) {
            audioContextRef.current.close();
            audioContextRef.current = null;
        }
        analyserRef.current = null;
    };

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            chunksRef.current = [];

            // Set up Web Audio API for silence detection
            const audioContext = new AudioContext();
            const source = audioContext.createMediaStreamSource(stream);
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 2048; // Increase buffer size for better resolution
            source.connect(analyser);
            
            audioContextRef.current = audioContext;
            analyserRef.current = analyser;

            const bufferLength = analyser.fftSize;
            const dataArray = new Uint8Array(bufferLength);
            const frequencyData = new Uint8Array(analyser.frequencyBinCount);
            
            const checkSilence = () => {
                if (!analyserRef.current) return;
                
                analyserRef.current.getByteTimeDomainData(dataArray);
                analyserRef.current.getByteFrequencyData(frequencyData);
                
                // Draw frequency visualization
                if (canvasRef.current) {
                    const canvas = canvasRef.current;
                    const ctx = canvas.getContext('2d');
                    if (ctx) {
                        const width = canvas.width;
                        const height = canvas.height;
                        ctx.clearRect(0, 0, width, height);
                        
                        // Only use the first 32 frequency bins for a cleaner look
                        const visualBins = 32;
                        const barWidth = width / visualBins;
                        let barHeight;
                        let x = 0;

                        for (let i = 0; i < visualBins; i++) {
                            // Scale frequency data for better visibility
                            barHeight = (frequencyData[i] / 255) * height;
                            
                            ctx.fillStyle = `hsla(${200 + (i * 2)}, 70%, 60%, 0.8)`;
                            ctx.fillRect(x, height - barHeight, barWidth - 1, barHeight);

                            x += barWidth;
                        }
                    }
                }

                // Calculate RMS (Root Mean Square) for silence detection
                let sum = 0;
                for (let i = 0; i < bufferLength; i++) {
                    const amplitude = (dataArray[i] - 128) / 128; // Normalize to -1..1
                    sum += amplitude * amplitude;
                }
                const rms = Math.sqrt(sum / bufferLength);

                // Threshold for "silence" - RMS is usually very small for silence
                // 0.01 is roughly -40dB, 0.02 is roughly -34dB
                if (rms < 0.02) {
                    if (!silenceTimerRef.current) {
                        silenceTimerRef.current = setTimeout(() => {
                            stopRecording();
                        }, 1000); // Stop after 1 second of silence
                    }
                } else {
                    if (silenceTimerRef.current) {
                        clearTimeout(silenceTimerRef.current);
                        silenceTimerRef.current = null;
                    }
                }

                animationFrameRef.current = requestAnimationFrame(checkSilence);
            };

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunksRef.current.push(e.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
                await transcribeAudio(audioBlob);

                // Stop all tracks to release microphone
                stream.getTracks().forEach(track => track.stop());
                cleanupAudio();
            };

            mediaRecorder.start();
            setIsRecording(true);
            animationFrameRef.current = requestAnimationFrame(checkSilence);
        } catch (error) {
            console.error('Error accessing microphone:', error);
            alert('Could not access microphone. Please ensure permissions are granted.');
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
            setIsProcessing(true);
        }
    };

    const transcribeAudio = async (audioBlob: Blob) => {
        try {
            const apiKey = import.meta.env.VITE_GEMINI_API_KEY;
            const modelName = import.meta.env.VITE_GEMINI_MODEL_NAME || 'gemini-2.0-flash-exp';

            if (!apiKey) {
                throw new Error('Gemini API Key not configured');
            }

            const genAI = new GoogleGenerativeAI(apiKey);
            const model = genAI.getGenerativeModel({ model: modelName });

            // Convert Blob to Base64
            const reader = new FileReader();
            reader.readAsDataURL(audioBlob);
            reader.onloadend = async () => {
                const base64Audio = (reader.result as string).split(',')[1];

                const result = await model.generateContent([
                    {
                        inlineData: {
                            mimeType: 'audio/webm',
                            data: base64Audio
                        }
                    },
                    { text: "Transcribe this audio exactly as spoken. Do not add any commentary or prefixes. Just return the text." }
                ]);

                const text = result.response.text();
                if (text) {
                    onTranscriptionComplete(text.trim());
                }
                setIsProcessing(false);
            };
        } catch (error) {
            console.error('Transcription error:', error);
            setIsProcessing(false);
        }
    };

    return (
        <div className="flex items-center gap-3">
            {isRecording && (
                <div className="flex items-center bg-zinc-900/50 rounded-full px-3 py-1 border border-zinc-800">
                    <canvas 
                        ref={canvasRef} 
                        width={60} 
                        height={20} 
                        className="w-[60px] h-[20px]"
                    />
                </div>
            )}
            {isProcessing ? (
                <div className="p-2 text-indigo-400 animate-pulse bg-indigo-500/10 rounded-full">
                    <Loader2 className="w-5 h-5 animate-spin" />
                </div>
            ) : isRecording ? (
                <button
                    onClick={stopRecording}
                    className="p-2 text-white bg-red-500/20 hover:bg-red-500/30 rounded-full transition-colors animate-pulse"
                    title="Stop Recording"
                >
                    <Square className="w-5 h-5 text-red-400 fill-current" />
                </button>
            ) : (
                <button
                    onClick={startRecording}
                    className="p-2 text-white/40 hover:text-indigo-400 hover:bg-indigo-500/10 rounded-full transition-colors"
                    title="Start Voice Input"
                >
                    <Mic className="w-5 h-5" />
                </button>
            )}
        </div>
    );
};

export default VoiceInput;

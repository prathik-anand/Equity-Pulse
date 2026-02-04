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

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            chunksRef.current = [];

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
            };

            mediaRecorder.start();
            setIsRecording(true);
        } catch (error) {
            console.error('Error accessing microphone:', error);
            alert('Could not access microphone. Please ensure permissions are granted.');
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
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
        <div className="flex items-center">
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

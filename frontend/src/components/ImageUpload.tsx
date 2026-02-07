import React, { useState, useRef, useImperativeHandle, forwardRef, useCallback } from 'react';
import { ImagePlus, X, Loader2 } from 'lucide-react';
import { supabase, STORAGE_BUCKET } from '../lib/supabase';

interface ImageUploadProps {
    onImagesChange: (urls: string[]) => void;
    maxImages?: number;
}

export interface ImageUploadRef {
    addFiles: (files: File[]) => Promise<void>;
    clearAll: () => void;
    hasImages: () => boolean;
}

interface ImageState {
    file: File;
    preview: string;
    url?: string;
}

export const ImageUpload = forwardRef<ImageUploadRef, ImageUploadProps>(({
    onImagesChange,
    maxImages = 5
}, ref) => {
    const [images, setImages] = useState<ImageState[]>([]);
    const [isUploading, setIsUploading] = useState(false);
    const [previewImage, setPreviewImage] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const uploadFiles = useCallback(async (files: File[]) => {
        if (files.length === 0) return;

        const remainingSlots = maxImages - images.length;
        const filesToProcess = files.slice(0, remainingSlots);

        if (!supabase) {
            console.error('Supabase not configured');
            return;
        }

        setIsUploading(true);

        const newImages: ImageState[] = [];

        for (const file of filesToProcess) {
            if (file.size > 5 * 1024 * 1024) {
                console.warn(`File ${file.name} exceeds 5MB limit`);
                continue;
            }

            const preview = URL.createObjectURL(file);
            const fileName = `${Date.now()}-${file.name || 'pasted-image.png'}`;
            const { data, error } = await supabase.storage
                .from(STORAGE_BUCKET)
                .upload(fileName, file, {
                    cacheControl: '3600',
                    upsert: false
                });

            if (error) {
                console.error('Upload error:', error);
                URL.revokeObjectURL(preview);
                continue;
            }

            const { data: urlData } = supabase.storage
                .from(STORAGE_BUCKET)
                .getPublicUrl(data.path);

            newImages.push({
                file,
                preview,
                url: urlData.publicUrl
            });
        }

        setImages(prev => {
            const updated = [...prev, ...newImages];
            onImagesChange(updated.map(img => img.url!).filter(Boolean));
            return updated;
        });
        setIsUploading(false);
    }, [images.length, maxImages, onImagesChange]);

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || []);
        await uploadFiles(files);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const removeImage = (index: number) => {
        setImages(prev => {
            const updated = prev.filter((_, i) => i !== index);
            onImagesChange(updated.map(img => img.url!).filter(Boolean));
            return updated;
        });
    };

    const clearAll = useCallback(() => {
        images.forEach(img => URL.revokeObjectURL(img.preview));
        setImages([]);
        onImagesChange([]);
    }, [images, onImagesChange]);

    useImperativeHandle(ref, () => ({
        addFiles: uploadFiles,
        clearAll,
        hasImages: () => images.length > 0
    }), [uploadFiles, clearAll, images.length]);

    if (!supabase) {
        return null;
    }

    return (
        <>
            {/* Lightbox Modal */}
            {previewImage && (
                <div
                    className="fixed inset-0 z-[100] bg-black/80 flex items-center justify-center p-4"
                    onClick={() => setPreviewImage(null)}
                >
                    <button
                        className="absolute top-4 right-4 text-white/80 hover:text-white p-2 bg-black/50 rounded-full"
                        onClick={() => setPreviewImage(null)}
                    >
                        <X className="w-6 h-6" />
                    </button>
                    <img
                        src={previewImage}
                        alt="Preview"
                        className="max-w-full max-h-[90vh] object-contain rounded-lg shadow-2xl"
                        onClick={(e) => e.stopPropagation()}
                    />
                </div>
            )}

            <div className="flex flex-col gap-2 w-full">
                {/* Image Preview Area */}
                {images.length > 0 && (
                    <div className="flex flex-wrap gap-2 p-2 bg-white/5 rounded-lg border border-white/10">
                        {images.map((img, index) => (
                            <div key={index} className="relative group">
                                <img
                                    src={img.preview}
                                    alt={`Attachment ${index + 1}`}
                                    className="h-16 w-auto max-w-[120px] rounded-lg object-cover border border-white/20 shadow-md cursor-pointer hover:opacity-80 transition-opacity"
                                    onClick={() => setPreviewImage(img.preview)}
                                />
                                <button
                                    type="button"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        removeImage(index);
                                    }}
                                    className="absolute -top-2 -right-2 bg-red-500/90 hover:bg-red-500 text-white rounded-full p-1 shadow-lg transition-all"
                                >
                                    <X className="w-3 h-3" />
                                </button>
                            </div>
                        ))}
                        {isUploading && (
                            <div className="h-16 w-16 rounded-lg bg-white/10 flex items-center justify-center border border-white/20">
                                <Loader2 className="w-5 h-5 animate-spin text-indigo-400" />
                            </div>
                        )}
                    </div>
                )}

                {/* Upload Button Row */}
                <div className="flex items-center gap-2">
                    <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isUploading || images.length >= maxImages}
                        className="p-2 text-white/40 hover:text-white/80 hover:bg-white/10 rounded-lg transition-colors disabled:opacity-50"
                        title="Attach images (or paste with Ctrl+V)"
                    >
                        {isUploading && images.length === 0 ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <ImagePlus className="w-5 h-5" />
                        )}
                    </button>

                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        multiple
                        onChange={handleFileSelect}
                        className="hidden"
                    />
                </div>
            </div>
        </>
    );
});

ImageUpload.displayName = 'ImageUpload';

export default ImageUpload;

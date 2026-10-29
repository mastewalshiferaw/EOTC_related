'use client';
import { useState, useRef } from 'react';
import ReactCrop, { type Crop, PixelCrop } from 'react-image-crop';
import 'react-image-crop/dist/ReactCrop.css';

interface ImageCropModalProps {
  imageSrc: string;
  isDark: boolean;
  onCropComplete: (croppedBlob: Blob) => void;
  onUseOriginal: () => void;
  onClose: () => void;
}

function CropIcon({ className = "w-3.5 h-3.5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 2v14a2 2 0 0 0 2 2h14" />
      <path d="M18 22V8a2 2 0 0 0-2-2H2" />
    </svg>
  );
}

function ExpandIcon({ className = "w-3.5 h-3.5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="15 3 21 3 21 9" />
      <polyline points="9 21 3 21 3 15" />
      <line x1="21" y1="3" x2="14" y2="10" />
      <line x1="3" y1="21" x2="10" y2="14" />
    </svg>
  );
}

function CloseIcon({ className = "w-3.5 h-3.5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

export default function ImageCropModal({
  imageSrc,
  isDark,
  onCropComplete,
  onUseOriginal,
  onClose,
}: ImageCropModalProps) {
  const [crop, setCrop] = useState<Crop>();
  const [completedCrop, setCompletedCrop] = useState<PixelCrop>();
  const [processing, setProcessing] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  const onImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const { width, height } = e.currentTarget;
    // Default initial crop to 85% centered
    const initialWidth = width * 0.85;
    const initialHeight = height * 0.85;
    const initialX = (width - initialWidth) / 2;
    const initialY = (height - initialHeight) / 2;

    const initialCrop: Crop = {
      unit: 'px',
      width: initialWidth,
      height: initialHeight,
      x: initialX,
      y: initialY,
    };
    setCrop(initialCrop);
    setCompletedCrop({
      unit: 'px',
      width: initialWidth,
      height: initialHeight,
      x: initialX,
      y: initialY,
    });
  };

  const handleApplyCrop = async () => {
    const image = imgRef.current;
    if (!image || !completedCrop || completedCrop.width <= 0 || completedCrop.height <= 0) {
      onUseOriginal();
      return;
    }

    try {
      setProcessing(true);
      const canvas = document.createElement('canvas');
      const scaleX = image.naturalWidth / image.width;
      const scaleY = image.naturalHeight / image.height;

      canvas.width = Math.max(1, Math.floor(completedCrop.width * scaleX));
      canvas.height = Math.max(1, Math.floor(completedCrop.height * scaleY));

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        onUseOriginal();
        return;
      }

      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';

      ctx.drawImage(
        image,
        completedCrop.x * scaleX,
        completedCrop.y * scaleY,
        completedCrop.width * scaleX,
        completedCrop.height * scaleY,
        0,
        0,
        canvas.width,
        canvas.height
      );

      canvas.toBlob((blob) => {
        setProcessing(false);
        if (blob) {
          onCropComplete(blob);
        } else {
          onUseOriginal();
        }
      }, 'image/png');
    } catch (err) {
      console.error('Crop error:', err);
      setProcessing(false);
      onUseOriginal();
    }
  };

  const modalBg = isDark ? 'bg-[#12141a] border-zinc-800 text-zinc-100' : 'bg-white border-zinc-200 text-zinc-900';
  const headerBorder = isDark ? 'border-zinc-800' : 'border-zinc-200';
  const previewBg = isDark ? 'bg-[#08090d]' : 'bg-zinc-100/70';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className={`relative max-w-4xl w-full max-h-[92vh] flex flex-col rounded-3xl border shadow-2xl overflow-hidden ${modalBg}`}>
        {/* Header */}
        <div className={`p-5 flex items-center justify-between border-b ${headerBorder}`}>
          <div>
            <h3 className="text-base font-bold tracking-tight">Crop Text</h3>
            <p className={`text-xs mt-0.5 ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>
              Select the text area to remove borders, shadows, and noise.
            </p>
          </div>
          <button
            onClick={onClose}
            className={`p-2 rounded-xl border transition ${isDark ? 'border-zinc-800 hover:bg-zinc-800 text-zinc-400 hover:text-white' : 'border-zinc-200 hover:bg-zinc-100 text-zinc-600 hover:text-black'}`}
            title="Close"
          >
            <CloseIcon className="w-4 h-4" />
          </button>
        </div>

        {/* Cropper Viewport */}
        <div className={`flex-1 p-6 overflow-auto flex items-center justify-center min-h-[350px] max-h-[60vh] ${previewBg}`}>
          <ReactCrop
            crop={crop}
            onChange={(_, percentCrop) => setCrop(percentCrop)}
            onComplete={(c) => setCompletedCrop(c)}
            className="rounded-lg overflow-hidden shadow-md"
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              ref={imgRef}
              src={imageSrc}
              alt="Crop text preview"
              onLoad={onImageLoad}
              className="max-h-[52vh] max-w-full object-contain select-none"
            />
          </ReactCrop>
        </div>

        {/* Action Controls */}
        <div className={`p-4 sm:p-5 flex flex-wrap items-center justify-between gap-3 border-t ${headerBorder}`}>
          <button
            type="button"
            onClick={onClose}
            className={`flex items-center gap-1.5 text-xs font-semibold px-3.5 py-2 rounded-xl border transition ${isDark ? 'border-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-800' : 'border-zinc-300 text-zinc-600 hover:text-black hover:bg-zinc-100'}`}
          >
            <CloseIcon className="w-3.5 h-3.5" />
            <span>Cancel</span>
          </button>

          <div className="flex items-center gap-2.5">
            <button
              type="button"
              onClick={onUseOriginal}
              className={`flex items-center gap-1.5 text-xs font-semibold px-3.5 py-2 rounded-xl border transition ${isDark ? 'border-zinc-700 bg-zinc-800/80 text-zinc-300 hover:bg-zinc-700 hover:text-white' : 'border-zinc-300 bg-zinc-50 text-zinc-700 hover:bg-zinc-100 hover:text-black shadow-sm'}`}
            >
              <ExpandIcon className="w-3.5 h-3.5" />
              <span>Full</span>
            </button>

            <button
              type="button"
              disabled={processing}
              onClick={handleApplyCrop}
              className={`flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider px-4 py-2 rounded-xl shadow-md transition disabled:opacity-50 ${isDark ? 'bg-zinc-100 text-zinc-900 hover:bg-white' : 'bg-zinc-900 text-white hover:bg-black'}`}
            >
              <CropIcon className="w-3.5 h-3.5" />
              <span>{processing ? "Cropping" : "Crop"}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

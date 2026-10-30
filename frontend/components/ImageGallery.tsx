/** 🔥 Professional Image Gallery Component
 * 
 * Features:
 * - Smooth image transitions
 * - Professional hover effects
 * - Responsive grid layout
 * - Professional captions
 */

import React, { useState } from 'react';

interface ImageItem {
  id: string;
  src: string;
  caption: string;
  title: string;
  category: string;
}

interface ImageGalleryProps {
  images: ImageItem[];
  columns?: number;
}

const ImageGallery: React.FC<ImageGalleryProps> = ({ 
  images, 
  columns = 3 
}) => {
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  return (
    <div className="grid gap-6" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
      {images.map((image) => (
        <div
          key={image.id}
          className="relative overflow-hidden rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 group cursor-pointer"
          onClick={() => setSelectedImage(image.src)}
        >
          <img
            src={image.src}
            alt={image.title}
            className="w-full h-64 object-cover transition-transform duration-300 group-hover:scale-110"
          />
          
          {/* Image Overlay with Caption */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <div className="absolute bottom-0 left-0 right-0 p-4 text-white transform translate-y-full group-hover:translate-y-0 transition-transform duration-300">
              <h3 className="text-lg font-semibold mb-1">{image.title}</h3>
              <p className="text-sm opacity-90">{image.caption}</p>
              <span className="inline-block px-2 py-1 bg-green-600 text-white text-xs rounded-full">
                {image.category}
              </span>
            </div>
          </div>
        </div>
      ))}

      {/* 🔥 Selected Image Modal */}
      {selectedImage && (
        <div 
          className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedImage(null)}
        >
          <div 
            className="relative max-w-4xl max-h-full"
            onClick={(e) => e.stopPropagation()}
          >
            <img
              src={selectedImage}
              alt="Selected image"
              className="w-full h-full object-contain rounded-xl"
            />
            <button
              onClick={() => setSelectedImage(null)}
              className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm text-white p-2 rounded-full hover:bg-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageGallery;

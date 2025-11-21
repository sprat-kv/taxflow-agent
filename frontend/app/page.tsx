'use client';

import { useState } from 'react';
import { Upload, FileText, ArrowRight, CheckCircle, Loader2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';

export default function LandingPage() {
  const router = useRouter();
  const [files, setFiles] = useState<File[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files).filter(
        file => file.type === 'application/pdf'
      );
      setFiles(prev => [...prev, ...newFiles]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files).filter(
        file => file.type === 'application/pdf'
      );
      setFiles(prev => [...prev, ...newFiles]);
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleStart = async () => {
    if (files.length === 0) return;

    setIsUploading(true);

    // Create FormData
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    try {
      // Upload files to create session
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBaseUrl}/api/sessions`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      const sessionId = data.session_id; // Adjust based on actual API response

      // Navigate to process page with session ID
      console.log('Session created:', sessionId);
      router.push(`/process/${sessionId}`);

    } catch (error) {
      console.error('Error uploading files:', error);
      alert('Failed to upload files. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 p-6">
      <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">

        {/* Left Side: Description */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          className="space-y-8"
        >
          <div className="space-y-4">
            <h1 className="text-5xl font-bold tracking-tight text-gray-900">
              Tax Filing, <span className="text-primary">Simplified.</span>
            </h1>
            <p className="text-xl text-gray-600 leading-relaxed">
              Experience the future of tax preparation. Our AI-powered agent extracts data from your documents,
              calculates your taxes with precision, and generates your Form 1040 in seconds.
            </p>
          </div>

          <div className="space-y-4">
            {[
              'Secure Document Processing',
              'Instant Data Extraction',
              'Accurate Tax Calculations',
              'Ready-to-file Form 1040'
            ].map((feature, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                </div>
                <span className="text-gray-700 font-medium">{feature}</span>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Right Side: Upload Box */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="glass-panel rounded-2xl p-8 shadow-xl bg-white/80 backdrop-blur-xl border border-white/20"
        >
          <div className="space-y-6">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-semibold text-gray-900">Upload Documents</h2>
              <p className="text-gray-500">Drag & drop your W-2s, 1099s, or other tax forms</p>
            </div>

            <div
              className={`
                border-2 border-dashed rounded-xl p-10 text-center transition-all duration-200 cursor-pointer
                ${isDragging ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-primary/50 hover:bg-gray-50'}
              `}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => document.getElementById('file-upload')?.click()}
            >
              <input
                id="file-upload"
                type="file"
                multiple
                accept=".pdf"
                className="hidden"
                onChange={handleFileSelect}
              />
              <div className="flex flex-col items-center space-y-4">
                <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center text-primary">
                  <Upload className="w-8 h-8" />
                </div>
                <div className="space-y-1">
                  <p className="font-medium text-gray-700">Click to upload or drag and drop</p>
                  <p className="text-sm text-gray-500">PDF files only</p>
                </div>
              </div>
            </div>

            {/* File List */}
            {files.length > 0 && (
              <div className="space-y-3 max-h-60 overflow-y-auto pr-2">
                {files.map((file, index) => (
                  <motion.div
                    key={`${file.name}-${index}`}
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-100 shadow-sm"
                  >
                    <div className="flex items-center space-x-3 overflow-hidden">
                      <FileText className="w-5 h-5 text-blue-500 flex-shrink-0" />
                      <span className="text-sm font-medium text-gray-700 truncate">{file.name}</span>
                      <span className="text-xs text-gray-400 flex-shrink-0">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </span>
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); removeFile(index); }}
                      className="text-gray-400 hover:text-red-500 transition-colors"
                    >
                      ×
                    </button>
                  </motion.div>
                ))}
              </div>
            )}

            <button
              onClick={handleStart}
              disabled={files.length === 0 || isUploading}
              className={`
                w-full py-4 rounded-xl font-semibold text-lg shadow-lg transition-all duration-200 flex items-center justify-center space-x-2
                ${files.length > 0 && !isUploading
                  ? 'bg-primary text-white hover:bg-blue-600 hover:shadow-blue-500/30 transform hover:-translate-y-0.5'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'}
              `}
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <>
                  <span>Start Processing</span>
                  <ArrowRight className="w-5 h-5" />
                </>
              )}
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

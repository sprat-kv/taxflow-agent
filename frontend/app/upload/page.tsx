'use client';

import { useState, useRef } from 'react';
import { Upload, FileText, ArrowRight, Loader2, Zap } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';

export default function UploadPage() {
    const router = useRouter();
    const [files, setFiles] = useState<File[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

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

        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        try {
            const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiBaseUrl}/api/sessions`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            const data = await response.json();
            const sessionId = data.session_id;
            router.push(`/process/${sessionId}`);

        } catch (error) {
            console.error('Error uploading files:', error);
            alert('Failed to upload files. Please try again.');
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col font-sans">
            {/* Simple Navbar */}
            <nav className="bg-white border-b border-gray-100 px-6 py-4">
                <div className="max-w-7xl mx-auto flex justify-between items-center">
                    <div className="flex items-center space-x-2 cursor-pointer" onClick={() => router.push('/')}>
                        <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold">
                            <Zap className="w-5 h-5" />
                        </div>
                        <span className="text-xl font-bold text-gray-900 tracking-tight">TaxFlow</span>
                    </div>
                </div>
            </nav>

            <main className="flex-grow flex items-center justify-center p-6">
                <div className="max-w-2xl w-full space-y-8">
                    <div className="text-center space-y-2">
                        <h1 className="text-3xl font-bold text-gray-900">Upload Your Tax Documents</h1>
                        <p className="text-gray-500">We support W-2s, 1099s, and other standard tax forms in PDF format.</p>
                    </div>

                    <div className="bg-white rounded-3xl p-8 shadow-xl border border-gray-100">
                        <div
                            className={`
                relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 cursor-pointer
                ${isDragging
                                    ? 'border-blue-500 bg-blue-50/50 scale-[1.02]'
                                    : 'border-gray-200 hover:border-blue-400 hover:bg-gray-50'
                                }
              `}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                multiple
                                accept=".pdf"
                                className="hidden"
                                onChange={handleFileSelect}
                            />

                            <div className="flex flex-col items-center space-y-4">
                                <div className={`
                  w-20 h-20 rounded-full bg-blue-50 flex items-center justify-center text-blue-600
                  transition-transform duration-300 ${isDragging ? 'scale-110' : ''}
                `}>
                                    <Upload className="w-10 h-10" />
                                </div>
                                <div className="space-y-1">
                                    <p className="font-semibold text-gray-900 text-lg">Click to upload or drag and drop</p>
                                    <p className="text-sm text-gray-500">PDF files only</p>
                                </div>
                            </div>
                        </div>

                        <AnimatePresence>
                            {files.length > 0 && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: 'auto' }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="mt-6 space-y-3 max-h-60 overflow-y-auto pr-2 custom-scrollbar"
                                >
                                    {files.map((file, index) => (
                                        <motion.div
                                            key={`${file.name}-${index}`}
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            exit={{ opacity: 0, x: 10 }}
                                            className="flex items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-100"
                                        >
                                            <div className="flex items-center space-x-3 overflow-hidden">
                                                <div className="p-2 bg-white rounded-lg border border-gray-200">
                                                    <FileText className="w-4 h-4 text-blue-600" />
                                                </div>
                                                <div className="flex flex-col min-w-0">
                                                    <span className="text-sm font-medium text-gray-700 truncate">{file.name}</span>
                                                    <span className="text-xs text-gray-400">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                                                </div>
                                            </div>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); removeFile(index); }}
                                                className="p-1 hover:bg-red-100 rounded-full text-gray-400 hover:text-red-500 transition-colors"
                                            >
                                                ×
                                            </button>
                                        </motion.div>
                                    ))}
                                </motion.div>
                            )}
                        </AnimatePresence>

                        <div className="mt-8">
                            <button
                                onClick={handleStart}
                                disabled={files.length === 0 || isUploading}
                                className={`
                  w-full py-4 rounded-xl font-bold text-lg shadow-lg transition-all duration-300 flex items-center justify-center space-x-2
                  ${files.length > 0 && !isUploading
                                        ? 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow-blue-500/30 transform hover:-translate-y-0.5'
                                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'}
                `}
                            >
                                {isUploading ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        <span>Processing...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>Start Processing</span>
                                        <ArrowRight className="w-5 h-5" />
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

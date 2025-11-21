'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, FileText } from 'lucide-react';

interface LoadingScreenProps {
    fileCount: number;
    onComplete: () => void;
}

export default function LoadingScreen({ fileCount, onComplete }: LoadingScreenProps) {
    const [progress, setProgress] = useState(0);
    const [currentStep, setCurrentStep] = useState(0);

    const steps = [
        'Uploading documents...',
        'Analyzing file structure...',
        'Extracting tax data...',
        'Validating information...',
        'Preparing your session...'
    ];

    useEffect(() => {
        // Simulate processing time: ~8-10s per document
        const totalDuration = fileCount * 9000;
        const intervalTime = 100;
        const stepsCount = totalDuration / intervalTime;
        const increment = 100 / stepsCount;

        const timer = setInterval(() => {
            setProgress(prev => {
                if (prev >= 100) {
                    clearInterval(timer);
                    setTimeout(onComplete, 500); // Small delay before transition
                    return 100;
                }
                return prev + increment;
            });
        }, intervalTime);

        // Cycle through text steps
        const stepInterval = setInterval(() => {
            setCurrentStep(prev => (prev + 1) % steps.length);
        }, totalDuration / steps.length);

        return () => {
            clearInterval(timer);
            clearInterval(stepInterval);
        };
    }, [fileCount, onComplete, steps.length]);

    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 p-6">
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-full max-w-md bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl p-8 border border-white/20 text-center space-y-8"
            >
                <div className="relative w-32 h-32 mx-auto">
                    {/* Circular Progress Background */}
                    <svg className="w-full h-full transform -rotate-90">
                        <circle
                            cx="64"
                            cy="64"
                            r="60"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="transparent"
                            className="text-gray-100"
                        />
                        <circle
                            cx="64"
                            cy="64"
                            r="60"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="transparent"
                            strokeDasharray={377}
                            strokeDashoffset={377 - (377 * progress) / 100}
                            className="text-primary transition-all duration-300 ease-out"
                            strokeLinecap="round"
                        />
                    </svg>

                    {/* Center Icon */}
                    <div className="absolute inset-0 flex items-center justify-center">
                        {progress < 100 ? (
                            <span className="text-2xl font-bold text-primary">{Math.round(progress)}%</span>
                        ) : (
                            <CheckCircle2 className="w-12 h-12 text-green-500 animate-bounce" />
                        )}
                    </div>
                </div>

                <div className="space-y-2">
                    <h3 className="text-xl font-semibold text-gray-900">Processing {fileCount} Document{fileCount > 1 ? 's' : ''}</h3>
                    <motion.p
                        key={currentStep}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-gray-500 h-6"
                    >
                        {progress >= 100 ? 'Complete!' : steps[currentStep]}
                    </motion.p>
                </div>

                {/* File Icons Animation */}
                <div className="flex justify-center space-x-2">
                    {[...Array(Math.min(fileCount, 5))].map((_, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                        >
                            <FileText className={`w-6 h-6 ${progress > (i + 1) * (100 / fileCount) ? 'text-green-500' : 'text-gray-300'}`} />
                        </motion.div>
                    ))}
                </div>
            </motion.div>
        </div>
    );
}

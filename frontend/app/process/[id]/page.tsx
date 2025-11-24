'use client';

import { useEffect, useState, use, useRef } from 'react';
import { useRouter } from 'next/navigation';
import LoadingScreen from '../../components/LoadingScreen';
import MandatoryFieldsForm from '../../components/MandatoryFieldsForm';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, ArrowRight, Zap } from 'lucide-react';

interface ProcessPageProps {
    params: Promise<{ id: string }>;
}

interface AgentLog {
    timestamp: string;
    node: "aggregator" | "calculator" | "validator" | "advisor";
    message: string;
    type: "info" | "success" | "warning" | "error";
}

function ActivityFeed({ logs }: { logs: AgentLog[] }) {
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    const getIcon = (type: string) => {
        switch (type) {
            case "success": return "✅";
            case "warning": return "⚠️";
            case "error": return "❌";
            default: return "ℹ️";
        }
    };

    const getColor = (type: string) => {
        switch (type) {
            case "success": return "text-green-600";
            case "warning": return "text-yellow-600";
            case "error": return "text-red-600";
            default: return "text-blue-600";
        }
    };

    return (
        <div className="w-full max-w-2xl bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
            <div className="bg-gray-50 px-4 py-3 border-b border-gray-100 flex justify-between items-center">
                <h3 className="font-semibold text-gray-700 flex items-center gap-2">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    Agent Activity Feed
                </h3>
                <span className="text-xs text-gray-400 font-mono">LIVE</span>
            </div>
            <div ref={scrollRef} className="h-64 overflow-y-auto p-4 space-y-3 bg-white">
                {logs.length === 0 && (
                    <p className="text-gray-400 text-center italic text-sm">Waiting for agent to start...</p>
                )}
                {logs.map((log, index) => (
                    <motion.div
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex items-start space-x-3 p-2 rounded hover:bg-gray-50 transition-colors"
                    >
                        <span className="text-lg mt-0.5">{getIcon(log.type)}</span>
                        <div className="flex-1 min-w-0">
                            <p className={`text-sm font-medium ${getColor(log.type)}`}>
                                {log.message}
                            </p>
                            <div className="flex items-center gap-2 mt-1">
                                <span className="text-[10px] uppercase tracking-wider font-bold text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">
                                    {log.node}
                                </span>
                                <span className="text-[10px] text-gray-400 font-mono">
                                    {new Date(log.timestamp).toLocaleTimeString()}
                                </span>
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
}

export default function ProcessPage({ params }: ProcessPageProps) {
    const { id: sessionId } = use(params);
    const router = useRouter();

    // Workflow States
    const [status, setStatus] = useState<'loading' | 'mandatory_info' | 'processing' | 'agent_input' | 'complete'>('loading');
    const [fileCount, setFileCount] = useState(1);
    const [missingFields, setMissingFields] = useState<string[]>([]);
    const [agentMessage, setAgentMessage] = useState('');
    const [agentInputData, setAgentInputData] = useState<Record<string, string>>({});
    const [logs, setLogs] = useState<AgentLog[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Extraction State
    const [isExtractionDone, setIsExtractionDone] = useState(false);
    const [isLoadingScreenDone, setIsLoadingScreenDone] = useState(false);
    const extractionStarted = useRef(false);

    // Custom messages for better UX
    const customMessages = ["Extracting information", "Estimating tax fields", "Aggregating Result", "Calculating Tax"];
    const [messageIndex, setMessageIndex] = useState(0);

    // ... (useEffect for initSession remains same) ...
    useEffect(() => {
        const initSession = async () => {
            if (extractionStarted.current) return;
            extractionStarted.current = true;

            try {
                const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

                // 1. Fetch Session
                const res = await fetch(`${apiBaseUrl}/api/sessions/${sessionId}`);
                if (!res.ok) throw new Error('Failed to fetch session');

                const data = await res.json();
                setFileCount(data.documents?.length || 1);

                // 2. Trigger Extraction for all documents
                if (data.documents && data.documents.length > 0) {
                    console.log('Starting extraction for', data.documents.length, 'documents...');
                    const extractionPromises = data.documents.map((doc: any) =>
                        fetch(`${apiBaseUrl}/api/documents/${doc.id}/extract`, {
                            method: 'POST'
                        }).then(r => {
                            if (!r.ok) console.error(`Failed to extract doc ${doc.id}`);
                            return r;
                        })
                    );

                    await Promise.all(extractionPromises);
                    console.log('All documents extracted successfully');
                }

                setIsExtractionDone(true);

            } catch (error) {
                console.error('Error initializing session:', error);
                setIsExtractionDone(true);
            }
        };

        initSession();
    }, [sessionId]);

    // ... (useEffect for status transition remains same) ...
    useEffect(() => {
        if (isExtractionDone && isLoadingScreenDone && status === 'loading') {
            setStatus('mandatory_info');
        }
    }, [isExtractionDone, isLoadingScreenDone, status]);

    useEffect(() => {
        if (status === 'processing') {
            const interval = setInterval(() => {
                setMessageIndex(prev => (prev < customMessages.length - 1 ? prev + 1 : prev));
            }, 2500);
            return () => clearInterval(interval);
        }
    }, [status]);

    // ... (handleLoadingComplete remains same) ...
    const handleLoadingComplete = () => {
        setIsLoadingScreenDone(true);
    };

    // ... (handleMandatorySubmit remains same) ...
    const handleMandatorySubmit = async (data: Record<string, string>) => {
        setStatus('processing');
        try {
            const mappedData = {
                filer_name: data.full_name,
                filer_ssn: data.ssn,
                home_address: data.address,
                filing_status: data.filing_status,
                tax_year: data.tax_year
            };
            await runAgentLoop(mappedData);
        } catch (error) {
            console.error('Error submitting mandatory info:', error);
            alert('Something went wrong. Please try again.');
            setStatus('mandatory_info');
        }
    };

    // Step 3: Agent Loop (Polls/Posts to /process)
    const runAgentLoop = async (inputData: Record<string, string> = {}) => {
        try {
            const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

            const personalInfoKeys = ['filer_name', 'filer_ssn', 'home_address', 'digital_assets', 'occupation'];
            const personalInfo: Record<string, string> = {};
            const userInputs: Record<string, string> = {};

            Object.entries(inputData).forEach(([key, value]) => {
                if (personalInfoKeys.includes(key)) {
                    personalInfo[key] = value;
                } else if (key !== 'filing_status' && key !== 'tax_year') {
                    userInputs[key] = value;
                }
            });

            const payload = {
                filing_status: inputData.filing_status,
                tax_year: inputData.tax_year,
                personal_info: Object.keys(personalInfo).length > 0 ? personalInfo : undefined,
                user_inputs: Object.keys(userInputs).length > 0 ? userInputs : undefined
            };

            const res = await fetch(`${apiBaseUrl}/api/sessions/${sessionId}/process`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error('Processing failed');

            const result = await res.json();
            console.log('Agent Result:', result);

            if (result.logs) {
                setLogs(result.logs);
                // Scroll to bottom
                if (scrollRef.current) {
                    scrollRef.current.scrollIntoView({ behavior: 'smooth' });
                }
            }

            // Handle Agent States
            if (result.status === 'waiting_for_user' || result.status === 'missing_info') {
                setMissingFields(result.missing_fields || []);
                setAgentMessage(result.message || 'We need a bit more information.');
                setStatus('agent_input');
            } else if (result.status === 'complete' || result.status === 'completed' || result.status === 'success') {
                // Save result to localStorage for SummaryPage
                if (result.calculation_result) {
                    localStorage.setItem(`tax_result_${sessionId}`, JSON.stringify(result.calculation_result));
                }
                // Save Advisor Feedback
                if (result.advisor_feedback) {
                    localStorage.setItem(`advisor_feedback_${sessionId}`, result.advisor_feedback);
                }

                // Add a small delay to let user see the "Success" log
                setTimeout(() => {
                    setStatus('complete');
                    router.push(`/summary/${sessionId}`);
                }, 2000);
            } else {
                if (result.status === 'processing') {
                    setTimeout(() => runAgentLoop(), 2000);
                }
            }
        } catch (error) {
            console.error('Agent loop error:', error);
            alert('Error processing tax return. See console.');
        }
    };

    // ... (handleAgentInputSubmit remains same) ...
    const handleAgentInputSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setStatus('processing');
        runAgentLoop(agentInputData);
    };

    // Render Views based on Status
    if (status === 'loading') {
        return <LoadingScreen fileCount={fileCount} onComplete={handleLoadingComplete} />;
    }

    if (status === 'mandatory_info') {
        return <MandatoryFieldsForm onSubmit={handleMandatorySubmit} />;
    }

    // Calculate progress based on message index for smoother feel
    const progress = Math.min(20 + (messageIndex * 25), 95);

    if (status === 'processing') {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 p-4 md:p-6 relative overflow-hidden">
                {/* Background Blobs */}
                <div className="absolute top-[-20%] right-[-10%] w-[300px] md:w-[600px] h-[300px] md:h-[600px] bg-blue-200/30 rounded-full blur-[50px] md:blur-[100px] animate-pulse"></div>
                <div className="absolute bottom-[-20%] left-[-10%] w-[300px] md:w-[600px] h-[300px] md:h-[600px] bg-indigo-200/30 rounded-full blur-[50px] md:blur-[100px] animate-pulse animation-delay-2000"></div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="relative z-10 w-full max-w-xl"
                >
                    <div className="bg-white/80 backdrop-blur-2xl rounded-3xl shadow-2xl border border-white/50 overflow-hidden">
                        {/* Header Section */}
                        <div className="p-6 md:p-10 text-center space-y-6 relative">
                            <div className="inline-flex items-center justify-center w-16 h-16 md:w-20 md:h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/30 mb-2">
                                <Zap className="w-8 h-8 md:w-10 md:h-10 text-white animate-pulse" />
                            </div>

                            <div className="space-y-2">
                                <h2 className="text-2xl md:text-3xl font-bold text-gray-900 tracking-tight">
                                    AI Agent is Working
                                </h2>
                                <p className="text-gray-500 text-base md:text-lg">
                                    Analyzing your documents...
                                </p>
                            </div>

                            {/* Progress Bar */}
                            <div className="w-full max-w-md mx-auto mt-8 space-y-3">
                                <div className="flex justify-between text-sm font-medium text-gray-600 px-1">
                                    <span>Progress</span>
                                    <span>{Math.round(progress)}%</span>
                                </div>
                                <div className="h-2 md:h-3 w-full bg-gray-100 rounded-full overflow-hidden shadow-inner">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${progress}%` }}
<<<<<<< HEAD
                                        transition={{ type: "spring" as const, stiffness: 50, damping: 15 }}
=======
                                        transition={{ type: "spring", stiffness: 50, damping: 15 }}
>>>>>>> fa00ea120ed9fb0b332b66b8ce5e0600ac353737
                                        className="h-full bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-full relative"
                                    >
                                        <div className="absolute inset-0 bg-white/20 animate-shimmer skew-x-12"></div>
                                    </motion.div>
                                </div>
                            </div>
                        </div>

                        {/* Current Activity Focus View */}
                        <div className="bg-gray-50/50 border-t border-gray-100 p-6 md:p-8 min-h-[140px] flex flex-col items-center justify-center text-center">
                            <div className="flex items-center space-x-2 mb-4">
                                <span className="relative flex h-2.5 w-2.5">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-indigo-500"></span>
                                </span>
                                <span className="text-xs font-bold text-indigo-500 uppercase tracking-wider">Current Task</span>
                            </div>

                            <AnimatePresence mode='wait'>
                                <motion.div
                                    key={messageIndex} // Key change triggers animation
                                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    exit={{ opacity: 0, y: -10, scale: 0.95 }}
                                    transition={{ duration: 0.3 }}
                                    className="max-w-sm"
                                >
                                    <p className="text-gray-800 font-semibold text-lg md:text-xl leading-relaxed">
                                        {customMessages[messageIndex]}
                                    </p>
                                    <p className="text-xs text-gray-400 mt-2 font-mono uppercase">
                                        AI_AGENT • PROCESSING
                                    </p>
                                </motion.div>
                            </AnimatePresence>
                        </div>
                    </div>
                </motion.div>
            </div>
        );
    }

    if (status === 'agent_input') {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 p-6">
                <div className="w-full max-w-lg mb-6">
                    <ActivityFeed logs={logs} />
                </div>

                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="w-full max-w-lg bg-white rounded-2xl shadow-xl p-8"
                >
                    <div className="flex items-start space-x-4 mb-6">
                        <div className="p-3 bg-yellow-100 rounded-full text-yellow-600">
                            <AlertCircle className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-gray-900">Additional Info Needed</h3>
                            <p className="text-gray-600 mt-1">{agentMessage}</p>
                        </div>
                    </div>

                    <form onSubmit={handleAgentInputSubmit} className="space-y-4">
                        {missingFields.map((field) => (
                            <div key={field} className="space-y-2">
                                <label className="text-sm font-medium text-gray-700 capitalize">
                                    {field.replace(/_/g, ' ')}
                                </label>
                                <input
                                    type="text"
                                    required
                                    className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 outline-none"
                                    onChange={(e) => setAgentInputData(prev => ({ ...prev, [field]: e.target.value }))}
                                />
                            </div>
                        ))}

                        <button
                            type="submit"
                            className="w-full py-3 bg-primary text-white rounded-xl font-semibold shadow-lg hover:bg-blue-600 transition-all mt-4 flex items-center justify-center gap-2"
                        >
                            <span>Submit & Continue</span>
                            <ArrowRight className="w-4 h-4" />
                        </button>
                    </form>
                </motion.div>
            </div>
        );
    }

    return null;
}

'use client';

import { useEffect, useState, use, useRef } from 'react';
import { useRouter } from 'next/navigation';
import LoadingScreen from '../../components/LoadingScreen';
import MandatoryFieldsForm from '../../components/MandatoryFieldsForm';
import { motion } from 'framer-motion';
import { AlertCircle, ArrowRight } from 'lucide-react';

interface ProcessPageProps {
    params: Promise<{ id: string }>;
}

export default function ProcessPage({ params }: ProcessPageProps) {
    const { id: sessionId } = use(params);
    const router = useRouter();

    // Workflow States
    const [status, setStatus] = useState<'loading' | 'mandatory_info' | 'processing' | 'agent_input' | 'complete'>('loading');
    const [fileCount, setFileCount] = useState(1); // Default, will fetch real count
    const [missingFields, setMissingFields] = useState<string[]>([]);
    const [agentMessage, setAgentMessage] = useState('');
    const [agentInputData, setAgentInputData] = useState<Record<string, string>>({});

    // Extraction State
    const [isExtractionDone, setIsExtractionDone] = useState(false);
    const [isLoadingScreenDone, setIsLoadingScreenDone] = useState(false);
    const extractionStarted = useRef(false);

    // Fetch session details and trigger extraction on mount
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
                // Even if error, we might want to proceed or show error
                setIsExtractionDone(true); // Proceed to let agent handle missing data
            }
        };

        initSession();
    }, [sessionId]);

    // Watch for both Loading Screen and Extraction to be done
    useEffect(() => {
        if (isExtractionDone && isLoadingScreenDone && status === 'loading') {
            setStatus('mandatory_info');
        }
    }, [isExtractionDone, isLoadingScreenDone, status]);

    // Step 1: Loading Screen Complete
    const handleLoadingComplete = () => {
        setIsLoadingScreenDone(true);
    };

    // Step 2: Submit Mandatory Info -> Start Agent Processing
    const handleMandatorySubmit = async (data: Record<string, string>) => {
        setStatus('processing');
        try {
            // Map frontend keys to backend expected keys
            const mappedData = {
                filer_name: data.full_name,
                filer_ssn: data.ssn,
                home_address: data.address,
                filing_status: data.filing_status,
                tax_year: data.tax_year
            };

            // First, update session with initial data (if endpoint exists, or pass to process)
            // For now, we'll pass it directly to the process loop
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

            // Construct payload based on backend ProcessSessionRequest schema
            // If inputData contains personal info keys, put them in personal_info dict
            // Otherwise, put them in user_inputs

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
            console.log('DEBUG: Backend response:', result);
            console.log('DEBUG: Response status:', result.status);

            // Handle Agent States
            if (result.status === 'waiting_for_user' || result.status === 'missing_info') {
                setMissingFields(result.missing_fields || []);
                setAgentMessage(result.message || 'We need a bit more information.');
                setStatus('agent_input');
            } else if (result.status === 'complete' || result.status === 'completed' || result.status === 'success') {
                // Save result to localStorage for SummaryPage to use as fallback
                if (result.calculation_result) {
                    localStorage.setItem(`tax_result_${sessionId}`, JSON.stringify(result.calculation_result));
                }
                setStatus('complete');
                router.push(`/summary/${sessionId}`);
            } else {
                // If still processing or other state, maybe poll again? 
                // For this demo, we assume one-shot or specific stops.
                // If it returns "processing", we might need a delay and retry.
                if (result.status === 'processing') {
                    setTimeout(() => runAgentLoop(), 2000);
                }
            }
        } catch (error) {
            console.error('Agent loop error:', error);
            alert('Error processing tax return. See console.');
        }
    };

    // Step 4: Handle Dynamic Agent Input
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

    if (status === 'processing') {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
                <div className="text-center space-y-4">
                    <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto"></div>
                    <h2 className="text-2xl font-semibold text-gray-900">AI Agent is working...</h2>
                    <p className="text-gray-500">Analyzing data, checking rules, and calculating taxes.</p>
                </div>
            </div>
        );
    }

    if (status === 'agent_input') {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 p-6">
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

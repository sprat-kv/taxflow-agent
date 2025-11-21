'use client';

import { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Download, RefreshCw, DollarSign, CheckCircle, FileText } from 'lucide-react';

interface SummaryPageProps {
    params: Promise<{ id: string }>;
}

interface TaxResult {
    gross_income?: number;
    taxable_income?: number;
    tax_liability?: number;
    refund_or_owed?: number;
    standard_deduction?: number;
    status?: string;
    advisor_feedback?: string;
}

function AdvisorFeedback({ feedback, isRefund }: { feedback: string | null, isRefund: boolean }) {
    if (!feedback) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className={`rounded-2xl p-6 border-l-4 shadow-md my-8 ${isRefund
                    ? 'bg-green-50 border-green-500'
                    : 'bg-amber-50 border-amber-500'
                }`}
        >
            <div className="flex items-start">
                <div className="flex-shrink-0">
                    {isRefund ? (
                        <CheckCircle className="h-6 w-6 text-green-600" />
                    ) : (
                        <div className="h-6 w-6 text-amber-600 font-bold text-xl">!</div>
                    )}
                </div>
                <div className="ml-4 flex-1">
                    <h3 className={`text-lg font-bold mb-2 ${isRefund ? 'text-green-900' : 'text-amber-900'
                        }`}>
                        💡 Your Personalized Tax Advice
                    </h3>
                    <div className={`prose prose-sm max-w-none whitespace-pre-line ${isRefund ? 'text-green-800' : 'text-amber-800'
                        }`}>
                        {feedback}
                    </div>
                </div>
            </div>
        </motion.div>
    );
}

export default function SummaryPage({ params }: SummaryPageProps) {
    const { id: sessionId } = use(params);
    const router = useRouter();
    const [taxData, setTaxData] = useState<TaxResult | null>(null);
    const [loading, setLoading] = useState(true);
    const [advisorFeedback, setAdvisorFeedback] = useState<string | null>(null);

    useEffect(() => {
        const fetchResults = async () => {
            try {
                // 1. Try to get from LocalStorage first
                const storedData = localStorage.getItem(`tax_result_${sessionId}`);
                const storedFeedback = localStorage.getItem(`advisor_feedback_${sessionId}`);

                if (storedFeedback) {
                    setAdvisorFeedback(storedFeedback);
                }

                let localResult = null;
                if (storedData) {
                    try {
                        localResult = JSON.parse(storedData);
                    } catch (e) {
                        console.error('Error parsing local storage data', e);
                    }
                }

                // 2. Fetch from API
                const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const res = await fetch(`${apiBaseUrl}/api/sessions/${sessionId}`);

                if (res.ok) {
                    const data = await res.json();

                    // Update feedback from API if available
                    if (data.advisor_feedback) {
                        setAdvisorFeedback(data.advisor_feedback);
                    }

                    const result = data.calculation_result || localResult || {
                        gross_income: 0,
                        taxable_income: 0,
                        tax_liability: 0,
                        refund_or_owed: 0,
                        standard_deduction: 0,
                        status: 'owed'
                    };
                    setTaxData(result);
                } else if (localResult) {
                    setTaxData(localResult);
                }
            } catch (error) {
                console.error('Error fetching summary:', error);
                const storedData = localStorage.getItem(`tax_result_${sessionId}`);
                if (storedData) {
                    setTaxData(JSON.parse(storedData));
                }
            } finally {
                setLoading(false);
            }
        };
        fetchResults();
    }, [sessionId]);

    // ... (handleDownload remains same) ...
    const handleDownload = async () => {
        try {
            const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const res = await fetch(`${apiBaseUrl}/api/reports/${sessionId}/1040`, {
                method: 'POST',
            });

            if (res.ok) {
                const blob = await res.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `Form1040_${sessionId}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                alert('Failed to generate PDF. Please try again.');
            }
        } catch (error) {
            console.error('Download error:', error);
            alert('Error downloading file.');
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
        );
    }

    const isRefund = taxData?.status === 'refund';

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-6">
            <div className="max-w-4xl mx-auto space-y-8">

                {/* Header */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center space-y-2"
                >
                    <div className="inline-flex items-center justify-center p-3 bg-green-100 rounded-full mb-4">
                        <CheckCircle className="w-8 h-8 text-green-600" />
                    </div>
                    <h1 className="text-4xl font-bold text-gray-900">Tax Return Completed!</h1>
                    <p className="text-xl text-gray-600">Here is your 2024 tax summary.</p>
                </motion.div>

                {/* Main Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Gross Income */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
                    >
                        <div className="flex items-center space-x-3 mb-2">
                            <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                                <DollarSign className="w-5 h-5" />
                            </div>
                            <span className="text-gray-500 font-medium">Gross Income</span>
                        </div>
                        <p className="text-3xl font-bold text-gray-900">
                            ${taxData?.gross_income?.toLocaleString() || '0.00'}
                        </p>
                    </motion.div>

                    {/* Taxable Income */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100"
                    >
                        <div className="flex items-center space-x-3 mb-2">
                            <div className="p-2 bg-purple-100 rounded-lg text-purple-600">
                                <FileText className="w-5 h-5" />
                            </div>
                            <span className="text-gray-500 font-medium">Taxable Income</span>
                        </div>
                        <p className="text-3xl font-bold text-gray-900">
                            ${taxData?.taxable_income?.toLocaleString() || '0.00'}
                        </p>
                    </motion.div>

                    {/* Refund / Owed */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        className={`rounded-2xl p-6 shadow-lg border ${isRefund ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}
                    >
                        <div className="flex items-center space-x-3 mb-2">
                            <div className={`p-2 rounded-lg ${isRefund ? 'bg-green-200 text-green-700' : 'bg-red-200 text-red-700'}`}>
                                <DollarSign className="w-5 h-5" />
                            </div>
                            <span className={`font-medium ${isRefund ? 'text-green-700' : 'text-red-700'}`}>
                                {isRefund ? 'Estimated Refund' : 'Amount Owed'}
                            </span>
                        </div>
                        <p className={`text-3xl font-bold ${isRefund ? 'text-green-700' : 'text-red-700'}`}>
                            ${Math.abs(taxData?.refund_or_owed || 0).toLocaleString()}
                        </p>
                    </motion.div>
                </div>

                {/* Advisor Feedback */}
                <AdvisorFeedback feedback={advisorFeedback} isRefund={isRefund} />

                {/* Detailed Breakdown */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.4 }}
                    className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 p-8"
                >
                    <h3 className="text-lg font-semibold text-gray-900 mb-6">Calculation Details</h3>
                    <div className="space-y-4">
                        <div className="flex justify-between py-3 border-b border-gray-100">
                            <span className="text-gray-600">Total Tax Liability</span>
                            <span className="font-medium text-gray-900">${taxData?.tax_liability?.toLocaleString() || '0.00'}</span>
                        </div>
                        <div className="flex justify-between py-3 border-b border-gray-100">
                            <span className="text-gray-600">Standard Deduction</span>
                            <span className="font-medium text-gray-900">${taxData?.standard_deduction?.toLocaleString() || '0.00'}</span>
                        </div>
                    </div>
                </motion.div>

                {/* Actions */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.5 }}
                    className="flex flex-col sm:flex-row gap-4 justify-center pt-8"
                >
                    <button
                        onClick={handleDownload}
                        className="flex items-center justify-center space-x-2 px-8 py-4 bg-primary text-white rounded-xl font-semibold shadow-lg hover:bg-blue-600 hover:shadow-blue-500/30 transition-all transform hover:-translate-y-0.5"
                    >
                        <Download className="w-5 h-5" />
                        <span>Download Form 1040</span>
                    </button>

                    <button
                        onClick={() => router.push('/')}
                        className="flex items-center justify-center space-x-2 px-8 py-4 bg-white text-gray-700 border border-gray-200 rounded-xl font-semibold hover:bg-gray-50 hover:border-gray-300 transition-all"
                    >
                        <RefreshCw className="w-5 h-5" />
                        <span>Start New Return</span>
                    </button>
                </motion.div>

            </div>
        </div>
    );
}

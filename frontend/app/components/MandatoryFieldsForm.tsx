'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { User, CreditCard, MapPin, Calendar, ArrowRight, FileText } from 'lucide-react';

interface MandatoryFieldsFormProps {
    onSubmit: (data: Record<string, string>) => void;
}

export default function MandatoryFieldsForm({ onSubmit }: MandatoryFieldsFormProps) {
    const [formData, setFormData] = useState({
        full_name: '',
        ssn: '',
        address: '',
        filing_status: 'single',
        tax_year: '2024'
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit(formData);
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-50 p-6">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="w-full max-w-2xl bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl p-8 border border-white/20"
            >
                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-gray-900">Basic Information</h2>
                    <p className="text-gray-500">We need a few details to start your tax return.</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                        {/* Full Name */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                                <User className="w-4 h-4" /> Full Name
                            </label>
                            <input
                                type="text"
                                name="full_name"
                                required
                                value={formData.full_name}
                                onChange={handleChange}
                                className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                                placeholder="John Doe"
                            />
                        </div>

                        {/* SSN */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                                <CreditCard className="w-4 h-4" /> Social Security Number
                            </label>
                            <input
                                type="text"
                                name="ssn"
                                required
                                pattern="\d{3}-?\d{2}-?\d{4}"
                                title="XXX-XX-XXXX"
                                value={formData.ssn}
                                onChange={handleChange}
                                className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                                placeholder="XXX-XX-XXXX"
                            />
                        </div>

                        {/* Address */}
                        <div className="col-span-1 md:col-span-2 space-y-2">
                            <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                                <MapPin className="w-4 h-4" /> Current Address
                            </label>
                            <input
                                type="text"
                                name="address"
                                required
                                value={formData.address}
                                onChange={handleChange}
                                className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all"
                                placeholder="123 Main St, City, State, ZIP"
                            />
                        </div>

                        {/* Filing Status */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                                <FileText className="w-4 h-4" /> Filing Status
                            </label>
                            <div className="relative">
                                <select
                                    name="filing_status"
                                    value={formData.filing_status}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/20 outline-none transition-all appearance-none bg-white"
                                >
                                    <option value="single">Single</option>
                                    <option value="married_filing_jointly">Married Filing Jointly</option>
                                    <option value="head_of_household">Head of Household</option>
                                </select>
                                <div className="absolute right-4 top-1/2 transform -translate-y-1/2 pointer-events-none text-gray-500">
                                    ▼
                                </div>
                            </div>
                        </div>

                        {/* Tax Year */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                                <Calendar className="w-4 h-4" /> Tax Year
                            </label>
                            <input
                                type="text"
                                name="tax_year"
                                value={formData.tax_year}
                                disabled
                                className="w-full px-4 py-3 rounded-lg border border-gray-200 bg-gray-50 text-gray-500 cursor-not-allowed"
                            />
                        </div>
                    </div>

                    <div className="pt-4">
                        <button
                            type="submit"
                            className="w-full py-4 bg-primary text-white rounded-xl font-semibold text-lg shadow-lg hover:bg-blue-600 hover:shadow-blue-500/30 transform hover:-translate-y-0.5 transition-all duration-200 flex items-center justify-center space-x-2"
                        >
                            <span>Continue to Tax Calculation</span>
                            <ArrowRight className="w-5 h-5" />
                        </button>
                    </div>
                </form>
            </motion.div>
        </div>
    );
}

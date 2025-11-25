'use client';

import { useState, useEffect } from 'react';
import { ArrowRight, CheckCircle, Shield, Zap, Brain, DollarSign, Clock, Star, ChevronRight, Menu, X } from 'lucide-react';
import { motion, useScroll, useTransform, useSpring } from 'framer-motion';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function LandingPage() {
  const router = useRouter();
  const { scrollY } = useScroll();
  const y1 = useTransform(scrollY, [0, 500], [0, 200]);
  const y2 = useTransform(scrollY, [0, 500], [0, -150]);
  const opacity = useTransform(scrollY, [0, 300], [1, 0]);
  const scale = useTransform(scrollY, [0, 300], [1, 0.9]);

  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.3
      }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 30 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        type: "spring" as const,
        stiffness: 50
      }
    }
  };

  return (
    <div className="min-h-screen bg-white selection:bg-blue-100 selection:text-blue-900 overflow-hidden font-sans">

      {/* Background Elements */}
      <div className="fixed inset-0 z-0 pointer-events-none bg-[radial-gradient(#e5e7eb_1px,transparent_1px)] [background-size:16px_16px] opacity-[0.4]"></div>
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[800px] h-[800px] bg-blue-100/40 rounded-full mix-blend-multiply filter blur-[120px] animate-blob"></div>
        <div className="absolute top-[-10%] right-[-10%] w-[800px] h-[800px] bg-purple-100/40 rounded-full mix-blend-multiply filter blur-[120px] animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-[-20%] left-[20%] w-[800px] h-[800px] bg-pink-100/40 rounded-full mix-blend-multiply filter blur-[120px] animate-blob animation-delay-4000"></div>
      </div>

      {/* Navbar */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${isScrolled ? 'bg-white/80 backdrop-blur-md border-b border-gray-100 py-4' : 'bg-transparent py-6'}`}>
        <div className="max-w-7xl mx-auto px-6 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center text-white font-bold shadow-lg shadow-blue-500/20">
              <Zap className="w-6 h-6" />
            </div>
            <span className="text-2xl font-bold text-gray-900 tracking-tight">TaxFlow</span>
          </div>

          <div className="hidden md:flex items-center space-x-8">
            <a href="#features" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">Features</a>
            <a href="#how-it-works" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">How it Works</a>
            <a href="#pricing" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">Pricing</a>
          </div>

          <div className="flex items-center space-x-4">
            <button className="hidden md:block text-sm font-medium text-gray-600 hover:text-gray-900">Sign In</button>
            <Link href="/upload">
              <button className="px-6 py-2.5 rounded-full bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 transition-all hover:shadow-lg transform hover:-translate-y-0.5 flex items-center space-x-2">
                <span>Get Started</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative z-10 pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">

            {/* Left Content */}
            <motion.div
              variants={container}
              initial="hidden"
              animate="show"
              className="space-y-8 relative z-20"
            >
              <motion.div variants={item} className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-white border border-blue-100 text-blue-600 text-sm font-semibold shadow-sm backdrop-blur-sm">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                </span>
                <span>AI-Powered Tax Filing for 2025</span>
              </motion.div>

              <motion.h1 variants={item} className="text-6xl lg:text-8xl font-bold tracking-tight text-gray-900 leading-[1.05]">
                Your Taxes. <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 animate-shimmer bg-[length:200%_100%]">
                  Done in Seconds.
                </span>
              </motion.h1>

              <motion.p variants={item} className="text-xl text-gray-600 leading-relaxed max-w-lg">
                Stop overpaying CPAs. Upload your W-2, let our AI handle the math, and get your maximum refund instantly.
              </motion.p>

              <motion.div variants={item} className="flex flex-col sm:flex-row gap-4 pt-4">
                <Link href="/upload" className="w-full sm:w-auto">
                  <button className="w-full sm:w-auto px-8 py-4 rounded-full bg-blue-600 text-white text-lg font-bold hover:bg-blue-700 transition-all shadow-xl shadow-blue-500/30 hover:shadow-blue-500/40 transform hover:-translate-y-1 flex items-center justify-center space-x-2 group">
                    <span>Start Your Return</span>
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  </button>
                </Link>
                <button className="w-full sm:w-auto px-8 py-4 rounded-full bg-white text-gray-700 text-lg font-bold border border-gray-200 hover:bg-gray-50 transition-all flex items-center justify-center space-x-2">
                  <span className="w-6 h-6 rounded-full bg-gray-100 flex items-center justify-center">▶</span>
                  <span>Watch Demo</span>
                </button>
              </motion.div>

              <motion.div variants={item} className="flex items-center gap-6 pt-8 border-t border-gray-100">
                <div className="flex -space-x-3">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="w-10 h-10 rounded-full border-2 border-white bg-gray-200 overflow-hidden">
                      <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${i + 20}`} alt="User" />
                    </div>
                  ))}
                  <div className="w-10 h-10 rounded-full border-2 border-white bg-gray-100 flex items-center justify-center text-xs font-bold text-gray-600">+2k</div>
                </div>
                <div className="text-sm">
                  <div className="flex text-yellow-400 mb-1">
                    {[1, 2, 3, 4, 5].map(i => <Star key={i} className="w-4 h-4 fill-current" />)}
                  </div>
                  <p className="text-gray-500"><span className="font-bold text-gray-900">Trusted by 10,000+</span> filers</p>
                </div>
              </motion.div>
            </motion.div>

            {/* Right Content: 3D Visuals */}
            <motion.div
              style={{ opacity, scale }}
              initial={{ opacity: 0, x: 100 }}
              animate={{ opacity: 1, x: 0 }}
<<<<<<< HEAD
              transition={{ duration: 1, delay: 0.5, type: "spring" as const }}
=======
              transition={{ duration: 1, delay: 0.5, type: "spring" }}
>>>>>>> fa00ea120ed9fb0b332b66b8ce5e0600ac353737
              className="relative h-[600px] hidden lg:block perspective-1000"
            >
              {/* Main Card */}
              <motion.div
                style={{ y: y2, rotateX: 5, rotateY: -5 }}
                className="absolute top-10 right-10 w-[400px] bg-white rounded-[2rem] shadow-2xl border border-gray-100 p-6 z-20"
              >
                <div className="flex justify-between items-center mb-6">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                      <DollarSign className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 font-bold uppercase tracking-wider">Estimated Refund</p>
                      <p className="text-2xl font-bold text-gray-900">$3,482.00</p>
                    </div>
                  </div>
                  <div className="px-3 py-1 bg-green-50 text-green-700 text-xs font-bold rounded-full">Success</div>
                </div>
                <div className="space-y-3">
                  <div className="h-2 bg-gray-100 rounded-full w-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: "100%" }}
                      transition={{ duration: 1.5, delay: 1 }}
                      className="h-full bg-green-500"
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-400">
                    <span>Processing W-2...</span>
                    <span>100%</span>
                  </div>
                </div>
              </motion.div>

              {/* Secondary Card */}
              <motion.div
                style={{ y: y1, rotateX: 5, rotateY: -5 }}
                className="absolute bottom-20 left-0 w-[350px] bg-white/90 backdrop-blur-xl rounded-[2rem] shadow-xl border border-gray-100 p-6 z-30"
              >
                <div className="flex items-center space-x-4 mb-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                    <Brain className="w-6 h-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900">AI Analysis</h3>
                    <p className="text-sm text-gray-500">Found 3 deductions</p>
                  </div>
                </div>
                <div className="space-y-2">
                  {['Student Loan Interest', 'Charitable Contributions', 'Home Office'].map((item, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 2 + (i * 0.2) }}
                      className="flex items-center space-x-2 text-sm text-gray-600 bg-gray-50 p-2 rounded-lg"
                    >
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>{item}</span>
                    </motion.div>
                  ))}
                </div>
              </motion.div>

              {/* Decorative Blobs */}
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-gradient-to-br from-blue-400/20 to-purple-400/20 rounded-full filter blur-3xl animate-pulse z-10"></div>
            </motion.div>
          </div>
        </div>
      </main>

      {/* Social Proof Marquee */}
      <div className="py-12 border-y border-gray-100 bg-gray-50/50 overflow-hidden">
        <div className="max-w-7xl mx-auto px-6 mb-8 text-center">
          <p className="text-sm font-semibold text-gray-500 uppercase tracking-widest">Trusted by employees at</p>
        </div>
        <div className="relative flex overflow-x-hidden group">
          <div className="animate-shimmer flex space-x-16 whitespace-nowrap opacity-40 grayscale hover:grayscale-0 transition-all duration-500">
            {['Google', 'Meta', 'Amazon', 'Netflix', 'Microsoft', 'Apple', 'Tesla', 'Stripe', 'Uber', 'Airbnb'].map((company, i) => (
              <span key={i} className="text-2xl font-bold text-gray-800">{company}</span>
            ))}
            {['Google', 'Meta', 'Amazon', 'Netflix', 'Microsoft', 'Apple', 'Tesla', 'Stripe', 'Uber', 'Airbnb'].map((company, i) => (
              <span key={`dup-${i}`} className="text-2xl font-bold text-gray-800">{company}</span>
            ))}
          </div>
        </div>
      </div>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-32 relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-3xl mx-auto mb-20">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Taxes on Autopilot</h2>
            <p className="text-xl text-gray-600">We've simplified the process down to three clicks. No tax knowledge required.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 relative">
            {/* Connecting Line */}
            <div className="hidden md:block absolute top-12 left-[16%] right-[16%] h-0.5 bg-gradient-to-r from-blue-200 via-purple-200 to-pink-200 z-0"></div>

            {[
              {
                step: "01",
                title: "Upload Docs",
                desc: "Drag & drop your W-2, 1099, or just take a photo.",
                icon: <UploadIcon />
              },
              {
                step: "02",
                title: "AI Analysis",
                desc: "Our engine extracts data and finds every deduction.",
                icon: <BrainIcon />
              },
              {
                step: "03",
                title: "Get Paid",
                desc: "Review your refund and file instantly with the IRS.",
                icon: <MoneyIcon />
              }
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.2 }}
                className="relative z-10 flex flex-col items-center text-center group"
              >
                <div className="w-24 h-24 bg-white rounded-2xl shadow-xl border border-gray-100 flex items-center justify-center mb-8 group-hover:scale-110 transition-transform duration-300 relative">
                  <div className="absolute -top-3 -right-3 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold text-sm border-4 border-white">
                    {item.step}
                  </div>
                  {item.icon}
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-3">{item.title}</h3>
                <p className="text-gray-600 leading-relaxed max-w-xs">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 bg-gray-900 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-blue-900/40 via-gray-900 to-gray-900"></div>
        <div className="max-w-4xl mx-auto px-6 relative z-10 text-center">
          <h2 className="text-5xl font-bold text-white mb-8">Ready to get your refund?</h2>
          <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto">Join thousands of smart filers who switched to TaxFlow this year. It takes less than 2 minutes.</p>
          <Link href="/upload">
            <button className="px-10 py-5 rounded-full bg-white text-gray-900 text-xl font-bold hover:bg-blue-50 transition-all shadow-2xl hover:shadow-white/20 transform hover:-translate-y-1">
              Start Free Now
            </button>
          </Link>
          <p className="mt-6 text-sm text-gray-500">No credit card required • IRS Approved • 256-bit Encryption</p>
        </div>
      </section>

    </div>
  );
}

function UploadIcon() {
  return (
    <svg className="w-10 h-10 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
    </svg>
  );
}

function BrainIcon() {
  return (
    <svg className="w-10 h-10 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  );
}

function MoneyIcon() {
  return (
    <svg className="w-10 h-10 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

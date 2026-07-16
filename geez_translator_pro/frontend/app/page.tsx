'use client';

import { useState } from 'react';
import axios from 'axios';

export default function GezPro() {
  // State Management
  const [activeTab, setActiveTab] = useState<'upload' | 'type'>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [inputText, setInputText] = useState("");
  const [targetLang, setTargetLang] = useState("amh_Ethi"); // amh_Ethi (Amharic) or eng_Latn (English)
  const [results, setResults] = useState({ original: "", translated: "" });
  const [loading, setLoading] = useState(false);

  // Copy to Clipboard Utility
  const copyToClipboard = (text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    alert("Copied to clipboard!");
  };

  // Main Processing Function
  const handleProcess = async () => {
    setLoading(true);
    setResults({ original: "", translated: "" }); // Clear previous results

    try {
      if (activeTab === 'upload') {
        if (!file) {
          alert("Please select an image or PDF file first.");
          setLoading(false);
          return;
        }
        const formData = new FormData();
        formData.append('file', file);
        formData.append('target', targetLang);

        const res = await axios.post('http://127.0.0.1:8000/api/upload/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        setResults({ 
          original: res.data.original_geez || res.data.geez_text, 
          translated: res.data.translated_text 
        });

      } else {
        if (!inputText.trim()) {
          alert("Please type some Ge'ez text.");
          setLoading(false);
          return;
        }

        const res = await axios.post('http://127.0.0.1:8000/api/translate-text/', {
          text: inputText,
          target: targetLang
        });

        setResults({ 
          original: res.data.original_geez, 
          translated: res.data.translated_text 
        });
      }
    } catch (e: any) {
      console.error(e);
      alert("Error: Make sure your Django backend is running and Gemini API key is valid.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f4f7f6] text-gray-900 font-sans">
      
      {/* 1. Header Section */}
      <header className="bg-[#1a237e] text-white py-6 px-6 md:px-20 shadow-2xl flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="bg-yellow-500 p-2 rounded-lg">
             <span className="text-2xl font-bold text-blue-900">ግ</span>
          </div>
          <h1 className="text-2xl font-serif tracking-widest font-bold">
            ግዕዝ <span className="text-yellow-400 font-sans text-xl">TRANSLATE</span>
          </h1>
        </div>

        {/* Language Toggles */}
        <div className="flex bg-blue-800/50 p-1 rounded-full border border-blue-400">
          <button 
            onClick={() => setTargetLang("amh_Ethi")}
            className={`px-6 py-2 rounded-full text-sm font-bold transition-all ${targetLang === 'amh_Ethi' ? 'bg-yellow-500 text-blue-900 shadow-lg' : 'text-blue-100 hover:text-white'}`}
          >
            AMHARIC
          </button>
          <button 
            onClick={() => setTargetLang("eng_Latn")}
            className={`px-6 py-2 rounded-full text-sm font-bold transition-all ${targetLang === 'eng_Latn' ? 'bg-yellow-500 text-blue-900 shadow-lg' : 'text-blue-100 hover:text-white'}`}
          >
            ENGLISH
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto mt-10 p-4 pb-20">
        
        {/* 2. Tab Selection */}
        <div className="flex mb-8 bg-white rounded-xl p-1.5 shadow-md w-fit mx-auto border border-gray-200">
          <button 
            onClick={() => setActiveTab('upload')}
            className={`flex items-center gap-2 px-8 py-3 rounded-lg font-semibold transition-all ${activeTab === 'upload' ? 'bg-[#1a237e] text-white shadow-md' : 'text-gray-500 hover:bg-gray-100'}`}
          >
            📄 Upload Document
          </button>
          <button 
            onClick={() => setActiveTab('type')}
            className={`flex items-center gap-2 px-8 py-3 rounded-lg font-semibold transition-all ${activeTab === 'type' ? 'bg-[#1a237e] text-white shadow-md' : 'text-gray-500 hover:bg-gray-100'}`}
          >
            ⌨️ Type Ge'ez
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          
          {/* 3. Input Section */}
          <div className="bg-white rounded-3xl shadow-xl p-8 border border-gray-100 flex flex-col justify-between">
            <div>
              <h2 className="text-lg font-bold text-gray-700 mb-4 uppercase tracking-wider">
                {activeTab === 'upload' ? "Select Ge'ez Source" : "Enter Ge'ez Text"}
              </h2>
              
              {activeTab === 'upload' ? (
                <div className="relative border-2 border-dashed border-blue-100 rounded-2xl p-16 text-center hover:border-blue-400 hover:bg-blue-50/50 transition-all group">
                  <input 
                    type="file" 
                    accept="image/*,application/pdf"
                    onChange={(e) => setFile(e.target.files?.[0] || null)} 
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  <div className="space-y-4">
                    <div className="text-4xl">📁</div>
                    <p className="text-gray-600 font-medium">
                      {file ? file.name : "Click or Drag Ge'ez Image/PDF"}
                    </p>
                    <p className="text-xs text-gray-400">Supported: JPG, PNG, PDF</p>
                  </div>
                </div>
              ) : (
                <textarea 
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Type Ge'ez here... (e.g., በስመ አብ...)"
                  className="w-full h-72 p-6 border border-gray-200 rounded-2xl focus:ring-4 focus:ring-blue-100 focus:border-blue-400 outline-none text-xl leading-relaxed font-serif bg-gray-50 transition-all"
                />
              )}
            </div>

            <button 
              onClick={handleProcess}
              disabled={loading}
              className={`w-full mt-8 py-5 rounded-2xl font-black text-lg tracking-widest shadow-xl transform transition-all active:scale-95 ${
                loading 
                  ? 'bg-gray-300 cursor-not-allowed text-gray-500' 
                  : 'bg-gradient-to-r from-blue-700 to-blue-900 text-white hover:from-blue-800 hover:to-black'
              }`}
            >
              {loading ? "TRANSLATING..." : "GENERATE TRANSLATION"}
            </button>
          </div>

          {/* 4. Output Section */}
          <div className="flex flex-col gap-6">
            
            {/* Original Ge'ez Text Result */}
            <div className="bg-white rounded-3xl shadow-lg p-6 border border-gray-100">
              <div className="flex justify-between items-center mb-3">
                <span className="text-xs uppercase tracking-[0.2em] text-gray-400 font-black">Original Ge'ez</span>
                {results.original && (
                  <button onClick={() => copyToClipboard(results.original)} className="text-xs text-blue-600 hover:underline font-bold">COPY</button>
                )}
              </div>
              <div className="h-32 overflow-y-auto text-gray-700 font-serif text-lg leading-relaxed whitespace-pre-wrap">
                {results.original || <span className="text-gray-300 italic">Waiting for text extraction...</span>}
              </div>
            </div>

            {/* Translation Result */}
            <div className="bg-gradient-to-br from-[#1a237e] to-[#0d1240] rounded-3xl shadow-2xl p-8 text-white min-h-[400px] flex flex-col relative overflow-hidden">
              {/* Decorative background circle */}
              <div className="absolute -bottom-20 -right-20 w-64 h-64 bg-white/5 rounded-full blur-3xl"></div>
              
              <div className="flex justify-between items-center mb-6 relative z-10">
                <span className="text-xs uppercase tracking-[0.2em] text-blue-200 font-black">
                  {targetLang === 'amh_Ethi' ? "Amharic Translation" : "English Translation"}
                </span>
                {results.translated && (
                  <button 
                    onClick={() => copyToClipboard(results.translated)}
                    className="bg-white/10 hover:bg-white/20 px-4 py-2 rounded-xl text-xs font-bold transition-all border border-white/10"
                  >
                    COPY RESULT
                  </button>
                )}
              </div>

              <div className="relative z-10 text-xl md:text-2xl leading-relaxed font-medium font-serif whitespace-pre-wrap">
                {results.translated || (
                  <div className="space-y-4 opacity-20">
                    <div className="h-4 bg-white rounded w-3/4"></div>
                    <div className="h-4 bg-white rounded w-full"></div>
                    <div className="h-4 bg-white rounded w-5/6"></div>
                  </div>
                )}
              </div>
            </div>
          </div>

        </div>
      </main>

      {/* 5. Footer */}
      <footer className="text-center py-10 text-gray-400 text-sm">
        <p>© {new Date().getFullYear()} Ge'ez Translator Pro • Powered by Gemini AI</p>
      </footer>
    </div>
  );
}
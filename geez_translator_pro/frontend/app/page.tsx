'use client';

import { useState } from 'react';
import axios from 'axios';

export default function GezPro() {
  const [activeTab, setActiveTab] = useState<'upload' | 'type'>('upload');
  const [file, setFile] = useState<File | null>(null);
  const [inputText, setInputText] = useState("");
  const [targetLang, setTargetLang] = useState("amh_Ethi"); // amh_Ethi or eng_Latn
  const [results, setResults] = useState({ original: "", translated: "" });
  const [loading, setLoading] = useState(false);

  const handleProcess = async () => {
    setLoading(true);
    try {
      if (activeTab === 'upload') {
        if (!file) return alert("Select a file");
        const formData = new FormData();
        formData.append('file', file);
        formData.append('target', targetLang);
        const res = await axios.post('http://127.0.0.1:8000/api/upload/', formData);
        setResults({ original: res.data.original_geez, translated: res.data.translated_text });
      } else {
        if (!inputText) return alert("Enter text");
        const res = await axios.post('http://127.0.0.1:8000/api/translate-text/', {
          text: inputText,
          target: targetLang
        });
        setResults({ original: res.data.original_geez, translated: res.data.translated_text });
      }
    } catch (e) {
      alert("Error: Make sure the backend is running");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f8f9fa] text-gray-900 font-sans">
      {/* Header */}
      <header className="bg-[#1a237e] text-white py-6 px-10 shadow-lg flex justify-between items-center">
        <h1 className="text-2xl font-serif tracking-widest font-bold">ግዕዝ <span className="text-yellow-400">TRANSLATE</span></h1>
        <div className="flex gap-4">
          <button 
            onClick={() => setTargetLang("amh_Ethi")}
            className={`px-4 py-1 rounded-full border ${targetLang === 'amh_Ethi' ? 'bg-yellow-400 text-blue-900' : 'border-white'}`}
          >Amharic</button>
          <button 
            onClick={() => setTargetLang("eng_Latn")}
            className={`px-4 py-1 rounded-full border ${targetLang === 'eng_Latn' ? 'bg-yellow-400 text-blue-900' : 'border-white'}`}
          >English</button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto mt-10 p-4">
        {/* Tab Selection */}
        <div className="flex mb-6 bg-white rounded-lg p-1 shadow-sm w-fit mx-auto border">
          <button 
            onClick={() => setActiveTab('upload')}
            className={`px-6 py-2 rounded-md transition ${activeTab === 'upload' ? 'bg-[#1a237e] text-white shadow' : 'text-gray-500'}`}
          >Document Upload</button>
          <button 
            onClick={() => setActiveTab('type')}
            className={`px-6 py-2 rounded-md transition ${activeTab === 'type' ? 'bg-[#1a237e] text-white shadow' : 'text-gray-500'}`}
          >Type Ge'ez Text</button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Input Section */}
          <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
               Input Source
            </h2>
            
            {activeTab === 'upload' ? (
              <div className="border-2 border-dashed border-blue-200 rounded-xl p-12 text-center hover:bg-blue-50 transition cursor-pointer">
                <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-blue-100 file:text-blue-700 hover:file:bg-blue-200"/>
                <p className="mt-4 text-gray-400 text-sm italic">Upload Image or PDF of Ge'ez Manuscript</p>
              </div>
            ) : (
              <textarea 
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Type Ge'ez text here... (e.g. በስመ አብ ወወልድ...)"
                className="w-full h-64 p-4 border rounded-xl focus:ring-2 focus:ring-blue-500 outline-none text-lg leading-relaxed font-serif"
              />
            )}

            <button 
              onClick={handleProcess}
              disabled={loading}
              className="w-full mt-6 bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-4 rounded-xl shadow-lg transform active:scale-95 transition-all"
            >
              {loading ? "Translating Divine Language..." : "START TRANSLATION"}
            </button>
          </div>

          {/* Output Section */}
          <div className="space-y-6">
            <div className="bg-white rounded-2xl shadow-xl p-6 border border-gray-100">
              <span className="text-xs uppercase tracking-widest text-gray-400 font-bold">Extracted Script</span>
              <div className="mt-2 h-32 overflow-y-auto text-gray-800 font-serif text-lg leading-relaxed">
                {results.original || "Ge'ez text will appear here..."}
              </div>
            </div>

            <div className="bg-[#1a237e] rounded-2xl shadow-2xl p-6 text-white min-h-[300px]">
              <span className="text-xs uppercase tracking-widest text-blue-200 font-bold">Translated Revelation</span>
              <div className="mt-4 text-xl leading-relaxed font-medium">
                {results.translated || "Waiting for translation..."}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
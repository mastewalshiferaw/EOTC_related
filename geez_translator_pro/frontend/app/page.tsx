'use client';
import { useState, useRef, ClipboardEvent, ChangeEvent } from 'react';
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export default function MasGeezTranslator() {
  // Light mode as default
  const [isDark, setIsDark] = useState(false);
  const [inputText, setInputText] = useState("");
  const [outputText, setOutputText] = useState("");
  const [sourceLang, setSourceLang] = useState("Ge'ez");
  const [targetLang, setTargetLang] = useState("Amharic");
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("Ready");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processImageFile = async (file: File) => {
    setLoading(true);
    setStatusMessage("Running Hybrid OCR...");
    const formData = new FormData();
    formData.append('file', file);
    formData.append('lang', sourceLang);

    try {
      const res = await axios.post(`${API_BASE}/api/ocr-only/`, formData);
      const extracted = res.data.text || "";
      setInputText((prev) => (prev ? prev + "\n" + extracted : extracted));
      setStatusMessage("Text extracted successfully");
    } catch (err: any) {
      console.error(err);
      setStatusMessage("OCR Failed. Please try another image.");
    } finally {
      setLoading(false);
    }
  };

  const handlePaste = async (e: ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf("image") !== -1) {
        const file = items[i].getAsFile();
        if (file) {
          e.preventDefault();
          await processImageFile(file);
        }
      }
    }
  };

  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await processImageFile(file);
    }
  };

  const handleTranslate = async () => {
    if (!inputText.trim()) return;
    setLoading(true);
    setStatusMessage("Translating...");
    try {
      const res = await axios.post(`${API_BASE}/api/translate-flexible/`, {
        text: inputText,
        source: sourceLang,
        target: targetLang,
      });
      setOutputText(res.data.translation || "");
      setStatusMessage("Done");
    } catch (err: any) {
      console.error(err);
      setStatusMessage("Translation Failed");
    } finally {
      setLoading(false);
    }
  };

  const swapLanguages = () => {
    const currentSource = sourceLang;
    setSourceLang(targetLang);
    setTargetLang(currentSource);
    if (outputText) {
      setInputText(outputText);
      setOutputText("");
    }
  };

  const pageTheme = isDark ? 'bg-[#0b0d11] text-zinc-100' : 'bg-[#f8f9fa] text-zinc-900';
  const navBorder = isDark ? 'border-zinc-800' : 'border-zinc-200';
  const selectStyle = isDark 
    ? 'bg-zinc-900 border-zinc-700 text-zinc-100' 
    : 'bg-white border-zinc-300 text-zinc-800 shadow-sm';
  const optionStyle = isDark ? 'bg-zinc-900 text-zinc-100' : 'bg-white text-zinc-900';

  return (
    <div className={`min-h-screen transition-colors duration-300 font-sans ${pageTheme}`}>
      {/* Top Navbar */}
      <nav className={`max-w-5xl mx-auto p-6 flex justify-between items-center border-b ${navBorder}`}>
        <div className="flex items-center gap-2.5">
          <span className={`font-black text-2xl tracking-tighter uppercase italic ${isDark ? 'text-white' : 'text-zinc-900'}`}>
            MAS_GEEZ
          </span>
          <span className={`text-[10px] border px-2 py-0.5 rounded font-bold tracking-widest uppercase ${isDark ? 'border-zinc-700 text-zinc-400 bg-zinc-900' : 'border-zinc-300 text-zinc-600 bg-zinc-100'}`}>
            Translator Pro
          </span>
        </div>

        {/* Theme Toggle Button */}
        <button 
          onClick={() => setIsDark(!isDark)} 
          className={`flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full border transition ${isDark ? 'border-zinc-700 bg-zinc-800 text-zinc-200 hover:bg-zinc-700' : 'border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-100 shadow-sm'}`}
        >
          <span>{isDark ? '☀️ Light' : '🌙 Dark'}</span>
        </button>
      </nav>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto p-6 lg:p-12">
        {/* Language Selectors */}
        <div className="flex items-center gap-3 mb-6">
          <select 
            value={sourceLang} 
            onChange={(e) => setSourceLang(e.target.value)} 
            className={`border rounded-xl px-3.5 py-2 outline-none font-semibold text-xs tracking-wide cursor-pointer transition ${selectStyle}`}
          >
            <option value="Ge'ez" className={optionStyle}>Ge'ez (ግዕዝ)</option>
            <option value="Amharic" className={optionStyle}>Amharic (አማርኛ)</option>
            <option value="English" className={optionStyle}>English</option>
          </select>

          <button 
            onClick={swapLanguages} 
            title="Swap languages" 
            className={`p-2 rounded-xl border text-sm font-bold transition hover:scale-105 active:scale-95 ${isDark ? 'border-zinc-700 bg-zinc-900 text-zinc-300 hover:bg-zinc-800' : 'border-zinc-300 bg-white text-zinc-700 hover:bg-zinc-100 shadow-sm'}`}
          >
            ⇄
          </button>

          <select 
            value={targetLang} 
            onChange={(e) => setTargetLang(e.target.value)} 
            className={`border rounded-xl px-3.5 py-2 outline-none font-semibold text-xs tracking-wide cursor-pointer transition ${selectStyle}`}
          >
            <option value="Amharic" className={optionStyle}>Amharic (አማርኛ)</option>
            <option value="English" className={optionStyle}>English</option>
            <option value="Ge'ez" className={optionStyle}>Ge'ez (ግዕዝ)</option>
          </select>
        </div>

        {/* Translation Split Cards */}
        <div className={`grid grid-cols-1 lg:grid-cols-2 gap-px rounded-3xl overflow-hidden border shadow-2xl transition-colors ${isDark ? 'bg-zinc-800/80 border-zinc-800' : 'bg-zinc-300/80 border-zinc-200'}`}>
          {/* Left: Input / OCR Area */}
          <div className={`p-8 min-h-[500px] flex flex-col transition-colors ${isDark ? 'bg-[#12141a]' : 'bg-white'}`}>
            <textarea 
              onPaste={handlePaste}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className={`flex-1 bg-transparent border-none outline-none resize-none text-xl font-serif leading-relaxed transition ${isDark ? 'text-zinc-100 placeholder:text-zinc-500' : 'text-zinc-900 placeholder:text-zinc-400'}`}
              placeholder="Type, paste text, or paste image (Ctrl+V)..."
            />
            
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              accept="image/*" 
              className="hidden" 
            />

            <div className={`mt-6 pt-4 flex flex-wrap justify-between items-center gap-4 border-t ${isDark ? 'border-zinc-800/80' : 'border-zinc-100'}`}>
              <div className="flex items-center gap-3">
                <button 
                  type="button" 
                  onClick={() => fileInputRef.current?.click()}
                  className={`text-xs font-semibold px-3.5 py-2 rounded-xl border transition flex items-center gap-2 ${isDark ? 'border-zinc-700 bg-zinc-800/70 text-zinc-300 hover:bg-zinc-700 hover:text-white' : 'border-zinc-300 bg-zinc-50 text-zinc-700 hover:bg-zinc-100 hover:text-black shadow-sm'}`}
                >
                  <span>📷</span> Upload Image
                </button>
                <p className={`text-xs font-medium uppercase tracking-wider ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>
                  {loading ? "Processing..." : statusMessage}
                </p>
              </div>

              <button 
                onClick={handleTranslate} 
                disabled={loading || !inputText.trim()}
                className={`px-8 py-2.5 rounded-full text-xs font-bold uppercase tracking-widest transition disabled:opacity-40 disabled:cursor-not-allowed ${isDark ? 'bg-zinc-100 text-zinc-900 hover:bg-white shadow-md' : 'bg-zinc-900 text-white hover:bg-black shadow-sm'}`}
              >
                {loading ? "Translating..." : "Translate"}
              </button>
            </div>
          </div>

          {/* Right: Output Translation Area */}
          <div className={`p-8 min-h-[500px] flex flex-col transition-colors ${isDark ? 'bg-[#0d0f14]' : 'bg-[#fafafa]'}`}>
            <div className={`flex-1 text-xl font-serif leading-relaxed overflow-y-auto whitespace-pre-wrap transition ${isDark ? 'text-zinc-100' : 'text-zinc-900'}`}>
              {outputText ? (
                outputText
              ) : (
                <span className={`italic text-lg ${isDark ? 'text-zinc-600' : 'text-zinc-400'}`}>
                  Translation will appear here...
                </span>
              )}
            </div>

            {outputText && (
              <div className={`mt-6 pt-4 flex justify-end border-t ${isDark ? 'border-zinc-800/80' : 'border-zinc-200/80'}`}>
                <button 
                  onClick={() => { 
                    navigator.clipboard.writeText(outputText); 
                    setStatusMessage("Copied to clipboard!"); 
                  }} 
                  className={`text-xs font-semibold px-3 py-1.5 rounded-lg border transition ${isDark ? 'border-zinc-700 bg-zinc-800/60 text-zinc-300 hover:text-white hover:bg-zinc-700' : 'border-zinc-300 bg-white text-zinc-700 hover:text-black hover:bg-zinc-100 shadow-sm'}`}
                >
                  📋 Copy Result
                </button>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className={`py-6 w-full text-center text-[10px] uppercase tracking-[0.4em] ${isDark ? 'text-zinc-600' : 'text-zinc-400'}`}>
        MAS_GEEZ Digital Philology
      </footer>
    </div>
  );
}

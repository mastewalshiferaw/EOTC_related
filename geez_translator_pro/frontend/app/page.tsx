'use client';
import { useState, useRef, ClipboardEvent, ChangeEvent } from 'react';
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export default function MasGeezTranslator() {
  const [isDark, setIsDark] = useState(true);
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

  const theme = isDark ? 'bg-[#0a0a0a] text-zinc-400' : 'bg-zinc-50 text-zinc-600';

  return (
    <div className={`min-h-screen transition-colors duration-500 font-sans ${theme}`}>
      <nav className="max-w-5xl mx-auto p-6 flex justify-between items-center border-b border-zinc-900/10">
        <div className="flex items-center gap-2">
          <span className={`font-black text-2xl tracking-tighter uppercase italic ${isDark ? 'text-white' : 'text-black'}`}>MAS_GEEZ</span>
          <span className="text-[9px] border border-zinc-800 px-2 py-0.5 rounded text-zinc-500 uppercase font-bold tracking-widest">Translator Pro</span>
        </div>
        <button onClick={() => setIsDark(!isDark)} className="text-[10px] font-bold uppercase tracking-widest opacity-40 hover:opacity-100 transition">
          {isDark ? 'Light' : 'Dark'}
        </button>
      </nav>

      <main className="max-w-5xl mx-auto p-6 lg:p-12">
        <div className="flex items-center gap-3 mb-8">
          <select value={sourceLang} onChange={(e) => setSourceLang(e.target.value)} className="bg-transparent border border-zinc-800/40 rounded-lg px-3 py-1 outline-none font-bold text-xs uppercase tracking-widest cursor-pointer">
            <option value="Ge'ez">Ge'ez (ግዕዝ)</option>
            <option value="Amharic">Amharic (አማርኛ)</option>
            <option value="English">English</option>
          </select>

          <button onClick={swapLanguages} title="Swap languages" className="px-2 py-1 rounded border border-zinc-800/30 text-xs font-bold opacity-50 hover:opacity-100 transition">
            ⇄
          </button>

          <select value={targetLang} onChange={(e) => setTargetLang(e.target.value)} className="bg-transparent border border-zinc-800/40 rounded-lg px-3 py-1 outline-none font-bold text-xs uppercase tracking-widest cursor-pointer">
            <option value="Amharic">Amharic (አማርኛ)</option>
            <option value="English">English</option>
            <option value="Ge'ez">Ge'ez (ግዕዝ)</option>
          </select>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-px bg-zinc-800/20 border border-zinc-800/20 rounded-3xl overflow-hidden shadow-2xl">
          <div className={`p-8 min-h-[480px] flex flex-col ${isDark ? 'bg-zinc-900/40' : 'bg-white'}`}>
            <textarea 
              onPaste={handlePaste}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="flex-1 bg-transparent border-none outline-none resize-none text-xl font-serif leading-relaxed placeholder:opacity-20"
              placeholder="Type, paste text, or paste image (Ctrl+V)..."
            />
            
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              accept="image/*" 
              className="hidden" 
            />

            <div className="mt-6 flex flex-wrap justify-between items-center gap-4">
              <div className="flex items-center gap-3">
                <button 
                  type="button" 
                  onClick={() => fileInputRef.current?.click()}
                  className="text-[10px] font-bold uppercase tracking-widest border border-zinc-800/50 px-3 py-1.5 rounded-lg opacity-60 hover:opacity-100 transition flex items-center gap-1.5"
                >
                  <span>📷</span> Upload Image
                </button>
                <p className="text-[10px] uppercase tracking-widest opacity-40 font-bold">{loading ? "Processing..." : statusMessage}</p>
              </div>

              <button 
                onClick={handleTranslate} 
                disabled={loading || !inputText.trim()}
                className={`px-10 py-3 rounded-full text-[10px] font-black uppercase tracking-[0.2em] transition disabled:opacity-30 ${isDark ? 'bg-white text-black hover:bg-zinc-200' : 'bg-black text-white hover:bg-zinc-800'}`}
              >
                {loading ? "Translating..." : "Translate"}
              </button>
            </div>
          </div>

          <div className={`p-8 min-h-[480px] flex flex-col ${isDark ? 'bg-[#050505]' : 'bg-zinc-100/50'}`}>
            <div className="flex-1 text-xl font-serif leading-relaxed overflow-y-auto whitespace-pre-wrap selection:bg-zinc-500">
              {outputText || <span className="opacity-10 italic">Translation will appear here...</span>}
            </div>
            {outputText && (
              <button 
                onClick={() => { navigator.clipboard.writeText(outputText); setStatusMessage("Copied to clipboard!"); }} 
                className="self-end text-[10px] font-bold uppercase tracking-widest opacity-40 hover:opacity-100 transition mt-4"
              >
                Copy Result
              </button>
            )}
          </div>
        </div>
      </main>

      <footer className="fixed bottom-6 w-full text-center text-[9px] uppercase tracking-[0.5em] opacity-15">
        MAS_GEEZ Digital Philology
      </footer>
    </div>
  );
}

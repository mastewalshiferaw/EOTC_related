'use client';
import { useState, ClipboardEvent } from 'react';
import axios from 'axios';

export default function GezStudio() {
  const [isDark, setIsDark] = useState(true);
  const [inputText, setInputText] = useState("");
  const [amhText, setAmhText] = useState("");
  const [engText, setEngText] = useState("");
  const [loading, setLoading] = useState(false);

  // 1. Paste Image Logic
  const handlePaste = async (e: ClipboardEvent) => {
    const items = e.clipboardData.items;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf("image") !== -1) {
        const file = items[i].getAsFile();
        if (!file) return;
        setLoading(true);
        const formData = new FormData();
        formData.append('file', file);
        try {
          const res = await axios.post('http://127.0.0.1:8000/api/ocr-only/', formData);
          setInputText((prev) => prev + " " + res.data.text);
        } catch (err) {
          alert("OCR Failed. Check Google Cloud JSON key.");
        } finally { setLoading(false); }
      }
    }
  };

  // 2. Dual Translation Logic
  const handleTranslate = async () => {
    if (!inputText) return;
    setLoading(true);
    try {
      const resAmh = await axios.post('http://127.0.0.1:8000/api/translate-flexible/', {
        text: inputText, source: "Ge'ez", target: "Amharic"
      });
      const resEng = await axios.post('http://127.0.0.1:8000/api/translate-flexible/', {
        text: inputText, source: "Ge'ez", target: "English"
      });
      setAmhText(resAmh.data.translation);
      setEngText(resEng.data.translation);
    } catch (err) {
      alert("AI Error. Check Backend.");
    } finally { setLoading(false); }
  };

  const theme = isDark ? 'bg-zinc-950 text-zinc-300 border-zinc-800' : 'bg-zinc-50 text-zinc-800 border-zinc-200';

  return (
    <div className={`min-h-screen p-4 md:p-12 transition-all duration-700 ${theme}`}>
      <nav className="max-w-5xl mx-auto flex justify-between items-center mb-12">
        <h1 className="font-serif italic text-2xl tracking-tighter font-black uppercase">Gez.AI</h1>
        <button onClick={() => setIsDark(!isDark)} className="text-[10px] font-bold uppercase tracking-widest border px-3 py-1 rounded-full opacity-50 hover:opacity-100">
          {isDark ? 'Light Mode' : 'Dark Mode'}
        </button>
      </nav>

      <main className="max-w-5xl mx-auto space-y-6">
        {/* Unified Input */}
        <div className={`rounded-3xl border p-2 transition-all ${isDark ? 'bg-zinc-900' : 'bg-white shadow-xl'}`}>
          <textarea 
            onPaste={handlePaste}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            className="w-full h-48 p-6 bg-transparent outline-none resize-none text-2xl font-serif placeholder:opacity-20"
            placeholder="Type or Paste Image..."
          />
          <div className="flex justify-between items-center p-4">
            <span className="text-[9px] uppercase tracking-widest opacity-30 italic">{loading ? 'AI Processing...' : 'Ready'}</span>
            <button onClick={handleTranslate} className={`px-10 py-3 rounded-2xl font-bold uppercase text-xs tracking-widest transition-all ${isDark ? 'bg-white text-black hover:bg-zinc-200' : 'bg-black text-white hover:bg-zinc-800'}`}>
              Translate
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className={`p-8 rounded-3xl border ${isDark ? 'bg-zinc-900/50' : 'bg-white shadow-lg'}`}>
            <label className="text-[9px] font-black uppercase opacity-20 block mb-4">Amharic</label>
            <p className="text-xl font-serif leading-relaxed">{amhText || '...'}</p>
          </div>
          <div className={`p-8 rounded-3xl border ${isDark ? 'bg-zinc-900/50' : 'bg-white shadow-lg'}`}>
            <label className="text-[9px] font-black uppercase opacity-20 block mb-4">English</label>
            <p className="text-lg leading-relaxed italic opacity-80">{engText || '...'}</p>
          </div>
        </div>
      </main>
    </div>
  );
}
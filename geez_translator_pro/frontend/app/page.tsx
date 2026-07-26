'use client';
import { useState, ClipboardEvent } from 'react';
import axios from 'axios';

export default function MasGeezTranslator() {
  const [isDark, setIsDark] = useState(true);
  const [inputText, setInputText] = useState("");
  const [outputText, setOutputText] = useState("");
  const [sourceLang, setSourceLang] = useState("Ge'ez");
  const [targetLang, setTargetLang] = useState("Amharic");
  const [loading, setLoading] = useState(false);

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
          alert("OCR Failed.");
        } finally { setLoading(false); }
      }
    }
  };

  const handleTranslate = async () => {
    if (!inputText) return;
    setLoading(true);
    try {
      const res = await axios.post('http://127.0.0.1:8000/api/translate-flexible/', {
        text: inputText,
        source: sourceLang,
        target: targetLang
      });
      setOutputText(res.data.translation);
    } catch (err) {
      alert("Translation Failed");
    } finally { setLoading(false); }
  };

  const theme = isDark ? 'bg-[#0a0a0a] text-zinc-400' : 'bg-zinc-50 text-zinc-600';

  return (
    <div className={`min-h-screen transition-colors duration-500 font-sans ${theme}`}>
      <nav className="max-w-5xl mx-auto p-6 flex justify-between items-center border-b border-zinc-900/10">
        <div className="flex items-center gap-2">
            <span className={`font-black text-2xl tracking-tighter uppercase italic ${isDark ? 'text-white' : 'text-black'}`}>MAS_GEEZ</span>
            <span className="text-[9px] border border-zinc-800 px-2 py-0.5 rounded text-zinc-500 uppercase font-bold tracking-widest">Translator</span>
        </div>
        <button onClick={() => setIsDark(!isDark)} className="text-[10px] font-bold uppercase tracking-widest opacity-30 hover:opacity-100">
          {isDark ? 'Light' : 'Dark'}
        </button>
      </nav>

      <main className="max-w-5xl mx-auto p-6 lg:p-12">
        <div className="flex items-center gap-4 mb-8">
          <select value={sourceLang} onChange={(e) => setSourceLang(e.target.value)} className="bg-transparent border-none outline-none font-bold text-xs uppercase tracking-widest cursor-pointer">
            <option value="Ge'ez">Ge'ez</option>
            <option value="Amharic">Amharic</option>
            <option value="English">English</option>
          </select>
          <span className="opacity-20 text-xs">→</span>
          <select value={targetLang} onChange={(e) => setTargetLang(e.target.value)} className="bg-transparent border-none outline-none font-bold text-xs uppercase tracking-widest cursor-pointer">
            <option value="Amharic">Amharic</option>
            <option value="English">English</option>
            <option value="Ge'ez">Ge'ez</option>
          </select>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-px bg-zinc-800/20 border border-zinc-800/20 rounded-3xl overflow-hidden shadow-2xl">
          <div className={`p-8 min-h-[450px] flex flex-col ${isDark ? 'bg-zinc-900/40' : 'bg-white'}`}>
            <textarea 
              onPaste={handlePaste}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="flex-1 bg-transparent border-none outline-none resize-none text-2xl font-serif leading-relaxed placeholder:opacity-20"
              placeholder="Paste image or type..."
            />
            <div className="mt-6 flex justify-between items-center">
                <p className="text-[9px] uppercase tracking-widest opacity-20 font-bold">{loading ? "Analyzing..." : "Ready"}</p>
                <button onClick={handleTranslate} className={`px-10 py-3 rounded-full text-[10px] font-black uppercase tracking-[0.2em] transition ${isDark ? 'bg-white text-black hover:bg-zinc-200' : 'bg-black text-white hover:bg-zinc-800'}`}>
                  Translate
                </button>
            </div>
          </div>

          <div className={`p-8 min-h-[450px] flex flex-col ${isDark ? 'bg-[#050505]' : 'bg-zinc-100/50'}`}>
             <div className="flex-1 text-2xl font-serif leading-relaxed overflow-y-auto whitespace-pre-wrap selection:bg-zinc-500">
                {outputText || <span className="opacity-5 italic">Meaning...</span>}
             </div>
             <button onClick={() => {navigator.clipboard.writeText(outputText); alert("Copied!")}} className="self-end text-[9px] font-bold uppercase tracking-widest opacity-20 hover:opacity-100">
               Copy Result
             </button>
          </div>
        </div>
      </main>

      <footer className="fixed bottom-6 w-full text-center text-[9px] uppercase tracking-[0.5em] opacity-10">
        MAS_GEEZ Digital Philology
      </footer>
    </div>
  );
}
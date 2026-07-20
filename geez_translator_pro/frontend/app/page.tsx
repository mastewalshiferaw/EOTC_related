'use client';
import { useState, ClipboardEvent } from 'react';
import axios from 'axios';

export default function GezStudio() {
  const [isDark, setIsDark] = useState(true);
  const [inputText, setInputText] = useState("");
  const [outputText, setOutputText] = useState("");
  const [sourceLang, setSourceLang] = useState("Ge'ez");
  const [targetLang, setTargetLang] = useState("Amharic");
  const [loading, setLoading] = useState(false);

  // 1. Paste Image -> OCR -> Populate Text Area (No auto-translate)
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
  
  // Check if the backend returned an error string instead of text
  if (res.data.text.startsWith("Google Error") || res.data.text.startsWith("System Error")) {
      alert(res.data.text);
  } else {
      setInputText((prev) => prev + " " + res.data.text);
  }
} catch (err) {
  alert("Connection to Backend failed. Check if Django is running.");
}
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

  return (
    <div className={`min-h-screen transition-colors duration-500 font-sans ${isDark ? 'bg-[#0a0a0a] text-zinc-400' : 'bg-white text-zinc-600'}`}>
      
      {/* Navigation */}
      <nav className="max-w-5xl mx-auto p-6 flex justify-between items-center border-b border-zinc-900/10">
        <div className="flex items-center gap-2">
            <span className={`font-black text-xl tracking-tighter ${isDark ? 'text-white' : 'text-black'}`}>GEZ.AI</span>
            <span className="text-[10px] bg-zinc-800 px-2 py-0.5 rounded text-zinc-400 uppercase">Studio</span>
        </div>
        <button onClick={() => setIsDark(!isDark)} className="text-[10px] font-bold uppercase tracking-widest opacity-50 hover:opacity-100">
          {isDark ? 'Light' : 'Dark'}
        </button>
      </nav>

      <main className="max-w-5xl mx-auto p-6 lg:p-12">
        
        {/* Language Selection Bar */}
        <div className="flex items-center gap-4 mb-6">
          <select 
            value={sourceLang} 
            onChange={(e) => setSourceLang(e.target.value)}
            className={`bg-transparent border-none outline-none font-bold text-sm ${isDark ? 'text-zinc-200' : 'text-black'}`}
          >
            <option value="Ge'ez">Ge'ez</option>
            <option value="Amharic">Amharic</option>
            <option value="English">English</option>
          </select>

          <span className="opacity-20 text-xs">→</span>

          <select 
            value={targetLang} 
            onChange={(e) => setTargetLang(e.target.value)}
            className={`bg-transparent border-none outline-none font-bold text-sm ${isDark ? 'text-zinc-200' : 'text-black'}`}
          >
            <option value="Amharic">Amharic</option>
            <option value="English">English</option>
            <option value="Ge'ez">Ge'ez</option>
          </select>
        </div>

        {/* Main Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-px bg-zinc-900/20 border border-zinc-900/20 rounded-2xl overflow-hidden shadow-2xl">
          
          {/* Input Area */}
          <div className={`p-8 min-h-[400px] flex flex-col ${isDark ? 'bg-zinc-900/50' : 'bg-white border-r'}`}>
            <textarea 
              onPaste={handlePaste}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="flex-1 bg-transparent border-none outline-none resize-none text-2xl font-serif leading-relaxed placeholder:text-zinc-800"
              placeholder="Paste image or type text here..."
            />
            <div className="mt-4 flex justify-between items-center">
                <p className="text-[9px] uppercase tracking-widest opacity-30 italic">
                  {loading ? "System processing..." : "Ready"}
                </p>
                <button 
                  onClick={handleTranslate}
                  className={`px-8 py-3 rounded-full text-xs font-black uppercase tracking-widest transition ${isDark ? 'bg-white text-black hover:bg-zinc-200' : 'bg-black text-white hover:bg-zinc-800'}`}
                >
                  Translate
                </button>
            </div>
          </div>

          {/* Output Area */}
          <div className={`p-8 min-h-[400px] flex flex-col ${isDark ? 'bg-black' : 'bg-zinc-50'}`}>
             <div className="flex-1 text-2xl font-serif leading-relaxed overflow-y-auto whitespace-pre-wrap">
                {outputText || <span className="opacity-10 italic">Result will appear here...</span>}
             </div>
             <button 
                onClick={() => {navigator.clipboard.writeText(outputText); alert("Copied!")}}
                className="self-end text-[9px] font-bold uppercase tracking-widest opacity-30 hover:opacity-100"
             >
               Copy Text
             </button>
          </div>

        </div>

        <p className="mt-8 text-center text-[9px] uppercase tracking-[0.4em] opacity-20">
          Classical Ethiopic Scholarly Workspace
        </p>
      </main>
    </div>
  );
}
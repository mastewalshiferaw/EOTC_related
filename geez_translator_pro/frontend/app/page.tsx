'use client';

import { useState } from 'react';
import axios from 'axios';

export default function GezTranslator() {
  const [file, setFile] = useState<File | null>(null);
  const [geezText, setGeezText] = useState("");
  const [translatedText, setTranslatedText] = useState("");
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) {
      alert("Please select a file first!");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      // Note: We point to our Django API URL
      const response = await axios.post('http://127.0.0.1:8000/api/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setGeezText(response.data.original_geez);
      setTranslatedText(response.data.translated_text);
    } catch (error) {
      console.error("Error uploading document:", error);
      alert("Something went wrong with the translation.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-md p-6">
        <h1 className="text-3xl font-bold text-center mb-8 text-blue-900">Ge'ez Document Translator</h1>

        <div className="flex flex-col items-center border-2 border-dashed border-gray-300 p-10 rounded-lg bg-gray-50">
          <input 
            type="file" 
            className="mb-4"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <button 
            onClick={handleUpload}
            disabled={loading}
            className={`px-8 py-3 rounded-full text-white font-semibold ${loading ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700 transition'}`}
          >
            {loading ? "Processing (OCR & AI)..." : "Translate Now"}
          </button>
        </div>

        {/* Results Area */}
        <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h2 className="font-bold mb-2">Extracted Ge'ez</h2>
            <div className="p-4 bg-gray-50 border rounded-lg h-64 overflow-y-auto whitespace-pre-wrap">
              {geezText || "No text extracted yet."}
            </div>
          </div>
          <div>
            <h2 className="font-bold mb-2">Translation (Amharic/English)</h2>
            <div className="p-4 bg-blue-50 border border-blue-100 rounded-lg h-64 overflow-y-auto whitespace-pre-wrap text-blue-900 font-medium">
              {translatedText || "Translation will appear here..."}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
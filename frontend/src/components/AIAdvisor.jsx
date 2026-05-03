import { useState } from 'react'
import { advisorApi } from '../services/api'

export default function AIAdvisor({ moleculeId, moleculeName }) {
  const [open, setOpen] = useState(false)
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [chatHistory, setChatHistory] = useState([])

  async function loadAnalysis() {
    if (!moleculeId) return
    setLoading(true)
    try {
      const res = await advisorApi.analyze(moleculeId)
      setAnalysis(res.data)
    } catch (e) { console.error(e) }
    setLoading(false)
  }

  async function askQuestion() {
    if (!question.trim() || !moleculeId) return
    const q = question
    setQuestion('')
    setChatHistory(prev => [...prev, { role: 'user', text: q }])
    setLoading(true)
    try {
      const res = await advisorApi.analyze(moleculeId, q)
      setChatHistory(prev => [...prev, { role: 'ai', text: res.data.answer || 'Sem resposta disponivel.' }])
      if (!analysis) setAnalysis(res.data)
    } catch (e) {
      setChatHistory(prev => [...prev, { role: 'ai', text: 'Erro ao consultar IA.' }])
    }
    setLoading(false)
  }

  if (!moleculeId) return null

  return (
    <>
      {/* Botao flutuante */}
      <button onClick={() => { setOpen(!open); if (!analysis) loadAnalysis() }}
        className="fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full bg-gradient-to-br from-accent-cyan to-accent-teal text-navy-950 shadow-2xl flex items-center justify-center hover:scale-110 transition-transform"
        title="Consultor IA">
        <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
      </button>

      {/* Painel */}
      {open && (
        <div className="fixed bottom-24 right-6 z-40 w-96 max-h-[600px] bg-navy-800 rounded-2xl border border-navy-600/50 shadow-2xl flex flex-col overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 border-b border-navy-600/50 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-white">Consultor IA</h3>
              <p className="text-[10px] text-gray-500">{moleculeName || `Molecula #${moleculeId}`}</p>
            </div>
            <button onClick={() => setOpen(false)} className="text-gray-500 hover:text-white">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>

          {/* Conteudo */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3" style={{ maxHeight: 400 }}>
            {/* Analise automatica */}
            {analysis && (
              <>
                {/* Score */}
                <div className="text-center mb-3">
                  <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold ${
                    analysis.candidate_score >= 70 ? 'bg-accent-green/15 text-accent-green border border-accent-green/30' :
                    analysis.candidate_score >= 40 ? 'bg-yellow-400/15 text-yellow-400 border border-yellow-400/30' :
                    'bg-red-400/15 text-red-400 border border-red-400/30'
                  }`}>
                    Score: {analysis.candidate_score}/100
                  </div>
                </div>

                {/* Insights */}
                {analysis.insights?.map((t, i) => (
                  <div key={`i${i}`} className="flex gap-2 text-xs">
                    <svg className="w-4 h-4 flex-shrink-0 text-accent-green mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4" /></svg>
                    <span className="text-gray-300">{t}</span>
                  </div>
                ))}

                {/* Warnings */}
                {analysis.warnings?.map((t, i) => (
                  <div key={`w${i}`} className="flex gap-2 text-xs">
                    <svg className="w-4 h-4 flex-shrink-0 text-yellow-400 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
                    <span className="text-gray-300">{t}</span>
                  </div>
                ))}

                {/* Recomendacoes */}
                {analysis.recommendations?.map((t, i) => (
                  <div key={`r${i}`} className="flex gap-2 text-xs">
                    <svg className="w-4 h-4 flex-shrink-0 text-accent-cyan mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
                    <span className="text-gray-300">{t}</span>
                  </div>
                ))}
              </>
            )}

            {/* Chat history */}
            {chatHistory.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] px-3 py-2 rounded-xl text-xs ${
                  msg.role === 'user'
                    ? 'bg-accent-cyan/15 text-accent-cyan border border-accent-cyan/20'
                    : 'bg-navy-700/50 text-gray-300 border border-navy-600/30'
                }`}>
                  {msg.text}
                </div>
              </div>
            ))}

            {loading && <p className="text-xs text-gray-500 text-center">Analisando...</p>}
          </div>

          {/* Input */}
          <div className="p-3 border-t border-navy-600/50">
            <p className="text-[10px] text-gray-600 mb-2">Pergunte: "E viavel?", "Como melhorar?", "Solubilidade?", "Leishmaniose?"</p>
            <div className="flex gap-2">
              <input
                value={question}
                onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && askQuestion()}
                placeholder="Faca uma pergunta..."
                className="flex-1 bg-navy-700/50 border border-navy-600/50 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 outline-none focus:border-accent-cyan/50"
              />
              <button onClick={askQuestion} disabled={loading || !question.trim()}
                className="bg-accent-cyan text-navy-950 px-3 py-2 rounded-lg text-sm font-semibold disabled:opacity-50">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

import { useState } from 'react'
import { useAuth } from '../services/auth'

export default function Login() {
  const { login, register } = useAuth()
  const [isRegister, setIsRegister] = useState(false)
  const [form, setForm] = useState({ username: '', password: '', email: '', full_name: '', institution: 'UFRN' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (isRegister) {
        await register(form)
      } else {
        await login(form.username, form.password)
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao autenticar')
    }
    setLoading(false)
  }

  const inputCls = 'w-full bg-navy-700/50 border border-navy-600/50 rounded-lg px-4 py-2.5 text-sm text-white placeholder-gray-500 focus:ring-2 focus:ring-accent-cyan/50 focus:border-accent-cyan/50 outline-none'

  return (
    <div className="min-h-screen bg-navy-950 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent-cyan to-accent-teal flex items-center justify-center mx-auto mb-4">
            <svg className="w-9 h-9 text-navy-950" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-white">Pharma<span className="text-accent-cyan">AI</span></h1>
          <p className="text-gray-500 text-sm mt-1">IA que cria. Ciencia que transforma.</p>
        </div>

        {/* Card */}
        <div className="bg-navy-800 rounded-2xl border border-navy-600/50 p-8">
          <h2 className="text-xl font-semibold text-white mb-6">{isRegister ? 'Criar Conta' : 'Entrar'}</h2>

          {error && (
            <div className="bg-red-500/10 text-red-400 border border-red-500/20 px-4 py-2 rounded-lg text-sm mb-4">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Usuario</label>
              <input className={inputCls} value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} required />
            </div>

            {isRegister && (
              <>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Email</label>
                  <input type="email" className={inputCls} value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Nome Completo</label>
                  <input className={inputCls} value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Instituicao</label>
                  <input className={inputCls} value={form.institution} onChange={e => setForm({ ...form, institution: e.target.value })} />
                </div>
              </>
            )}

            <div>
              <label className="block text-sm text-gray-400 mb-1">Senha</label>
              <input type="password" className={inputCls} value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required />
            </div>

            <button type="submit" disabled={loading}
              className="w-full bg-gradient-to-r from-accent-cyan to-accent-teal text-navy-950 py-2.5 rounded-lg font-semibold text-sm hover:opacity-90 disabled:opacity-50 transition-opacity">
              {loading ? 'Aguarde...' : isRegister ? 'Criar Conta' : 'Entrar'}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button onClick={() => { setIsRegister(!isRegister); setError('') }}
              className="text-accent-cyan text-sm hover:text-accent-teal transition-colors">
              {isRegister ? 'Ja tem conta? Entrar' : 'Criar nova conta'}
            </button>
          </div>
        </div>

      </div>
    </div>
  )
}

'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Bot, Loader2 } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { getErrorMessage } from '@/lib/error'
import { useAgentStore } from '@/stores/agentStore'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export function ChatPanel() {
  const { threadId, proposal, setProposal } = useAgentStore()
  const quickPrompts = [
    'Hazla más ejecutiva en 6 bullets',
    'Enfatiza ROI y payback',
    'Reduce a 180 palabras',
  ]
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        'Estoy listo para refinar la propuesta. Puedes pedir foco en ROI, síntesis ejecutiva o ajuste de tono.',
    },
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (!input.trim()) return

    const userMsg = input.trim()
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setInput('')
    setIsTyping(true)

    if (!threadId) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'No hay sesión activa. Inicia una búsqueda primero para habilitar refinamiento.',
        },
      ])
      setIsTyping(false)
      return
    }

    if (!proposal) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: 'Primero genera una propuesta seleccionando casos. Luego podré refinarla contigo.',
        },
      ])
      setIsTyping(false)
      return
    }

    try {
      const response = await apiClient.post(`/agent/${threadId}/refine`, {
        instruction: userMsg,
      })
      const refined = response.data?.propuesta_final

      if (refined && typeof refined === 'string') {
        setProposal(refined)
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content:
              'Listo. Refiné la propuesta con tu instrucción y actualicé la versión actual en pantalla.',
          },
        ])
      } else {
        setMessages(prev => [
          ...prev,
          {
            role: 'assistant',
            content: 'No pude obtener una propuesta refinada en este intento. Intenta nuevamente.',
          },
        ])
      }
    } catch (error: unknown) {
      const message = getErrorMessage(error, 'Ocurrió un error refinando la propuesta.')
      setMessages(prev => [...prev, { role: 'assistant', content: message }])
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <div className="neo-glass-card flex flex-col h-[460px] md:h-[600px] overflow-hidden transition-all duration-200">
      {/* Header */}
      <div className="p-4 border-b border-white/10 bg-white/5 flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-[var(--accent-soft)] flex items-center justify-center text-white">
          <Bot size={18} />
        </div>
        <div>
          <h3 className="text-sm font-bold text-[var(--foreground)]">Asistente NEO</h3>
          <p className="text-[10px] text-emerald-300 font-medium flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-300 animate-pulse"></span>
            En línea
          </p>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4" aria-live="polite" aria-label="Historial de conversación">
        {messages.map((m, idx) => (
          <div key={idx} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] p-3 rounded-2xl text-sm ${
              m.role === 'user' 
                ? 'bg-[var(--accent-soft)] text-white rounded-tr-none' 
                : 'bg-white/10 text-[var(--foreground)] rounded-tl-none border border-white/10'
            }`}>
              {m.content}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-white/10 border border-white/10 p-3 rounded-2xl rounded-tl-none flex gap-1">
              <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce"></span>
              <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce [animation-delay:0.2s]"></span>
              <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce [animation-delay:0.4s]"></span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form
        className="p-4 border-t border-white/10"
        onSubmit={(e) => {
          e.preventDefault()
          handleSend()
        }}
      >
        <div className="mb-2 flex flex-wrap gap-2" aria-label="Sugerencias rápidas de refinamiento">
          {quickPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              disabled={isTyping}
              onClick={() => {
                setInput(prompt)
                inputRef.current?.focus()
              }}
              className="text-[11px] px-2.5 py-1 rounded-full border border-white/15 bg-white/8 text-slate-100 hover:bg-white/12 disabled:opacity-50 disabled:cursor-not-allowed transition-colors focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
            >
              {prompt}
            </button>
          ))}
        </div>
        <div className="relative">
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            aria-label="Instrucción para refinar propuesta"
            placeholder="Refina: tono, foco, ROI, longitud..."
            className="w-full pl-4 pr-12 py-2.5 bg-white/10 border border-white/10 rounded-lg text-sm text-[var(--foreground)] placeholder:text-slate-300/70 focus:ring-2 focus:ring-[var(--accent)] transition-all outline-none"
          />
          <button 
            type="submit"
            disabled={isTyping || !input.trim()}
            aria-label="Enviar instrucción"
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-[var(--accent)] hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed rounded-md transition-colors focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
          >
            {isTyping ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </div>
      </form>
    </div>
  )
}

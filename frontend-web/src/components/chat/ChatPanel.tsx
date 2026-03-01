'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { Send, Bot, Loader2 } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { getErrorMessage } from '@/lib/error'
import { useAgentStore } from '@/stores/agentStore'

interface Message {
  role: 'user' | 'assistant'
  content: string
  meta?: string
}

type ChatMode = 'chat' | 'refine'

export function ChatPanel() {
  const { threadId, proposal, setProposal } = useAgentStore()
  const [mode, setMode] = useState<ChatMode>('chat')
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        'Listo para ayudarte. Usa chat contextual para estrategia y casos, o refinamiento para ajustar la propuesta final.',
    },
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const quickPrompts = useMemo(
    () =>
      mode === 'chat'
        ? [
            '¿Qué 2 casos dan mayor evidencia para esta cuenta y por qué?',
            'Dame 3 propuestas de valor ejecutivas para esta empresa.',
            '¿Qué riesgo de implementación debemos anticipar?',
          ]
        : [
            'Hazla más ejecutiva en 6 bullets.',
            'Enfatiza ROI y payback en 12 meses.',
            'Reduce a 180 palabras con cierre comercial fuerte.',
          ],
    [mode],
  )

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const appendAssistant = (content: string, meta?: string) => {
    setMessages((prev) => [...prev, { role: 'assistant', content, meta }])
  }

  const handleSend = async () => {
    const userMsg = input.trim()
    if (!userMsg || isTyping) return

    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    setInput('')
    setIsTyping(true)

    if (!threadId) {
      appendAssistant('No hay sesión activa. Completa primero la parte superior para iniciar el flujo.')
      setIsTyping(false)
      return
    }

    try {
      if (mode === 'chat') {
        const response = await apiClient.post(`/agent/${threadId}/chat`, { message: userMsg })
        const answer = response.data?.answer
        const status = response.data?.status
        const guardrailCode = response.data?.guardrail_code

        if (typeof answer === 'string' && answer.trim()) {
          const meta =
            status === 'guardrail_blocked'
              ? `Bloqueado por guardrail${guardrailCode ? ` (${guardrailCode})` : ''}`
              : 'Respuesta contextual'
          appendAssistant(answer, meta)
        } else {
          appendAssistant('No se recibió respuesta válida del chat contextual.')
        }
      } else {
        if (!proposal) {
          appendAssistant('Primero genera una propuesta con los casos seleccionados y luego la refinamos.')
          setIsTyping(false)
          return
        }

        const response = await apiClient.post(`/agent/${threadId}/refine`, {
          instruction: userMsg,
        })
        const refined = response.data?.propuesta_final

        if (typeof refined === 'string' && refined.trim()) {
          setProposal(refined)
          appendAssistant('Refinamiento aplicado y propuesta actualizada.', 'Propuesta actualizada')
        } else {
          appendAssistant('No pude obtener una versión refinada en este intento.')
        }
      }
    } catch (error: unknown) {
      appendAssistant(getErrorMessage(error, 'Ocurrió un error procesando tu solicitud.'))
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <div className="neo-glass-card flex flex-col h-[520px] overflow-hidden">
      <div className="p-4 border-b border-white/10 bg-white/5 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-[var(--accent-soft)] flex items-center justify-center text-white">
            <Bot size={18} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[var(--foreground)]">Asistente de Valor</h3>
            <p className="text-[10px] text-slate-300">Chat contextual y refinamiento de propuesta</p>
          </div>
        </div>
        <div className="inline-flex rounded-lg border border-white/15 bg-white/5 p-1">
          <button
            type="button"
            onClick={() => setMode('chat')}
            className={`px-2.5 py-1 text-[11px] rounded-md ${mode === 'chat' ? 'bg-[var(--accent-soft)] text-white' : 'text-slate-200 hover:bg-white/10'}`}
          >
            Chat
          </button>
          <button
            type="button"
            onClick={() => setMode('refine')}
            disabled={!proposal}
            className={`px-2.5 py-1 text-[11px] rounded-md ${mode === 'refine' ? 'bg-[var(--accent-soft)] text-white' : 'text-slate-200 hover:bg-white/10'} disabled:opacity-50`}
          >
            Refinar
          </button>
        </div>
      </div>
      {!proposal && (
        <p className="px-4 py-2 text-[11px] text-amber-200 border-b border-white/10 bg-amber-200/10">
          El modo Refinar se habilita cuando generes una propuesta.
        </p>
      )}

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3" aria-live="polite">
        {messages.map((m, idx) => (
          <div key={idx} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[88%] p-3 rounded-2xl text-sm ${
                m.role === 'user'
                  ? 'bg-[var(--accent-soft)] text-white rounded-tr-none'
                  : 'bg-white/10 text-[var(--foreground)] rounded-tl-none border border-white/10'
              }`}
            >
              <p>{m.content}</p>
              {m.meta && <p className="mt-1 text-[10px] text-slate-300">{m.meta}</p>}
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

      <form
        className="p-4 border-t border-white/10"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault()
          const dropped = e.dataTransfer.getData('text/plain')?.trim()
          if (!dropped) return
          setInput((prev) => (prev ? `${prev}\n${dropped}` : dropped))
          inputRef.current?.focus()
        }}
        onSubmit={(e) => {
          e.preventDefault()
          void handleSend()
        }}
      >
        <p className="mb-2 text-[11px] text-slate-300">
          Tip: arrastra chips de contexto desde la columna derecha hacia este input.
        </p>
        <div className="mb-2 flex flex-wrap gap-2">
          {quickPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              disabled={isTyping}
              onClick={() => {
                setInput(prompt)
                inputRef.current?.focus()
              }}
              className="text-[11px] px-2.5 py-1 rounded-full border border-white/15 bg-white/8 text-slate-100 hover:bg-white/12 disabled:opacity-50"
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
            maxLength={600}
            placeholder={mode === 'chat' ? 'Pregunta estratégica con contexto...' : 'Instrucción de refinamiento...'}
            className="w-full pl-4 pr-12 py-2.5 bg-white/10 border border-white/10 rounded-lg text-sm text-[var(--foreground)] placeholder:text-slate-300/70 focus:ring-2 focus:ring-[var(--accent)] outline-none"
          />
          <button
            type="submit"
            disabled={isTyping || !input.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-[var(--accent)] hover:bg-white/10 disabled:opacity-50 rounded-md"
            aria-label="Enviar mensaje"
          >
            {isTyping ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </div>
      </form>
    </div>
  )
}

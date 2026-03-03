'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { useDroppable } from '@dnd-kit/core'
import { Send, Bot, Loader2, X, WandSparkles, Copy, CheckCheck } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { getErrorMessage } from '@/lib/error'
import { useAgentStore } from '@/stores/agentStore'

interface Message {
  role: 'user' | 'assistant'
  content: string
  meta?: string
  isProposal?: boolean
}

type ChatMode = 'chat' | 'refine'

interface ChatPanelProps {
  onGenerate?: () => void
  isGenerating?: boolean
}

// ── Markdown renderer básico ────────────────────────────────────────
function renderMarkdown(text: string): React.ReactNode[] {
  return text.split(/\n{2,}/).map((block, i) => {
    const t = block.trim()
    if (!t) return null
    if (/^#{1,3} /.test(t)) {
      return <h3 key={i} className="neo-proposal-bubble" style={{ marginTop: i > 0 ? 10 : 0 }}>{inlineFmt(t.replace(/^#{1,3} /, ''))}</h3>
    }
    const lines = t.split('\n')
    if (lines.every((l) => /^[-*] /.test(l.trim()))) {
      return <ul key={i} className="neo-proposal-bubble" style={{ paddingLeft: 14, marginBottom: 6 }}>
        {lines.map((l, j) => <li key={j}>{inlineFmt(l.replace(/^[-*] /, ''))}</li>)}
      </ul>
    }
    if (/^\d+\. /.test(lines[0]?.trim() ?? '')) {
      return <ol key={i} className="neo-proposal-bubble" style={{ paddingLeft: 16, marginBottom: 6 }}>
        {lines.map((l, j) => <li key={j}>{inlineFmt(l.replace(/^\d+\. /, ''))}</li>)}
      </ol>
    }
    return <p key={i} className="neo-proposal-bubble">{inlineFmt(t)}</p>
  }).filter(Boolean)
}

function inlineFmt(text: string): React.ReactNode {
  return text.split(/(\*\*[^*]+\*\*)/g).map((p, i) =>
    /^\*\*[^*]+\*\*$/.test(p)
      ? <strong key={i} style={{ color: '#f4f9ff', fontWeight: 700 }}>{p.slice(2, -2)}</strong>
      : p,
  )
}

export function ChatPanel({ onGenerate, isGenerating }: ChatPanelProps) {
  const {
    threadId, proposal, setProposal,
    selectedCaseIds, contextChips, removeContextChip, clearContextChips,
  } = useAgentStore()

  const [mode, setMode] = useState<ChatMode>('chat')
  const [messages, setMessages] = useState<Message[]>([{
    role: 'assistant',
    content: 'Listo. Selecciona casos en el panel izquierdo y genera una propuesta, o escríbeme una pregunta estratégica.',
  }])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const lastProposalRef = useRef<string | null>(null)

  const { setNodeRef: setDropRef, isOver: isDropOver } = useDroppable({ id: 'chat-drop-zone' })

  // Inyectar propuesta en el historial cuando se genera/refina
  useEffect(() => {
    if (!proposal || proposal === lastProposalRef.current) return
    const isRefinement = lastProposalRef.current !== null
    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        content: proposal,
        meta: isRefinement ? 'Propuesta refinada' : 'Propuesta generada',
        isProposal: true,
      },
    ])
    lastProposalRef.current = proposal
  }, [proposal])

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [messages])

  const quickPrompts = useMemo(() =>
    mode === 'chat'
      ? [
          '¿Qué 2 casos dan mayor evidencia para esta cuenta?',
          'Dame 3 propuestas de valor ejecutivas.',
          '¿Qué riesgo de implementación debemos anticipar?',
        ]
      : [
          'Hazla más ejecutiva en 6 bullets.',
          'Enfatiza ROI y payback en 12 meses.',
          'Reduce a 180 palabras con cierre comercial.',
        ],
    [mode],
  )

  const buildMessageWithChips = (userMsg: string): string => {
    if (contextChips.length === 0) return userMsg
    const ctx = contextChips.map((c) => c.text).join(' | ')
    return `${userMsg}\n\n[Contexto: ${ctx}]`
  }

  const handleSend = async () => {
    const userMsg = input.trim()
    if (!userMsg || isTyping) return

    const fullMsg = buildMessageWithChips(userMsg)
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    setInput('')
    clearContextChips()
    setIsTyping(true)

    if (!threadId) {
      setMessages((prev) => [...prev, { role: 'assistant', content: 'No hay sesión activa. Completa el formulario de búsqueda primero.' }])
      setIsTyping(false)
      return
    }

    try {
      if (mode === 'chat') {
        const response = await apiClient.post(`/agent/${threadId}/chat`, { message: fullMsg })
        const answer = response.data?.answer
        const status = response.data?.status
        const guardrailCode = response.data?.guardrail_code
        if (typeof answer === 'string' && answer.trim()) {
          setMessages((prev) => [...prev, {
            role: 'assistant',
            content: answer,
            meta: status === 'guardrail_blocked'
              ? `Guardrail${guardrailCode ? ` (${guardrailCode})` : ''}`
              : undefined,
          }])
        } else {
          setMessages((prev) => [...prev, { role: 'assistant', content: 'No se recibió respuesta válida.' }])
        }
      } else {
        if (!proposal) {
          setMessages((prev) => [...prev, { role: 'assistant', content: 'Primero genera una propuesta para refinarla.' }])
          setIsTyping(false)
          return
        }
        const response = await apiClient.post(`/agent/${threadId}/refine`, { instruction: fullMsg })
        const refined = response.data?.propuesta_final
        if (typeof refined === 'string' && refined.trim()) {
          setProposal(refined)
          // el useEffect de proposal lo añade como mensaje
        } else {
          setMessages((prev) => [...prev, { role: 'assistant', content: 'No pude refinar la propuesta en este intento.' }])
        }
      }
    } catch (error: unknown) {
      setMessages((prev) => [...prev, { role: 'assistant', content: getErrorMessage(error, 'Error procesando tu solicitud.') }])
    } finally {
      setIsTyping(false)
    }
  }

  const handleCopy = async (content: string, idx: number) => {
    await navigator.clipboard.writeText(content)
    setCopiedIdx(idx)
    setTimeout(() => setCopiedIdx(null), 2000)
  }

  return (
    <div className="neo-glass-card flex flex-col overflow-hidden" style={{ height: '100%' }}>
      {/* Header */}
      <div className="p-3 border-b border-white/10 bg-white/5 flex items-center justify-between gap-3" style={{ flexShrink: 0 }}>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-[var(--accent-soft)] flex items-center justify-center text-white">
            <Bot size={18} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[var(--foreground)]">Asistente de Valor</h3>
            <p className="text-[10px] text-slate-300">Chat · propuesta · refinamiento</p>
          </div>
        </div>
        <div className="inline-flex rounded-lg border border-white/15 bg-white/5 p-1">
          <button type="button" onClick={() => setMode('chat')}
            className={`px-2.5 py-1 text-[11px] rounded-md ${mode === 'chat' ? 'bg-[var(--accent-soft)] text-white' : 'text-slate-200 hover:bg-white/10'}`}>
            Chat
          </button>
          <button type="button" onClick={() => setMode('refine')} disabled={!proposal}
            className={`px-2.5 py-1 text-[11px] rounded-md ${mode === 'refine' ? 'bg-[var(--accent-soft)] text-white' : 'text-slate-200 hover:bg-white/10'} disabled:opacity-50`}>
            Refinar
          </button>
        </div>
      </div>

      {/* Barra de generar propuesta */}
      {selectedCaseIds.length > 0 && onGenerate && (
        <div className="neo-generate-bar" style={{ flexShrink: 0 }}>
          <span style={{ fontSize: 11, color: '#b3d5ff' }}>
            {selectedCaseIds.length} caso{selectedCaseIds.length > 1 ? 's' : ''} seleccionado{selectedCaseIds.length > 1 ? 's' : ''}
          </span>
          <button
            type="button"
            onClick={onGenerate}
            disabled={isGenerating}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 5,
              padding: '5px 12px', borderRadius: 8,
              background: 'linear-gradient(135deg, #5678ff, #3ab8ff)',
              border: '1px solid rgba(166,192,255,0.6)',
              color: 'white', fontSize: 11, fontWeight: 700,
              cursor: isGenerating ? 'not-allowed' : 'pointer',
              opacity: isGenerating ? 0.6 : 1,
            }}
          >
            {isGenerating
              ? <><Loader2 size={13} className="animate-spin" /> Generando…</>
              : <><WandSparkles size={13} /> Generar propuesta</>}
          </button>
        </div>
      )}

      {/* Drop hint */}
      <div
        ref={setDropRef}
        style={{
          padding: '5px 14px', fontSize: 10, flexShrink: 0,
          color: isDropOver ? '#7bf7ff' : '#4a5e7a',
          background: isDropOver ? 'rgba(74,111,255,0.1)' : 'transparent',
          borderBottom: '1px solid rgba(255,255,255,0.05)',
          transition: 'background 140ms ease, color 140ms ease',
          textAlign: 'center',
        }}
      >
        {isDropOver ? '↓ Suelta aquí para añadir como contexto' : 'Arrastra una ficha de caso aquí para usarla como contexto →'}
      </div>

      {/* Chips de contexto activos */}
      {contextChips.length > 0 && (
        <div className="neo-chips-bar" style={{ flexShrink: 0 }}>
          {contextChips.map((chip) => (
            <span key={chip.id} className="neo-active-chip" title={chip.text}>
              {chip.label}
              <button
                type="button"
                className="neo-active-chip__remove"
                onClick={() => removeContextChip(chip.id)}
                aria-label={`Quitar contexto ${chip.label}`}
              >
                <X size={9} />
              </button>
            </span>
          ))}
        </div>
      )}

      {/* Mensajes */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3" aria-live="polite" style={{ minHeight: 0 }}>
        {messages.map((m, idx) => (
          <div key={idx} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {m.isProposal ? (
              <div
                style={{
                  width: '100%',
                  background: 'rgba(14,23,46,0.7)',
                  border: '1px solid rgba(108,140,255,0.35)',
                  borderRadius: 16,
                  padding: '12px 14px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <span style={{ fontSize: 10, color: '#7bf7ff', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    {m.meta ?? 'Propuesta generada'}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopy(m.content, idx)}
                    style={{
                      display: 'inline-flex', alignItems: 'center', gap: 4,
                      fontSize: 10, color: copiedIdx === idx ? '#8ff8be' : '#7a93b8',
                      background: 'transparent', border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: 6, padding: '2px 7px', cursor: 'pointer',
                    }}
                  >
                    {copiedIdx === idx ? <CheckCheck size={12} /> : <Copy size={12} />}
                    {copiedIdx === idx ? 'Copiado' : 'Copiar'}
                  </button>
                </div>
                <div>{renderMarkdown(m.content)}</div>
              </div>
            ) : (
              <div className={`max-w-[88%] p-3 rounded-2xl text-sm ${
                m.role === 'user'
                  ? 'bg-[var(--accent-soft)] text-white rounded-tr-none'
                  : 'bg-white/10 text-[var(--foreground)] rounded-tl-none border border-white/10'
              }`}>
                <p style={{ fontSize: 13, lineHeight: 1.5 }}>{m.content}</p>
                {m.meta && <p className="mt-1 text-[10px] text-slate-300">{m.meta}</p>}
              </div>
            )}
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-white/10 border border-white/10 p-3 rounded-2xl rounded-tl-none flex gap-1">
              <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce" />
              <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce [animation-delay:0.2s]" />
              <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce [animation-delay:0.4s]" />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <form
        className="p-3 border-t border-white/10"
        style={{ flexShrink: 0 }}
        onSubmit={(e) => { e.preventDefault(); void handleSend() }}
      >
        <div className="mb-2 flex flex-wrap gap-1.5">
          {quickPrompts.map((prompt) => (
            <button key={prompt} type="button" disabled={isTyping}
              onClick={() => { setInput(prompt); inputRef.current?.focus() }}
              className="text-[10px] px-2 py-1 rounded-full border border-white/15 bg-white/8 text-slate-100 hover:bg-white/12 disabled:opacity-50">
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
            placeholder={mode === 'chat' ? 'Pregunta estratégica…' : 'Instrucción de refinamiento…'}
            className="w-full pl-4 pr-11 py-2.5 bg-white/10 border border-white/10 rounded-lg text-sm text-[var(--foreground)] placeholder:text-slate-300/60 focus:ring-2 focus:ring-[var(--accent)] outline-none"
          />
          <button type="submit" disabled={isTyping || !input.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-[var(--accent)] hover:bg-white/10 disabled:opacity-50 rounded-md"
            aria-label="Enviar mensaje">
            {isTyping ? <Loader2 size={17} className="animate-spin" /> : <Send size={17} />}
          </button>
        </div>
      </form>
    </div>
  )
}

'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { useDroppable } from '@dnd-kit/core'
import { Send, Bot, Loader2, X, Copy, CheckCheck, Edit3 } from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import { apiClient } from '@/lib/api'
import { getErrorMessage } from '@/lib/error'
import { useAgentStore } from '@/stores/agentStore'
import { NeoLoader } from '@/components/ui/NeoLoader'

interface Message {
  role: 'user' | 'assistant'
  content: string
  meta?: string
  isProposal?: boolean
}

type ChatMode = 'chat' | 'refine'

interface ChatPanelProps {
  isGenerating?: boolean
}

// ── Markdown renderer ────────────────────────────────────────────────────────
function inlineFmt(text: string): React.ReactNode {
  return text.split(/(\*\*[^*]+\*\*)/g).map((p, i) =>
    /^\*\*[^*]+\*\*$/.test(p) ? (
      <strong key={i} style={{ color: '#ffffff', fontWeight: 700 }}>
        {p.slice(2, -2)}
      </strong>
    ) : (
      p
    ),
  )
}

function renderMarkdown(text: string): React.ReactNode[] {
  return text
    .split(/\n{2,}/)
    .map((block, i) => {
      const t = block.trim()
      if (!t) return null

      if (/^#{1,4} /.test(t)) {
        const level = (t.match(/^(#+) /)?.[1]?.length ?? 2) as 1 | 2 | 3 | 4
        const sizes: Record<number, string> = { 1: '20px', 2: '18px', 3: '16px', 4: '15px' }
        return (
          <p
            key={i}
            style={{
              fontFamily: 'var(--font-serif), Georgia, serif',
              color: '#7ba3f0',
              fontSize: sizes[level] ?? '16px',
              fontWeight: 700,
              lineHeight: 1.35,
              margin: '18px 0 8px',
            }}
          >
            {inlineFmt(t.replace(/^#{1,4} /, ''))}
          </p>
        )
      }

      const lines = t.split('\n')
      if (lines.length > 0 && lines.every((l) => /^[-*] /.test(l.trim()))) {
        return (
          <ul
            key={i}
            style={{
              fontFamily: 'var(--font-body), sans-serif',
              color: '#f5f5ff',
              fontSize: '15px',
              lineHeight: 1.85,
              paddingLeft: 22,
              marginBottom: 16,
              listStyle: 'disc',
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
            }}
          >
            {lines.map((l, j) => (
              <li key={j} style={{ paddingLeft: 4 }}>
                {inlineFmt(l.replace(/^[-*] /, '').trim())}
              </li>
            ))}
          </ul>
        )
      }

      if (/^\d+\. /.test(lines[0]?.trim() ?? '')) {
        return (
          <ol
            key={i}
            style={{
              fontFamily: 'var(--font-body), sans-serif',
              color: '#f5f5ff',
              fontSize: '15px',
              lineHeight: 1.85,
              paddingLeft: 24,
              marginBottom: 16,
              listStyle: 'decimal',
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
            }}
          >
            {lines.map((l, j) => (
              <li key={j} style={{ paddingLeft: 4 }}>
                {inlineFmt(l.replace(/^\d+\. /, '').trim())}
              </li>
            ))}
          </ol>
        )
      }

      return (
        <p
          key={i}
          style={{
            fontFamily: 'var(--font-body), sans-serif',
            color: '#f5f5ff',
            fontSize: '15px',
            lineHeight: 1.9,
            marginBottom: 16,
          }}
        >
          {inlineFmt(t)}
        </p>
      )
    })
    .filter(Boolean)
}
// ────────────────────────────────────────────────────────────────────────────

export function ChatPanel({ isGenerating }: ChatPanelProps) {
  const {
    threadId,
    proposal,
    setProposal,
    selectedCaseIds,
    contextChips,
    removeContextChip,
    clearContextChips,
    useClientProfile,
  } = useAgentStore()

  const [mode, setMode] = useState<ChatMode>('chat')
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        'Listo para trabajar. Selecciona casos en el panel de la izquierda y genera una propuesta, o escríbeme una pregunta estratégica sobre el cliente o la oportunidad.',
    },
  ])
  const [input, setInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null)
  const prefersReducedMotion = useReducedMotion()
  const inputRef = useRef<HTMLInputElement>(null)
  const lastProposalRef = useRef<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { setNodeRef: setDropRef, isOver: isDropOver } = useDroppable({ id: 'chat-drop-zone' })

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
    if (!isRefinement) setMode('refine')
  }, [proposal])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isTyping])

  useEffect(() => {
    if (isGenerating) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [isGenerating])

  const quickPrompts = useMemo(
    () =>
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
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'No hay sesión activa. Completa el formulario de búsqueda primero.' },
      ])
      setIsTyping(false)
      return
    }

    try {
      if (mode === 'refine' && proposal) {
        const response = await apiClient.post(`/agent/${threadId}/refine`, {
          instruction: fullMsg,
          use_client_profile: useClientProfile,
        })
        const refined = response.data?.propuesta_final
        if (typeof refined === 'string' && refined.trim()) {
          setProposal(refined)
        } else {
          setMessages((prev) => [
            ...prev,
            { role: 'assistant', content: 'No pude refinar la propuesta en este intento.' },
          ])
        }
      } else {
        const response = await apiClient.post(`/agent/${threadId}/chat`, {
          message: fullMsg,
          use_client_profile: useClientProfile,
        })
        const answer = response.data?.answer
        const status = response.data?.status
        const guardrailCode = response.data?.guardrail_code
        if (typeof answer === 'string' && answer.trim()) {
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: answer,
              meta:
                status === 'guardrail_blocked'
                  ? `Guardrail${guardrailCode ? ` (${guardrailCode})` : ''}`
                  : undefined,
            },
          ])
        } else {
          setMessages((prev) => [...prev, { role: 'assistant', content: 'No se recibió respuesta válida.' }])
        }
      }
    } catch (error: unknown) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: getErrorMessage(error, 'Error procesando tu solicitud.') },
      ])
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
    <div style={{ height: '100%', minHeight: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

      {/* Header bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '10px 16px',
          borderBottom: '1px solid rgba(123,163,240,0.20)',
          background: 'rgba(5,5,140,0.18)',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            width: 34,
            height: 34,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 8,
            border: '1px solid rgba(123,163,240,0.30)',
            background: 'rgba(123,163,240,0.12)',
            color: '#7ba3f0',
            flexShrink: 0,
          }}
        >
          <Bot size={18} />
        </div>
        <div>
          <p
            style={{
              margin: 0,
              fontSize: 16,
              fontWeight: 700,
              color: '#f5f5ff',
              fontFamily: 'var(--font-serif), Georgia, serif',
            }}
          >
            NEO Strategy Co-Pilot
          </p>
          <p
            style={{
              margin: 0,
              fontSize: 12,
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-body), sans-serif',
            }}
          >
            {mode === 'chat' ? 'Análisis estratégico · Propuesta de valor' : 'Modo refinamiento activo'}
          </p>
        </div>
        {proposal && (
          <button
            type="button"
            onClick={() => setMode(mode === 'chat' ? 'refine' : 'chat')}
            style={{
              marginLeft: 'auto',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 5,
              padding: '6px 14px',
              border: `1px solid ${mode === 'refine' ? '#7ba3f0' : 'rgba(123,163,240,0.20)'}`,
              borderRadius: 8,
              background: mode === 'refine' ? 'rgba(123,163,240,0.15)' : 'rgba(5,5,140,0.40)',
              color: mode === 'refine' ? '#7ba3f0' : 'var(--text-muted)',
              fontSize: 13,
              fontWeight: 600,
              fontFamily: 'var(--font-body), sans-serif',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 200ms ease',
            }}
          >
            <Edit3 size={13} />
            {mode === 'refine' ? 'Modo Chat' : 'Refinar'}
          </button>
        )}
      </div>

      {/* DnD drop zone */}
      <div
        ref={setDropRef}
        style={{
          padding: isDropOver ? '8px 16px' : '3px 16px',
          fontSize: 12,
          flexShrink: 0,
          color: isDropOver ? '#7ba3f0' : 'transparent',
          background: isDropOver ? 'rgba(123,163,240,0.08)' : 'transparent',
          borderBottom: isDropOver ? '1px solid rgba(123,163,240,0.3)' : '1px solid transparent',
          textAlign: 'center',
          transition: 'all 150ms ease',
          fontFamily: 'var(--font-body), sans-serif',
          fontWeight: 600,
          pointerEvents: 'all',
          minHeight: isDropOver ? 32 : 4,
        }}
      >
        {isDropOver ? '↓ Suelta aquí para añadir como contexto' : ''}
      </div>

      {/* Context chips */}
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

      {/* Loading indicator when generating */}
      {isGenerating && <NeoLoader compact className="border-t-0 rounded-none" />}

      {/* Message list */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '18px',
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
          background: 'transparent',
        }}
        aria-live="polite"
      >
        {messages.map((m, idx) => (
          <div
            key={idx}
            style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}
          >
            {m.isProposal ? (
              /* ── Proposal bubble ── */
              <motion.div
                initial={prefersReducedMotion ? false : { opacity: 0, y: 14 }}
                animate={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
                transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                style={{
                  width: '100%',
                  background: 'rgba(5,5,140,0.40)',
                  backdropFilter: 'blur(12px)',
                  WebkitBackdropFilter: 'blur(12px)',
                  border: '1px solid rgba(123,163,240,0.25)',
                  borderRadius: 12,
                  padding: '18px 20px',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: 14,
                  }}
                >
                  <span
                    style={{
                      fontSize: 12,
                      color: '#7ba3f0',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      letterSpacing: '0.08em',
                      fontFamily: 'var(--font-mono), monospace',
                    }}
                  >
                    {m.meta ?? 'Propuesta generada'}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopy(m.content, idx)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 5,
                      fontSize: 11,
                      color: copiedIdx === idx ? '#7ba3f0' : 'var(--text-muted)',
                      background: 'rgba(5,5,140,0.4)',
                      border: '1px solid rgba(123,163,240,0.20)',
                      borderRadius: 8,
                      padding: '4px 10px',
                      cursor: 'pointer',
                      fontFamily: 'var(--font-body), sans-serif',
                      transition: 'all 200ms ease',
                    }}
                  >
                    {copiedIdx === idx ? <CheckCheck size={12} /> : <Copy size={12} />}
                    {copiedIdx === idx ? 'Copiado' : 'Copiar'}
                  </button>
                </div>
                <div className="neo-proposal-bubble">{renderMarkdown(m.content)}</div>
              </motion.div>
            ) : m.role === 'user' ? (
              /* ── User message ── */
              <div
                style={{
                  maxWidth: '82%',
                  background: 'rgba(123,163,240,0.12)',
                  border: '1px solid rgba(123,163,240,0.35)',
                  borderRadius: '12px 12px 2px 12px',
                  padding: '12px 16px',
                  fontFamily: 'var(--font-body), sans-serif',
                  fontSize: 15,
                  lineHeight: 1.7,
                  color: '#f5f5ff',
                }}
              >
                {m.content}
              </div>
            ) : (
              /* ── Assistant message ── */
              <div
                className="neo-chat-assistant-msg"
                style={{ maxWidth: '88%' }}
              >
                <div className="neo-proposal-bubble">{renderMarkdown(m.content)}</div>
                {m.meta && (
                  <p
                    style={{
                      marginTop: 8,
                      fontSize: 11,
                      color: 'var(--text-muted)',
                      fontFamily: 'var(--font-mono), monospace',
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                    }}
                  >
                    {m.meta}
                  </p>
                )}
              </div>
            )}
          </div>
        ))}

        {isTyping && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div
              style={{
                display: 'flex',
                gap: 6,
                padding: '12px 16px',
                background: 'rgba(5,5,140,0.40)',
                border: '1px solid rgba(123,163,240,0.20)',
                borderRadius: 12,
                backdropFilter: 'blur(8px)',
              }}
            >
              <span
                style={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  background: '#7ba3f0',
                  animation: 'bounce 1s infinite',
                }}
              />
              <span
                style={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  background: '#7ba3f0',
                  animation: 'bounce 1s 0.2s infinite',
                }}
              />
              <span
                style={{
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  background: '#7ba3f0',
                  animation: 'bounce 1s 0.4s infinite',
                }}
              />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input form */}
      <form
        style={{
          flexShrink: 0,
          borderTop: '1px solid rgba(123,163,240,0.20)',
          background: 'rgba(5,5,140,0.18)',
          padding: '12px 16px',
        }}
        onSubmit={(e) => {
          e.preventDefault()
          void handleSend()
        }}
      >
        {/* Quick prompts */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
          {quickPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              disabled={isTyping}
              onClick={() => {
                setInput(prompt)
                inputRef.current?.focus()
              }}
              style={{
                padding: '5px 12px',
                border: '1px solid rgba(123,163,240,0.25)',
                borderRadius: 999,
                background: 'rgba(123,163,240,0.08)',
                color: '#7ba3f0',
                fontSize: 12,
                fontWeight: 600,
                fontFamily: 'var(--font-body), sans-serif',
                cursor: 'pointer',
                opacity: isTyping ? 0.5 : 1,
                transition: 'all 200ms ease',
              }}
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Input field */}
        <div style={{ position: 'relative' }}>
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            maxLength={600}
            placeholder={
              mode === 'refine'
                ? 'Instrucción de refinamiento de propuesta...'
                : 'Pregunta estratégica sobre el cliente o la oportunidad...'
            }
            style={{
              width: '100%',
              padding: '12px 48px 12px 16px',
              border: '1px solid rgba(123,163,240,0.20)',
              borderRadius: 10,
              background: 'rgba(5,5,140,0.40)',
              backdropFilter: 'blur(8px)',
              color: '#f5f5ff',
              fontSize: 15,
              fontFamily: 'var(--font-body), sans-serif',
              outline: 'none',
              boxSizing: 'border-box',
              transition: 'border-color 200ms ease, box-shadow 200ms ease',
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = '#7ba3f0'
              e.currentTarget.style.boxShadow = '0 0 12px rgba(123,163,240,0.2)'
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = 'rgba(123,163,240,0.20)'
              e.currentTarget.style.boxShadow = 'none'
            }}
          />
          <button
            type="submit"
            disabled={isTyping || !input.trim()}
            style={{
              position: 'absolute',
              right: 8,
              top: '50%',
              transform: 'translateY(-50%)',
              padding: 8,
              borderRadius: 8,
              border: 'none',
              background: input.trim() ? 'linear-gradient(135deg, #05058c, #7ba3f0)' : 'transparent',
              color: '#7ba3f0',
              cursor: 'pointer',
              opacity: isTyping || !input.trim() ? 0.4 : 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 200ms ease',
            }}
            aria-label="Enviar mensaje"
          >
            {isTyping ? <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> : <Send size={18} color="#ffffff" />}
          </button>
        </div>

        {/* Selected cases count hint */}
        {selectedCaseIds.length > 0 && (
          <p
            style={{
              marginTop: 8,
              fontSize: 12,
              color: 'var(--text-muted)',
              fontFamily: 'var(--font-mono), monospace',
              textAlign: 'center',
            }}
          >
            {selectedCaseIds.length} caso{selectedCaseIds.length !== 1 ? 's' : ''} seleccionado{selectedCaseIds.length !== 1 ? 's' : ''} como base de evidencia
          </p>
        )}
      </form>
    </div>
  )
}

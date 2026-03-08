'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { Send, Bot, Loader2, Copy, CheckCheck, Edit3 } from 'lucide-react'
import { motion, useReducedMotion } from 'framer-motion'
import { useAppStore } from '@/stores/appStore'
import { useChatMessage } from '@/hooks/useApi'
import type { ChatMessage } from '@/stores/appStore'

type ChatMode = 'chat' | 'refinar'

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
        const sizes: Record<number, string> = { 1: '18px', 2: '16px', 3: '15px', 4: '14px' }
        return (
          <p
            key={i}
            style={{
              fontFamily: 'var(--font-serif), Georgia, serif',
              color: '#7ba3f0',
              fontSize: sizes[level] ?? '15px',
              fontWeight: 700,
              lineHeight: 1.35,
              margin: '12px 0 6px',
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
              fontSize: '13px',
              lineHeight: 1.7,
              paddingLeft: 18,
              marginBottom: 10,
              listStyle: 'disc',
              display: 'flex',
              flexDirection: 'column',
              gap: 3,
            }}
          >
            {lines.map((l, j) => (
              <li key={j} style={{ paddingLeft: 2 }}>
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
              fontSize: '13px',
              lineHeight: 1.7,
              paddingLeft: 20,
              marginBottom: 10,
              listStyle: 'decimal',
              display: 'flex',
              flexDirection: 'column',
              gap: 3,
            }}
          >
            {lines.map((l, j) => (
              <li key={j} style={{ paddingLeft: 2 }}>
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
            fontSize: '13px',
            lineHeight: 1.75,
            marginBottom: 10,
          }}
        >
          {inlineFmt(t)}
        </p>
      )
    })
    .filter(Boolean)
}
// ────────────────────────────────────────────────────────────────────────────

export function ChatPanel() {
  const {
    threadId,
    chatMessages,
    addChatMessage,
    chatMode,
    setChatMode,
    proposalRawText,
    selectedCaseIds,
  } = useAppStore()

  const chatMutation = useChatMessage()
  const [input, setInput] = useState('')
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null)
  const prefersReducedMotion = useReducedMotion()
  const inputRef = useRef<HTMLInputElement>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const mode: ChatMode = chatMode === 'refinar' ? 'refinar' : 'chat'
  const isTyping = chatMutation.isPending

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [chatMessages, isTyping])

  const quickPrompts = useMemo(
    () =>
      mode === 'chat'
        ? [
            'Top 2 casos con mayor evidencia',
            '3 propuestas de valor ejecutivas',
            'Riesgo de implementacion',
          ]
        : [
            'Mas ejecutiva en 6 bullets',
            'Enfatiza ROI en 12 meses',
            'Reduce a 180 palabras',
          ],
    [mode],
  )

  const handleSend = () => {
    const userMsg = input.trim()
    if (!userMsg || isTyping) return

    addChatMessage({ role: 'user', content: userMsg })
    setInput('')

    if (!threadId) {
      addChatMessage({
        role: 'assistant',
        content: 'No hay sesion activa. Completa la busqueda primero.',
      })
      return
    }

    chatMutation.mutate({ message: userMsg, mode })
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
          gap: 10,
          padding: '8px 14px',
          borderBottom: '1px solid rgba(123,163,240,0.20)',
          background: 'rgba(5,5,140,0.18)',
          flexShrink: 0,
        }}
      >
        <div
          style={{
            width: 28,
            height: 28,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 7,
            border: '1px solid rgba(123,163,240,0.30)',
            background: 'rgba(123,163,240,0.12)',
            color: '#7ba3f0',
            flexShrink: 0,
          }}
        >
          <Bot size={14} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: '#f5f5ff', fontFamily: 'var(--font-serif)' }}>
            NEO Co-Pilot
          </p>
          <p style={{ margin: 0, fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-body)' }}>
            {mode === 'chat' ? 'Analisis estrategico' : 'Refinamiento activo'}
          </p>
        </div>
        {proposalRawText && (
          <button
            type="button"
            onClick={() => setChatMode(mode === 'refinar' ? 'chat' : 'refinar')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 4,
              padding: '4px 10px',
              border: `1px solid ${mode === 'refinar' ? '#7ba3f0' : 'rgba(123,163,240,0.20)'}`,
              borderRadius: 7,
              background: mode === 'refinar' ? 'rgba(123,163,240,0.15)' : 'rgba(5,5,140,0.40)',
              color: mode === 'refinar' ? '#7ba3f0' : 'var(--text-muted)',
              fontSize: 11,
              fontWeight: 600,
              fontFamily: 'var(--font-body)',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              flexShrink: 0,
            }}
          >
            <Edit3 size={11} />
            {mode === 'refinar' ? 'Chat' : 'Refinar'}
          </button>
        )}
      </div>

      {/* Message list */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
          background: 'transparent',
        }}
        aria-live="polite"
      >
        {chatMessages.map((m: ChatMessage, idx: number) => (
          <div
            key={idx}
            style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}
          >
            {m.isProposal ? (
              <motion.div
                initial={prefersReducedMotion ? false : { opacity: 0, y: 8 }}
                animate={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
                transition={{ duration: 0.22 }}
                style={{
                  width: '100%',
                  background: 'rgba(5,5,140,0.40)',
                  backdropFilter: 'blur(12px)',
                  border: '1px solid rgba(123,163,240,0.25)',
                  borderRadius: 10,
                  padding: '12px 14px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <span style={{ fontSize: 11, color: '#7ba3f0', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', fontFamily: 'var(--font-mono)' }}>
                    {m.meta ?? 'Propuesta generada'}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopy(m.content, idx)}
                    style={{
                      display: 'inline-flex', alignItems: 'center', gap: 3, fontSize: 11,
                      color: copiedIdx === idx ? '#7ba3f0' : 'var(--text-muted)',
                      background: 'rgba(5,5,140,0.4)', border: '1px solid rgba(123,163,240,0.20)',
                      borderRadius: 6, padding: '3px 8px', cursor: 'pointer', fontFamily: 'var(--font-body)',
                    }}
                  >
                    {copiedIdx === idx ? <CheckCheck size={11} /> : <Copy size={11} />}
                    {copiedIdx === idx ? 'Copiado' : 'Copiar'}
                  </button>
                </div>
                <div className="neo-proposal-bubble">{renderMarkdown(m.content)}</div>
              </motion.div>
            ) : m.role === 'user' ? (
              <div
                style={{
                  maxWidth: '82%', background: 'rgba(123,163,240,0.12)',
                  border: '1px solid rgba(123,163,240,0.35)',
                  borderRadius: '10px 10px 2px 10px', padding: '8px 12px',
                  fontFamily: 'var(--font-body)', fontSize: 13, lineHeight: 1.6, color: '#f5f5ff',
                }}
              >
                {m.content}
              </div>
            ) : (
              <div className="neo-chat-assistant-msg" style={{ maxWidth: '90%' }}>
                <div className="neo-proposal-bubble">{renderMarkdown(m.content)}</div>
                {m.meta && (
                  <p style={{ marginTop: 4, fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    {m.meta}
                  </p>
                )}
              </div>
            )}
          </div>
        ))}

        {isTyping && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ display: 'flex', gap: 5, padding: '8px 12px', background: 'rgba(5,5,140,0.40)', border: '1px solid rgba(123,163,240,0.20)', borderRadius: 10, backdropFilter: 'blur(8px)' }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#7ba3f0', animation: 'bounce 1s infinite' }} />
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#7ba3f0', animation: 'bounce 1s 0.2s infinite' }} />
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#7ba3f0', animation: 'bounce 1s 0.4s infinite' }} />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input form */}
      <form
        style={{ flexShrink: 0, borderTop: '1px solid rgba(123,163,240,0.20)', background: 'rgba(5,5,140,0.18)', padding: '8px 12px' }}
        onSubmit={(e) => { e.preventDefault(); handleSend() }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 6 }}>
          {quickPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              disabled={isTyping}
              onClick={() => { setInput(prompt); inputRef.current?.focus() }}
              style={{
                padding: '3px 9px', border: '1px solid rgba(123,163,240,0.25)',
                borderRadius: 999, background: 'rgba(123,163,240,0.08)', color: '#7ba3f0',
                fontSize: 11, fontWeight: 600, fontFamily: 'var(--font-body)',
                cursor: 'pointer', opacity: isTyping ? 0.5 : 1,
              }}
            >
              {prompt}
            </button>
          ))}
        </div>

        <div style={{ position: 'relative' }}>
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            maxLength={600}
            placeholder={mode === 'refinar' ? 'Instruccion de refinamiento...' : 'Pregunta estrategica...'}
            style={{
              width: '100%', padding: '9px 40px 9px 12px',
              border: '1px solid rgba(123,163,240,0.20)', borderRadius: 9,
              background: 'rgba(5,5,140,0.40)', backdropFilter: 'blur(8px)',
              color: '#f5f5ff', fontSize: 13, fontFamily: 'var(--font-body)',
              outline: 'none', boxSizing: 'border-box',
            }}
            onFocus={(e) => { e.currentTarget.style.borderColor = '#7ba3f0'; e.currentTarget.style.boxShadow = '0 0 10px rgba(123,163,240,0.15)' }}
            onBlur={(e) => { e.currentTarget.style.borderColor = 'rgba(123,163,240,0.20)'; e.currentTarget.style.boxShadow = 'none' }}
          />
          <button
            type="submit"
            disabled={isTyping || !input.trim()}
            style={{
              position: 'absolute', right: 5, top: '50%', transform: 'translateY(-50%)',
              padding: 6, borderRadius: 7, border: 'none',
              background: input.trim() ? 'linear-gradient(135deg, #05058c, #7ba3f0)' : 'transparent',
              color: '#7ba3f0', cursor: 'pointer', opacity: isTyping || !input.trim() ? 0.4 : 1,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
            aria-label="Enviar mensaje"
          >
            {isTyping ? <Loader2 size={15} style={{ animation: 'spin 1s linear infinite' }} /> : <Send size={15} color="#ffffff" />}
          </button>
        </div>

        {selectedCaseIds.length > 0 && (
          <p style={{ marginTop: 5, fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', textAlign: 'center' }}>
            {selectedCaseIds.length} caso{selectedCaseIds.length !== 1 ? 's' : ''} seleccionado{selectedCaseIds.length !== 1 ? 's' : ''}
          </p>
        )}
      </form>
    </div>
  )
}

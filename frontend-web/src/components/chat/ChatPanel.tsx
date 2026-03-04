'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import { useDroppable } from '@dnd-kit/core'
import { Send, Bot, Loader2, X, WandSparkles, Copy, CheckCheck, Gauge } from 'lucide-react'
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
  onGenerate?: () => void
  isGenerating?: boolean
}

function formatProposalWithEmojis(input: string): string {
  const raw = input.trim()
  if (!raw) return raw

  let text = raw
    .replace(/(^|\n)\s*(#+\s*)?dolor del cliente\s*:?/gi, '\n🎯 Dolor del Cliente:')
    .replace(/(^|\n)\s*(#+\s*)?solucion propuesta\s*:?/gi, '\n💡 Solución Propuesta:')
    .replace(/(^|\n)\s*(#+\s*)?impacto( y roi)?\s*:?/gi, '\n🚀 Impacto y ROI:')

  const hasExecutiveBlocks = /🎯\s*Dolor del Cliente:/i.test(text) || /💡\s*Solución Propuesta:/i.test(text) || /🚀\s*Impacto y ROI:/i.test(text)
  if (hasExecutiveBlocks) return text.trim()

  const chunks = raw.split(/\n{2,}/).map((c) => c.trim()).filter(Boolean)
  const dolor = chunks[0] ?? raw
  const solucion = chunks[1] ?? 'Definir la solución propuesta con alcance funcional y operativo.'
  const impacto = chunks.slice(2).join('\n\n') || 'Cuantificar impacto económico y métricas de ejecución esperadas.'

  return [
    `🎯 Dolor del Cliente: ${dolor}`,
    `💡 Solución Propuesta: ${solucion}`,
    `🚀 Impacto y ROI: ${impacto}`,
  ].join('\n\n')
}

function inlineFmt(text: string): React.ReactNode {
  return text.split(/(\*\*[^*]+\*\*)/g).map((p, i) =>
    /^\*\*[^*]+\*\*$/.test(p) ? (
      <strong key={i} className="font-semibold text-violet-400">
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
      if (/^#{1,3} /.test(t)) {
        return (
          <h3 key={i} className="mb-1 mt-2 text-sm font-bold leading-relaxed text-zinc-50 first:mt-0">
            {inlineFmt(t.replace(/^#{1,3} /, ''))}
          </h3>
        )
      }
      const lines = t.split('\n')
      if (lines.every((l) => /^[-*] /.test(l.trim()))) {
        return (
          <ul key={i} className="mb-2 list-disc space-y-1 pl-4 text-sm leading-relaxed text-zinc-300">
            {lines.map((l, j) => (
              <li key={j}>{inlineFmt(l.replace(/^[-*] /, ''))}</li>
            ))}
          </ul>
        )
      }
      if (/^\d+\. /.test(lines[0]?.trim() ?? '')) {
        return (
          <ol key={i} className="mb-2 list-decimal space-y-1 pl-5 text-sm leading-relaxed text-zinc-300">
            {lines.map((l, j) => (
              <li key={j}>{inlineFmt(l.replace(/^\d+\. /, ''))}</li>
            ))}
          </ol>
        )
      }
      return (
        <p key={i} className="mb-2 text-sm leading-loose text-zinc-300 last:mb-0">
          {inlineFmt(t)}
        </p>
      )
    })
    .filter(Boolean)
}

export function ChatPanel({ onGenerate, isGenerating }: ChatPanelProps) {
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
        'Listo. Selecciona casos en el panel izquierdo y genera una propuesta, o escribeme una pregunta estrategica.',
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
        content: formatProposalWithEmojis(proposal),
        meta: isRefinement ? 'Propuesta refinada' : 'Propuesta generada',
        isProposal: true,
      },
    ])
    lastProposalRef.current = proposal
  }, [proposal])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isTyping])

  const quickPrompts = useMemo(
    () =>
      mode === 'chat'
        ? [
            'Que 2 casos dan mayor evidencia para esta cuenta?',
            'Dame 3 propuestas de valor ejecutivas.',
            'Que riesgo de implementacion debemos anticipar?',
          ]
        : [
            'Hazla mas ejecutiva en 6 bullets.',
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
        { role: 'assistant', content: 'No hay sesion activa. Completa el formulario de busqueda primero.' },
      ])
      setIsTyping(false)
      return
    }

    try {
      if (mode === 'chat') {
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
              meta: status === 'guardrail_blocked' ? `Guardrail${guardrailCode ? ` (${guardrailCode})` : ''}` : undefined,
            },
          ])
        } else {
          setMessages((prev) => [...prev, { role: 'assistant', content: 'No se recibio respuesta valida.' }])
        }
      } else {
        if (!proposal) {
          setMessages((prev) => [...prev, { role: 'assistant', content: 'Primero genera una propuesta para refinarla.' }])
          setIsTyping(false)
          return
        }
        const response = await apiClient.post(`/agent/${threadId}/refine`, {
          instruction: fullMsg,
          use_client_profile: useClientProfile,
        })
        const refined = response.data?.propuesta_final
        if (typeof refined === 'string' && refined.trim()) {
          setProposal(refined)
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

  const handleGenerateClick = () => {
    if (!onGenerate || isGenerating) return
    onGenerate()
  }

  return (
    <div className="h-full min-h-0 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between gap-3 border-b border-zinc-800 bg-[#121212] p-3" style={{ flexShrink: 0 }}>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md border border-zinc-800 bg-zinc-900 text-violet-400">
            <Bot size={18} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-zinc-50">Asistente de Valor</h3>
            <p className="text-[10px] text-zinc-400">Chat · propuesta · refinamiento</p>
          </div>
        </div>
        <div className="inline-flex rounded-md border border-zinc-800 bg-zinc-900 p-1">
          <button
            type="button"
            onClick={() => setMode('chat')}
            className={`rounded-md px-2.5 py-1 text-[11px] ${mode === 'chat' ? 'bg-violet-400 text-black' : 'text-zinc-300 hover:text-zinc-50'}`}
          >
            Chat
          </button>
          <button
            type="button"
            onClick={() => setMode('refine')}
            disabled={!proposal}
            className={`rounded-md px-2.5 py-1 text-[11px] ${mode === 'refine' ? 'bg-violet-400 text-black' : 'text-zinc-300 hover:text-zinc-50'} disabled:opacity-50`}
          >
            Refinar
          </button>
        </div>
      </div>

      {selectedCaseIds.length > 0 && onGenerate && (
        <>
          <div className="neo-generate-bar flex-shrink-0">
            <span className="inline-flex items-center gap-1 text-[11px] font-mono font-bold text-zinc-400">
              <Gauge className="h-3 w-3 text-violet-400" />
              {selectedCaseIds.length} caso{selectedCaseIds.length > 1 ? 's' : ''} seleccionado{selectedCaseIds.length > 1 ? 's' : ''}
            </span>
            <button
              type="button"
              onClick={handleGenerateClick}
              disabled={Boolean(isGenerating)}
              className="inline-flex items-center gap-1 rounded-md border border-violet-400 bg-violet-400 px-3 py-1 text-[11px] font-bold text-black disabled:opacity-50"
            >
              <WandSparkles size={13} />
              {isGenerating ? 'Generando...' : 'Generar propuesta'}
            </button>
          </div>
          {isGenerating && <NeoLoader compact className="border-t-0 rounded-none" />}
        </>
      )}

      <div
        ref={setDropRef}
        style={{
          padding: '5px 14px',
          fontSize: 10,
          flexShrink: 0,
          color: isDropOver ? '#a78bfa' : '#a1a1aa',
          background: isDropOver ? '#18181b' : 'transparent',
          borderBottom: '1px solid #27272a',
          textAlign: 'center',
        }}
      >
        {isDropOver ? '↓ Suelta aqui para anadir como contexto' : 'Arrastra una ficha de caso aqui para usarla como contexto ->'}
      </div>

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

      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-[#0e0e0e]" aria-live="polite">
        {messages.map((m, idx) => (
          <div key={idx} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {m.isProposal ? (
              <motion.div
                initial={prefersReducedMotion ? false : { opacity: 0, y: 14 }}
                animate={prefersReducedMotion ? undefined : { opacity: 1, y: 0 }}
                transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
                style={{
                  width: '100%',
                  background: '#121212',
                  border: '1px solid #27272a',
                  borderRadius: 6,
                  padding: '12px 14px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <span style={{ fontSize: 10, color: '#a78bfa', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    {m.meta ?? 'Propuesta generada'}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleCopy(m.content, idx)}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 4,
                      fontSize: 10,
                      color: copiedIdx === idx ? '#a78bfa' : '#a1a1aa',
                      background: '#0f0f0f',
                      border: '1px solid #27272a',
                      borderRadius: 6,
                      padding: '2px 7px',
                      cursor: 'pointer',
                    }}
                  >
                    {copiedIdx === idx ? <CheckCheck size={12} /> : <Copy size={12} />}
                    {copiedIdx === idx ? 'Copiado' : 'Copiar'}
                  </button>
                </div>
                <div>{renderMarkdown(m.content)}</div>
              </motion.div>
            ) : (
              <div
                className={`max-w-[88%] rounded-md border p-3 text-sm ${
                  m.role === 'user' ? 'border-violet-400 bg-[#121212] text-zinc-50' : 'border-zinc-800 bg-[#121212] text-zinc-300'
                }`}
              >
                <p style={{ fontSize: 13, lineHeight: 1.75 }}>{m.content}</p>
                {m.meta && <p className="mt-1 text-[10px] text-zinc-400">{m.meta}</p>}
              </div>
            )}
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="flex gap-1 rounded-md border border-zinc-800 bg-[#121212] p-3">
              <span className="h-1.5 w-1.5 animate-bounce rounded-sm bg-zinc-500" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-sm bg-zinc-500 [animation-delay:0.2s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-sm bg-zinc-500 [animation-delay:0.4s]" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form
        className="mt-auto flex-shrink-0 border-t border-zinc-800 bg-[#121212] p-3"
        onSubmit={(e) => {
          e.preventDefault()
          void handleSend()
        }}
      >
        <div className="mb-2 flex flex-wrap gap-1.5">
          {quickPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              disabled={isTyping}
              onClick={() => {
                setInput(prompt)
                inputRef.current?.focus()
              }}
              className="rounded-md border border-zinc-800 bg-zinc-900 px-2 py-1 text-[10px] text-zinc-300 hover:text-zinc-50 disabled:opacity-50"
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
            placeholder={mode === 'chat' ? 'Pregunta estrategica...' : 'Instruccion de refinamiento...'}
            className="w-full rounded-md border border-zinc-800 bg-zinc-900 py-2.5 pl-4 pr-11 text-sm text-zinc-50 placeholder:text-zinc-500 outline-none focus:border-violet-400"
          />
          <button
            type="submit"
            disabled={isTyping || !input.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-violet-400 hover:bg-zinc-900 disabled:opacity-50"
            aria-label="Enviar mensaje"
          >
            {isTyping ? <Loader2 size={17} className="animate-spin" /> : <Send size={17} />}
          </button>
        </div>
      </form>
    </div>
  )
}

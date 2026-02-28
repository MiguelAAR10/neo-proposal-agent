import axios from 'axios'

export function getErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'object' && detail && 'message' in detail) {
      const maybeMessage = (detail as { message?: unknown }).message
      if (typeof maybeMessage === 'string' && maybeMessage.trim()) {
        return maybeMessage
      }
    }
    if (typeof detail === 'string' && detail.trim()) {
      return detail
    }
    if (typeof error.message === 'string' && error.message.trim()) {
      return error.message
    }
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message
  }

  return fallback
}

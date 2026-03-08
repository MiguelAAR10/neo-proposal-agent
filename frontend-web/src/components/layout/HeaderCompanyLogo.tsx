'use client'

import { useMemo, useState } from 'react'
import Image from 'next/image'
import type { Client } from '@/stores/appStore'

interface HeaderCompanyLogoProps {
  selectedClient: Client | null
}

function slugifyCompany(value: string): string {
  return value.trim().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\s+/g, '-')
}

function getInitials(value: string): string {
  return value
    .split(/\s+/)
    .map((part) => part[0] ?? '')
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

export function HeaderCompanyLogo({ selectedClient }: HeaderCompanyLogoProps) {
  const [failedLogos, setFailedLogos] = useState<Record<string, true>>({})

  const companyLogoSrc = useMemo(() => {
    if (!selectedClient?.name) return null
    return `/logos/companies/${slugifyCompany(selectedClient.name)}.png`
  }, [selectedClient])

  const logoError = companyLogoSrc ? Boolean(failedLogos[companyLogoSrc]) : false

  if (selectedClient && logoError) {
    return (
      <div className="neo-header-company-logo" aria-label={selectedClient.display_name}>
        <span className="neo-header-company-logo__fallback">
          {getInitials(selectedClient.display_name || selectedClient.name)}
        </span>
      </div>
    )
  }

  if (selectedClient && companyLogoSrc) {
    return (
      <div className="neo-header-company-logo">
        <Image
          src={companyLogoSrc}
          alt={`Logo ${selectedClient.display_name}`}
          width={44}
          height={44}
          className="neo-header-company-logo__img"
          onError={() => setFailedLogos((prev) => ({ ...prev, [companyLogoSrc]: true }))}
          unoptimized
        />
      </div>
    )
  }

  return (
    <div className="neo-header-company-logo">
      <Image
        src="/logos/neo-primary.svg"
        alt="Neo Intelligence"
        width={44}
        height={44}
        className="neo-header-company-logo__img neo-header-company-logo__img--neo"
        priority
        unoptimized
      />
    </div>
  )
}

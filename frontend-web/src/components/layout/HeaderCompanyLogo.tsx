'use client'

import { useState } from 'react'
import Image from 'next/image'

const CONSULTORA_LOGO_SRC = '/logos/brand/consultora-primary.png'

export function HeaderCompanyLogo() {
  const [brandLogoFailed, setBrandLogoFailed] = useState(false)

  return (
    brandLogoFailed ? (
      <div className="neo-header-company-logo neo-header-company-logo--fallback">
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
    ) : (
      <div className="neo-header-company-logo neo-header-company-logo--brand">
        <Image
          src={CONSULTORA_LOGO_SRC}
          alt="Logo consultora"
          width={164}
          height={44}
          className="neo-header-company-logo__img neo-header-company-logo__img--brand"
          onError={() => setBrandLogoFailed(true)}
          priority
          unoptimized
        />
      </div>
    )
  )
}

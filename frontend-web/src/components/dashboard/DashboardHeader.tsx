"use client";

import { useEffect, useMemo, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Building, RefreshCcw, LayoutDashboard } from "lucide-react";

interface DashboardHeaderProps {
  companyLabel: string;
  companyValue: string;
  companyOptions: Array<{ value: string; label: string }>;
  onCompanyChange: (value: string) => void;
  onReset: () => void;
}

function slugifyCompany(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, "");
}

export function DashboardHeader({
  companyLabel,
  companyValue,
  companyOptions,
  onCompanyChange,
  onReset,
}: DashboardHeaderProps) {
  const [logoFailed, setLogoFailed] = useState(false);
  const companyLogoSrc = useMemo(() => {
    const slug = slugifyCompany(companyValue);
    return slug ? `/logos/${slug}.png` : "";
  }, [companyValue]);

  useEffect(() => {
    setLogoFailed(false);
  }, [companyLogoSrc]);

  return (
    <header className="neo-main-header">
      <div className="neo-main-header__left">
        <Image
          src="/logos/neo-primary.svg"
          alt="NEO Logo"
          width={180}
          height={52}
          className="h-11 w-auto"
          priority
        />
        <div className="neo-main-header__meta">
          <p className="neo-main-header__title">NEO Commercial Intelligence</p>
          <p className="neo-main-header__subtitle">{companyLabel || "Exploración abierta por problema"}</p>
        </div>
      </div>
      <div className="neo-main-header__center">
        <input
          value={companyValue}
          onChange={(event) => onCompanyChange(event.target.value)}
          list="neo-company-targets"
          className="neo-main-header__search"
          placeholder="Selecciona empresa objetivo..."
        />
        <datalist id="neo-company-targets">
          {companyOptions.map((item) => (
            <option key={item.value} value={item.value}>
              {item.label}
            </option>
          ))}
        </datalist>
      </div>
      <div className="neo-main-header__right">
        <div className="neo-company-badge" title={companyValue || "Sin empresa seleccionada"}>
          <span className="neo-company-badge__logo">
            {!logoFailed && companyLogoSrc ? (
              <Image
                src={companyLogoSrc}
                alt={`Logo ${companyValue}`}
                width={22}
                height={22}
                className="neo-company-badge__logo-img"
                onError={() => setLogoFailed(true)}
                unoptimized
              />
            ) : (
              <Building className="h-4 w-4 text-zinc-400" />
            )}
          </span>
          <div className="neo-company-badge__meta">
            <span className="neo-company-badge__label">Empresa objetivo</span>
            <span className="neo-company-badge__value">{companyValue || "Sin seleccionar"}</span>
          </div>
        </div>
        <Link href="/ops" className="neo-pill neo-pill--header">
          <LayoutDashboard className="h-4 w-4" />
          Panel Ops
        </Link>
        <button type="button" onClick={onReset} className="neo-pill neo-pill--header">
          <RefreshCcw className="h-4 w-4" />
          Reiniciar
        </button>
      </div>
    </header>
  );
}

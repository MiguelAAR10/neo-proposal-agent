"use client";

import Image from "next/image";
import Link from "next/link";
import { RefreshCcw, LayoutDashboard } from "lucide-react";

interface DashboardHeaderProps {
  companyLabel: string;
  companyValue: string;
  companyOptions: Array<{ value: string; label: string }>;
  onCompanyChange: (value: string) => void;
  onReset: () => void;
}

export function DashboardHeader({
  companyLabel,
  companyValue,
  companyOptions,
  onCompanyChange,
  onReset,
}: DashboardHeaderProps) {
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

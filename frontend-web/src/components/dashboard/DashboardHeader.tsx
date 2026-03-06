"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Building, RefreshCcw, LayoutDashboard, ChevronDown, Check } from "lucide-react";

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
    .replace(/\s+/g, "-");
}

export function DashboardHeader({
  companyLabel,
  companyValue,
  companyOptions,
  onCompanyChange,
  onReset,
}: DashboardHeaderProps) {
  const [logoFailed, setLogoFailed] = useState(false);
  const [clientLogoFailed, setClientLogoFailed] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const companyLogoSrc = useMemo(() => {
    const slug = slugifyCompany(companyValue);
    return slug ? `/logos/companies/${slug}.png` : "";
  }, [companyValue]);

  useEffect(() => {
    setLogoFailed(false);
  }, [companyLogoSrc]);

  // Close dropdown on outside click
  useEffect(() => {
    if (!isDropdownOpen) return;
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [isDropdownOpen]);

  const handleSelectCompany = useCallback(
    (value: string) => {
      onCompanyChange(value);
      setIsDropdownOpen(false);
    },
    [onCompanyChange],
  );

  return (
    <header className="neo-main-header">
      {/* Left: Official logo + separator + title */}
      <div className="flex items-center gap-6 pl-4">
        <Image
          src={clientLogoFailed ? "/logos/neo-primary.svg" : "/logos/client-logo.png"}
          alt="NEO 25 Años"
          width={180}
          height={52}
          className="h-10 w-auto object-contain brightness-0 invert opacity-95"
          priority
          unoptimized
          onError={() => setClientLogoFailed(true)}
        />
        <div className="h-8 w-px bg-[#7ba3f0]/30 hidden md:block" />
        <h1 className="text-[#f5f5ff] text-xl font-serif tracking-wide m-0 hidden md:block">
          Commercial Intelligence
        </h1>
      </div>

      {/* Center: Company logo selector dropdown */}
      <div className="neo-main-header__center" ref={dropdownRef} style={{ position: "relative" }}>
        <button
          type="button"
          onClick={() => setIsDropdownOpen((prev) => !prev)}
          className="neo-company-selector-trigger"
          aria-expanded={isDropdownOpen}
          aria-haspopup="listbox"
        >
          <span className="neo-company-selector-trigger__logo">
            {!logoFailed && companyLogoSrc ? (
              <Image
                src={companyLogoSrc}
                alt={companyValue}
                width={28}
                height={28}
                className="neo-company-badge__logo-img"
                onError={() => setLogoFailed(true)}
                unoptimized
              />
            ) : (
              <Building className="h-5 w-5 text-[#7ba3f0]" />
            )}
          </span>
          <span className="neo-company-selector-trigger__text">
            {companyValue || "Selecciona empresa"}
          </span>
          <ChevronDown
            className="h-4 w-4 text-[#a8b8e8]"
            style={{
              marginLeft: "auto",
              transition: "transform 200ms ease",
              transform: isDropdownOpen ? "rotate(180deg)" : "rotate(0deg)",
            }}
          />
        </button>

        {/* Dropdown grid */}
        {isDropdownOpen && (
          <div className="neo-company-dropdown" role="listbox" aria-label="Seleccionar empresa">
            <div className="neo-company-dropdown__grid">
              {companyOptions.map((option) => {
                const slug = slugifyCompany(option.value);
                const logoPath = `/logos/companies/${slug}.png`;
                const isSelected = option.value === companyValue;
                return (
                  <button
                    key={option.value}
                    type="button"
                    role="option"
                    aria-selected={isSelected}
                    className={`neo-company-card${isSelected ? " neo-company-card--selected" : ""}`}
                    onClick={() => handleSelectCompany(option.value)}
                  >
                    <span className="neo-company-card__logo">
                      <Image
                        src={logoPath}
                        alt={option.label}
                        width={36}
                        height={36}
                        className="neo-company-card__logo-img"
                        unoptimized
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = "none";
                        }}
                      />
                    </span>
                    <span className="neo-company-card__name">{option.label}</span>
                    {isSelected && <Check className="neo-company-card__check" />}
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Right: company badge + actions */}
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
              <Building className="h-4 w-4 text-[#7ba3f0]" />
            )}
          </span>
          <div className="neo-company-badge__meta">
            <span className="neo-company-badge__label">Empresa objetivo</span>
            <span className="neo-company-badge__value">{companyValue || "Sin seleccionar"}</span>
          </div>
        </div>
        <Link href="/ops" className="neo-header-action-btn">
          <LayoutDashboard className="h-4 w-4" />
          Panel Ops
        </Link>
        <button type="button" onClick={onReset} className="neo-header-action-btn">
          <RefreshCcw className="h-4 w-4" />
          Reiniciar
        </button>
      </div>
    </header>
  );
}

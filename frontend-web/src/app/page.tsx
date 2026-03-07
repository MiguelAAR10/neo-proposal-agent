"use client";

import { useCallback } from "react";
import dynamic from "next/dynamic";
import Image from "next/image";
import Link from "next/link";
import { LayoutDashboard, RefreshCcw, User } from "lucide-react";
import { useAppStore } from "@/stores/appStore";
import { AppTabs } from "@/components/layout/AppTabs";
import { EmptyState } from "@/components/screens/EmptyState";
import { ClientSelectionForm } from "@/components/screens/ClientSelectionForm";
import { ActiveWorkspace } from "@/components/screens/ActiveWorkspace";

// Lazy-load screens that are not on the critical path
const ProfileInsights = dynamic(() =>
  import("@/components/screens/ProfileInsights").then((m) => ({ default: m.ProfileInsights })),
  { ssr: false }
);
const ProposalReview = dynamic(() =>
  import("@/components/screens/ProposalReview").then((m) => ({ default: m.ProposalReview })),
  { ssr: false }
);
const TeamAssignment = dynamic(() =>
  import("@/components/screens/TeamAssignment").then((m) => ({ default: m.TeamAssignment })),
  { ssr: false }
);

export default function HomePage() {
  const {
    activeTab,
    setActiveTab,
    activeScreen,
    setActiveScreen,
    selectedClient,
    selectedArea,
    setChatMode,
    reset,
  } = useAppStore();

  const handleStartDiscovery = useCallback(() => {
    setActiveScreen(2);
  }, [setActiveScreen]);

  const handleBackToEmpty = useCallback(() => {
    setActiveScreen(1);
  }, [setActiveScreen]);

  const handleNavigateToInsights = useCallback(() => {
    setActiveScreen(4);
  }, [setActiveScreen]);

  const handleBackToWorkspace = useCallback(() => {
    setActiveScreen(3);
  }, [setActiveScreen]);

  const handleAcceptProposal = useCallback(() => {
    setActiveScreen(6);
  }, [setActiveScreen]);

  const handleRejectProposal = useCallback(() => {
    setChatMode("refinar");
    setActiveScreen(3);
  }, [setChatMode, setActiveScreen]);

  const handleSendToTeam = useCallback(() => {
    // Future: POST /agent/{tid}/assign
    setActiveScreen(1);
    reset();
  }, [setActiveScreen, reset]);

  const handleReset = useCallback(() => {
    reset();
  }, [reset]);

  // Determine client label for header
  const clientLabel = selectedClient
    ? `${selectedClient.display_name}${selectedArea ? ` · ${selectedArea}` : ""}`
    : null;

  return (
    <main className="neo-two-panel-page">
      {/* ── Top Header ── */}
      <header className="neo-main-header">
        {/* Left: Logo */}
        <div className="neo-main-header__left">
          <Image
            src="/logos/neo-primary.svg"
            alt="Neo Intelligence"
            width={160}
            height={44}
            className="neo-header-logo"
            priority
            unoptimized
          />
        </div>

        {/* Center: Client tag + Tabs */}
        <div className="neo-main-header__center">
          {clientLabel && (
            <span className="neo-client-badge">
              {clientLabel}
            </span>
          )}
          <AppTabs activeTab={activeTab} onTabChange={setActiveTab} />
        </div>

        {/* Right: Actions + Avatar */}
        <div className="neo-main-header__right">
          <Link href="/ops" className="neo-header-action-btn">
            <LayoutDashboard className="h-4 w-4" />
            Panel Ops
          </Link>
          <button type="button" onClick={handleReset} className="neo-header-action-btn">
            <RefreshCcw className="h-4 w-4" />
            Reiniciar
          </button>
          <div className="neo-avatar">
            <User size={16} />
          </div>
        </div>
      </header>

      {/* ── Screen Router ── */}
      <div className="neo-two-panel-container">
        {activeScreen === 1 && (
          <EmptyState onStart={handleStartDiscovery} />
        )}

        {activeScreen === 2 && (
          <ClientSelectionForm onBack={handleBackToEmpty} />
        )}

        {activeScreen === 3 && (
          <ActiveWorkspace onNavigateToInsights={handleNavigateToInsights} />
        )}

        {activeScreen === 4 && (
          <ProfileInsights onBack={handleBackToWorkspace} />
        )}

        {activeScreen === 5 && (
          <ProposalReview
            onAccept={handleAcceptProposal}
            onReject={handleRejectProposal}
          />
        )}

        {activeScreen === 6 && (
          <TeamAssignment onSend={handleSendToTeam} />
        )}
      </div>
    </main>
  );
}

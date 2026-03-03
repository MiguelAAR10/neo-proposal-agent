"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { getErrorMessage } from "@/lib/error";
import { useAgentStore } from "@/stores/agentStore";
import type { DashboardControls, DraggableContextCard, DroppableCaseCard, SourceSwitch } from "@/types/dashboard";

interface CatalogEntry {
  name: string;
  display_name: string;
  vertical: string;
}

const FALLBACK_CATALOG: CatalogEntry[] = [
  { name: "BCP", display_name: "BCP", vertical: "Banca" },
  { name: "INTERBANK", display_name: "Interbank", vertical: "Banca" },
  { name: "BBVA", display_name: "BBVA", vertical: "Banca" },
  { name: "ALICORP", display_name: "Alicorp", vertical: "Consumo masivo" },
  { name: "RIMAC", display_name: "Rimac", vertical: "Seguros" },
  { name: "PACIFICO", display_name: "Pacifico", vertical: "Seguros" },
  { name: "SCOTIABANK", display_name: "Scotiabank", vertical: "Banca" },
  { name: "MIBANCO", display_name: "MiBanco", vertical: "Microfinanzas" },
  { name: "CREDICORP", display_name: "Credicorp", vertical: "Servicios financieros" },
  { name: "PLAZA VEA", display_name: "Plaza Vea", vertical: "Retail" },
  { name: "FALABELLA", display_name: "Falabella", vertical: "Retail" },
  { name: "SODIMAC", display_name: "Sodimac", vertical: "Retail" },
];

export const AREA_OPTIONS = [
  "Comercial",
  "Operaciones",
  "Finanzas",
  "Marketing",
  "TI",
  "Innovación",
  "Atención al cliente",
  "Supply Chain",
];

export const DEFAULT_CONTEXT_CARDS: DraggableContextCard[] = [
  {
    id: "ctx-fraude-global",
    title: "Fraude Global",
    category: "risk",
    summary: "Escalada de fraude digital y presión regulatoria en banca/seguros.",
    severity: "high",
  },
  {
    id: "ctx-friccion-5min",
    title: "Fricción >5 min",
    category: "signal",
    summary: "Procesos críticos con tiempos de resolución mayores a 5 minutos.",
    severity: "medium",
  },
  {
    id: "ctx-riesgo-ia",
    title: "Riesgo IA",
    category: "macro",
    summary: "Gobierno y trazabilidad de modelos IA como condición de adopción.",
    severity: "high",
  },
  {
    id: "ctx-costos-operativos",
    title: "Costo Operativo",
    category: "opportunity",
    summary: "Capacidad de reducción OPEX con automatización orientada a evidencia.",
    severity: "medium",
  },
];

function mapCase(raw: Record<string, unknown>): DroppableCaseCard {
  const id = String(raw.id ?? raw.case_id ?? "");
  return {
    id,
    caseId: String(raw.case_id ?? id),
    tipo: String(raw.tipo ?? "AI").toUpperCase() === "NEO" ? "NEO" : "AI",
    titulo: String(raw.titulo ?? "Caso sin título"),
    empresa: String(raw.empresa ?? "N/A"),
    industria: String(raw.industria ?? "N/A"),
    area: String(raw.area ?? "N/A"),
    problema: String(raw.problema ?? "Sin detalle"),
    solucion: String(raw.solucion ?? "Sin detalle"),
    beneficios: Array.isArray(raw.beneficios)
      ? (raw.beneficios as string[])
      : raw.beneficios
        ? String(raw.beneficios)
        : undefined,
    tecnologias: Array.isArray(raw.tecnologias)
      ? (raw.tecnologias as string[]).map((value) => String(value))
      : [],
    kpiImpacto: raw.kpi_impacto ? String(raw.kpi_impacto) : undefined,
    urlSlide: raw.url_slide ? String(raw.url_slide) : undefined,
    score: Number(raw.score ?? raw.score_raw ?? 0),
    scoreRaw: Number(raw.score_raw ?? raw.score ?? 0),
    scoreClientFit: raw.score_client_fit ? Number(raw.score_client_fit) : undefined,
    matchType: raw.match_type ? String(raw.match_type) : undefined,
    matchReason: raw.match_reason ? String(raw.match_reason) : undefined,
  };
}

export function useDashboardController() {
  const store = useAgentStore();
  const {
    threadId,
    empresa,
    area,
    proposal,
    cases,
    selectedCaseIds,
    setSession,
    setProposal,
    selectCase,
    setError,
    setWarning,
    setLoading,
    reset,
  } = store;

  const [searchBridge, setSearchBridge] = useState("");
  const [dragMessage, setDragMessage] = useState<string | null>(null);
  const [controls, setControls] = useState<DashboardControls>({
    empresa: "BCP",
    rubro: "Banca",
    area: "Comercial",
    switch: "both",
    problema: "",
  });
  const [contextCards] = useState<DraggableContextCard[]>(DEFAULT_CONTEXT_CARDS);

  const catalogQuery = useQuery({
    queryKey: ["prioritized-clients"],
    queryFn: async () => {
      const response = await apiClient.get("/api/prioritized-clients");
      const raw = Array.isArray(response.data?.catalog) ? (response.data.catalog as CatalogEntry[]) : [];
      return raw.length > 0 ? raw : FALLBACK_CATALOG;
    },
    staleTime: 1000 * 60 * 10,
  });

  const catalog = catalogQuery.data ?? FALLBACK_CATALOG;

  const searchMutation = useMutation({
    mutationFn: async () => {
      setLoading(true);
      const response = await apiClient.post("/agent/start", controls);
      return response.data;
    },
    onSuccess: (data) => {
      const mappedCases: DroppableCaseCard[] = Array.isArray(data.casos_encontrados)
        ? data.casos_encontrados.map((item: Record<string, unknown>) => mapCase(item))
        : [];
      setSession({
        threadId: String(data.thread_id),
        empresa: String(data.empresa ?? controls.empresa),
        area: String(data.area ?? controls.area),
        problema: String(data.problema ?? controls.problema),
        cases: mappedCases,
        neoCases: mappedCases.filter((item) => item.tipo === "NEO"),
        aiCases: mappedCases.filter((item) => item.tipo === "AI"),
        topMatchGlobal: null,
        topMatchGlobalReason: null,
        perfil: data.perfil_cliente ?? null,
        profileStatus: data.profile_status ?? null,
        inteligenciaSector: data.inteligencia_sector ?? null,
        warning: data.warning ?? null,
      });
      setError(null);
      setWarning(data.warning ?? null);
      setLoading(false);
    },
    onError: (error: unknown) => {
      setError(getErrorMessage(error, "No se pudo ejecutar la búsqueda."));
      setLoading(false);
    },
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      if (!threadId) throw new Error("No hay sesión activa");
      if (selectedCaseIds.length === 0) throw new Error("Arrastra al menos un caso a Propuesta de Valor");
      const response = await apiClient.post(`/agent/${threadId}/select`, {
        case_ids: selectedCaseIds,
      });
      return response.data;
    },
    onSuccess: (data) => {
      setProposal(String(data.propuesta_final ?? ""));
      setWarning(data.warning ?? null);
      setError(null);
    },
    onError: (error: unknown) => {
      setError(getErrorMessage(error, "No se pudo generar la propuesta."));
    },
  });

  const visibleCases = useMemo(() => {
    const q = searchBridge.trim().toLowerCase();
    const mapped = cases as unknown as DroppableCaseCard[];
    if (!q) return mapped;
    return mapped.filter((item) =>
      `${item.titulo} ${item.empresa} ${item.problema} ${item.matchReason ?? ""}`.toLowerCase().includes(q),
    );
  }, [cases, searchBridge]);

  const submitContextInsight = async (contextCard: DraggableContextCard): Promise<void> => {
    const companyId = (empresa || controls.empresa || "GENERAL").trim();
    await apiClient.post(`/intel/company/${encodeURIComponent(companyId)}/insights`, {
      author: "Dashboard Context DnD",
      text: `Contexto ${contextCard.title}: ${contextCard.summary}`,
      source: "drag_context_dashboard",
    });
    setDragMessage(`Contexto inyectado: ${contextCard.title}`);
  };

  const submitCaseInsight = async (caseCard: DroppableCaseCard): Promise<void> => {
    const companyId = (empresa || controls.empresa || "GENERAL").trim();
    await apiClient.post(`/intel/company/${encodeURIComponent(companyId)}/insights`, {
      author: "Dashboard DragDrop",
      text: [
        `Caso: ${caseCard.titulo}`,
        `Problema: ${caseCard.problema}`,
        `Solución: ${caseCard.solucion}`,
        `Impacto: ${caseCard.kpiImpacto ?? "N/A"}`,
      ].join(" | "),
      source: "drag_case_dashboard",
    });
    setDragMessage(`Insight de caso procesado: ${caseCard.titulo}`);
  };

  const onDropCase = async (caseCard: DroppableCaseCard): Promise<void> => {
    if (!selectedCaseIds.includes(caseCard.id)) selectCase(caseCard.id);
    await submitCaseInsight(caseCard);
  };

  const onDropContext = async (contextCard: DraggableContextCard): Promise<void> => {
    await submitContextInsight(contextCard);
  };

  const onCompanyChange = (companyName: string) => {
    const found = catalog.find((entry) => entry.name === companyName);
    setControls((prev) => ({
      ...prev,
      empresa: companyName,
      rubro: found?.vertical ?? prev.rubro,
    }));
  };

  return {
    threadId,
    empresa,
    area,
    proposal,
    selectedCaseIds,
    controls,
    setControls,
    searchBridge,
    setSearchBridge,
    contextCards,
    catalog,
    visibleCases,
    dragMessage,
    onCompanyChange,
    onDropCase,
    onDropContext,
    searchMutation,
    generateMutation,
    reset,
  };
}

export type { SourceSwitch };


export type SourceSwitch = "neo" | "ai" | "both";

export interface DroppableCaseCard {
  id: string;
  caseId?: string;
  tipo: "AI" | "NEO";
  titulo: string;
  empresa: string;
  industria: string;
  area: string;
  problema: string;
  solucion: string;
  beneficios?: string[] | string;
  tecnologias: string[];
  kpiImpacto?: string;
  urlSlide?: string;
  score: number;
  scoreRaw: number;
  scoreClientFit?: number;
  matchType?: "exacto" | "relacionado" | "inspiracional" | string;
  matchReason?: string;
}

export interface DraggableContextCard {
  id: string;
  title: string;
  category: "macro" | "risk" | "opportunity" | "signal";
  summary: string;
  severity: "low" | "medium" | "high";
}

export interface DashboardControls {
  empresa: string;
  rubro: string;
  area: string;
  switch: SourceSwitch;
  problema: string;
}

export interface DashboardState {
  threadId: string | null;
  loading: boolean;
  generating: boolean;
  dragLoading: boolean;
  error: string | null;
  warning: string | null;
  proposal: string;
  searchQuery: string;
  controls: DashboardControls;
  cases: DroppableCaseCard[];
  contextCards: DraggableContextCard[];
  droppedCaseIds: string[];
  intelEvents: Array<{
    caseId: string;
    companyId: string;
    createdAt: string;
    status: "success" | "error";
    message: string;
  }>;
}

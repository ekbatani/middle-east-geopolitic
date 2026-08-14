"use client";

import React, { useState, useEffect } from "react";
import { AuthProvider } from "../context/AuthContext";
import { Navbar } from "../components/layout/Navbar";
import { Sidebar, NavSection } from "../components/layout/Sidebar";
import { IntelligenceDashboard } from "../components/intelligence/IntelligenceDashboard";
import { GeospatialMapView } from "../components/map/GeospatialMapView";
import { NetworkGraphView } from "../components/graph/NetworkGraphView";
import { RiskEngineView } from "../components/risks/RiskEngineView";
import { ScenariosView } from "../components/scenarios/ScenariosView";
import { ForecastsView } from "../components/forecasts/ForecastsView";
import { ReportsView } from "../components/reports/ReportsView";
import { InvestigationsView } from "../components/investigations/InvestigationsView";
import { MonitorsView } from "../components/monitors/MonitorsView";
import { ActorsView } from "../components/actors/ActorsView";
import { ClaimsView } from "../components/claims/ClaimsView";
import { ReviewQueueView } from "../components/review/ReviewQueueView";
import { DisagreementsView } from "../components/analysis/DisagreementsView";
import { ImageryView } from "../components/imagery/ImageryView";
import { SourcesView } from "../components/sources/SourcesView";
import { reviewService } from "../services";

function MainApp() {
  const [activeSection, setActiveSection] = useState<NavSection>("dashboard");
  const [pendingReviewCount, setPendingReviewCount] = useState<number>(0);

  useEffect(() => {
    async function checkReviewQueue() {
      try {
        const pending = await reviewService.listPending({ status: "pending", limit: 100 });
        setPendingReviewCount(pending.length);
      } catch {
        // ignore if offline
      }
    }
    checkReviewQueue();
    const interval = setInterval(checkReviewQueue, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleQuickAction = (action: string) => {
    if (action === "daily_brief") {
      setActiveSection("reports");
    } else if (action === "submit_source") {
      setActiveSection("sources");
    }
  };

  const renderActiveSection = () => {
    switch (activeSection) {
      case "dashboard":
        return <IntelligenceDashboard onNavigate={(s) => setActiveSection(s as NavSection)} />;
      case "map":
        return <GeospatialMapView />;
      case "graph":
        return <NetworkGraphView />;
      case "risks":
        return <RiskEngineView />;
      case "scenarios":
        return <ScenariosView />;
      case "forecasts":
        return <ForecastsView />;
      case "reports":
        return <ReportsView />;
      case "investigations":
        return <InvestigationsView />;
      case "monitors":
        return <MonitorsView />;
      case "actors":
        return <ActorsView />;
      case "claims":
        return <ClaimsView />;
      case "review":
        return <ReviewQueueView />;
      case "disagreements":
        return <DisagreementsView />;
      case "imagery":
        return <ImageryView />;
      case "sources":
        return <SourcesView />;
      default:
        return <IntelligenceDashboard onNavigate={(s) => setActiveSection(s as NavSection)} />;
    }
  };

  return (
    <div className="min-h-screen bg-[#06080f] text-slate-100 flex flex-col font-sans selection:bg-sky-600 selection:text-white">
      {/* Top Navigation */}
      <Navbar onOpenQuickAction={handleQuickAction} activeSection={activeSection} />

      {/* Main Workspace Layout */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          activeSection={activeSection}
          onSelectSection={setActiveSection}
          pendingReviewCount={pendingReviewCount}
        />

        {/* Dynamic Main Section */}
        <main className="flex-1 p-6 overflow-y-auto custom-scrollbar h-[calc(100vh-4rem)]">
          <div className="max-w-7xl mx-auto">{renderActiveSection()}</div>
        </main>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}

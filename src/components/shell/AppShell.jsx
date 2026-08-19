import { useEffect } from "react";
import { useLocation, useOutlet, useParams } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import ComplianceFooter from "../ComplianceFooter";
import PageTransition from "../PageTransition";
import GlobalHeader from "./GlobalHeader";
import TabBar from "./TabBar";
import { useApp } from "../../context/AppContext";
import { writeLastGroupId } from "../../utils/routes";
import "./shell.css";

export default function AppShell() {
  const location = useLocation();
  const { groupId } = useParams();
  const { groups } = useApp();

  // useOutlet (not <Outlet/>) so AnimatePresence holds on to the *old* route
  // element while it exits. <Outlet/> reads live context and would swap to the
  // incoming route mid-exit.
  const outlet = useOutlet();

  // Only remember groups the user is actually a member of, so the "/" resolver
  // can never send them somewhere that 403s.
  useEffect(() => {
    if (groupId && groups.some((g) => String(g.id) === String(groupId))) {
      writeLastGroupId(groupId);
    }
  }, [groupId, groups]);

  return (
    <div className="app-shell">
      <GlobalHeader />
      <main className="app-shell-main">
        <AnimatePresence mode="wait">
          <PageTransition key={location.pathname}>{outlet}</PageTransition>
        </AnimatePresence>
        <ComplianceFooter />
      </main>
      <TabBar />
    </div>
  );
}

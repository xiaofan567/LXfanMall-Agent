import { Outlet } from "react-router";
import { TopBar } from "./TopBar";
import { Footer } from "./Footer";
import { AIFloatingBall } from "./AIFloatingBall";

export function Layout() {
  return (
    <div className="min-h-screen bg-[#f5f5f5]">
      {/* Sticky top bar */}
      <div className="sticky top-0 z-40 shadow-md">
        <TopBar />
      </div>

      {/* Main route content goes here */}
      <Outlet />

      {/* Footer */}
      <Footer />

      {/* Fixed AI floating ball */}
      <AIFloatingBall />
    </div>
  );
}
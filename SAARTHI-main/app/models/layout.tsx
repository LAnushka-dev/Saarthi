import type { ReactNode } from "react";
import ModelSidebar from "../components/ModelSidebar";

export default function ModelsLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-slate-950 to-slate-900 text-white">
      <div className="mx-auto flex min-h-screen max-w-[1600px] flex-col md:flex-row">
        <ModelSidebar />
        <main className="flex-1 p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}

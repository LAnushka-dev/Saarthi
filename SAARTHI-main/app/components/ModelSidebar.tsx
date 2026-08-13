"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MODEL_CATALOG } from "../data/modelCatalog";

export default function ModelSidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-full border-r border-green-900/70 bg-black/80 p-4 md:w-80">
      <div className="mb-5 rounded-lg border border-green-900/60 bg-slate-950/80 p-4">
        <h2 className="text-lg font-bold text-green-400">SAARTHI ML Models</h2>
        <p className="mt-1 text-xs text-slate-300">
          Green + blue theme across all model pages.
        </p>
        <Link
          href="/"
          className="mt-3 inline-block rounded-md bg-green-700 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-green-600"
        >
          Back to World Map
        </Link>
      </div>

      <nav className="space-y-2">
        {MODEL_CATALOG.map((model) => {
          const active = pathname === model.path;
          return (
            <Link
              key={model.id}
              href={model.path}
              className={`block rounded-lg border px-3 py-3 transition ${
                active
                  ? "border-blue-500 bg-blue-900/30"
                  : "border-green-900/50 bg-black/40 hover:border-green-600 hover:bg-green-900/20"
              }`}
            >
              <p className="text-sm font-semibold text-green-300">{model.name}</p>
              <p className="mt-1 text-xs text-slate-300">{model.description}</p>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}

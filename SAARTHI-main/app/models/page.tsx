import { MODEL_CATALOG } from "../data/modelCatalog";
import Link from "next/link";

export default function ModelsHomePage() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-green-400 md:text-3xl">
        Model Dashboard
      </h1>
      <p className="mt-2 max-w-3xl text-sm text-slate-300">
        Select any ML model from the sidebar or from the cards below. Each model
        has a dedicated frontend page with the same green and blue design scheme.
      </p>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {MODEL_CATALOG.map((model) => (
          <Link
            href={model.path}
            key={model.id}
            className="rounded-xl border border-green-900/50 bg-black/40 p-4 transition hover:border-blue-500"
          >
            <h2 className="text-lg font-semibold text-blue-300">{model.name}</h2>
            <p className="mt-2 text-sm text-slate-300">{model.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

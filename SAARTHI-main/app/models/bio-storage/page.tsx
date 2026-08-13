import { readFile } from "node:fs/promises";
import path from "node:path";

export default async function BioStoragePage() {
  const htmlPath = path.join(
    process.cwd(),
    "ML model",
    "biomodel",
    "crop_storage_model.html"
  );

  const originalHtml = await readFile(htmlPath, "utf-8");

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-green-400">Bio Storage Model</h1>
      <p className="text-sm text-slate-300">
        Showing the original biomodel frontend exactly as provided.
      </p>
      <div className="overflow-hidden rounded-xl border border-green-900/50 bg-black/40">
        <iframe
          title="Original Biomodel Frontend"
          srcDoc={originalHtml}
          className="h-[85vh] w-full bg-white"
        />
      </div>
    </div>
  );
}

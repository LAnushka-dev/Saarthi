import { readFile } from "node:fs/promises";
import path from "node:path";

export default async function CropKnowledgePage() {
  const htmlPath = path.join(
    process.cwd(),
    "ML model",
    "agri_intelligence_platform.html"
  );
  const originalHtml = await readFile(htmlPath, "utf-8");
  const pageHtml = originalHtml.replace(
    "</body>",
    "<script>window.addEventListener('load',function(){if(window.switchPage){window.switchPage('m1')}});</script></body>"
  );

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-green-400">Crop Knowledge Engine</h1>
      <p className="text-sm text-slate-300">
        Showing your original integrated frontend (Model 1 tab).
      </p>
      <div className="overflow-hidden rounded-xl border border-green-900/50 bg-black/40">
        <iframe
          title="Original Crop Knowledge Frontend"
          srcDoc={pageHtml}
          className="h-[85vh] w-full bg-white"
        />
      </div>
    </div>
  );
}

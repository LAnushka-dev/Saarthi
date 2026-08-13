"use client";

import { useCallback, useEffect, useState } from "react";

const ROUTE_API = "http://127.0.0.1:8000/api/graph";

export default function RouteOptimizationClient() {
  const [status, setStatus] = useState<"checking" | "ok" | "fail">("checking");
  const [detail, setDetail] = useState("");

  const check = useCallback(async () => {
    setStatus("checking");
    try {
      const r = await fetch(ROUTE_API, { method: "GET", cache: "no-store" });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setStatus("ok");
      setDetail("");
    } catch (e) {
      setStatus("fail");
      setDetail(e instanceof Error ? e.message : "Cannot reach route backend");
    }
  }, []);

  useEffect(() => {
    check();
    const t = setInterval(check, 8000);
    return () => clearInterval(t);
  }, [check]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-green-400">Route Optimization</h1>
      <p className="text-sm text-slate-300">
        This screen loads the original FastAPI + static UI on{" "}
        <code className="text-blue-300">127.0.0.1:8000</code>. Start that server
        in another terminal, or use <code className="text-blue-300">npm run dev:all</code>{" "}
        from the project root to run Next.js and the route backend together.
      </p>

      <div
        className={`rounded-lg border p-3 text-sm ${
          status === "ok"
            ? "border-green-700 bg-green-950/40 text-green-200"
            : status === "fail"
              ? "border-amber-700 bg-amber-950/40 text-amber-100"
              : "border-slate-600 bg-slate-950/60 text-slate-300"
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span>
            Backend:{" "}
            <strong>
              {status === "checking" && "Checking…"}
              {status === "ok" && "Connected"}
              {status === "fail" && "Not reachable"}
            </strong>
            {detail ? ` — ${detail}` : null}
          </span>
          <button
            type="button"
            onClick={check}
            className="rounded border border-slate-500 px-2 py-1 text-xs hover:bg-slate-800"
          >
            Retry
          </button>
        </div>
      </div>

      <div className="rounded-lg border border-blue-900/50 bg-slate-950/70 p-3 font-mono text-[11px] leading-relaxed text-slate-200">
        <div className="mb-1 text-slate-400">Terminal (project root):</div>
        npm run dev:route-opt
        <br />
        <span className="text-slate-500">or both apps:</span> npm run dev:all
      </div>

      <div className="overflow-hidden rounded-xl border border-green-900/50 bg-black/40">
        {status === "ok" ? (
          <iframe
            title="Route Optimization"
            src="http://127.0.0.1:8000/"
            className="h-[85vh] w-full bg-white"
          />
        ) : (
          <div className="flex h-[40vh] items-center justify-center bg-slate-900 px-4 text-center text-sm text-slate-400">
            {status === "checking"
              ? "Looking for the route server on port 8000…"
              : "Start the backend (see commands above), then click Retry or wait for auto-refresh."}
          </div>
        )}
      </div>
    </div>
  );
}

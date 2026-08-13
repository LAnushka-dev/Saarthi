"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Map, { Source, Layer, MapRef } from "react-map-gl/maplibre";
import "maplibre-gl/dist/maplibre-gl.css";
import stateData from "../data/stateData";

type UserRole = "supplier" | "transport" | null;

export default function IndiaMap() {
  const mapRef = useRef<MapRef | null>(null);
  const router = useRouter();

  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const [activeState, setActiveState] = useState<string | null>(null);
  const [role, setRole] = useState<UserRole>(null);

  return (
    <>
      <Map
        ref={mapRef}
        initialViewState={{
          longitude: 78.9629,
          latitude: 20.5937,
          zoom: 4.5
        }}
        style={{ width: "100vw", height: "100vh" }}
        mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
        interactiveLayerIds={["states-fill"]}

        /* 🔥 HOVER */
        onMouseMove={(e) => {
          const map = mapRef.current?.getMap();
          const feature = e.features?.[0];
          if (!map) return;

          if (hoveredId !== null) {
            map.setFeatureState(
              { source: "india", id: hoveredId },
              { hover: false }
            );
          }

          if (feature?.id !== undefined) {
            setHoveredId(feature.id as number);
            map.setFeatureState(
              { source: "india", id: feature.id },
              { hover: true }
            );
          }
        }}

        onMouseLeave={() => {
          const map = mapRef.current?.getMap();
          if (map && hoveredId !== null) {
            map.setFeatureState(
              { source: "india", id: hoveredId },
              { hover: false }
            );
          }
          setHoveredId(null);
        }}

        /* 🔥 CLICK */
        onClick={(e) => {
          const feature = e.features?.[0];
          if (feature?.properties?.name) {
            setActiveState(feature.properties.name);
          }
        }}
      >
        <Source
          id="india"
          type="geojson"
          data="/india_states.geojson"
          generateId
        >
          {/* INTERACTION LAYER */}
          <Layer
            id="states-fill"
            type="fill"
            paint={{
              "fill-color": "#000",
              "fill-opacity": 0
            }}
          />

          {/* STATE BOUNDARIES */}
          <Layer
            id="states-outline"
            type="line"
            paint={{
              "line-color": [
                "case",
                ["boolean", ["feature-state", "hover"], false],
                "#22c55e",
                [
                  "case",
                  ["==", ["get", "name"], activeState],
                  "#22c55e",
                  "#15803d"
                ]
              ],
              "line-width": [
                "case",
                ["==", ["get", "name"], activeState],
                3,
                [
                  "case",
                  ["boolean", ["feature-state", "hover"], false],
                  2.5,
                  1.2
                ]
              ]
            }}
          />
        </Source>
      </Map>

      {/* 🔥 RIGHT SIDEBAR */}
      <aside className="absolute top-0 right-0 h-full w-80 bg-black/90 text-white p-5 border-l border-green-900 overflow-y-auto">

        {/* 📍 STATE OVERVIEW */}
        {activeState && stateData[activeState] && (
          <div className="mb-6 pb-4 border-b border-gray-700">
            <h2 className="text-xl font-bold text-green-400 mb-2">
              {activeState}
            </h2>

            <div className="space-y-1 text-sm">
              <div>🌾 Demand: {stateData[activeState].demand}</div>
              <div>📦 Supply: {stateData[activeState].supply}</div>
              <div>🚚 Trucks: {stateData[activeState].trucks}</div>
              <div>❄️ Cold Storage: {stateData[activeState].coldStorage}</div>

              <span
                className={`inline-block mt-2 px-3 py-1 rounded text-xs ${
                  stateData[activeState].urgency === "high"
                    ? "bg-red-600"
                    : stateData[activeState].urgency === "medium"
                    ? "bg-yellow-500 text-black"
                    : "bg-green-600"
                }`}
              >
                Urgency: {stateData[activeState].urgency}
              </span>
            </div>
          </div>
        )}

        {/* 🔐 LOGIN OPTIONS (NAVIGATION) */}
        {!role && (
          <div className="mb-6">
            <h3 className="font-semibold mb-3 text-gray-300">
              Login as
            </h3>

            <button
              onClick={() => router.push("/login/supplier")}
              className="w-full mb-3 px-4 py-3 rounded bg-green-700 hover:bg-green-600 transition text-left"
            >
              🌾 Supplier
              <div className="text-xs text-green-200">
                Farmers • Mandis • Warehouses
              </div>
            </button>

            <button
              onClick={() => router.push("/login/transporter")}
              className="w-full px-4 py-3 rounded bg-blue-700 hover:bg-blue-600 transition text-left"
            >
              🚚 Transportation
              <div className="text-xs text-blue-200">
                Trucks • Fleet • Logistics
              </div>
            </button>
          </div>
        )}
      </aside>
    </>
  );
}
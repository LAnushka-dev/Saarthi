export type ModelItem = {
  id: string;
  name: string;
  path: string;
  description: string;
};

export const MODEL_CATALOG: ModelItem[] = [
  {
    id: "model1",
    name: "Crop Knowledge Engine",
    path: "/models/crop-knowledge",
    description: "State and season wise crop intelligence with smart matching.",
  },
  {
    id: "model2",
    name: "Production Forecast",
    path: "/models/production-forecast",
    description: "Predicts upcoming production using crop and climate signals.",
  },
  {
    id: "model3",
    name: "Surplus Deficit Analyzer",
    path: "/models/surplus-deficit",
    description: "Zone level food balance and alert recommendations.",
  },
  {
    id: "biomodel",
    name: "Bio Storage Model",
    path: "/models/bio-storage",
    description: "Storage planning and quality safety guidance for produce.",
  },
  {
    id: "route-optimization",
    name: "Route Optimization",
    path: "/models/route-optimization",
    description: "Logistics routing, delay risk awareness, and trip planning.",
  },
];

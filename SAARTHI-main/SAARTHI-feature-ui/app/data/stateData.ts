const stateData: Record<
  string,
  {
    demand: string;
    supply: string;
    trucks: number;
    coldStorage: string;
    urgency: "low" | "medium" | "high";
  }
> = {
  Maharashtra: {
    demand: "High",
    supply: "Medium",
    trucks: 120,
    coldStorage: "Available",
    urgency: "high"
  },
  Gujarat: {
    demand: "Medium",
    supply: "High",
    trucks: 90,
    coldStorage: "Limited",
    urgency: "medium"
  },
  Karnataka: {
    demand: "Low",
    supply: "High",
    trucks: 70,
    coldStorage: "Available",
    urgency: "low"
  }
};

export default stateData;
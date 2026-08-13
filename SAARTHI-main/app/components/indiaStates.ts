import admin1 from "./ne_admin1.geojson";

const indiaStates = {
  type: "FeatureCollection",
  features: (admin1 as any).features
    .filter(
      (f: any) =>
        f.properties?.admin === "India" &&
        f.properties?.name &&
        f.geometry
    )
    .map((f: any) => ({
      ...f,
      properties: {
        state: f.properties.name
      }
    }))
};

export default indiaStates;
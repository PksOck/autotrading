import type { components } from "./schema";

export type SystemStatus = components["schemas"]["SystemStatus"];
export type ServiceStatus = components["schemas"]["ServiceStatus"];
export type ServiceState = ServiceStatus["state"];

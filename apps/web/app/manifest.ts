import type { MetadataRoute } from "next";
import messages from "@/messages/sl.json";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: messages.app.name,
    short_name: messages.app.name,
    display: "standalone",
    start_url: "/",
    background_color: "#f5f6f8",
    theme_color: "#ffffff",
    icons: [{ src: "/icon.svg", sizes: "any", type: "image/svg+xml", purpose: "any" }],
  };
}

import type { MetadataRoute } from "next";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://127.0.0.1:3000";

export default function sitemap(): MetadataRoute.Sitemap {
  return ["/", "/methodology", "/watchlist", "/paper", "/instruments/AMZN"].map((route) => ({
    url: `${siteUrl}${route}`,
  }));
}

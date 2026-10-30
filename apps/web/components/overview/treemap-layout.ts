import { hierarchy, treemap, treemapSquarify } from "d3-hierarchy";

export type TreemapTile<T> = { item: T; x: number; y: number; width: number; height: number };

/** Squarified treemap: tile area is proportional to `weight` (OV-01). */
export function computeTreemap<T extends { weight: number }>(
  items: T[],
  width: number,
  height: number,
  padding = 3,
): TreemapTile<T>[] {
  const held = items.filter((i) => i.weight > 0);
  if (!held.length || width <= 0 || height <= 0) return [];
  type Node = { children?: T[] } | T;
  const root = hierarchy<Node>({ children: held }, (d) =>
    "children" in d ? d.children : undefined,
  )
    .sum((d) => ("weight" in d ? d.weight : 0))
    .sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
  treemap<Node>().tile(treemapSquarify).size([width, height]).paddingInner(padding).round(true)(
    root,
  );
  return root.leaves().map((leaf) => {
    const node = leaf as typeof leaf & { x0: number; y0: number; x1: number; y1: number };
    return {
      item: leaf.data as T,
      x: node.x0,
      y: node.y0,
      width: node.x1 - node.x0,
      height: node.y1 - node.y0,
    };
  });
}

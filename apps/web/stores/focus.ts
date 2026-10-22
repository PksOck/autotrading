import { create } from "zustand";

/** LX-03 cross-highlighting: the entity currently hovered anywhere on the screen. */
type FocusState = {
  hovered: string | null;
  setHovered: (entity: string | null) => void;
};

export const useFocusStore = create<FocusState>((set) => ({
  hovered: null,
  setHovered: (hovered) => set({ hovered }),
}));

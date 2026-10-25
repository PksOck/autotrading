import { render, screen } from "@testing-library/react";
import { renderToString } from "react-dom/server";
import { shortcutLabel, useShortcutLabel } from "./platform";

describe("platform shortcut label", () => {
  it.each([
    [{ platform: "MacIntel" }, "⌘K"],
    [{ userAgentData: { platform: "macOS" }, platform: "Win32" }, "⌘K"],
    [{ platform: "Win32" }, "Ctrl K"],
    [{ userAgent: "Mozilla/5.0 (Linux; Android 15)" }, "Ctrl K"],
    [{ userAgent: "Mozilla/5.0 (Macintosh; Intel Mac OS X)" }, "⌘K"],
    [{ platform: "iPhone", userAgent: "iPhone like Mac OS X" }, "Ctrl K"],
    [{ platform: "MacIntel", maxTouchPoints: 5 }, "Ctrl K"],
  ])("detects %j", (nav, label) => {
    expect(shortcutLabel(nav)).toBe(label);
  });

  it("defaults to Ctrl K without a navigator", () => {
    expect(shortcutLabel()).toBe("Ctrl K");
  });

  it("uses a stable server snapshot even on a Mac, then reads the client platform", () => {
    const original = Object.getOwnPropertyDescriptor(navigator, "platform");
    Object.defineProperty(navigator, "platform", { configurable: true, value: "MacIntel" });
    function Label() {
      return <kbd>{useShortcutLabel()}</kbd>;
    }
    try {
      expect(renderToString(<Label />)).toContain("Ctrl K");
      render(<Label />);
      expect(screen.getByText("⌘K")).toBeVisible();
    } finally {
      if (original) Object.defineProperty(navigator, "platform", original);
      else Reflect.deleteProperty(navigator, "platform");
    }
  });
});

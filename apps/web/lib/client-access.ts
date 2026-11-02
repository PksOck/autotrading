export const SESSION_ENDED = "preza:session-ended";
export function signalSessionEnd() {
  window.dispatchEvent(new Event(SESSION_ENDED));
  try {
    localStorage.setItem(SESSION_ENDED, `${Date.now()}:${Math.random()}`);
  } catch {
    /* Polling still revokes other tabs. */
  }
}

import { createContext, useContext } from "react";

// Shared app state for the authenticated shell. Replaces the prop-drilling
// that previously ran from App down through every route element.
export const AppContext = createContext(null);

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) {
    throw new Error("useApp must be used inside AppContext.Provider");
  }
  return ctx;
}

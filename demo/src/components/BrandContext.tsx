/** The brand (colors and fonts) every component draws with. The composition provides it once. */
import { createContext, useContext } from "react";
import type { Brand } from "../catalog/schemas";

const BrandContext = createContext<Brand | null>(null);

export const BrandProvider = BrandContext.Provider;

/** Return the brand, or fail loudly when a component is rendered outside the composition. */
export const useBrand = (): Brand => {
  const brand = useContext(BrandContext);
  if (brand === null) {
    throw new Error("useBrand() was called outside <BrandProvider>");
  }
  return brand;
};

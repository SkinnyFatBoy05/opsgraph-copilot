import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import App from "./App";


describe("OpsGraph application shell", () => {
  it("keeps both domain workspaces directly discoverable", () => {
    render(<App />);

    expect(screen.getByRole("button", { name: /Bank Operations/i })).toBeVisible();
    expect(screen.getByRole("button", { name: /AwardLens AU/i })).toBeVisible();
  });
});

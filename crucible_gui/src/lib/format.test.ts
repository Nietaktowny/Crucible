import { describe, expect, it } from "vitest";

import {
  getErrorMessage,
  formatDuration,
  formatNumber,
  formatRelativeDate,
} from "./format";

describe("getErrorMessage", () => {
  it("prefers the server-provided message on the error cause", () => {
    const error = new Error("Request failed", {
      cause: { message: "Workflow not found: demo" },
    });

    expect(getErrorMessage(error)).toBe("Workflow not found: demo");
  });

  it("falls back to the error's own message when there is no cause", () => {
    expect(getErrorMessage(new Error("Network error"))).toBe("Network error");
  });

  it("returns a generic message for non-Error values", () => {
    expect(getErrorMessage("just a string")).toBe("Something went wrong.");
    expect(getErrorMessage(undefined)).toBe("Something went wrong.");
  });
});

describe("formatDuration", () => {
  it("returns an em dash for missing values", () => {
    expect(formatDuration(null)).toBe("—");
    expect(formatDuration(undefined)).toBe("—");
    expect(formatDuration(Number.NaN)).toBe("—");
  });

  it("renders sub-second durations in milliseconds", () => {
    expect(formatDuration(0.25)).toBe("250ms");
  });

  it("renders sub-minute durations in seconds", () => {
    expect(formatDuration(2.456)).toBe("2.46s");
    expect(formatDuration(45)).toBe("45.0s");
  });

  it("renders minute-scale durations as minutes and seconds", () => {
    expect(formatDuration(125)).toBe("2m 5s");
  });
});

describe("formatNumber", () => {
  it("returns an em dash for missing values", () => {
    expect(formatNumber(null)).toBe("—");
    expect(formatNumber(undefined)).toBe("—");
  });

  it("formats with locale thousands separators", () => {
    expect(formatNumber(1234567)).toBe(new Intl.NumberFormat().format(1234567));
  });
});

describe("formatRelativeDate", () => {
  it("reports very recent timestamps as 'just now'", () => {
    expect(formatRelativeDate(new Date())).toBe("just now");
  });

  it("reports minute-scale timestamps in minutes", () => {
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60_000);
    expect(formatRelativeDate(fiveMinutesAgo)).toBe("5m ago");
  });

  it("reports hour-scale timestamps in hours", () => {
    const threeHoursAgo = new Date(Date.now() - 3 * 60 * 60_000);
    expect(formatRelativeDate(threeHoursAgo)).toBe("3h ago");
  });

  it("reports day-scale timestamps in days", () => {
    const twoDaysAgo = new Date(Date.now() - 2 * 24 * 60 * 60_000);
    expect(formatRelativeDate(twoDaysAgo)).toBe("2d ago");
  });

  it("falls back to a locale date string beyond a week", () => {
    const twoWeeksAgo = new Date(Date.now() - 14 * 24 * 60 * 60_000);
    expect(formatRelativeDate(twoWeeksAgo)).toBe(twoWeeksAgo.toLocaleDateString());
  });
});

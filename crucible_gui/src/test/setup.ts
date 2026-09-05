import "@testing-library/jest-dom/vitest";

// Mantine components measure elements via matchMedia/ResizeObserver, which
// jsdom doesn't implement. Stub them so component tests don't crash.
if (!window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  });
}

if (!("ResizeObserver" in window)) {
  class ResizeObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  // @ts-expect-error -- test-only stub
  window.ResizeObserver = ResizeObserverStub;
}

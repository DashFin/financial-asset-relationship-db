// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom'

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn()
  }))
})

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  static disconnect () {
    // no-op: required placeholder for teardown
  }

  static observe () {
    // intentionally empty placeholder for tests
  }

  /**
   * Returns an empty array of records.
   * @returns {any[]} An empty array of records.
   */
  static takeRecords () {
    return []
  }

  static unobserve () {
    // no-op placeholder for ResizeObserver.unobserve in Jest environment
  }
}

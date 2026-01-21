/* eslint-env jest */
/* eslint-disable class-methods-use-this, no-empty-function */

// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom'

/**
 * Creates a Jest mock for window.matchMedia.
 * Supports programmatic changes via `setMatches` and timer integration.
 */
const createMatchMedia = ({ defaultMatches = false } = {}) => {
  const listeners = new Set()
  let matches = defaultMatches

  const mqlFactory = (query) => {
    const media = String(query ?? '')
    const mql = {
      get matches() {
        return matches
      },
      media,
      onchange: null,

      /**
       * Programmatically set match status.
       * Triggers listeners asynchronously (simulates browser event loop).
       */
      setMatches(newValue) {
        matches = Boolean(newValue)
        const event = { type: 'change', matches, media }

        // Run listeners asynchronously
        setTimeout(() => {
          listeners.forEach((listener) => listener(event))
          if (typeof mql.onchange === 'function') {
            mql.onchange(event)
          }
        }, 0)
      },

      // Deprecated listeners
      addListener: jest.fn((listener) => {
        if (typeof listener === 'function') listeners.add(listener)
      }),
      removeListener: jest.fn((listener) => {
        listeners.delete(listener)
      }),

      // Standard API
      addEventListener: jest.fn((eventName, listener) => {
        if (eventName === 'change') listeners.add(listener)
      }),
      removeEventListener: jest.fn((eventName, listener) => {
        if (eventName === 'change') listeners.delete(listener)
      }),

      dispatchEvent: jest.fn((event) => {
        listeners.forEach((listener) => listener(event))
        if (typeof mql.onchange === 'function') {
          mql.onchange(event)
        }
        return true
      }),
    }

    return mql
  }

  const mockFn = jest.fn(mqlFactory)

  // Allow clearing listeners between tests
  mockFn.clearListeners = () => listeners.clear()

  return mockFn
}

// Apply globally
Object.defineProperty(window, 'matchMedia', {
  configurable: true,
  writable: true,
  value: createMatchMedia(),
})

// -----------------------------------------------------------------------------
// Mock IntersectionObserver
// -----------------------------------------------------------------------------

class MockIntersectionObserver {
  constructor(callback = () => {}, options = {}) {
    this._callback = callback
    this._options = options
    this._elements = new Set()
  }

  observe = jest.fn((element) => {
    if (element) this._elements.add(element)
  })

  unobserve = jest.fn((element) => {
    this._elements.delete(element)
  })

  disconnect = jest.fn(() => {
    this._elements.clear()
  })

  takeRecords = jest.fn(() => [])

  /**
   * Simulates intersection changes for observed elements.
   * @param {Array<{ target: Element, isIntersecting: boolean, intersectionRatio?: number }>} entries
   */
  simulateIntersect(entries) {
    const normalizedEntries = entries.map((entry) => ({
      target: entry.target,
      isIntersecting: Boolean(entry.isIntersecting),
      intersectionRatio: entry.intersectionRatio ?? (entry.isIntersecting ? 1 : 0),
      boundingClientRect: entry.target.getBoundingClientRect
        ? entry.target.getBoundingClientRect()
        : {},
      intersectionRect: entry.isIntersecting
        ? entry.target.getBoundingClientRect?.() ?? {}
        : {},
      rootBounds: {},
      time: Date.now(),
    }))
    this._callback(normalizedEntries, this)
  }
}

// Apply globally
Object.defineProperty(window, 'IntersectionObserver', {
  configurable: true,
  writable: true,
  value: MockIntersectionObserver,
})

Object.defineProperty(global, 'IntersectionObserver', {
  configurable: true,
  writable: true,
  value: MockIntersectionObserver,
})

// -----------------------------------------------------------------------------
// Jest cleanup
// -----------------------------------------------------------------------------

afterEach(() => {
  if (typeof window.matchMedia?.mockClear === 'function') {
    window.matchMedia.mockClear()
    if (typeof window.matchMedia.clearListeners === 'function') {
      window.matchMedia.clearListeners()
    }
  }
})

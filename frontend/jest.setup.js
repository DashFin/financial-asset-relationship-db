/* eslint-env jest */
/* eslint-disable class-methods-use-this, no-empty-function */

// Learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom'

/**
 * Creates a mock matchMedia function for Jest.
 */
const createMatchMedia = ({ defaultMatches = false } = {}) =>
  jest.fn().mockImplementation((query) => {
    const listeners = new Set()
    const media = String(query ?? '')
    let matches = defaultMatches

    const addChangeListener = (listener) => {
      if (typeof listener === 'function') listeners.add(listener)
    }

    const removeChangeListener = (listener) => {
      listeners.delete(listener)
    }

    const mql = {
      get matches () {
        return matches
      },
      media,
      onchange: null,

      setMatches (newValue) {
        matches = Boolean(newValue)
        const event = { type: 'change', matches, media }
        listeners.forEach((listener) => listener(event))
        if (typeof mql.onchange === 'function') {
          mql.onchange(event)
        }
      },

      addListener: jest.fn(addChangeListener),
      removeListener: jest.fn(removeChangeListener),

      addEventListener: jest.fn((eventName, listener) => {
        if (eventName === 'change') addChangeListener(listener)
      }),
      removeEventListener: jest.fn((eventName, listener) => {
        if (eventName === 'change') removeChangeListener(listener)
      }),

      dispatchEvent: jest.fn((event) => {
        listeners.forEach((listener) => listener(event))
        if (typeof mql.onchange === 'function') {
          mql.onchange(event)
        }
        return true
      })
    }

    return mql
  })

Object.defineProperty(window, 'matchMedia', {
  configurable: true,
  writable: true,
  value: createMatchMedia()
})

/**
 * MockIntersectionObserver simulates the IntersectionObserver API.
 * - Stores observed elements.
 * - Calls the callback when `simulateIntersect` is invoked.
 */
class MockIntersectionObserver {
  constructor (callback = () => {}, options = {}) {
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
  simulateIntersect (entries) {
    const normalizedEntries = entries.map((entry) => ({
      target: entry.target,
      isIntersecting: Boolean(entry.isIntersecting),
      intersectionRatio:
        entry.intersectionRatio ?? (entry.isIntersecting ? 1 : 0),
      boundingClientRect: entry.target.getBoundingClientRect
        ? entry.target.getBoundingClientRect()
        : {},
      intersectionRect: entry.isIntersecting
        ? (entry.target.getBoundingClientRect?.() ?? {})
        : {},
      rootBounds: {},
      time: Date.now()
    }))
    this._callback(normalizedEntries, this)
  }
}

// Apply globally for tests
Object.defineProperty(window, 'IntersectionObserver', {
  configurable: true,
  writable: true,
  value: MockIntersectionObserver
})

Object.defineProperty(global, 'IntersectionObserver', {
  configurable: true,
  writable: true,
  value: MockIntersectionObserver
})

// Cleanup after each test
afterEach(() => {
  if (typeof window.matchMedia?.mockClear === 'function') {
    window.matchMedia.mockClear()
  }
})

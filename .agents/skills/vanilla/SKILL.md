---
name: vanilla
description: >-
  Standardized instructions, architectural principles, and patterns for zero-build, dependency-free vanilla frontend web development. Use this skill whenever building, refactoring, or designing frontend web apps, native Custom Web Components, decoupled REST API data flows, and state-reactivity Proxy bindings.
---

# Vanilla Frontend Web Application Development Guide

A standardized runbook and architectural guide for developing fast, zero-build, dependency-free frontend web applications using modern web standards, native Custom Web Components, decoupled REST API communication, and proxy-based state reactivity.

---

## 1. Core Principles & Philosophy

1. **Zero Build Step**: No bundlers (Webpack, Vite, Rollup, Parcel), no transpilers (Babel), and no build pipelines. Code runs directly in the browser as standard ES modules (`<script type="module">`).
2. **Zero Frontend Runtime Dependencies**: Rely entirely on native Web Standards (DOM APIs, Web Components, `fetch`, CSS variables, CSS grid/flexbox). Avoid framework runtimes and external AJAX/state libraries.
3. **Decoupled Architecture (REST API Backend)**: The frontend is strictly a static client (HTML/CSS/JS) communicating with the backend purely through standard REST API endpoints (JSON over HTTP).
4. **Terse & Minimalist**: Write the minimum amount of JavaScript needed for functionality. Prefer inline logic for short helpers (~8 lines or fewer) over heavy abstraction layers.

---

## 2. REST API & Data Flow

### 2.1. Complete Separation
- The frontend is entirely independent of backend rendering or server memory.
- All dynamic data is fetched asynchronously over HTTP using native `fetch()`.

### 2.2. Data Requests via `fetch`
Data requests should originate from:
- **Web Components directly** (for component-scoped or localized data):
  ```javascript
  async loadData() {
    try {
      const res = await fetch('/api/items');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const items = await res.json();
      app.state.items = items; // Update reactive state
    } catch (err) {
      console.error('Failed to load items:', err);
    }
  }
  ```
- **Global / Shared API Service** (when shared across multiple components or requiring centralized auth header injection):
  ```javascript
  globalThis.API = {
    async get(endpoint) {
      const res = await fetch(endpoint, {
        headers: { 'Accept': 'application/json' }
      });
      if (!res.ok) throw new Error(`API Error ${res.status}`);
      return res.json();
    }
  };
  ```

---

## 3. State Reactivity Pattern (`state-reactivity.js`)

State reactivity is lightweight and transparent, powered by a native ES6 `Proxy` that triggers `.render(value)` on any DOM element declaring matching `data="<key>"` attributes.

### 3.1. Implementation of `state-reactivity.js`

```javascript
// state-reactivity.js
globalThis.app = globalThis.app || {};

app.state = new Proxy({}, {
  set(target, prop, value) {
    target[prop] = value;

    // Notify all DOM elements subscribing to this state key
    document.querySelectorAll(`[data="${prop}"]`).forEach(el => {
      if (typeof el.render === 'function') {
        el.render(value);
      }
    });

    return true;
  }
});
```

### 3.2. Reactivity Rules
1. **State Mutation**: Modify shared data exclusively via `app.state.<key> = value`.
2. **DOM Binding**: Elements declare their dependency using attribute `data="<key>"` (e.g. `<user-profile data="currentUser"></user-profile>` or `this.setAttribute('data', 'currentUser')`).
3. **Reactive Method**: Any component listening to `data="<key>"` implements `render(data)` which receives the new value and updates its DOM.
4. **No Cross-Component Invocations**: Components must never call methods directly on sibling or parent components. Inter-component updates flow exclusively through `app.state`.

---

## 4. Custom Web Component Architecture

All visible UI components are implemented as native Web Components extending `HTMLElement`.

### 4.1. Complete Component Pattern Example

```javascript
class ItemList extends HTMLElement {
  connectedCallback() {
    // 1. Subscribe to reactive state key
    this.setAttribute('data', 'items');

    // 2. Initial render with current state (if present)
    this.render(app.state.items || []);

    // 3. Fetch initial data if not already loaded
    if (!app.state.items) {
      this.fetchItems();
    }
  }

  async fetchItems() {
    this.innerHTML = `<div class="loading">Loading items...</div>`;
    try {
      const res = await fetch('/api/items');
      const data = await res.json();
      // Updating app.state automatically triggers this.render(data)
      app.state.items = data;
    } catch (err) {
      this.innerHTML = `<div class="error">Failed to load items: ${err.message}</div>`;
    }
  }

  render(items) {
    if (!Array.isArray(items) || items.length === 0) {
      this.innerHTML = `<p class="empty-state">No items found.</p>`;
      return;
    }

    this.innerHTML = `
      <ul class="items-list">
        ${items.map(item => `
          <li class="item-card" data-id="${item.id}">
            <h3>${item.title}</h3>
            <p>${item.description}</p>
            <button class="btn-select" data-id="${item.id}">Select</button>
          </li>
        `).join('')}
      </ul>
    `;

    // Attach local event listeners
    this.querySelectorAll('.btn-select').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const id = e.currentTarget.dataset.id;
        const selected = (app.state.items || []).find(i => i.id === id);
        // Mutating another state key notifies any component bound to 'selectedItem'
        app.state.selectedItem = selected;
      });
    });
  }
}

customElements.define('item-list', ItemList);
export default ItemList;
```

---

## 5. Agent Implementation Checklist

When building or reviewing frontend web features, verify:

- [ ] **Strictly Frontend**: Is the frontend completely decoupled from server implementation details, relying solely on REST API endpoints?
- [ ] **No Bundler Dependencies**: Are scripts standard ES modules loaded natively in HTML (`<script type="module">`)?
- [ ] **Encapsulated Components**: Does every visible UI element extend `HTMLElement` and register via `customElements.define`?
- [ ] **Reactivity via Proxy**: Are state updates channeled through `app.state.<key> = ...` and components bound with `data="<key>"`?
- [ ] **Component Lifecycle**: Does each reactive component implement `render(value)`?
- [ ] **Native Data Fetching**: Are network requests made via standard `fetch()`?
- [ ] **Terse & Clean**: Is the code concise, readable, and free of framework boilerplate?

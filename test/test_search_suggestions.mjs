import assert from 'node:assert/strict';
import test from 'node:test';

test('document suggestions use their source URL for mouse and keyboard navigation', async () => {
  const createElement = () => {
    const attributes = new Map();
    const element = {
      children: [],
      listeners: {},
      classList: { add() {}, remove() {} },
      appendChild(child) { this.children.push(child); },
      get firstChild() { return this.children[0]; },
      set innerHTML(value) { this.children = []; this.html = value; },
      get innerHTML() { return this.html; },
      setAttribute(name, value) { attributes.set(name, value); },
      getAttribute(name) { return attributes.get(name); },
      hasAttribute(name) { return attributes.has(name); },
      addEventListener(name, listener) { this.listeners[name] = listener; },
    };
    return element;
  };
  const inputs = ['searchinput', 'searchinput-mobile'].map(id => ({
    id,
    value: 'predicate-fields',
    parentElement: createElement(),
    closest() { return {}; },
    setAttribute() {},
  }));
  let initialize;
  globalThis.document = {
    createElement,
    querySelectorAll: () => inputs,
    getElementById: id => inputs.flatMap(input => input.parentElement.firstChild.children)
      .find(element => element.id === id),
    addEventListener: (name, listener) => { initialize = listener; },
  };
  globalThis.window = { location: { href: '' } };

  try {
    const { getHandlerForInput } = await import('../js/handle_search_suggestions.js');
    initialize();
    const cases = [
      ['pyvespa', '/examples/feed_performance.html', 'https://vespa-engine.github.io/pyvespa/examples/feed_performance.html'],
      ['open', '/en/schemas/predicate-fields.html#configuration', 'https://docs.vespa.ai/en/schemas/predicate-fields.html#configuration'],
      ['cloud', '/en/operations', 'https://cloud.vespa.ai/en/operations'],
      ['blog', '/stateful-model-serving/', 'https://blog.vespa.ai/stateful-model-serving/'],
      ['vespaai', '/resources', 'https://vespa.ai/resources'],
      ['vespaapps', '/examples/README.md', 'https://github.com/vespa-engine/sample-apps/tree/master/examples/README.md'],
    ];
    for (const input of inputs) {
      const handler = getHandlerForInput(input.id);
      for (const [namespace, path, expected] of cases) {
        handler.handleSuggestionResults([
          { fields: { namespace, path, title: 'Feeding performance¶' } },
        ], []);
        const suggestion = input.parentElement.firstChild.firstChild;
        assert.equal(suggestion.getAttribute('data-path'), expected);

        const event = { preventDefault() {}, stopPropagation() {} };
        suggestion.listeners.mousedown(event);
        assert.equal(window.location.href, expected);

        window.location.href = '';
        handler.handleArrowKeys({ ...event, key: 'ArrowDown', target: input });
        handler.handleArrowKeys({ ...event, key: 'Enter', target: input });
        assert.equal(window.location.href, expected);
      }
    }
  } finally {
    delete globalThis.document;
    delete globalThis.window;
  }
});

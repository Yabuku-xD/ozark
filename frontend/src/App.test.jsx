import { describe, expect, test } from 'vitest';

import App from './App.jsx';

describe('App', () => {
  test('exports the main application component', () => {
    expect(typeof App).toBe('function');
  });
});

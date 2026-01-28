# Testing Guide

## Setup

Install test dependencies:

```bash
npm install --save-dev @testing-library/react-native @testing-library/jest-native jest jest-expo @types/jest
```

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

## Test Structure

Tests are located in the `__tests__` directory, mirroring the source structure:

```
__tests__/
  ├── hooks/
  │   └── useChartData.test.ts
  ├── services/
  │   ├── api/
  │   │   └── client.test.ts
  │   └── storage.test.ts
  └── utils/
      └── responsive.test.ts
```

## Writing Tests

### Unit Tests

Test individual functions and utilities:

```typescript
import { someFunction } from '@/utils/someUtil';

describe('someFunction', () => {
  it('should do something', () => {
    const result = someFunction(input);
    expect(result).toBe(expected);
  });
});
```

### Hook Tests

Use `renderHook` from `@testing-library/react-native`:

```typescript
import { renderHook } from '@testing-library/react-native';
import { useSomeHook } from '@/hooks/useSomeHook';

describe('useSomeHook', () => {
  it('should return expected value', () => {
    const { result } = renderHook(() => useSomeHook());
    expect(result.current).toBe(expected);
  });
});
```

### Integration Tests

Test API client and service integrations:

```typescript
import { apiClient } from '@/services/api/client';

describe('API Client', () => {
  it('should fetch data', async () => {
    const data = await apiClient.getSessions();
    expect(data).toBeDefined();
  });
});
```

## Mocking

### Native Modules

Native modules are automatically mocked in `jest.setup.js`:
- AsyncStorage
- Expo modules (Constants, Speech, AV)
- React Native BLE PLX
- React Native Reanimated

### Custom Mocks

Create mocks in `__mocks__` directory:

```typescript
// __mocks__/someModule.ts
export const mockedFunction = jest.fn();
```

## Coverage

Coverage reports are generated in the `coverage` directory. Configure coverage thresholds in `jest.config.js`.

## Best Practices

1. **Test behavior, not implementation**
2. **Use descriptive test names**
3. **Keep tests isolated**
4. **Mock external dependencies**
5. **Test edge cases**
6. **Maintain test coverage above 70%**

## Troubleshooting

### TypeScript Errors

If you see TypeScript errors in tests:
1. Ensure `@types/jest` is installed
2. Check `tsconfig.json` includes test files
3. Verify Jest types are configured

### Module Not Found

If tests can't find modules:
1. Check `jest.config.js` moduleNameMapper
2. Verify path aliases in `tsconfig.json`
3. Ensure mocks are in correct location

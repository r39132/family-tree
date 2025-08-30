module.exports = {
  testEnvironment: 'jsdom',
  testMatch: ['**/__tests__/**/*.test.ts?(x)'],
  transform: {
    '^.+\\.(ts|tsx)$': ['ts-jest', { tsconfig: 'tsconfig.json' }],
  },
  moduleNameMapper: {
    '^next/router$': '<rootDir>/__mocks__/nextRouterMock.js',
  },
  setupFilesAfterEnv: ['@testing-library/jest-dom/extend-expect'],
};
/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^next/link$': '<rootDir>/test/__mocks__/nextLinkMock.js'
  },
  testMatch: ['**/?(*.)+(spec|test).[jt]s?(x)']
};

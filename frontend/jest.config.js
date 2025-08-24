/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^next/link$': '<rootDir>/test/__mocks__/nextLinkMock.js'
  },
  testMatch: ['**/?(*.)+(spec|test).[jt]s?(x)']
};

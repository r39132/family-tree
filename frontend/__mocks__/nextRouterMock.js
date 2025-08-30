module.exports = {
  useRouter: () => ({ push: jest.fn(), events: { on: jest.fn(), off: jest.fn(), emit: jest.fn() } }),
};

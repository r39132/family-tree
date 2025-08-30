/** @jest-environment jsdom */
import '@testing-library/jest-dom';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Home from '../pages/index';

// Mock next/router
jest.mock('next/router', () => ({
  useRouter: () => ({ push: jest.fn(), events: { on: jest.fn(), off: jest.fn(), emit: jest.fn() } })
}));

// Mock API
jest.mock('../lib/api', () => ({
  api: async (path: string, opts?: any) => {
    if(path === '/tree/unsaved') return { unsaved: true };
    if(path === '/tree/versions') return [
      { id: 'id-2', created_at: '2025-08-28T17:30:00.000Z', version: 2 },
      { id: 'id-1', created_at: '2025-08-27T17:30:00.000Z', version: 1 },
    ];
    if(path === '/tree') return { roots: [], members: [] };
    if(path === '/tree/save') return { id: 'id-3', created_at: '2025-08-29T17:30:00.000Z', version: 3 };
    if(path === '/tree/recover') return { ok: true };
    if(path === '/tree/move') return { ok: true };
    return {};
  }
}));

describe('Tree Versioning UI', () => {
  test('shows unsaved warning and Save/Recover controls', async () => {
    render(<Home />);
    expect(await screen.findByText(/You have unsaved changes/i)).toBeInTheDocument();
    expect(screen.getByText(/Save Tree/i)).toBeInTheDocument();
    expect(screen.getByText(/Recover/i)).toBeInTheDocument();
  });

  test('saving clears unsaved flag', async () => {
    render(<Home />);
    const saveBtn = await screen.findByText(/Save Tree/i);
    fireEvent.click(saveBtn);
    await waitFor(() => expect(screen.queryByText(/You have unsaved changes/i)).not.toBeInTheDocument());
  });

  test('navigation guard triggers beforeunload when unsaved', async () => {
    render(<Home />);
    // Unsaved is true from mocked API
    const event = new Event('beforeunload', { cancelable: true });
    // jsdom Event lacks returnValue; mimic minimal behavior
    // @ts-ignore
    (event as any).returnValue = undefined;
    const prevented = !window.dispatchEvent(event);
    // Some environments will not support cancelable beforeunload; accept either prevented or returnValue set
    // @ts-ignore
    expect(prevented || (event as any).returnValue === '').toBeTruthy();
  });
});

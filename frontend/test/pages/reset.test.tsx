import { render, screen } from '@testing-library/react';
import user from '@testing-library/user-event';
import Reset from '../../pages/reset';

jest.mock('next/router', () => ({
  useRouter: () => ({ isReady: true, query: {}, push: jest.fn() })
}));

describe('Reset page', () => {
  it('toggles visibility for both password fields without layout shift', async () => {
    const { container } = render(<Reset />);
    // New password
    const newInput = screen.getByPlaceholderText('New password') as HTMLInputElement;
    const toggleButtons = container.querySelectorAll('button.toggle-pass');
    expect(newInput.type).toBe('password');
    const widthBefore = newInput.getBoundingClientRect().width;
    await user.click(toggleButtons[0] as Element);
    expect(newInput.type).toBe('text');
    const widthAfter = newInput.getBoundingClientRect().width;
    expect(widthAfter).toBe(widthBefore);

    // Confirm password
    const confirmInput = screen.getByPlaceholderText('Confirm password') as HTMLInputElement;
    expect(confirmInput.type).toBe('password');
    const width2Before = confirmInput.getBoundingClientRect().width;
    await user.click(toggleButtons[1] as Element);
    expect(confirmInput.type).toBe('text');
    const width2After = confirmInput.getBoundingClientRect().width;
    expect(width2After).toBe(width2Before);
  });
});

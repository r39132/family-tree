/**
 * Tests for age-based filtering in marriage-related dropdowns
 */

import { calculateAge, isEligibleForMarriage } from '../lib/dateUtils';

describe('Date Utility Functions', () => {
  describe('calculateAge', () => {
    it('calculates age correctly for MM/DD/YYYY format', () => {
      // Use explicit date construction to avoid timezone issues
      const referenceDate = new Date(2025, 9, 11); // October 11, 2025 (month is 0-indexed)
      const dob = '10/11/2007'; // Exactly 18 years old today
      expect(calculateAge(dob, referenceDate)).toBe(18);
    });

    it('calculates age correctly when birthday has not occurred this year', () => {
      const referenceDate = new Date(2025, 9, 11); // October 11, 2025
      const dob = '10/12/2007'; // Birthday is tomorrow, still 17
      expect(calculateAge(dob, referenceDate)).toBe(17);
    });

    it('calculates age correctly when birthday has occurred this year', () => {
      const referenceDate = new Date(2025, 9, 11); // October 11, 2025
      const dob = '10/10/2007'; // Birthday was yesterday, now 18
      expect(calculateAge(dob, referenceDate)).toBe(18);
    });

    it('handles YYYY-MM-DD format', () => {
      const referenceDate = new Date(2025, 9, 11); // October 11, 2025
      const dob = '2007-10-11'; // Exactly 18 years old
      expect(calculateAge(dob, referenceDate)).toBe(18);
    });

    it('returns null for invalid date string', () => {
      expect(calculateAge('invalid')).toBeNull();
    });

    it('returns null for empty string', () => {
      expect(calculateAge('')).toBeNull();
    });

    it('returns null for null', () => {
      expect(calculateAge(null)).toBeNull();
    });

    it('returns null for undefined', () => {
      expect(calculateAge(undefined)).toBeNull();
    });

    it('calculates correct age for someone over 18', () => {
      const referenceDate = new Date(2025, 9, 11); // October 11, 2025
      const dob = '05/15/1990'; // 35 years old
      expect(calculateAge(dob, referenceDate)).toBe(35);
    });

    it('calculates correct age for someone under 18', () => {
      const referenceDate = new Date(2025, 9, 11); // October 11, 2025
      const dob = '05/15/2010'; // 15 years old
      expect(calculateAge(dob, referenceDate)).toBe(15);
    });

    it('uses current date when no reference date provided', () => {
      const dob = '01/01/2000';
      const age = calculateAge(dob);
      expect(age).toBeGreaterThan(20); // Should be at least in their 20s
    });
  });

  describe('isEligibleForMarriage', () => {
    it('returns true for someone exactly 18 years old', () => {
      const today = new Date();
      const eighteenYearsAgo = new Date(today.getFullYear() - 18, today.getMonth(), today.getDate());
      const dob = `${String(eighteenYearsAgo.getMonth() + 1).padStart(2, '0')}/${String(eighteenYearsAgo.getDate()).padStart(2, '0')}/${eighteenYearsAgo.getFullYear()}`;
      expect(isEligibleForMarriage(dob)).toBe(true);
    });

    it('returns true for someone over 18 years old', () => {
      expect(isEligibleForMarriage('05/15/1990')).toBe(true);
    });

    it('returns false for someone under 18 years old', () => {
      const today = new Date();
      const sixteenYearsAgo = new Date(today.getFullYear() - 16, today.getMonth(), today.getDate());
      const dob = `${String(sixteenYearsAgo.getMonth() + 1).padStart(2, '0')}/${String(sixteenYearsAgo.getDate()).padStart(2, '0')}/${sixteenYearsAgo.getFullYear()}`;
      expect(isEligibleForMarriage(dob)).toBe(false);
    });

    it('returns false for someone who will turn 18 tomorrow', () => {
      const today = new Date();
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);
      const eighteenYearsAgoTomorrow = new Date(tomorrow.getFullYear() - 18, tomorrow.getMonth(), tomorrow.getDate());
      const dob = `${String(eighteenYearsAgoTomorrow.getMonth() + 1).padStart(2, '0')}/${String(eighteenYearsAgoTomorrow.getDate()).padStart(2, '0')}/${eighteenYearsAgoTomorrow.getFullYear()}`;
      expect(isEligibleForMarriage(dob)).toBe(false);
    });

    it('returns false for invalid date', () => {
      expect(isEligibleForMarriage('invalid')).toBe(false);
    });

    it('returns false for null', () => {
      expect(isEligibleForMarriage(null)).toBe(false);
    });

    it('returns false for undefined', () => {
      expect(isEligibleForMarriage(undefined)).toBe(false);
    });

    it('returns false for empty string', () => {
      expect(isEligibleForMarriage('')).toBe(false);
    });

    it('handles edge case: birthday on leap day', () => {
      const dob = '02/29/2004'; // Leap year birthday
      const referenceDate = new Date(2023, 2, 1); // March 1, 2023 (month is 0-indexed)
      const age = calculateAge(dob, referenceDate);
      // Born Feb 29, 2004. In 2023 (non-leap year), their birthday is considered Feb 28.
      // By March 1, 2023, they've already passed Feb 28, so they're 19.
      expect(age).toBe(19);
    });
  });
});

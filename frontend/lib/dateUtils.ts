/**
 * Calculate age from a date of birth string
 * Supports multiple date formats: MM/DD/YYYY, YYYY-MM-DD
 * @param dob - Date of birth string
 * @param referenceDate - Optional reference date (defaults to today)
 * @returns Age in years, or null if DOB is invalid
 */
export function calculateAge(dob: string | null | undefined, referenceDate?: Date): number | null {
  if (!dob) return null;

  let birthDate: Date | null = null;

  // Try MM/DD/YYYY format (primary format used in the app)
  const mmddyyyyMatch = dob.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (mmddyyyyMatch) {
    const [, month, day, year] = mmddyyyyMatch;
    birthDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
  }

  // Try YYYY-MM-DD format
  if (!birthDate) {
    const yyyymmddMatch = dob.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (yyyymmddMatch) {
      const [, year, month, day] = yyyymmddMatch;
      birthDate = new Date(parseInt(year), parseInt(month) - 1, parseInt(day));
    }
  }

  // Try ISO string or timestamp
  if (!birthDate) {
    const parsed = new Date(dob);
    if (!isNaN(parsed.getTime())) {
      birthDate = parsed;
    }
  }

  if (!birthDate || isNaN(birthDate.getTime())) {
    return null;
  }

  const today = referenceDate || new Date();
  let age = today.getFullYear() - birthDate.getFullYear();

  // Adjust if birthday hasn't occurred this year yet
  const monthDiff = today.getMonth() - birthDate.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
    age--;
  }

  return Math.max(0, age);
}

/**
 * Check if a member is at least 18 years old
 * @param dob - Date of birth string
 * @returns true if member is 18 or older, false otherwise
 */
export function isEligibleForMarriage(dob: string | null | undefined): boolean {
  const age = calculateAge(dob);
  return age !== null && age >= 18;
}

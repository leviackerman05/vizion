const EMAIL_PATTERN = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

const ALLOWED_EMAIL_DOMAINS = new Set([
  "gmail.com",
  "googlemail.com",
  "outlook.com",
  "hotmail.com",
  "live.com",
  "msn.com",
  "yahoo.com",
  "yahoo.co.in",
  "yahoo.co.uk",
  "yahoo.ca",
  "ymail.com",
  "rocketmail.com",
  "icloud.com",
  "me.com",
  "mac.com",
  "proton.me",
  "protonmail.com",
  "pm.me",
  "aol.com",
  "zoho.com",
  "mail.com",
  "gmx.com",
  "gmx.de",
  "gmx.net",
  "fastmail.com",
  "tutanota.com",
  "tuta.io",
  "hey.com",
  "rediffmail.com",
]);

const ALLOWED_DOMAIN_SUFFIXES = [".edu", ".ac.uk", ".edu.in", ".edu.au"];

export function validateSignupEmail(email: string): string | null {
  const normalized = email.trim().toLowerCase();
  if (!normalized) return "Email is required";
  if (!EMAIL_PATTERN.test(normalized)) return "Enter a valid email address";

  const domain = normalized.split("@")[1];
  if (ALLOWED_EMAIL_DOMAINS.has(domain)) return null;
  if (ALLOWED_DOMAIN_SUFFIXES.some((suffix) => domain.endsWith(suffix))) return null;

  return "Use Gmail, Outlook, Yahoo, iCloud, Proton, or a school (.edu) email";
}

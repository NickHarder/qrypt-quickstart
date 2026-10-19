/**
 * The project's TypeScript entry point. Replace this module with the product's first slice; it is
 * here so the gate has typed, linted and tested code to check from the first commit.
 */

/**
 * Say hello to someone by name.
 *
 * @param personName - The name to greet, as the person writes it.
 * @returns The greeting, ready to show.
 */
export function greetingFor(personName: string): string {
  const trimmedName = personName.trim();
  return `Hello, ${trimmedName}.`;
}

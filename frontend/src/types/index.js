/**
 * Barrel file for JSDoc typedefs. This project uses plain JavaScript
 * (not TypeScript), so nothing here is imported at runtime — these
 * files exist purely so editors (VS Code/WebStorm via the TS
 * language server, which understands JSDoc) provide autocomplete
 * and inline shape-checking when working with API responses,
 * component props, and hook return values across the codebase.
 *
 * To get hover/autocomplete on a shape in a .jsx file, reference it
 * in a JSDoc comment, e.g.:
 *
 *   /**
 *    * @param {import("@/types/email").EmailListItem} email
 *    *\/
 *   function EmailRow({ email }) { ... }
 *
 * Re-exporting here is mostly organizational — each domain file
 * remains the actual source of the typedefs.
 */
export * from "./user";
export * from "./email";
export * from "./task";
export * from "./meeting";
export * from "./automation";
export * from "./copilot";
export * from "./analytics";
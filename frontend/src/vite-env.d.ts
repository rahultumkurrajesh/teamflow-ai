/// <reference types="vite/client" />

/** Typed env access, so a missing variable is a compile error rather than
 *  an undefined string concatenated into a URL at runtime. */
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

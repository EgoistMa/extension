function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Lightweight local version gate used by popup/content scripts.
// This repository currently ships without a remote version control service,
// so we default to enabled.
const versionChecker = {
  async checkVersion() {
    try {
      const manifest = chrome?.runtime?.getManifest?.();
      return {
        enable: true,
        version_name: manifest?.version || "unknown"
      };
    } catch {
      return {
        enable: true,
        version_name: "unknown"
      };
    }
  }
};

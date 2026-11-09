// Debug builds install as a separate app (dev.lunochkin.algocoach.dev, "algo-coach dev") next to the
// release one, so a Metro-connected dev build never replaces the daily app.
const fs = require('fs');
const path = require('path');
const { withAppBuildGradle, withDangerousMod } = require('expo/config-plugins');

module.exports = function withDevVariant(config) {
  config = withAppBuildGradle(config, (cfg) => {
    const marker = 'applicationIdSuffix ".dev"';
    if (!cfg.modResults.contents.includes(marker)) {
      cfg.modResults.contents = cfg.modResults.contents.replace(
        /buildTypes \{\s*debug \{/,
        (m) => `${m}\n            ${marker}`,
      );
    }
    return cfg;
  });
  return withDangerousMod(config, [
    'android',
    (cfg) => {
      const dir = path.join(cfg.modRequest.platformProjectRoot, 'app', 'src', 'debug', 'res', 'values');
      fs.mkdirSync(dir, { recursive: true });
      fs.writeFileSync(
        path.join(dir, 'strings.xml'),
        '<resources>\n  <string name="app_name">algo-coach dev</string>\n</resources>\n',
      );
      return cfg;
    },
  ]);
};

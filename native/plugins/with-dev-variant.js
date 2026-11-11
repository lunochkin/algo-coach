// Debug builds install as a separate app (dev.lunochkin.algocoach.dev, "Algo Dev") next to the
// release one, so a Metro-connected dev build never replaces the daily app. The build type
// decides every difference, so one prebuilt project serves both builds.
const fs = require('fs');
const path = require('path');
const { withAndroidManifest, withAppBuildGradle, withDangerousMod } = require('expo/config-plugins');

module.exports = function withDevVariant(config) {
  const scheme = config.scheme;

  // the dev app registers a scheme of its own, so the release app on the same phone never
  // receives the dev app's sign-in code
  config = withAndroidManifest(config, (cfg) => {
    for (const activity of cfg.modResults.manifest.application?.[0]?.activity ?? []) {
      for (const filter of activity['intent-filter'] ?? []) {
        for (const data of filter.data ?? []) {
          if (data.$['android:scheme'] === scheme) data.$['android:scheme'] = '${appScheme}';
        }
      }
    }
    return cfg;
  });

  config = withAppBuildGradle(config, (cfg) => {
    const marker = 'applicationIdSuffix ".dev"';
    if (!cfg.modResults.contents.includes(marker)) {
      // the release block is left as generated: with-pinned-keystore matches its first lines
      cfg.modResults.contents = cfg.modResults.contents
        .replace(/defaultConfig \{/, (m) => `${m}\n        manifestPlaceholders += [appScheme: "${scheme}"]`)
        .replace(
          /buildTypes \{\s*debug \{/,
          (m) => `${m}\n            ${marker}\n            manifestPlaceholders += [appScheme: "${scheme}dev"]`,
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
        '<resources>\n  <string name="app_name">Algo Dev</string>\n</resources>\n',
      );
      return cfg;
    },
  ]);
};

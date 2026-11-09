// Release builds are signed with the private key in signing/, which git ignores: an update
// signed by another key installs only after an uninstall, which drops unsynced records. Debug
// builds ("algo-coach dev", a separate app) keep the public React Native debug key.
const fs = require('fs');
const path = require('path');
const { withAppBuildGradle, withDangerousMod } = require('expo/config-plugins');

const RELEASE = `        release {
            def props = new Properties()
            file('keystore.properties').withInputStream { props.load(it) }
            storeFile file(props['storeFile'])
            storePassword props['storePassword']
            keyAlias props['keyAlias']
            keyPassword props['keyPassword']
        }
`;

module.exports = function withPinnedKeystore(config) {
  config = withAppBuildGradle(config, (cfg) => {
    let gradle = cfg.modResults.contents;
    if (!gradle.includes("file('keystore.properties')")) {
      gradle = gradle.replace(/(signingConfigs \{\n[\s\S]*?\n {8}\}\n)/, (block) => block + RELEASE);
      gradle = gradle.replace(
        /(release \{\n(?:\s*\/\/.*\n)*\s*)signingConfig signingConfigs\.debug/,
        '$1signingConfig signingConfigs.release',
      );
    }
    cfg.modResults.contents = gradle;
    return cfg;
  });
  return withDangerousMod(config, [
    'android',
    (cfg) => {
      const signing = path.join(cfg.modRequest.projectRoot, 'signing');
      const app = path.join(cfg.modRequest.platformProjectRoot, 'app');
      for (const name of ['debug.keystore', 'release.keystore', 'keystore.properties']) {
        const from = path.join(signing, name);
        if (!fs.existsSync(from)) {
          throw new Error(`signing/${name} is missing: native/README.md gives where the key lives`);
        }
        fs.copyFileSync(from, path.join(app, name));
      }
      return cfg;
    },
  ]);
};

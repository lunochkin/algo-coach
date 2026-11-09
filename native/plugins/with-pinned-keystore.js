// Release builds are signed with signing/debug.keystore (the React Native debug key), copied in
// on every prebuild so the signature stays the same and `adb install -r` keeps working.
const fs = require('fs');
const path = require('path');
const { withDangerousMod } = require('expo/config-plugins');

module.exports = function withPinnedKeystore(config) {
  return withDangerousMod(config, [
    'android',
    (cfg) => {
      const src = path.join(cfg.modRequest.projectRoot, 'signing', 'debug.keystore');
      const dst = path.join(cfg.modRequest.platformProjectRoot, 'app', 'debug.keystore');
      fs.copyFileSync(src, dst);
      return cfg;
    },
  ]);
};

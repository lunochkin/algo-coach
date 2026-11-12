// Android shows the system keyboard again for a focused field when the app returns from
// the background, past `showSoftInputOnFocus={false}`, so a short reply opened two keyboards.
// stateAlwaysHidden keeps it closed until a field that wants it is pressed.
const { withAndroidManifest } = require('expo/config-plugins');

module.exports = function withHiddenKeyboard(config) {
  return withAndroidManifest(config, (cfg) => {
    for (const activity of cfg.modResults.manifest.application?.[0]?.activity ?? []) {
      if (activity.$['android:name'] === '.MainActivity')
        activity.$['android:windowSoftInputMode'] = 'adjustResize|stateAlwaysHidden';
    }
    return cfg;
  });
};

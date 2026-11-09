// The dev build (`just native-dev-apk`) registers a scheme of its own, so the
// release app on the same phone never receives the dev app's sign-in code.
module.exports = ({ config }) => ({
  ...config,
  scheme: process.env.APP_VARIANT === 'dev' ? 'algocoachdev' : config.scheme,
});

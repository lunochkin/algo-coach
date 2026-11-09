import { router } from 'expo-router';
import { useEffect } from 'react';

/**
 * The engine's redirect after a sign-in, `algocoach://signed-in`. The browser
 * sheet takes the code from it, and Android also hands the link to the router,
 * which would otherwise show it as an unmatched route. Steps back at once.
 */
export default function SignedIn() {
  useEffect(() => {
    if (router.canGoBack()) router.back();
    else router.replace('/settings');
  }, []);
  return null;
}

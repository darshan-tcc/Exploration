import { useEffect, useRef, useState } from "react";

let initializedClientId = null;
let activeCredentialHandler = null;

function handleGoogleCredential(response) {
  activeCredentialHandler?.(response);
}

function decodeJwtPayload(token) {
  const payload = token.split(".")[1]
    .replace(/-/g, "+")
    .replace(/_/g, "/");

  const bytes = Uint8Array.from(
    atob(payload),
    (character) => character.charCodeAt(0)
  );

  return JSON.parse(new TextDecoder().decode(bytes));
}

function GoogleLogin() {
  const buttonRef = useRef(null);
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

    if (!clientId) {
      setError("Google Client ID is missing.");
      return;
    }

    activeCredentialHandler = (response) => {
      try {
        const user = decodeJwtPayload(response.credential);

        setProfile(user);
        setError("");
      } catch {
        setError("Unable to read Google sign-in response.");
      }
    };

    let cancelled = false;

    const initializeGoogle = () => {
      if (
        cancelled ||
        !window.google?.accounts?.id ||
        !buttonRef.current
      ) {
        return;
      }

      if (initializedClientId !== clientId) {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleGoogleCredential
        });

        initializedClientId = clientId;
      }

      buttonRef.current.innerHTML = "";

      window.google.accounts.id.renderButton(
        buttonRef.current,
        {
          theme: "outline",
          size: "large",
          text: "signin_with",
          shape: "rectangular",
          width: 280
        }
      );
    };

    const script = document.querySelector(
      'script[src="https://accounts.google.com/gsi/client"]'
    );

    if (window.google?.accounts?.id) {
      initializeGoogle();
    } else if (script) {
      script.addEventListener("load", initializeGoogle);
    } else {
      setError("Google Identity Services script is missing.");
    }

    return () => {
      cancelled = true;
      script?.removeEventListener("load", initializeGoogle);
      activeCredentialHandler = null;
    };
  }, []);

  const handleLogout = () => {
    window.google?.accounts.id.disableAutoSelect();

    setProfile(null);
    setError("");
  };

  return (
    <div>
      <h2>Google Sign-In</h2>

      {error && <p>{error}</p>}

      {!profile ? (
        <div ref={buttonRef}></div>
      ) : (
        <div>
          <h3>Welcome, {profile.name}</h3>

          <img
            src={profile.picture}
            alt="Profile"
            width="80"
            style={{ borderRadius: "50%" }}
          />

          <p>Email: {profile.email}</p>

          <button onClick={handleLogout}>
            Logout
          </button>
        </div>
      )}
    </div>
  );
}

export default GoogleLogin;
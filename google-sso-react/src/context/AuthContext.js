import {
  createContext,
  useContext,
  useState
} from "react";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [idToken, setIdToken] = useState(null);

  const login = (userData, token) => {
    setUser(userData);
    setIdToken(token);
  };

  const logout = () => {
    setUser(null);
    setIdToken(null);

    window.google?.accounts.id.disableAutoSelect();
  };

  const isAuthenticated = Boolean(user && idToken);

  return (
    <AuthContext.Provider
      value={{
        user,
        idToken,
        isAuthenticated,
        login,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider"
    );
  }

  return context;
}
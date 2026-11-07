import { createContext } from 'react';

// { user, status: 'loading' | 'ready', signIn, signUp, logout } — provided by AuthProvider
const AuthContext = createContext(null);

export default AuthContext;

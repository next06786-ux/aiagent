import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type PropsWithChildren,
} from 'react';
import {
  changePassword as changePasswordRequest,
  fetchUser,
  login as loginRequest,
  logout as logoutRequest,
  register as registerRequest,
  updateUser,
  verifyToken,
} from '../services/auth';
import type {
  ChangePasswordPayload,
  LoginPayload,
  RegisterPayload,
  UpdateProfilePayload,
  UserInfo,
} from '../types/api';

interface AuthState {
  token: string;
  user: UserInfo | null;
}

interface AuthContextValue {
  user: UserInfo | null;
  token: string;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<{ is_admin?: boolean; [key: string]: any }>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  updateProfile: (payload: UpdateProfilePayload) => Promise<void>;
  changePassword: (payload: ChangePasswordPayload) => Promise<void>;
  quickLocalLogin: () => Promise<void>;
}

const STORAGE_KEY = 'choicerealm.web.auth';
const MOCK_TOKEN_PREFIX = 'local-demo-token';

const AuthContext = createContext<AuthContextValue | null>(null);

function readStorage(): AuthState {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { token: '', user: null };
    }

    const parsed = JSON.parse(raw) as Partial<AuthState>;
    return {
      token: parsed.token || '',
      user: parsed.user || null,
    };
  } catch {
    return { token: '', user: null };
  }
}

function writeStorage(state: AuthState) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function clearStorage() {
  window.localStorage.removeItem(STORAGE_KEY);
}

function isMockToken(token: string) {
  return token.startsWith(MOCK_TOKEN_PREFIX);
}

function buildMockUser(): UserInfo {
  return {
    user_id: '2c2139f7-bab4-483d-9882-ae83ce8734cd',
    username: 'demo',
    email: 'demo@local.dev',
    nickname: '本地演示账号',
    avatar_url: '',
    is_verified: true,
    created_at: new Date().toISOString(),
    last_login: new Date().toISOString(),
  };
}

export function AuthProvider({ children }: PropsWithChildren) {
  const initialState = readStorage();
  const [user, setUser] = useState<UserInfo | null>(initialState.user);
  const [token, setToken] = useState(initialState.token);
  const [isLoading, setIsLoading] = useState(true);
  const initializedRef = useRef(false);

  useEffect(() => {
    writeStorage({ token, user });
  }, [token, user]);

  useEffect(() => {
    if (initializedRef.current) {
      return;
    }
    initializedRef.current = true;

    async function bootstrap() {
      if (!token || !user?.user_id) {
        setIsLoading(false);
        return;
      }

      if (isMockToken(token)) {
        setIsLoading(false);
        return;
      }

      try {
        const verifyResult = await verifyToken(token);
        if (!verifyResult.valid || !verifyResult.userId) {
          clearStorage();
          setToken('');
          setUser(null);
          setIsLoading(false);
          return;
        }

        const freshUser = await fetchUser(verifyResult.userId);
        setUser(freshUser);
      } catch {
        clearStorage();
        setToken('');
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }

    void bootstrap();
  }, [token, user]);

  const value: AuthContextValue = {
    user,
    token,
    isLoading,
    isAuthenticated: Boolean(user && token),
    async login(payload) {
      const result = await loginRequest(payload);
      const nextUser: UserInfo = {
        user_id: result.user_id,
        username: result.username,
        email: result.email,
        nickname: result.nickname,
        avatar_url: result.avatar_url,
        is_verified: false,
      };
      setToken(result.token);
      setUser(nextUser);
      
      // 返回结果，包含 is_admin 字段
      return result;
    },
    async register(payload) {
      const result = await registerRequest(payload);
      const nextUser: UserInfo = {
        user_id: result.user_id,
        username: result.username,
        email: result.email,
        nickname: result.nickname,
        avatar_url: result.avatar_url,
        is_verified: false,
      };
      setToken(result.token);
      setUser(nextUser);
    },
    async logout() {
      try {
        if (token && !isMockToken(token)) {
          await logoutRequest(token);
        }
      } finally {
        clearStorage();
        setToken('');
        setUser(null);
      }
    },
    async refreshUser() {
      if (!user?.user_id || isMockToken(token)) {
        return;
      }
      const freshUser = await fetchUser(user.user_id);
      setUser(freshUser);
    },
    async updateProfile(payload) {
      if (!user?.user_id) {
        return;
      }

      if (isMockToken(token)) {
        setUser((current) => (current ? { ...current, ...payload } : current));
        return;
      }

      const updated = await updateUser(user.user_id, payload);
      setUser(updated);
    },
    async changePassword(payload) {
      if (!user?.user_id || isMockToken(token)) {
        return;
      }
      await changePasswordRequest(user.user_id, payload);
    },
    async quickLocalLogin() {
      const mockUser = buildMockUser();
      setToken(`${MOCK_TOKEN_PREFIX}-${Date.now()}`);
      setUser(mockUser);
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext must be used inside AuthProvider');
  }
  return context;
}

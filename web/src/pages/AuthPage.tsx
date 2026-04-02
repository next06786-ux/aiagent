import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { LoadingOrbit } from '../components/common/LoadingOrbit';
import { useAuth } from '../hooks/useAuth';

type AuthMode = 'login' | 'register';

const QUICK_LOGIN_ACCOUNT = {
  username: 'demo',
  password: 'local-only',
};

export function AuthPage() {
  const navigate = useNavigate();
  const { login, register, quickLocalLogin } = useAuth();
  const [mode, setMode] = useState<AuthMode>('login');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    nickname: '',
  });

  useEffect(() => {
    setError('');
  }, [mode]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      if (mode === 'login') {
        await login({
          username: form.username.trim(),
          password: form.password,
        });
      } else {
        await register({
          username: form.username.trim(),
          email: form.email.trim(),
          password: form.password,
          nickname: form.nickname.trim() || form.username.trim(),
        });
      }
      navigate('/', { replace: true });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : '登录失败，请稍后重试');
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleQuickLogin() {
    setMode('login');
    setError('');
    setForm((current) => ({
      ...current,
      username: QUICK_LOGIN_ACCOUNT.username,
      password: QUICK_LOGIN_ACCOUNT.password,
    }));
    setIsSubmitting(true);

    try {
      await quickLocalLogin();
      navigate('/', { replace: true });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : '快捷登录失败，请稍后重试');
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-layout">
      <section className="auth-hero">
        <div className="hero-badge">HarmonyOS to Web</div>
        <h1>LifeSwarm Web</h1>
        <p>
          以 Harmony 风格为基底，把从鸿蒙端迁移过来的体验重新整理为更贴近原版的 Web 入口。
          这里保留沉浸式卡片、流体化层次和 AI 决策产品的未来感质感。
        </p>

        <div className="hero-points">
          <article>
            <strong>沉浸式首页气质</strong>
            <span>延续鸿蒙端的柔和高光、半透明分层与圆角卡片，先把品牌感和入口氛围立起来。</span>
          </article>
          <article>
            <strong>无后端也可体验</strong>
            <span>快捷登录会自动填入演示账号并直接进入系统，方便先联调页面和交互，不依赖接口可用性。</span>
          </article>
          <article>
            <strong>贴近鸿蒙化视觉</strong>
            <span>后续页面会继续对齐原始 Harmony 端的结构、节奏、反馈和动效，让功能与 UI 一起还原。</span>
          </article>
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-switch">
          <button
            className={`switch-chip${mode === 'login' ? ' is-active' : ''}`}
            onClick={() => setMode('login')}
            type="button"
          >
            登录
          </button>
          <button
            className={`switch-chip${mode === 'register' ? ' is-active' : ''}`}
            onClick={() => setMode('register')}
            type="button"
          >
            注册
          </button>
          <button
            className="switch-chip quick-login-chip"
            onClick={() => void handleQuickLogin()}
            type="button"
            disabled={isSubmitting}
          >
            快捷登录
          </button>
        </div>

        <div className="auth-header">
          <h2>{mode === 'login' ? '进入你的决策空间' : '创建你的 LifeSwarm 账号'}</h2>
          <p>
            {mode === 'login'
              ? '登录后继续查看 AI 对话、决策副本、历史推演与个人画像。'
              : '注册后即可开始构建你的 AI 决策工作台，并同步保留 Harmony 风格体验。'}
          </p>
          {mode === 'login' ? (
            <p className="auth-quick-tip">
              快捷登录为本地演示模式，不连接后端也能进入。演示账号：`{QUICK_LOGIN_ACCOUNT.username}`，
              演示密码：`{QUICK_LOGIN_ACCOUNT.password}`。
            </p>
          ) : null}
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            <span>用户名</span>
            <input
              className="input"
              value={form.username}
              onChange={(event) =>
                setForm((current) => ({ ...current, username: event.target.value }))
              }
              placeholder="请输入用户名"
              required
            />
          </label>

          {mode === 'register' ? (
            <>
              <label>
                <span>邮箱</span>
                <input
                  className="input"
                  type="email"
                  value={form.email}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, email: event.target.value }))
                  }
                  placeholder="name@example.com"
                  required
                />
              </label>

              <label>
                <span>昵称</span>
                <input
                  className="input"
                  value={form.nickname}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, nickname: event.target.value }))
                  }
                  placeholder="展示给 AI 决策系统的名字"
                />
              </label>
            </>
          ) : null}

          <label>
            <span>密码</span>
            <input
              className="input"
              type="password"
              value={form.password}
              onChange={(event) =>
                setForm((current) => ({ ...current, password: event.target.value }))
              }
              placeholder="请输入密码"
              required
            />
          </label>

          {error ? <div className="form-error">{error}</div> : null}

          <button className="button button-primary button-large" disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <LoadingOrbit />
                <span>{mode === 'login' ? '登录中...' : '注册中...'}</span>
              </>
            ) : (
              <span>{mode === 'login' ? '登录并进入' : '注册并开始使用'}</span>
            )}
          </button>
        </form>
      </section>
    </div>
  );
}

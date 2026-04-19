import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { LoadingOrbit } from '../components/common/LoadingOrbit';
import { PasswordStrengthIndicator } from '../components/auth/PasswordStrengthIndicator';
import { useAuth } from '../hooks/useAuth';
import {
  validateEmail,
  validateUsername,
  validatePassword,
} from '../utils/passwordValidator';

type AuthMode = 'login' | 'register' | 'admin';

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
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    nickname: '',
  });

  useEffect(() => {
    setError('');
    setFieldErrors({});
  }, [mode]);

  function validateForm(): boolean {
    const errors: Record<string, string> = {};

    // 验证用户名
    const usernameCheck = validateUsername(form.username.trim());
    if (!usernameCheck.valid) {
      errors.username = usernameCheck.message || '用户名格式不正确';
    }

    // 注册模式下验证邮箱
    if (mode === 'register') {
      if (!form.email.trim()) {
        errors.email = '邮箱不能为空';
      } else if (!validateEmail(form.email.trim())) {
        errors.email = '邮箱格式不正确';
      }
    }

    // 验证密码
    if (!form.password) {
      errors.password = '密码不能为空';
    } else if (mode === 'register') {
      const passwordStrength = validatePassword(form.password);
      if (passwordStrength.score < 2) {
        errors.password = '密码强度太弱，请使用更强的密码';
      }
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    setFieldErrors({});

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      if (mode === 'login' || mode === 'admin') {
        const result = await login({
          username: form.username.trim(),
          password: form.password,
        });
        
        // 根据后端返回的 is_admin 字段决定跳转
        // 如果用户是管理员，跳转到管理中心；否则跳转到主页
        if (result?.is_admin) {
          navigate('/admin', { replace: true });
        } else {
          navigate('/', { replace: true });
        }
      } else {
        await register({
          username: form.username.trim(),
          email: form.email.trim(),
          password: form.password,
          nickname: form.nickname.trim() || form.username.trim(),
        });
        navigate('/', { replace: true });
      }
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : '操作失败，请稍后重试');
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleQuickLogin() {
    setMode('login');
    setError('');
    setFieldErrors({});
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
        <div className="hero-badge">ChoiceRealm · 择境</div>
        <h1>择境 Web</h1>
        <p>
          智能决策支持系统，融合 AI 核心、知识图谱与多维度分析，
          为你的人生重要决策提供科学依据和智慧洞察。
        </p>

        <div className="hero-points">
          <article>
            <strong>AI 智能决策</strong>
            <span>多智能体协同分析，从教育、职业、人际等多维度评估决策方案，提供个性化建议。</span>
          </article>
          <article>
            <strong>知识星图构建</strong>
            <span>自动构建你的专属知识网络，发现隐藏关联，让每个决策都有历史数据支撑。</span>
          </article>
          <article>
            <strong>平行人生推演</strong>
            <span>通过塔罗牌决策游戏，探索不同选择的可能性，收集你的决策逻辑画像。</span>
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
          <button
            className={`switch-chip admin-login-chip${mode === 'admin' ? ' is-active' : ''}`}
            onClick={() => setMode('admin')}
            type="button"
          >
            管理员端
          </button>
        </div>

        <div className="auth-header">
          <h2>
            {mode === 'login' ? '进入你的决策空间' : 
             mode === 'register' ? '创建你的择境账号' : 
             '管理员登录'}
          </h2>
          <p>
            {mode === 'login'
              ? '登录后继续使用 AI 核心、决策副本、知识星图、平行人生等智能决策工具。'
              : mode === 'register'
              ? '注册后即可开始构建你的专属决策空间，让 AI 成为你的智慧伙伴。'
              : '请使用管理员账号登录，访问系统管理功能。'}
          </p>
          {mode === 'login' ? (
            <p className="auth-quick-tip">
              快捷登录为演示模式，账号：`{QUICK_LOGIN_ACCOUNT.username}`，
              密码：`{QUICK_LOGIN_ACCOUNT.password}`。管理员请点击上方"管理员端"按钮。
            </p>
          ) : mode === 'admin' ? (
            <p className="auth-admin-tip">
              管理员账号：`admin`，密码：`admin123`。登录后将进入管理中心。
            </p>
          ) : null}
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            <span>用户名</span>
            <input
              className={`input${fieldErrors.username ? ' input-error' : ''}`}
              value={form.username}
              onChange={(event) =>
                setForm((current) => ({ ...current, username: event.target.value }))
              }
              placeholder="请输入用户名"
              required
            />
            {fieldErrors.username && (
              <div className="field-error">{fieldErrors.username}</div>
            )}
          </label>

          {mode === 'register' ? (
            <>
              <label>
                <span>邮箱</span>
                <input
                  className={`input${fieldErrors.email ? ' input-error' : ''}`}
                  type="email"
                  value={form.email}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, email: event.target.value }))
                  }
                  placeholder="name@example.com"
                  required
                />
                {fieldErrors.email && (
                  <div className="field-error">{fieldErrors.email}</div>
                )}
              </label>

              <label>
                <span>昵称（可选）</span>
                <input
                  className="input"
                  value={form.nickname}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, nickname: event.target.value }))
                  }
                  placeholder="在择境中显示的名字"
                />
              </label>
            </>
          ) : null}

          <label>
            <span>密码</span>
            <input
              className={`input${fieldErrors.password ? ' input-error' : ''}`}
              type="password"
              value={form.password}
              onChange={(event) =>
                setForm((current) => ({ ...current, password: event.target.value }))
              }
              placeholder="请输入密码"
              required
            />
            {fieldErrors.password && (
              <div className="field-error">{fieldErrors.password}</div>
            )}
            {mode === 'register' && (
              <PasswordStrengthIndicator password={form.password} show={form.password.length > 0} />
            )}
          </label>

          {error ? <div className="form-error">{error}</div> : null}

          <button className="button button-primary button-large" disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <LoadingOrbit />
                <span>
                  {mode === 'login' ? '登录中...' : 
                   mode === 'register' ? '注册中...' : 
                   '管理员登录中...'}
                </span>
              </>
            ) : (
              <span>
                {mode === 'login' ? '登录并进入' : 
                 mode === 'register' ? '注册并开始使用' : 
                 '登录管理中心'}
              </span>
            )}
          </button>
        </form>
      </section>
    </div>
  );
}

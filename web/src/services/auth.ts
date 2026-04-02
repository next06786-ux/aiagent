import type {
  ApiEnvelope,
  ChangePasswordPayload,
  LoginPayload,
  LoginResponse,
  RegisterPayload,
  UpdateProfilePayload,
  UserInfo,
} from '../types/api';
import { ApiError, postJson, putJson, requestJson } from './api';

export async function login(payload: LoginPayload) {
  const result = await postJson<ApiEnvelope<LoginResponse>>(
    '/api/auth/login',
    payload,
  );

  if (result.code !== 200 || !result.data) {
    throw new ApiError(result.message || '登录失败', result.code, result);
  }

  return result.data;
}

export async function register(payload: RegisterPayload) {
  const result = await postJson<ApiEnvelope<LoginResponse>>(
    '/api/auth/register',
    payload,
  );

  if (result.code !== 200 || !result.data) {
    throw new ApiError(result.message || '注册失败', result.code, result);
  }

  return result.data;
}

export async function logout(token: string) {
  const result = await postJson<ApiEnvelope<null>>('/api/auth/logout', {
    token,
  });

  if (result.code !== 200) {
    throw new ApiError(result.message || '退出失败', result.code, result);
  }
}

export async function verifyToken(token: string) {
  const result = await postJson<ApiEnvelope<{ user_id?: string; valid: boolean }>>(
    '/api/auth/verify-token',
    {
      token,
    },
  );

  if (result.code !== 200 || !result.data?.valid) {
    return { valid: false, userId: '' };
  }

  return {
    valid: true,
    userId: result.data.user_id || '',
  };
}

export async function fetchUser(userId: string) {
  const result = await requestJson<ApiEnvelope<UserInfo>>(
    `/api/auth/user/${encodeURIComponent(userId)}`,
  );

  if (result.code !== 200 || !result.data) {
    throw new ApiError(result.message || '获取用户信息失败', result.code, result);
  }

  return result.data;
}

export async function updateUser(userId: string, payload: UpdateProfilePayload) {
  const result = await putJson<ApiEnvelope<UserInfo>>(
    `/api/auth/user/${encodeURIComponent(userId)}`,
    payload,
  );

  if (result.code !== 200 || !result.data) {
    throw new ApiError(result.message || '更新资料失败', result.code, result);
  }

  return result.data;
}

export async function changePassword(
  userId: string,
  payload: ChangePasswordPayload,
) {
  const result = await postJson<ApiEnvelope<null>>('/api/auth/change-password', {
    user_id: userId,
    ...payload,
  });

  if (result.code !== 200) {
    throw new ApiError(result.message || '修改密码失败', result.code, result);
  }
}

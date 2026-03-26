/**
 * 管理后台API客户端
 */
import { authServiceClient } from './client';

export interface User {
  user_id: string;
  username: string;
  email: string;
  display_name?: string;
  roles: string[];
  permissions: string[];
  status: string;
  last_login_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface UserDetail extends User {
  metadata: Record<string, any>;
  role_details: Array<{ id: string; name: string; code: string }>;
  permission_details: Array<{ id: string; name: string; code: string }>;
}

export interface Role {
  id: string;
  name: string;
  code: string;
  description: string;
  permissions: string[];
  is_system: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Permission {
  id: string;
  name: string;
  code: string;
  resource_type: string;
  permission_type: string;
  description: string;
  created_at?: string;
  updated_at?: string;
}

export interface MenuConfigItem {
  name: string;
  href: string;
  requiredPermission?: string;
  requireAdmin?: boolean;
  children?: MenuConfigItem[];
}

export interface ListResponse<T> {
  [key: string]: T[] | number;
  total: number;
  page: number;
  page_size: number;
}

// 创建用户请求（与后端 UserCreate 对应）
export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  display_name?: string;
  roles?: string[];
  permissions?: string[];
  status?: string;
  metadata?: Record<string, any>;
}

// 用户管理API
export async function getUsers(params: {
  page?: number;
  page_size?: number;
  search?: string;
  status?: string;
  role?: string;
}): Promise<ListResponse<User>> {
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.set('page', params.page.toString());
  if (params.page_size) queryParams.set('page_size', params.page_size.toString());
  if (params.search) queryParams.set('search', params.search);
  if (params.status) queryParams.set('status', params.status);
  if (params.role) queryParams.set('role', params.role);

  return authServiceClient.get<ListResponse<User>>(`/admin/users?${queryParams.toString()}`);
}

export async function getUser(userId: string): Promise<UserDetail> {
  return authServiceClient.get<UserDetail>(`/admin/users/${userId}`);
}

export async function createUser(userData: CreateUserRequest): Promise<User> {
  // auth-service 的路由签名为 create_user(user_data: UserCreate, ...)：
  // 只有一个 body 参数时，FastAPI 默认期望请求体是 UserCreate 字段本身（而不是再包一层 user_data）
  return authServiceClient.post<User>('/admin/users', userData);
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  password?: string;
  display_name?: string;
  roles?: string[];
  permissions?: string[];
  status?: string;
  metadata?: Record<string, any>;
}

export async function updateUser(userId: string, userData: UpdateUserRequest): Promise<User> {
  // 与后端 update_user(user_data: UserUpdate, ...) 对应：body 期望为 UserUpdate 字段本身
  return authServiceClient.put<User>(`/admin/users/${userId}`, userData);
}

export async function deleteUser(userId: string): Promise<void> {
  return authServiceClient.delete(`/admin/users/${userId}`);
}

export async function addRoleToUser(userId: string, roleId: string): Promise<void> {
  return authServiceClient.post(`/admin/users/${userId}/roles/${roleId}`, {});
}

export async function removeRoleFromUser(userId: string, roleId: string): Promise<void> {
  return authServiceClient.delete(`/admin/users/${userId}/roles/${roleId}`);
}

// 角色管理API
export async function getRoles(params: {
  page?: number;
  page_size?: number;
  search?: string;
}): Promise<ListResponse<Role>> {
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.set('page', params.page.toString());
  if (params.page_size) queryParams.set('page_size', params.page_size.toString());
  if (params.search) queryParams.set('search', params.search);

  return authServiceClient.get<ListResponse<Role>>(`/admin/roles?${queryParams.toString()}`);
}

export async function getRole(roleId: string): Promise<Role> {
  return authServiceClient.get<Role>(`/admin/roles/${roleId}`);
}

export async function createRole(roleData: Partial<Role>): Promise<Role> {
  return authServiceClient.post<Role>('/admin/roles', roleData);
}

export async function updateRole(roleId: string, roleData: Partial<Role>): Promise<Role> {
  return authServiceClient.put<Role>(`/admin/roles/${roleId}`, roleData);
}

export async function deleteRole(roleId: string): Promise<void> {
  return authServiceClient.delete(`/admin/roles/${roleId}`);
}

export async function addPermissionToRole(roleId: string, permissionId: string): Promise<void> {
  return authServiceClient.post(`/admin/roles/${roleId}/permissions/${permissionId}`, {});
}

export async function removePermissionFromRole(
  roleId: string,
  permissionId: string
): Promise<void> {
  return authServiceClient.delete(`/admin/roles/${roleId}/permissions/${permissionId}`);
}

// 权限管理API
export async function getPermissions(params: {
  page?: number;
  page_size?: number;
  search?: string;
  resource_type?: string;
  permission_type?: string;
}): Promise<ListResponse<Permission>> {
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.set('page', params.page.toString());
  if (params.page_size) queryParams.set('page_size', params.page_size.toString());
  if (params.search) queryParams.set('search', params.search);
  if (params.resource_type) queryParams.set('resource_type', params.resource_type);
  if (params.permission_type) queryParams.set('permission_type', params.permission_type);

  return authServiceClient.get<ListResponse<Permission>>(
    `/admin/permissions?${queryParams.toString()}`
  );
}

export async function getPermission(permissionId: string): Promise<Permission> {
  return authServiceClient.get<Permission>(`/admin/permissions/${permissionId}`);
}

export async function createPermission(permissionData: Partial<Permission>): Promise<Permission> {
  return authServiceClient.post<Permission>('/admin/permissions', permissionData);
}

export async function updatePermission(
  permissionId: string,
  permissionData: Partial<Permission>
): Promise<Permission> {
  return authServiceClient.put<Permission>(`/admin/permissions/${permissionId}`, permissionData);
}

export async function deletePermission(permissionId: string): Promise<void> {
  return authServiceClient.delete(`/admin/permissions/${permissionId}`);
}

// 菜单权限配置API
export async function getMenuConfig(): Promise<{ config: MenuConfigItem[] }> {
  return authServiceClient.get<{ config: MenuConfigItem[] }>('/admin/menus');
}

export async function saveMenuConfig(config: MenuConfigItem[]): Promise<{ config: MenuConfigItem[] }> {
  return authServiceClient.put<{ config: MenuConfigItem[] }>('/admin/menus', { config });
}

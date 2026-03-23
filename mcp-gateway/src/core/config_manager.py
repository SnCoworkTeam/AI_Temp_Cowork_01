"""
工具配置管理器
管理工具参数配置、连接池配置、认证凭据等
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
import json
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, db: Session, encryption_key: Optional[str] = None):
        self.db = db
        self._encryption_key = encryption_key
        self._cipher = None
        
        if encryption_key:
            try:
                # 确保密钥是32字节的base64编码
                key = encryption_key.encode()
                if len(key) != 44:  # Fernet key是44字节的base64字符串
                    # 使用密钥派生
                    import hashlib
                    key_hash = hashlib.sha256(key).digest()
                    key_b64 = base64.urlsafe_b64encode(key_hash)
                    key = key_b64
                self._cipher = Fernet(key)
            except Exception as e:
                logger.warning(f"Failed to initialize encryption: {str(e)}")
    
    def get_tool_config(self, tool_id: str) -> Dict[str, Any]:
        """获取工具配置"""
        try:
            from ..repositories.tool_repository import ToolRepository
            
            tool_repo = ToolRepository(self.db)
            tool = tool_repo.get_by_id(tool_id)
            
            if tool:
                return tool.config or {}
            return {}
            
        except Exception as e:
            logger.error(f"Error getting tool config: {str(e)}")
            return {}
    
    def update_tool_config(
        self,
        tool_id: str,
        config: Dict[str, Any],
        merge: bool = True
    ) -> bool:
        """更新工具配置"""
        try:
            from ..repositories.tool_repository import ToolRepository
            
            tool_repo = ToolRepository(self.db)
            return tool_repo.update_tool_config(tool_id, config, merge=merge)
            
        except Exception as e:
            logger.error(f"Error updating tool config: {str(e)}")
            return False
    
    def get_connection_pool_config(self, tool_id: str) -> Dict[str, Any]:
        """获取连接池配置"""
        try:
            config = self.get_tool_config(tool_id)
            return config.get("connection_pool", {})
        except Exception as e:
            logger.error(f"Error getting connection pool config: {str(e)}")
            return {}
    
    def update_connection_pool_config(
        self,
        tool_id: str,
        pool_config: Dict[str, Any]
    ) -> bool:
        """更新连接池配置"""
        try:
            config = self.get_tool_config(tool_id)
            config["connection_pool"] = pool_config
            return self.update_tool_config(tool_id, config, merge=False)
        except Exception as e:
            logger.error(f"Error updating connection pool config: {str(e)}")
            return False
    
    def get_credentials(
        self,
        tool_id: str,
        credential_key: str
    ) -> Optional[Dict[str, Any]]:
        """获取认证凭据（解密）"""
        try:
            config = self.get_tool_config(tool_id)
            credentials = config.get("credentials", {})
            
            encrypted_credential = credentials.get(credential_key)
            if not encrypted_credential:
                return None
            
            # 解密凭据
            if self._cipher:
                try:
                    decrypted = self._cipher.decrypt(encrypted_credential.encode())
                    return json.loads(decrypted.decode())
                except Exception as e:
                    logger.error(f"Error decrypting credential: {str(e)}")
                    return None
            else:
                # 如果没有加密，直接返回（不推荐）
                logger.warning("Encryption not available, returning plain credential")
                return encrypted_credential if isinstance(encrypted_credential, dict) else None
                
        except Exception as e:
            logger.error(f"Error getting credentials: {str(e)}")
            return None
    
    def set_credentials(
        self,
        tool_id: str,
        credential_key: str,
        credential_value: Dict[str, Any]
    ) -> bool:
        """设置认证凭据（加密存储）"""
        try:
            config = self.get_tool_config(tool_id)
            if "credentials" not in config:
                config["credentials"] = {}
            
            # 加密凭据
            if self._cipher:
                try:
                    credential_json = json.dumps(credential_value)
                    encrypted = self._cipher.encrypt(credential_json.encode())
                    config["credentials"][credential_key] = encrypted.decode()
                except Exception as e:
                    logger.error(f"Error encrypting credential: {str(e)}")
                    return False
            else:
                # 如果没有加密，直接存储（不推荐）
                logger.warning("Encryption not available, storing plain credential (not recommended)")
                config["credentials"][credential_key] = credential_value
            
            return self.update_tool_config(tool_id, config, merge=False)
            
        except Exception as e:
            logger.error(f"Error setting credentials: {str(e)}")
            return False
    
    def delete_credentials(
        self,
        tool_id: str,
        credential_key: str
    ) -> bool:
        """删除认证凭据"""
        try:
            config = self.get_tool_config(tool_id)
            if "credentials" in config and credential_key in config["credentials"]:
                del config["credentials"][credential_key]
                return self.update_tool_config(tool_id, config, merge=False)
            return True
        except Exception as e:
            logger.error(f"Error deleting credentials: {str(e)}")
            return False
    
    def get_parameter_config(self, tool_id: str) -> Dict[str, Any]:
        """获取工具参数配置"""
        try:
            from ..repositories.tool_repository import ToolRepository
            
            tool_repo = ToolRepository(self.db)
            tool = tool_repo.get_by_id(tool_id)
            
            if tool:
                return tool.parameters or {}
            return {}
            
        except Exception as e:
            logger.error(f"Error getting parameter config: {str(e)}")
            return {}
    
    def update_parameter_config(
        self,
        tool_id: str,
        parameters: Dict[str, Any]
    ) -> bool:
        """更新工具参数配置"""
        try:
            from ..repositories.tool_repository import ToolRepository
            
            tool_repo = ToolRepository(self.db)
            tool = tool_repo.get_by_id(tool_id)
            
            if tool:
                tool.parameters = parameters
                self.db.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating parameter config: {str(e)}")
            self.db.rollback()
            return False










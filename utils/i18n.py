"""
国际化(i18n)工具
支持多语言文本翻译、参数格式化、嵌套键访问
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from fastapi import Header, Depends

logger = logging.getLogger(__name__)


class I18nManager:
    """
    多语言管理器
    负责加载和管理所有语言文件
    """

    def __init__(self, locales_dir: str = "locales", default_lang: str = "en"):
        """
        初始化多语言管理器

        Args:
            locales_dir: 语言文件目录路径
            default_lang: 默认语言代码
        """
        self.locales_dir = Path(locales_dir)
        self.default_lang = default_lang
        self.translations: Dict[str, Dict] = {}
        self.supported_languages = set()
        self._load_translations()

    def _load_translations(self):
        """加载所有语言文件"""
        if not self.locales_dir.exists():
            logger.warning(f"语言文件目录 {self.locales_dir} 不存在，将创建该目录")
            self.locales_dir.mkdir(parents=True, exist_ok=True)
            return

        # 遍历所有JSON文件
        for file_path in self.locales_dir.glob("*.json"):
            lang = file_path.stem  # 文件名即语言代码
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.translations[lang] = json.load(f)
                    self.supported_languages.add(lang)
                logger.info(f"✓ 已加载语言: {lang} ({file_path})")
            except json.JSONDecodeError as e:
                logger.error(f"✗ 语言文件 {file_path} JSON格式错误: {e}")
            except Exception as e:
                logger.error(f"✗ 加载语言文件 {file_path} 失败: {e}")

        if not self.translations:
            logger.warning("未加载任何语言文件")
        else:
            logger.info(f"支持的语言: {', '.join(self.supported_languages)}")

    def get_translation(self, lang: str) -> Dict:
        """
        获取指定语言的翻译字典

        Args:
            lang: 语言代码

        Returns:
            翻译字典，如果语言不存在则返回默认语言
        """
        if lang in self.translations:
            return self.translations[lang]

        # 尝试提取主语言代码（如 zh-CN -> zh）
        main_lang = lang.split('-')[0].split('_')[0]
        if main_lang in self.translations:
            return self.translations[main_lang]

        # 返回默认语言
        return self.translations.get(self.default_lang, {})

    def is_supported(self, lang: str) -> bool:
        """检查是否支持该语言"""
        return lang in self.supported_languages

    def reload(self):
        """重新加载所有语言文件（热更新）"""
        logger.info("重新加载语言文件...")
        self.translations.clear()
        self.supported_languages.clear()
        self._load_translations()


# 全局单例
i18n_manager = I18nManager()


class I18n:
    """
    多语言实例
    用于具体翻译操作
    """

    def __init__(self, lang: str = "zh"):
        """
        初始化多语言实例

        Args:
            lang: 语言代码
        """
        self.lang = lang
        self.translations = i18n_manager.get_translation(lang)

    def t(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        """
        翻译文本

        Args:
            key: 翻译键，支持点号分隔的嵌套键，如 "greeting.hello"
            default: 默认值，如果找不到翻译则返回此值
            **kwargs: 格式化参数，用于替换文本中的占位符

        Returns:
            翻译后的文本
        """
        # 支持嵌套键，如 "greeting.hello"
        keys = key.split('.')
        value = self.translations

        # 逐层访问
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    break
            else:
                value = None
                break

        # 如果找不到翻译
        if value is None:
            if default is not None:
                return default
            logger.warning(f"翻译键 '{key}' 在语言 '{self.lang}' 中不存在")
            return key  # 返回键本身

        # 格式化参数
        if kwargs and isinstance(value, str):
            try:
                return value.format(**kwargs)
            except KeyError as e:
                logger.error(f"格式化参数缺失: {e}, key={key}, kwargs={kwargs}")
                return value
            except Exception as e:
                logger.error(f"格式化失败: {e}, key={key}, value={value}, kwargs={kwargs}")
                return value

        return str(value)

    def exists(self, key: str) -> bool:
        """
        检查翻译键是否存在

        Args:
            key: 翻译键

        Returns:
            是否存在
        """
        keys = key.split('.')
        value = self.translations

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return False

        return True

    def get_dict(self, key: str) -> Dict:
        """
        获取某个键下的所有翻译（返回字典）

        Args:
            key: 翻译键

        Returns:
            翻译字典
        """
        keys = key.split('.')
        value = self.translations

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, {})
            else:
                return {}

        return value if isinstance(value, dict) else {}


# ==================== FastAPI 依赖注入 ====================

def parse_accept_language(accept_language: Optional[str]) -> str:
    """
    解析 Accept-Language 请求头

    Args:
        accept_language: Accept-Language 请求头值

    Returns:
        语言代码
    """
    if not accept_language:
        return i18n_manager.default_lang

    # 解析第一个语言（优先级最高）
    try:
        # 格式: "zh-CN,zh;q=0.9,en;q=0.8"
        lang = accept_language.split(',')[0].split(';')[0].strip().lower()

        # 提取主语言代码
        main_lang = lang.split('-')[0].split('_')[0]

        # 检查是否支持
        if i18n_manager.is_supported(main_lang):
            return main_lang

        # 尝试完整的语言代码
        if i18n_manager.is_supported(lang):
            return lang

    except Exception as e:
        logger.error(f"解析 Accept-Language 失败: {e}")

    return i18n_manager.default_lang


def get_language(
        accept_language: Optional[str] = Header(
            None,
            alias="Accept-Language",
            description="客户端语言偏好"
        )
) -> str:
    """
    从请求头获取语言代码（FastAPI依赖）

    Args:
        accept_language: Accept-Language 请求头

    Returns:
        语言代码
    """
    return parse_accept_language(accept_language)


def get_i18n(lang: str = Depends(get_language)) -> I18n:
    """
    获取多语言实例（FastAPI依赖）

    Args:
        lang: 语言代码

    Returns:
        I18n实例
    """
    return I18n(lang)


# ==================== 工具函数 ====================

def reload_translations():
    """重新加载所有语言文件（用于热更新）"""
    i18n_manager.reload()


def get_supported_languages() -> list:
    """获取支持的语言列表"""
    return list(i18n_manager.supported_languages)


def add_translation(lang: str, translations: Dict):
    """
    动态添加翻译（用于运行时添加）

    Args:
        lang: 语言代码
        translations: 翻译字典
    """
    if lang in i18n_manager.translations:
        # 合并翻译
        i18n_manager.translations[lang].update(translations)
    else:
        i18n_manager.translations[lang] = translations

    i18n_manager.supported_languages.add(lang)
    logger.info(f"已添加/更新语言: {lang}")
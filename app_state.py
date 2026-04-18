from __future__ import annotations

import json
import os
from pathlib import Path

class AppState:
    """Управление настройками приложения в JSON формате"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Путь к файлу настроек
        self.config_file = 'app_settings.json'
        
        # Загружаем настройки при инициализации
        self.settings = self.load_settings()
        
        self._initialized = True
    
    def load_settings(self):
        """Загрузка настроек из JSON файла"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                
                # Сливаем с настройками по умолчанию
                return self._merge_with_defaults(loaded)
            else:
                # Используем настройки по умолчанию
                default_settings = self.get_default_settings()
                self.save_settings(default_settings)
                return default_settings
                
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
            return self.get_default_settings()
    
    def save_settings(self, settings=None):
        """Сохранение настроек в JSON файл"""
        try:
            if settings is None:
                settings = self.settings
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
            return False
    
    def get_default_settings(self):
        """Настройки по умолчанию"""
        return {
            'screen_size': '123123 x 123123',
            'font_family': 'Arial',
            'font_size': 12,
            'button_color': '#000000',
            'text_color': '#FFFFFF',
            'background_color': '#FFFFFF',
            'forecast_settings': {
                'default_open_hour': 9,
                'default_close_hour': 21,
                'per_dow_hours': None,
            },
        }

    @staticmethod
    def _deep_merge_forecast_settings(default_fs: dict, loaded_fs: dict | None) -> dict:
        """Глубокое слияние только блока forecast_settings (ключи дней — строки \"0\"..\"6\")."""
        if not loaded_fs or not isinstance(loaded_fs, dict):
            return dict(default_fs)
        out = dict(default_fs)
        for k, v in loaded_fs.items():
            if k == 'per_dow_hours':
                if v is None:
                    out['per_dow_hours'] = None
                elif isinstance(v, dict):
                    merged_dow = {}
                    base_dow = default_fs.get('per_dow_hours') or {}
                    if isinstance(base_dow, dict):
                        merged_dow.update(base_dow)
                    for dkey, dval in v.items():
                        if dval is None:
                            merged_dow.pop(str(dkey), None)
                        elif isinstance(dval, dict):
                            merged_dow[str(dkey)] = {
                                'open': int(dval.get('open', default_fs['default_open_hour'])),
                                'close': int(dval.get('close', default_fs['default_close_hour'])),
                            }
                    out['per_dow_hours'] = merged_dow if merged_dow else None
                else:
                    out['per_dow_hours'] = default_fs.get('per_dow_hours')
            elif k in ('default_open_hour', 'default_close_hour'):
                out[k] = int(v)
        return out
    
    def _merge_with_defaults(self, loaded_settings):
        """Слияние загруженных настроек с настройками по умолчанию"""
        default = self.get_default_settings()
        
        merged = default.copy()
        loaded_fs = loaded_settings.get('forecast_settings') if isinstance(loaded_settings, dict) else None
        merged.update({k: v for k, v in loaded_settings.items() if k != 'forecast_settings'})
        
        merged['forecast_settings'] = self._deep_merge_forecast_settings(
            default['forecast_settings'],
            loaded_fs,
        )
        
        for key in default.keys():
            if key not in merged:
                merged[key] = default[key]
        
        return merged
    
    def get(self, key, default=None):
        """Получение значения настройки"""
        return self.settings.get(key, default)
    
    def set(self, key, value, save=True):
        """Установка значения настройки"""
        self.settings[key] = value
        if save:
            self.save_settings()


# Глобальный экземпляр для удобного доступа
app_state = AppState()
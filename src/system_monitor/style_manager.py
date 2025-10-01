# style_manager.py
class StyleManager:
    """样式管理器"""

    @staticmethod
    def get_progress_bar_style(color, config):
        """获取进度条样式"""
        return f"""
            QProgressBar {{
                border: {config.get("border_width", 1)}px solid {config.get("border_color", "#ccc")};
                border-radius: {config.get("border_radius", 2)}px;
                background-color: rgba(255, 255, 255, {config.get("background_alpha", 100)});
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: {config.get("chunk_radius", 1)}px;
            }}
        """

    @staticmethod
    def get_label_style(config):
        """获取标签样式"""
        bg_color = (
            "transparent" if config.get("background_transparent", True) else "white"
        )
        return f"""
            QLabel {{
                background-color: {bg_color};
                font-size: {config.get("font_size", 10)}px;
                color: {config.get("color", "black")};
                padding: {config.get("padding", 1)}px;
            }}
        """

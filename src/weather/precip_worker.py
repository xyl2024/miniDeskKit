import requests
from PySide6.QtCore import QThread, Signal

from utils.logger import logger


# Precipitation: n.降水(雨/雪)
class PrecipWorker(QThread):
    precip_data = Signal(list)
    precip_summary = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, api_host, api_key, location, update_interval):
        super().__init__()
        self._running = True
        self.api_host = api_host
        self.api_key = api_key
        self.location = location  # 例如 "113.65,34.76" (经度,纬度)
        self.update_interval = update_interval
        self.base_url = "https://{api_host}/v7/minutely/5m?location={location}"

    def run(self):
        """在线程中循环获取降水数据"""
        while self._running:
            try:
                logger.info("开始获取降水量数据...")
                url = self.base_url.format(
                    api_host=self.api_host, location=self.location
                )
                headers = {"X-QW-Api-Key": self.api_key}
                response = requests.get(url, headers=headers, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    code = data.get("code")
                    if code == "200":
                        minutely_list = data.get("minutely", [])
                        summary = data.get("summary", "")
                        logger.info(f"Summary: {summary}")
                        logger.info(f"Precipitation: {minutely_list}")
                        self.precip_data.emit(minutely_list)
                        self.precip_summary.emit(summary)
                    else:
                        error_msg = f"API返回错误码: {code}"
                        logger.warning(error_msg)
                        self.error_occurred.emit(error_msg)
                else:
                    error_msg = f"HTTP请求失败，状态码: {response.status_code}"
                    logger.error(error_msg)
                    self.error_occurred.emit(error_msg)

            except requests.exceptions.Timeout:
                error_msg = "请求天气API超时"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
            except requests.exceptions.RequestException as e:
                error_msg = f"请求天气API时发生错误: {str(e)}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)
            except Exception as e:
                error_msg = f"获取天气数据时发生未知错误: {str(e)}"
                logger.error(error_msg)
                self.error_occurred.emit(error_msg)

            # 休眠指定时间
            if self._running:
                self.msleep(self.update_interval)

        logger.info("关闭 Minutely Precipitation Worker 线程")

    def stop(self):
        """停止线程"""
        self._running = False

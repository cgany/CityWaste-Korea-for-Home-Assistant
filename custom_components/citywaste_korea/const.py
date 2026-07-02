"""Constants for the CityWaste Korea integration."""

DOMAIN = "citywaste_korea"

CONF_TAGPRINTCD = "tagprintcd"
CONF_APTDONG = "aptdong"
CONF_APTHONO = "apthono"
CONF_MONITORED_CONDITIONS = "monitored_conditions"

DEFAULT_NAME = "Citywaste"
DEFAULT_MONITORED_CONDITIONS = ["total_kg", "total_count", "last_kg"]

BASE_URL = "https://www.citywaste.or.kr/portal/status/selectDischargerQuantityQuickMonthNew.do"
REFERER = "https://www.citywaste.or.kr/portal/status/selectSimpleEmissionQuantity.do"

MONITORED_CONDITIONS = {
    "total_count": ["Total count", None, "mdi:counter"],
    "last_kg": ["Last kg", "kg", "mdi:scale"],
    "last_date": ["Last date", None, "mdi:calendar-clock"],
    "total_kg": ["Total kg", "kg", "mdi:scale"],
    "address": ["Address", None, "mdi:home"],
}

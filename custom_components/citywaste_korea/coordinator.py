class CityWasteCoordinator(DataUpdateCoordinator):
    async def _async_update_data(self):
        return await self.hass.async_add_executor_job(
            self.api.fetch_data
        )

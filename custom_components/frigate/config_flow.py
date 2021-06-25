"""Adds config flow for Frigate."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_URL
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import FrigateApiClient, FrigateApiClientError
from .const import DEFAULT_HOST, DOMAIN

_LOGGER: logging.Logger = logging.getLogger(__name__)


class FrigateFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Frigate."""

    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(
        self, user_input: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Handle a flow initialized by the user."""

        if user_input is None:
            return self._show_config_form()

        try:
            # Cannot use cv.url validation in the schema itself, so
            # apply extra validation here.
            cv.url(user_input[CONF_URL])
        except vol.Invalid:
            return self._show_config_form(user_input, errors={"base": "invalid_url"})

        try:
            session = async_create_clientsession(self.hass)
            client = FrigateApiClient(user_input[CONF_URL], session)
            await client.async_get_stats()
        except FrigateApiClientError:
            return self._show_config_form(user_input, errors={"base": "cannot_connect"})

        # Search for duplicates with the same Frigate CONF_HOST value.
        for existing_entry in self._async_current_entries(include_ignore=False):
            if existing_entry.data.get(CONF_URL) == user_input[CONF_URL]:
                return self.async_abort(reason="already_configured")

        return self.async_create_entry(title=f"{user_input[CONF_URL]}", data=user_input)

    def _show_config_form(
        self,
        user_input: dict[str, Any] | None = None,
        errors: dict[str, Any] | None = None,
    ):  # pylint: disable=unused-argument
        """Show the configuration form."""
        if user_input is None:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_URL, default=user_input.get(CONF_URL, DEFAULT_HOST)
                    ): str
                }
            ),
            errors=errors,
        )

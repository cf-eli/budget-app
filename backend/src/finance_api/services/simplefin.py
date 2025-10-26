"""SimpleFin Class."""

import base64
import binascii
import logging

from aiohttp import (
    BasicAuth,
    ClientConnectorError,
    ClientConnectorSSLError,
    ClientSession,
    TCPConnector,
)

from finance_api.schemas.exceptions import (
    SimpleFinAuthError,
    SimpleFinClaimError,
    SimpleFinInvalidAccountURLError,
    SimpleFinInvalidClaimTokenError,
    SimpleFinPaymentRequiredError,
)
from finance_api.schemas.schema import FinancialData
from finance_api.services.mixins import LoggingMixin

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
LOGGER = logging.getLogger(__name__)

# HTTP Status Codes
HTTP_PAYMENT_REQUIRED = 402
HTTP_FORBIDDEN = 403


def _raise_claim_error() -> None:
    """Raise SimpleFin claim error."""
    raise SimpleFinClaimError


def _raise_payment_required_error() -> None:
    """Raise SimpleFin payment required error."""
    raise SimpleFinPaymentRequiredError


def _raise_auth_error() -> None:
    """Raise SimpleFin auth error."""
    raise SimpleFinAuthError


class SimpleFin(LoggingMixin):
    """SimpleFin Class."""

    def decode_claim_token(self, token_string: str) -> str:
        """
        Decode a setup token to get the claim URL.

        Args:
            token_string: Base64 encoded setup token

        Returns:
            str: The claim URL (e.g., https://bridge.simplefin.org/simplefin/claim/demo)

        Raises:
            SimpleFinInvalidClaimTokenError: If token is not valid base64

        """
        try:
            claim_url = base64.b64decode(token_string).decode("utf-8")
        except binascii.Error as err:
            raise SimpleFinInvalidClaimTokenError from err
        return claim_url

    def decode_access_url(self, access_url: str) -> tuple[str, str, str]:
        """
        Parse an access URL into its components.

        Args:
            access_url: Access URL (e.g., https://user:pass@bridge.simplefin.org/simplefin)

        Returns:
            tuple: (scheme, rest, auth) components

        Raises:
            SimpleFinInvalidAccountURLError: If URL format is invalid

        """
        try:
            self.log(f"Decoding access URL: {access_url}", level=logging.DEBUG)
            scheme, rest = access_url.split("//", 1)
            auth, rest = rest.split("@", 1)
        except ValueError as err:
            raise SimpleFinInvalidAccountURLError from err

        return scheme, rest, auth

    async def claim_setup_token(
        self,
        setup_token: str,
        *,
        verify_ssl: bool = True,
        proxy: str | None = None,
    ) -> str:
        """
        Claim a setup token and return an access URL.

        This performs the full claim flow:
        1. Decode setup token (base64) → claim URL
        2. POST to claim URL → access URL

        Args:
            setup_token: Base64 encoded setup token
            verify_ssl: Whether to verify SSL certificates
            proxy: Optional proxy server URL

        Returns:
            str: The access URL (e.g., https://user:pass@bridge.simplefin.org/simplefin)

        Raises:
            SimpleFinInvalidClaimTokenError: If token is not valid base64
            SimpleFinClaimError: If claim fails (403 response)
            ClientConnectorError: For connection errors
            ClientConnectorSSLError: For SSL connection errors

        """
        self.log(
            f"Claiming access URL with setup token: {setup_token}",
            level=logging.DEBUG,
        )

        # Step 1: Decode the setup token to get the claim URL
        claim_url = self.decode_claim_token(setup_token)
        self.log(f"Decoded setup token to claim URL: {claim_url}", level=logging.DEBUG)

        # Step 2: POST to claim URL to get access URL
        auth = BasicAuth(login="", password="")
        connector = TCPConnector(ssl=verify_ssl)

        try:
            async with ClientSession(auth=auth, connector=connector) as session:
                response = await session.post(claim_url, ssl=verify_ssl, proxy=proxy)
                if response.status == HTTP_FORBIDDEN:
                    _raise_claim_error()
                access_url: str = await response.text()
                self.log(f"Received access URL: {access_url}", level=logging.DEBUG)
                return access_url
        except (ClientConnectorError, ClientConnectorSSLError) as err:
            self.log(f"Connection error during claim: {err}", level=logging.ERROR)
            raise
        except Exception as e:
            self.log(f"Error claiming token: {e}", level=logging.ERROR)
            raise

    async def fetch_account_data(
        self,
        access_url: str,
        *,
        verify_ssl: bool = True,
        proxy: str | None = None,
        start_date: int | None = None,
        end_date: int | None = None,
    ) -> FinancialData:
        """
        Fetch financial data using an access URL.

        Args:
            access_url: The access URL (e.g., https://user:pass@bridge.simplefin.org/simplefin)
            verify_ssl: Whether to verify SSL certificates
            proxy: Optional proxy server URL
            start_date: Optional start date timestamp for filtering transactions
            end_date: Optional end date timestamp for filtering transactions

        Returns:
            FinancialData: The financial data retrieved from SimpleFin

        Raises:
            SimpleFinInvalidAccountURLError: If access URL format is invalid
            SimpleFinPaymentRequiredError: If payment is required (402)
            SimpleFinAuthError: If authentication fails (403)
            ClientConnectorError: For connection errors
            ClientConnectorSSLError: For SSL connection errors

        """
        self.log(
            f"Fetching account data with access URL: {access_url}",
            level=logging.DEBUG,
        )

        # Parse the access URL
        _scheme, _rest, auth = self.decode_access_url(access_url)
        ssl_context = verify_ssl
        connector = TCPConnector(ssl=ssl_context)

        try:
            auth = BasicAuth(login="", password="")
            access_url = access_url + "/accounts?pending=1"
            access_url = (
                f"{access_url}&start-date={start_date}"
                if start_date
                else f"{access_url}&start-date=978360153"
                # Monday, January 1, 2001 2:42:33 PM
            )
            if end_date:
                access_url = f"{access_url}&end-date={end_date}"
            async with ClientSession(auth=auth, connector=connector) as session:
                response = await session.get(access_url, ssl=verify_ssl, proxy=proxy)
                if response.status == HTTP_PAYMENT_REQUIRED:
                    _raise_payment_required_error()
                if response.status == HTTP_FORBIDDEN:
                    _raise_auth_error()
                data = await response.json()
                self.log(f"Data received from SimpleFin: {data}", level=logging.DEBUG)
            financial_data: FinancialData = FinancialData(**data)  # type: ignore[attr-defined]
            self.log(f"Parsed FinancialData: {financial_data}", level=logging.DEBUG)
            self.log(
                f"Data fetch for access URL {access_url} completed "
                f"for start date: {start_date} | end date: {end_date} completed.",
                level=logging.INFO,
            )
        except (ClientConnectorError, ClientConnectorSSLError) as err:
            self.log(f"Connection error during claim: {err}", level=logging.ERROR)
            raise
        except Exception as e:
            self.log(f"Error fetching data: {e}", level=logging.ERROR)
            raise
        else:
            return financial_data

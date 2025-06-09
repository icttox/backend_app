import requests
import json
import logging
import unicodedata
from django.conf import settings
from decouple import config

logger = logging.getLogger(__name__)

class OdooAuthError(Exception):
    """Custom exception for Odoo authentication errors."""
    pass

class OdooApiError(Exception):
    """Custom exception for general Odoo API errors."""
    pass

# Configuration for specific user credentials.
# Maps Django user email to a tuple: (Odoo Login Email, Env Var for Password, Env Var for API Key)
USER_CREDENTIAL_CONFIG_MAP = {
    "katia.reyes@gebesa.com": (
        "katia.reyes@gebesa.com",
        "ODOO_PASSWORD_KATIA",
        "ODOO_API_KEY_KATIA"
    ),
    "antonio.ramirez@gebesa.com": (
        "antonio.ramirez@gebesa.com",
        "ODOO_PASSWORD_ANTONIO",
        "ODOO_API_KEY_ANTONIO"
    ),
    "diana.delbosque@gebesa.com": (
        "diana.delbosque@gebesa.com",
        "ODOO_PASSWORD_DIANA",
        "ODOO_API_KEY_DIANA"
    ),
    "eduardo.salazar@gebesa.com": (
        "eduardo.salazar@gebesa.com",
        "ODOO_PASSWORD_EDUARDO",
        "ODOO_API_KEY_EDUARDO"
    ),
    "miguel.valenzuela@gebesa.com": (
        "miguel.valenzuela@gebesa.com",
        "ODOO_PASSWORD_MIGUEL",
        "ODOO_API_KEY_MIGUEL"
    ),
}

def normalize_string(s):
    if not s:
        return ''
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

class OdooService:
    """
    Servicio para interactuar con la API de Odoo
    """

    @staticmethod
    def create_purchase_order(data, user=None, unit_name=None):
        """
        Crea una orden de compra en Odoo.

        Args:
            data (dict): Datos para crear la orden de compra.
            user (User, optional): Usuario autenticado para determinar credenciales de API.
            unit_name (str, optional): Nombre de la unidad para fallback de credenciales.

        Returns:
            dict: Respuesta de la API de Odoo.

        Raises:
            OdooAuthError: If Odoo authentication fails.
            OdooApiError: For other Odoo API or communication errors.
        """
        try:
            odoo_endpoint = settings.ODOO_ENDPOINT
            if 'model=' not in odoo_endpoint:
                odoo_endpoint = f"{odoo_endpoint}?model=purchase.order"
            elif 'model=sale.order' in odoo_endpoint:
                odoo_endpoint = odoo_endpoint.replace('model=sale.order', 'model=purchase.order')
            logger.info(f"Usando endpoint de Odoo: {odoo_endpoint}")

            login_email_header = None
            password_header = None
            api_key_header = None

            # 1. Try specific user credentials based on Django user's email
            if user and hasattr(user, 'email') and user.email:
                django_user_email = user.email.lower()
                if django_user_email in USER_CREDENTIAL_CONFIG_MAP:
                    creds_config = USER_CREDENTIAL_CONFIG_MAP[django_user_email]
                    try:
                        login_email_header = creds_config[0]
                        password_header = config(creds_config[1])
                        api_key_header = config(creds_config[2])
                        logger.info(f"Using specific Odoo credentials for Django user: {django_user_email}")
                        # If specific credentials are fully loaded, the 'if not all(...)' block for fallback will be skipped.
                    except config.UndefinedValueError as e: # Catch if a specific env var is missing
                        err_msg = f"Missing Odoo credential environment variable for specific user {django_user_email}: {str(e)}. Please check server configuration."
                        logger.critical(err_msg)
                        raise OdooAuthError(err_msg) # Stop: specific buyer config error, do not fall back.
            
            # 2. Fallback to unit-based or default credentials if specific user credentials were not applicable
            # This block is entered if:
            #   - The user.email was not in USER_CREDENTIAL_CONFIG_MAP.
            #   - The user object was None or had no email attribute.
            # It is NOT entered if a specific buyer was matched but their env vars were missing (due to OdooAuthError above).
            #
            # If specific buyer credentials were not applicable (e.g., user.email not in map, or no user object),
            # then login_email_header, password_header, api_key_header will still be None.
            # In this case, it's an unauthorized attempt.
            if not all([login_email_header, password_header, api_key_header]):
                unauthorized_msg = "Odoo API access denied. User not configured for Odoo purchase order creation or missing credentials."
                if user and hasattr(user, 'email') and user.email:
                    unauthorized_msg = f"Odoo API access denied for user {user.email}. Not configured in USER_CREDENTIAL_CONFIG_MAP or missing credentials."
                elif user:
                     unauthorized_msg = f"Odoo API access denied for authenticated user (no email). Not configured for Odoo purchase order creation."
                else:
                    unauthorized_msg = "Odoo API access denied. Unauthenticated or user not configured for Odoo purchase order creation."
                
                logger.warning(unauthorized_msg)
                raise OdooAuthError(unauthorized_msg)

            # At this point, login_email_header, password_header, and api_key_header must be set
            # from a successfully matched and configured specific buyer.
            headers = {
                'Content-Type': 'application/json',
                'login': login_email_header,
                'password': password_header,
                'Api-Key': api_key_header
            }
            logger.info(f"Headers prepared for Odoo. Login: {login_email_header}")
            logger.info(f"Payload to be sent to Odoo: {json.dumps(data, indent=2)}") # Added payload logging

            response = requests.post(odoo_endpoint, json=data, headers=headers)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            
            odoo_response_data = response.json()

            # Check for application-level errors in Odoo's response string
            if 'result' in odoo_response_data and isinstance(odoo_response_data['result'], str):
                try:
                    inner_result_str = odoo_response_data['result']
                    inner_result = json.loads(inner_result_str) # Parse the JSON string
                    if isinstance(inner_result, dict):
                        if inner_result.get('status') == 'Error' or 'error' in inner_result:
                            error_message = inner_result.get('error', 'Unknown Odoo application error')
                            error_code = inner_result.get('error_code')
                            log_msg = f"Odoo application error: {error_message} (Code: {error_code})"
                            logger.error(log_msg)
                            if error_code == "102" or "Wrong login credentials" in error_message or "Access denied" in error_message:
                                raise OdooAuthError(f"Odoo authentication failed: {error_message}")
                            else:
                                raise OdooApiError(f"Odoo API error: {error_message} (Code: {error_code})")
                except json.JSONDecodeError:
                    logger.warning("Odoo 'result' field is a string but not valid JSON. Proceeding with raw response.")
                # OdooAuthError or OdooApiError raised above will be caught by the outer try-except

            return odoo_response_data

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error communicating with Odoo: {e.response.status_code} - {e.response.text[:500]}")
            if e.response.status_code in [401, 403]:
                raise OdooAuthError(f"Odoo HTTP authentication error: {e.response.status_code} - {e.response.text[:200]}") from e
            raise OdooApiError(f"Odoo HTTP error: {e.response.status_code} - {e.response.text[:200]}") from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with Odoo API: {str(e)}")
            raise OdooApiError(f"Communication error with Odoo: {str(e)}") from e
        except json.JSONDecodeError as e: # If response.json() or json.loads() fails
            response_text_snippet = response.text[:500] if 'response' in locals() else "Response object not available"
            logger.error(f"Error decoding JSON from Odoo: {str(e)}. Response text snippet: {response_text_snippet}")
            raise OdooApiError(f"Invalid JSON response from Odoo: {str(e)}") from e
        except OdooAuthError: # Re-raise to be handled by the caller
            raise
        except OdooApiError: # Re-raise to be handled by the caller
            raise
        except Exception as e: # Catch-all for unexpected errors
            logger.error(f"Unexpected error in Odoo service: {str(e)}", exc_info=True)
            raise OdooApiError(f"An unexpected error occurred: {str(e)}") from e

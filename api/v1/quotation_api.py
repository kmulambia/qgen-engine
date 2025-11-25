from uuid import UUID
from datetime import datetime, timezone
from fastapi import Depends, status, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from engine.models.quotation_model import QuotationModel
from engine.schemas.quotation_schemas import (
    QuotationSchema, 
    QuotationCreateSchema, 
    QuotationUpdateSchema,
    QuotationApproveSchema,
    QuotationResendSchema
)
from engine.schemas.quotation_change_history_schemas import (
    QuotationChangeHistorySchema,
    QuotationChangeHistoryListResponse
)
from engine.services.quotation_change_history_service import QuotationChangeHistoryService
from engine.services.quotation_service import QuotationService
from api.v1.base_api import BaseAPI
from engine.schemas.base_schemas import PaginatedResponse
from api.dependencies.authentication import authentication
from api.dependencies.db import get_db
from api.dependencies.error_handler import ErrorHandling
from api.dependencies.logging import logger
from api.dependencies.ratelimiter import rate_limit
from api.dependencies.mailer import send_email_message
from engine.schemas.token_schemas import TokenData
from engine.utils.config_util import load_config
from engine.utils.jwt_util import JWTUtil

config = load_config()
MODE = config.get_variable("MODE", "development")


class QuotationAPI(BaseAPI[QuotationModel, QuotationCreateSchema, QuotationUpdateSchema, QuotationSchema]):
    def __init__(self):
        super().__init__(
            QuotationService(),
            QuotationSchema,
            QuotationCreateSchema,
            QuotationUpdateSchema,
            QuotationModel,
            PaginatedResponse[QuotationSchema]
        )
        
        # Add custom endpoints
        self._setup_custom_routes()
    
    def _setup_custom_routes(self):
        """Setup custom quotation endpoints"""
        
        @self.router.post("/{quotation_id}/approve", response_model=QuotationSchema, status_code=status.HTTP_200_OK)
        @rate_limit()
        async def approve_quotation(
            request: Request,
            quotation_id: UUID,
            data: QuotationApproveSchema = None,
            db_conn: AsyncSession = Depends(get_db),
            token_data: TokenData = Depends(authentication),
        ):
            """Approve quotation (sets status to approved)"""
            try:
                # Approve quotation (updates status, generates token, sets sent_at)
                quotation = await self.service.approve_quotation(
                    db_conn=db_conn,
                    quotation_id=str(quotation_id),
                    token_data=token_data
                )
                
                # # Load relationships
                # await self._load_relationships_safely(db_conn, quotation)
                
                # # Get client email
                # client = quotation.client
                # if not client:
                #     logger.error(f"Client not found for quotation {quotation_id}")
                #     raise ErrorHandling.not_found("Client not found for quotation")
                
                # client_email = self.service._get_client_email(client)
                # if not client_email:
                #     logger.error(f"No email found for client {client.id}")
                #     raise ErrorHandling.bad_request("Client email address is required")
                
                # # Get website URL for quotation link
                # website_url = config.get_variable("WEBSITE_URL", "http://localhost:3000")
                # view_url = f"{website_url}/quotations/{quotation.id}?token={quotation.access_token}"
                
                # # Print link to terminal for testing
                # print("\n" + "="*80)
                # print("QUOTATION VIEW LINK (for testing):")
                # print(view_url)
                # print("="*80 + "\n")
                # logger.info(f"Quotation view link: {view_url}")
                
                # # Prepare email message
                # client_name = client.contact_person_name or client.company_name or "Valued Client"
                # first_name = client.contact_person_name.split()[0] if client.contact_person_name and " " in client.contact_person_name else client_name
                # last_name = client.contact_person_name.split(" ", 1)[1] if client.contact_person_name and " " in client.contact_person_name else ""
                
                # email_message = {
                #     "template": {
                #         "name": "quotation_approval",
                #         "data": {
                #             "user": {
                #                 "email": client_email,
                #                 "first_name": first_name,
                #                 "last_name": last_name
                #             },
                #             "quotation": {
                #                 "quotation_number": quotation.quotation_number or "N/A",
                #                 "title": quotation.title,
                #                 "total": str(quotation.total),
                #                 "currency": quotation.currency,
                #                 "valid_until": quotation.valid_until.strftime("%B %d, %Y") if quotation.valid_until else "",
                #                 "view_url": view_url
                #             },
                #             "subject": f"Quotation {quotation.quotation_number or 'N/A'} - {quotation.title}",
                #             "system_name": config.require_variable("NAME"),
                #             "support_email": config.require_variable("EMAIL")
                #         }
                #     }
                # }
                
                # # Queue email
                # await send_email_message(email_message)
                
                # Return updated quotation
                return QuotationSchema.model_validate(quotation)
                
            except Exception as e:
                error_message = str(e)
                if error_message == "quotation_not_found":
                    logger.error(f"Quotation not found: {quotation_id}, Request: {request.method} {request.url}")
                    raise ErrorHandling.not_found("Quotation not found")
                elif error_message == "invalid_quotation_status":
                    logger.error(f"Invalid quotation status: {quotation_id}, Request: {request.method} {request.url}")
                    raise ErrorHandling.bad_request("Quotation cannot be approved in its current status")
                elif error_message == "client_not_found":
                    logger.error(f"Client not found for quotation: {quotation_id}, Request: {request.method} {request.url}")
                    raise ErrorHandling.not_found("Client not found for quotation")
                elif error_message == "client_email_not_found":
                    logger.error(f"Client email not found: {quotation_id}, Request: {request.method} {request.url}")
                    raise ErrorHandling.bad_request("Client email address is required to send quotation")
                else:
                    error_details = str(e) if MODE == "development" else "An error occurred while approving the quotation."
                    logger.error(f"Error approving quotation: {e}, Request: {request.method} {request.url}")
                    raise ErrorHandling.server_error(error_details)
        
        @self.router.post("/{quotation_id}/resend", response_model=QuotationSchema, status_code=status.HTTP_200_OK)
        @rate_limit()
        async def resend_quotation(
            request: Request,
            quotation_id: UUID,
            data: QuotationResendSchema = None,
            db_conn: AsyncSession = Depends(get_db),
            token_data: TokenData = Depends(authentication),
        ):
            """Resend quotation to client via email"""
            try:
                # Resend quotation (updates sent_at, regenerates token if needed)
                quotation = await self.service.resend_quotation(
                    db_conn=db_conn,
                    quotation_id=str(quotation_id),
                    token_data=token_data
                )
                
                # Load relationships
                await self._load_relationships_safely(db_conn, quotation)
                
                # Get client email
                client = quotation.client
                if not client:
                    logger.error(f"Client not found for quotation {quotation_id}")
                    raise ErrorHandling.not_found("Client not found for quotation")
                
                client_email = self.service._get_client_email(client)
                if not client_email:
                    logger.error(f"No email found for client {client.id}")
                    raise ErrorHandling.bad_request("Client email address is required")
                
                # Get website URL for quotation link
                website_url = config.get_variable("WEBSITE_URL", "http://localhost:3000")
                view_url = f"{website_url}/quotations/{quotation.id}?token={quotation.access_token}"
                
                # Print link to terminal for testing
                print("\n" + "="*80)
                print("QUOTATION VIEW LINK (for testing):")
                print(view_url)
                print("="*80 + "\n")
                logger.info(f"Quotation view link: {view_url}")
                
                # Prepare email message
                client_name = client.contact_person_name or client.company_name or "Valued Client"
                first_name = client.contact_person_name.split()[0] if client.contact_person_name and " " in client.contact_person_name else client_name
                last_name = client.contact_person_name.split(" ", 1)[1] if client.contact_person_name and " " in client.contact_person_name else ""
                
                email_message = {
                    "template": {
                        "name": "quotation_approval",
                        "data": {
                            "user": {
                                "email": client_email,
                                "first_name": first_name,
                                "last_name": last_name
                            },
                            "quotation": {
                                "quotation_number": quotation.quotation_number or "N/A",
                                "title": quotation.title,
                                "total": str(quotation.total),
                                "currency": quotation.currency,
                                "valid_until": quotation.valid_until.strftime("%B %d, %Y") if quotation.valid_until else "",
                                "view_url": view_url
                            },
                            "subject": f"Quotation {quotation.quotation_number or 'N/A'} - {quotation.title}",
                            "system_name": config.require_variable("NAME"),
                            "support_email": config.require_variable("EMAIL")
                        }
                    }
                }
                
                # Queue email
                await send_email_message(email_message)
                
                # Return updated quotation
                return QuotationSchema.model_validate(quotation)
                
            except Exception as e:
                error_message = str(e)
                if error_message == "quotation_not_found":
                    logger.error(f"Quotation not found: {quotation_id}, Request: {request.method} {request.url}")
                    raise ErrorHandling.not_found("Quotation not found")
                elif error_message == "client_not_found":
                    logger.error(f"Client not found for quotation: {quotation_id}, Request: {request.method} {request.url}")
                    raise ErrorHandling.not_found("Client not found for quotation")
                elif error_message == "client_email_not_found":
                    logger.error(f"Client email not found: {quotation_id}, Request: {request.method} {request.url}")
                    raise ErrorHandling.bad_request("Client email address is required to resend quotation")
                else:
                    error_details = str(e) if MODE == "development" else "An error occurred while resending the quotation."
                    logger.error(f"Error resending quotation: {e}, Request: {request.method} {request.url}")
                    raise ErrorHandling.server_error(error_details)
        
        @self.router.get("/public/{token}", response_model=QuotationSchema)
        @rate_limit()
        async def get_quotation_by_token(
            request: Request,
            token: str,
            db_conn: AsyncSession = Depends(get_db),
        ):
            """Get quotation by public access token (no authentication required)"""
            try:
                # Decode and verify token
                try:
                    token_data = JWTUtil.decode_token(token)
                except ValueError as e:
                    logger.error(f"Invalid or expired token: {str(e)}, Request: {request.method} {request.url}")
                    raise ErrorHandling.unauthorized("Invalid or expired access token")
                
                # Validate token type
                if token_data.get("type") != "quotation_access":
                    logger.error(f"Invalid token type: {token_data.get('type')}, Request: {request.method} {request.url}")
                    raise ErrorHandling.unauthorized("Invalid access token")
                
                # Get quotation ID from token
                quotation_id = token_data.get("quotation_id")
                if not quotation_id:
                    logger.error(f"Quotation ID not found in token, Request: {request.method} {request.url}")
                    raise ErrorHandling.unauthorized("Invalid access token")
                
                # Get quotation (convert string ID to UUID)
                quotation = await self.service.get_by_id(db_conn, UUID(quotation_id))
                if not quotation:
                    logger.error(f"Quotation not found: {quotation_id}, Request: {request.method} {request.url}")
                    raise ErrorHandling.not_found("Quotation not found")
                
                # Verify token matches quotation
                if quotation.access_token != token:
                    logger.error(f"Token mismatch for quotation {quotation_id}, Request: {request.method} {request.url}")
                    raise ErrorHandling.unauthorized("Invalid access token")
                
                # Check if token is expired (additional check)
                if quotation.token_expires_at and quotation.token_expires_at < datetime.now(timezone.utc):
                    logger.error(f"Token expired for quotation {quotation_id}, Request: {request.method} {request.url}")
                    raise ErrorHandling.unauthorized("Access token has expired")
                
                # Load relationships
                await self._load_relationships_safely(db_conn, quotation)
                
                # Return quotation (read-only)
                return QuotationSchema.model_validate(quotation)
                
            except HTTPException:
                raise
            except Exception as e:
                error_details = str(e) if MODE == "development" else "An error occurred while retrieving the quotation."
                logger.error(f"Error retrieving quotation by token: {e}, Request: {request.method} {request.url}")
                raise ErrorHandling.server_error(error_details)

        @self.router.get("/{quotation_id}/history", response_model=QuotationChangeHistoryListResponse, status_code=status.HTTP_200_OK)
        @rate_limit()
        async def get_quotation_history(
            request: Request,
            quotation_id: UUID,
            limit: int = 50,
            offset: int = 0,
            db_conn: AsyncSession = Depends(get_db),
            token_data: TokenData = Depends(authentication)
        ):
            """
            Get the change history for a quotation.
            Returns paginated list of all changes with field-level details.
            """
            try:
                # Verify quotation exists
                quotation = await self.service.get_by_id(db_conn, quotation_id)
                if not quotation:
                    logger.error(f"Quotation not found: {quotation_id}, Request: {request.method} {request.url}")
                    raise ErrorHandling.not_found("Quotation not found")

                # Get change history
                change_history_service = QuotationChangeHistoryService()
                history_records = await change_history_service.get_quotation_history(
                    db_conn=db_conn,
                    quotation_id=quotation_id,
                    limit=limit,
                    offset=offset
                )

                # Convert to schemas
                history_items = [QuotationChangeHistorySchema.model_validate(record) for record in history_records]

                # Get total count (simplified - in production, you'd want a count query)
                # For now, if we got less than limit, that's the total
                total = len(history_items) if len(history_items) < limit else limit + 1

                return QuotationChangeHistoryListResponse(
                    items=history_items,
                    total=total,
                    limit=limit,
                    offset=offset
                )

            except HTTPException:
                raise
            except Exception as e:
                error_details = str(e) if MODE == "development" else "An error occurred while retrieving quotation history."
                logger.error(f"Error retrieving quotation history: {e}, Request: {request.method} {request.url}")
                raise ErrorHandling.server_error(error_details)


quotation_api = QuotationAPI()
router = quotation_api.router

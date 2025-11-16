# Amphibia Engine

Amphibia Engine is a core service engine that provides essential functionality for the Umodzi Source platform, including database seeding and email services.

## Services

### 1. Mailer Service

A flexible email service that supports multiple transport backends, with Postmark as the default transport.

#### Features
- Multiple transport support (currently Postmark)
- HTML template support
- Customizable email templates
- Async/await for efficient email sending
- Comprehensive logging

#### Running the Service

The mailer service runs as a consumer that processes email messages from the message queue:

```bash
python -m mailer
```

This will start the mailer service to process email messages from the configured message queue.

#### Configuration
Required environment variables:
- `POSTMARK_API_TOKEN`: API token for Postmark transport
- `EMAIL`: Default sender email (defaults to "engine@umodzisource.com")
- `AMQ_URI`: Message queue connection string
- `AMQ_QUEUE_NAME`: Name of the queue to consume from (default: "engine")
- `AMQ_EMAIL_SERVICE`: Name of the email service queue (default: "email")

### 2. Seeder Service

A database seeding service that initializes the application with required data and permissions.

#### Available Seeders
1. **Super Admin Role Permission Seeder**
   - Sets up initial super admin role and permissions
   - File: `super_admin_role_permission_seeder.py`

2. **Permission Seeder**
   - Seeds application-wide permissions
   - File: `permission_seeder.py`

3. **Workspace Type Seeder**
   - Seeds different types of workspaces
   - File: `workspace_type_seeder.py`

4. **Super User Seeder**
   - Creates a new super user with admin privileges
   - File: `user_seeder.py`
   - Requires SuperAdmin role and All permission to exist
   - Interactive prompt-based user creation
   - Validates email and phone number formats
   - Creates user credentials and workspace relationships

#### Usage

Run seeders using the command-line interface:

```bash
python -m seeder
```

The seeder service provides the following options:
1. **Seed Data Only**: Runs all seeders in sequence (recommended for first-time setup)
2. **Truncate Tables and Reseed**: Clears all data and runs seeders
3. **Rebuild Tables and Seed**: Drops and recreates all tables, then runs seeders
4. **Create Super User**: Creates a new super user with admin privileges
5. **Cancel**: Exits the seeder

#### Creating a Super User

To create a new super user:

1. First ensure the required roles and permissions exist:
   ```bash
   python -m seeder
   # Choose option 1: "Seed Data Only"
   ```

2. Then create the super user:
   ```bash
   python -m seeder
   # Choose option 4: "Create Super User"
   ```

3. Follow the interactive prompts to provide:
   - First name (required)
   - Last name (required)
   - Email (required, must be valid format)
   - Phone number (required, minimum 9 digits)
   - Password (required)
   - Sex (optional)
   - ID number (optional)
   - ID type (optional)
   - Date of birth (optional, YYYY-MM-DD format)

The seeder will validate all inputs and create the user with appropriate credentials and workspace relationships.

#### Dependencies
- Database connection configuration
- Required database tables and schemas
- Appropriate database permissions
- SuperAdmin role and All permission must exist for super user creation

## Development

### Adding New Transports
To add a new email transport:
1. Create a new transport class in `mailer/transports/`
2. Implement the `BaseTransport` interface
3. Add the transport to the `TRANSPORTS` dictionary in `__main__.py`

### Adding New Seeders
To add a new seeder:
1. Create a new seeder file in the `seeder/` directory
2. Implement the seeder logic
3. Add the seeder to the main seeder execution flow in `seeder/__main__.py`

## Error Handling

Both services include comprehensive error handling and logging:
- Failed email sends are logged with detailed error messages
- Seeder failures are logged with specific error contexts
- All operations are wrapped in try-except blocks with appropriate cleanup
- Super user creation includes validation for:
  - Existing users (email/phone)
  - Required roles and permissions
  - Input format validation
  - Database operation success

## Contributing

When contributing to these services:
1. Follow the existing code style and patterns
2. Add appropriate logging for new functionality
3. Update documentation for any new features
4. Include error handling for all new operations
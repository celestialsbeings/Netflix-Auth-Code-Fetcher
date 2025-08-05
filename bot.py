import os 
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, BusinessConnectionHandler, PreCheckoutQueryHandler, MessageHandler, filters, ConversationHandler
from firebase_db import users_db
from mail_access import extract_household_otp, extract_temp_auth_otp, extract_signin_otp
from keep_alive import keep_alive

keep_alive()
load_dotenv()
token = os.getenv('bot_token')

# Conversation states for add_user
USERID, EMAIL, PASSWORD, DURATION = range(4)

# Conversation states for update_user
UPDATE_USERID, UPDATE_FIELD, UPDATE_EMAIL, UPDATE_PASSWORD, UPDATE_DURATION, UPDATE_SUBSCRIBED = range(4, 10)

# Conversation states for remove_user and add_admin
REMOVE_USERID, ADD_ADMIN_USERID = range(10, 12)

# Conversation states for credential and email management
ADD_CREDENTIAL_EMAIL, ADD_CREDENTIAL_PASSWORD, ADD_BULK_CREDENTIALS, REMOVE_CREDENTIAL_EMAIL = range(12, 16)
ADD_USER_EMAIL_USERID, ADD_USER_EMAIL_EMAIL, ADD_USER_EMAIL_DURATION = range(16, 19)
REMOVE_USER_EMAIL_USERID, REMOVE_USER_EMAIL_EMAIL = range(19, 21)
VIEW_USER_INFO_USERID = range(21, 22)
SELECT_EMAIL_FOR_CODE = range(22, 23)

# Helper function to safely edit messages
async def safe_edit_message(query, message, reply_markup=None, parse_mode='HTML'):
    """Safely edit a message, handling 'Message is not modified' errors"""
    try:
        await query.message.edit_text(message, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        if "Message is not modified" in str(e):
            # Message content is identical, no need to edit
            pass
        else:
            # Re-raise other exceptions
            raise e

# Helper function to safely answer callback queries
async def safe_answer_callback(query):
    """Safely answer callback query, handling timeout errors"""
    try:
        await query.answer()
    except Exception as e:
        if "Query is too old" in str(e) or "timeout expired" in str(e):
            # Query is too old, but we can still process the callback
            print(f"Callback query timeout (continuing anyway): {e}")
        else:
            # Re-raise other exceptions
            raise e

# Admin notification function
async def notify_admins_new_user(update, user_db):
    """Notify all admins when a new user joins"""
    try:
        from telegram import Bot
        bot = Bot(token=os.getenv('bot_token'))

        admin_usernames, admin_ids = user_db.get_admin_users()
        user_info = user_db.get_user()

        if user_info:
            # Escape special characters for Markdown
            username = user_info.get('username', 'Unknown')
            userid = user_info.get('userid', 'Unknown')
            joined = str(user_info.get('joined', 'Unknown'))
            email = user_info.get('email', 'Not set')
            password = user_info.get('password', 'Not set')
            subscriber = 'Yes' if user_info.get('subscriber', False) else 'No'
            admin = 'Yes' if user_info.get('admin', False) else 'No'

            message = f"""🆕 <b>NEW USER JOINED</b> 🆕

👤 <b>Username:</b> @{username}
🆔 <b>User ID:</b> <code>{userid}</code>
📅 <b>Joined:</b> {joined}
📧 <b>Email:</b> {email}
🔐 <b>Password:</b> {password}
👥 <b>Subscriber:</b> {subscriber}
👑 <b>Admin:</b> {admin}

<b>Easy Copy Format:</b>
<pre>
User ID: {userid}
Username: @{username}
Email: {email}
Password: {password}
</pre>"""

            for admin_id in admin_ids:
                try:
                    await bot.send_message(chat_id=admin_id, text=message, parse_mode='HTML')
                except Exception as e:
                    print(f"Failed to notify admin {admin_id}: {e}")

    except Exception as e:
        print(f"Error notifying admins: {e}")


async def start(update: Update, context:ContextTypes.DEFAULT_TYPE):
    user = users_db(str(update.message.chat_id))

    user.remove_expired_subscriptions()

    # Check if user already exists before registering
    existing_user = user.get_user()
    is_new_user = existing_user is None

    user.register_user(update.message.from_user.username)

    # Only notify admins about genuinely new users
    if is_new_user:
        await notify_admins_new_user(update, user)
    message = """🎬 *Welcome to Netflix Codes Provider* 📺

I'm your personal Netflix assistant! Ready to help you access:
• Netflix Household Codes 🏠
• Login Authentication Codes 🔐

Let's get you streaming! 🍿"""
    
    keyboard = [
        [InlineKeyboardButton("🚀 Get Started Here", callback_data='get_started')]
    ]
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await safe_answer_callback(query)
    user = users_db(str(query.message.chat_id))
    user_info = user.get_user()    
    if query.data == 'get_started':
        if user_info and user_info.get('admin', False) == True:
            message = """✨ *Choose Your Netflix Journey* ✨

    Select from these options:"""
            
            keyboard = [
                [InlineKeyboardButton("👑 Admin Panel 🛠", callback_data='admin_pannel')],
                [InlineKeyboardButton("🔑 Get Authentication Code 🔐", callback_data='codes')],
                [InlineKeyboardButton("💳 Subscription Information 💳", callback_data='subscription_info')]
            ]
            await query.message.edit_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else:
            message = """✨ *Choose Your Netflix Journey* ✨

    Select from these options:"""
            
            keyboard = [
                [InlineKeyboardButton("🔑 Get Authentication Code 🔐", callback_data='codes')],
                [InlineKeyboardButton("💳 Subscription Information 💳", callback_data='subscription_info')]
            ]
            await query.message.edit_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif query.data == "admin_pannel":
        user = users_db(str(query.message.chat_id))
        user_info = user.get_user() 
        if not user_info or user_info.get('admin', False) != True:
            await query.message.edit_text("❌ You are not an admin. Please contact the bot owner.", parse_mode='HTML')
            return
        message = """👑 *Admin Panel* 👑

Select from these options:"""
        keyboard = [
            [InlineKeyboardButton("➕ Add New User 👤", callback_data='add_subscriber')],
            [InlineKeyboardButton("✏️ Update User Info 📝", callback_data="update_user")],
            [InlineKeyboardButton("👑 Add Admin 👤", callback_data='add_admin')],
            [InlineKeyboardButton("❌ Remove User 👤", callback_data='remove_subscriber')],
            [InlineKeyboardButton("� Manage Credentials 📧", callback_data='manage_credentials')],
            [InlineKeyboardButton("📨 Add User Email 📨", callback_data='add_user_email')],
            [InlineKeyboardButton("🗑️ Remove User Email 🗑️", callback_data='remove_user_email')],
            [InlineKeyboardButton("� View User Info 👤", callback_data='view_user_info')],
            [InlineKeyboardButton("��🔙 Back to Menu", callback_data='get_started')]
        ]
        await query.message.edit_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    elif query.data == 'codes':
        user = users_db(str(query.message.chat_id))
        user.remove_expired_subscriptions()
        user_info = user.get_user()
        user_emails = user.get_user_emails(str(query.message.chat_id))

        if user_emails:  # Check if user has active emails
            message = """🔑 *Netflix Authentication Codes* 🔑

    Choose the type of code you need:
    • Household Code - For managing devices in your Netflix household
    • Temporary Auth Code - For temporary login access"""
            keyboard = [
                [InlineKeyboardButton("🔑 Sign In Code 🔐", callback_data='signin_code')],
                [InlineKeyboardButton("🏠 Get Household Code 🏠", callback_data='household_code')],
                [InlineKeyboardButton("🔐 Get Temporary Authentication Code 🔐", callback_data='temp_auth_code')],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='get_started')]
            ]
            await query.message.edit_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else :
            admin_usernames, admin_id = user.get_admin_users()
            message = """❌ *Subscription Required* ❌

You currently don't have an active subscription.
Would you like to purchase one?"""
            
            keyboard = [
                [InlineKeyboardButton("💳 Purchase Subscription", url=f't.me/{admin_usernames[0]}')],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='get_started')]
            ]
            await query.message.edit_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            
    elif query.data == 'household_code':
        # Show email selection for household code
        user = users_db(str(query.message.chat_id))
        user.remove_expired_subscriptions()
        user_emails = user.get_user_emails(str(query.message.chat_id))

        if not user_emails:
            message = """❌ <b>No Active Emails</b> ❌

You don't have any active email accounts assigned. Please contact an admin to get access."""
            keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='get_started')]]
            await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')
            return

        if len(user_emails) == 1:
            # Only one email, proceed directly
            context.user_data['selected_email'] = user_emails[0]
            message = f"""🏠 <b>Send Netflix Household Code</b> 🏠

Sending code to: <code>{user_emails[0]['email']}</code>"""
            keyboard = [
                [InlineKeyboardButton("📤 Send Code!", callback_data='household_sended')],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')]
            ]
        else:
            # Multiple emails, show selection
            message = """🏠 <b>Select Email for Household Code</b> 🏠

Choose which email account to use:"""
            keyboard = []
            for i, email_data in enumerate(user_emails):
                keyboard.append([InlineKeyboardButton(f"📧 {email_data['email']}", callback_data=f'select_email_household_{i}')])
            keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')])

        await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')
    elif query.data == 'signin_code':
        # Show email selection for signin code
        user = users_db(str(query.message.chat_id))
        user.remove_expired_subscriptions()
        user_emails = user.get_user_emails(str(query.message.chat_id))

        if not user_emails:
            message = """❌ <b>No Active Emails</b> ❌

You don't have any active email accounts assigned. Please contact an admin to get access."""
            keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='get_started')]]
            await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')
            return

        if len(user_emails) == 1:
            # Only one email, proceed directly
            context.user_data['selected_email'] = user_emails[0]
            message = f"""🔑 <b>Send Sign In Code</b> 🔑

Sending code to: <code>{user_emails[0]['email']}</code>"""
            keyboard = [
                [InlineKeyboardButton("📤 Send Code!", callback_data='signin_sended')],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')]
            ]
        else:
            # Multiple emails, show selection
            message = """🔑 <b>Select Email for Sign In Code</b> 🔑

Choose which email account to use:"""
            keyboard = []
            for i, email_data in enumerate(user_emails):
                keyboard.append([InlineKeyboardButton(f"📧 {email_data['email']}", callback_data=f'select_email_signin_{i}')])
            keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')])

        await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')

    elif query.data =="temp_auth_code":
        # Show email selection for temp auth code
        user = users_db(str(query.message.chat_id))
        user.remove_expired_subscriptions()
        user_emails = user.get_user_emails(str(query.message.chat_id))

        if not user_emails:
            message = """❌ <b>No Active Emails</b> ❌

You don't have any active email accounts assigned. Please contact an admin to get access."""
            keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='get_started')]]
            await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')
            return

        if len(user_emails) == 1:
            # Only one email, proceed directly
            context.user_data['selected_email'] = user_emails[0]
            message = f"""🔐 <b>Send Temporary Authentication Code</b> 🔐

Sending code to: <code>{user_emails[0]['email']}</code>"""
            keyboard = [
                [InlineKeyboardButton("📤 Send Code!", callback_data='temp_auth_sended')],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')]
            ]
        else:
            # Multiple emails, show selection
            message = """🔐 <b>Select Email for Temp Auth Code</b> 🔐

Choose which email account to use:"""
            keyboard = []
            for i, email_data in enumerate(user_emails):
                keyboard.append([InlineKeyboardButton(f"📧 {email_data['email']}", callback_data=f'select_email_tempauth_{i}')])
            keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')])

        await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')

    # Handle email selection callbacks
    elif query.data.startswith('select_email_household_'):
        user = users_db(str(query.message.chat_id))
        user_emails = user.get_user_emails(str(query.message.chat_id))
        email_index = int(query.data.split('_')[-1])

        if email_index < len(user_emails):
            context.user_data['selected_email'] = user_emails[email_index]
            message = f"""🏠 <b>Send Netflix Household Code</b> 🏠

Sending code to: <code>{user_emails[email_index]['email']}</code>"""
            keyboard = [
                [InlineKeyboardButton("📤 Send Code!", callback_data='household_sended')],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')]
            ]
            await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')

    elif query.data.startswith('select_email_signin_'):
        user = users_db(str(query.message.chat_id))
        user_emails = user.get_user_emails(str(query.message.chat_id))
        email_index = int(query.data.split('_')[-1])

        if email_index < len(user_emails):
            context.user_data['selected_email'] = user_emails[email_index]
            message = f"""🔑 <b>Send Sign In Code</b> 🔑

Sending code to: <code>{user_emails[email_index]['email']}</code>"""
            keyboard = [
                [InlineKeyboardButton("📤 Send Code!", callback_data='signin_sended')],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')]
            ]
            await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')

    elif query.data.startswith('select_email_tempauth_'):
        user = users_db(str(query.message.chat_id))
        user_emails = user.get_user_emails(str(query.message.chat_id))
        email_index = int(query.data.split('_')[-1])

        if email_index < len(user_emails):
            context.user_data['selected_email'] = user_emails[email_index]
            message = f"""🔐 <b>Send Temporary Authentication Code</b> 🔐

Sending code to: <code>{user_emails[email_index]['email']}</code>"""
            keyboard = [
                [InlineKeyboardButton("📤 Send Code!", callback_data='temp_auth_sended')],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')]
            ]
            await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')

    elif query.data == 'household_sended':
        user = users_db(str(query.message.chat_id))

        # Get selected email from context
        selected_email_data = context.user_data.get('selected_email')
        if not selected_email_data:
            await safe_edit_message(query, "❌ No email selected. Please try again.", None, 'HTML')
            return

        username = selected_email_data['email']
        password = selected_email_data['password']
        try:
            link = extract_household_otp(username, password)
            print(link)
            if link:
                message = """✅ <b>Success!</b> ✅\n\nYour household code is:\n<code>{}</code>""".format(link)
                keyboard = [
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')]
                ]
            else:
                message = """❌ <b>Failed to Get Code</b> ❌\n\nUnable to retrieve household code. Please try again."""
                keyboard = [
                    [InlineKeyboardButton("🔄 Try Again", callback_data='household_code')],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')]
                ]
        except Exception as e:
            print(f"Email connection error: {e}")
            message = """❌ <b>Connection Error</b> ❌\n\nUnable to connect to email server. Please check your email configuration or try again later."""
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data='household_code')],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')]
            ]
            
        await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'Markdown')

    elif query.data == 'temp_auth_sended':
        user = users_db(str(query.message.chat_id))

        # Get selected email from context
        selected_email_data = context.user_data.get('selected_email')
        if not selected_email_data:
            await safe_edit_message(query, "❌ No email selected. Please try again.", None, 'HTML')
            return

        username = selected_email_data['email']
        password = selected_email_data['password']

        try:
            link = extract_temp_auth_otp(username, password)

            if link:
                message = """✅ <b>Success!</b> ✅\n\nYour Temporary Authentication code is:\n<code>{}</code>""".format(link)
                keyboard = [
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')]
                ]
            else:
                message = """❌ <b>Failed to Get Code</b> ❌\n\nUnable to retrieve Temporary Authentication code. Please try again."""
                keyboard = [
                    [InlineKeyboardButton("🔄 Try Again", callback_data='temp_auth_code')],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')]
                ]
        except Exception as e:
            print(f"Email connection error: {e}")
            message = """❌ <b>Connection Error</b> ❌\n\nUnable to connect to email server. Please check your email configuration or try again later."""
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data='temp_auth_code')],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')]
            ]
            
        await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'Markdown')
        
    elif query.data == 'signin_sended':
        user = users_db(str(query.message.chat_id))

        # Get selected email from context
        selected_email_data = context.user_data.get('selected_email')
        if not selected_email_data:
            await safe_edit_message(query, "❌ No email selected. Please try again.", None, 'HTML')
            return

        username = selected_email_data['email']
        password = selected_email_data['password']

        try:
            link = extract_signin_otp(username, password)

            if link:
                message = f"""✅ <b>Success!</b> ✅\n\nYour Sign In code is: <code>{link}</code>"""
                keyboard = [
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')]
                ]
            else:
                message = """❌ <b>Failed to Get Code</b> ❌\n\nUnable to retrieve Sign In code. Please try again."""
                keyboard = [
                    [InlineKeyboardButton("🔄 Try Again", callback_data='signin_code')],
                    [InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')]
                ]
        except Exception as e:
            print(f"Email connection error: {e}")
            message = """❌ <b>Connection Error</b> ❌\n\nUnable to connect to email server. Please check your email configuration or try again later."""
            keyboard = [
                [InlineKeyboardButton("🔄 Try Again", callback_data='signin_code')],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='codes')]
            ]
            
        await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')
                
    elif query.data == 'subscription_info':
        user = users_db(str(query.message.chat_id))
        user_info = user.get_user()
        user_emails = user.get_user_emails(str(query.message.chat_id))

        if user_emails:  # Check if user has active emails
            message = "✅ <b>Subscription Information</b> ✅\n\n"
            message += f"👤 <b>Username:</b> @{user_info.get('username', 'N/A')}\n"
            message += f"🆔 <b>User ID:</b> <code>{user_info.get('userid', 'N/A')}</code>\n"
            message += f"📅 <b>Joined:</b> {user_info.get('joined', 'N/A')}\n\n"

            message += f"📧 <b>Active Email Accounts ({len(user_emails)}):</b>\n"
            for i, email_data in enumerate(user_emails, 1):
                email = email_data.get('email', 'N/A')
                duration = email_data.get('duration')

                message += f"{i}. <code>{email}</code>\n"

                # Handle duration safely
                if duration:
                    try:
                        duration_str = datetime.fromtimestamp(float(duration)).strftime('%Y-%m-%d %H:%M:%S')
                        message += f"   ⏰ <b>Expires:</b> {duration_str}\n"
                    except (ValueError, TypeError):
                        message += "   ⏰ <b>Expires:</b> Invalid date\n"
                else:
                    message += "   ⏰ <b>Expires:</b> Not set\n"
                message += "\n"

            keyboard = [
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='get_started')]
            ]
            await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')
        else:
            admin_usernames, admin_ids = user.get_admin_users()
            message = "❌ <b>No Active Subscription</b> ❌\n\n"
            message += "You currently don't have any active email accounts assigned.\n"
            message += "Contact an admin to get access."

            keyboard = [
                [InlineKeyboardButton("💬 Contact Admin", url=f't.me/{admin_usernames[0]}')],
                [InlineKeyboardButton("🔙 Back to Menu", callback_data='get_started')]
            ]
            await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')

# Conversation handler functions for adding users
async def start_add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the add user conversation - only for admins"""
    query = update.callback_query
    await query.answer()

    message = """👤 <b>Add New Subscriber</b> 👤

Please enter the User ID of the person you want to add to the subscription.

You can find their User ID by asking them to start a conversation with this bot first.

Enter the User ID:"""
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='cancel_add_user')]]
    await query.message.edit_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    return USERID


async def get_userid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the target user ID"""
    userid = update.message.text.strip()

    # Check if user exists in database
    target_user = users_db(userid)
    user_info = target_user.get_user()

    if not user_info:
        await update.message.reply_text(
            "❌ User not found in database. Please make sure the user has started a conversation with this bot first.\n\n"
            "Please enter a valid User ID:",
            parse_mode='HTML'
        )
        return USERID

    # Store the target userid in context
    context.user_data['target_userid'] = userid
    context.user_data['target_username'] = user_info.get('username', 'Unknown')

    message = f"""✅ User found: {user_info.get('username', 'Unknown')}

📧 <b>Enter Email Address</b>

Please enter the email address for the Netflix account:"""
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='cancel_add_user')]]
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the email address"""
    email = update.message.text.strip()

    # Basic email validation
    if '@' not in email or '.' not in email:
        await update.message.reply_text(
            "❌ Please enter a valid email address:\n\n"
            "Example: user@example.com",
            parse_mode='HTML'
        )
        return EMAIL

    context.user_data['email'] = email

    message = """🔐 <b>Enter Password</b>

Please enter the password for the Netflix account:"""

    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='cancel_add_user')]]
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the password"""
    password = update.message.text.strip()

    if len(password) < 6:
        await update.message.reply_text(
            "❌ Password must be at least 6 characters long.\n\n"
            "Please enter a valid password:",
            parse_mode='HTML'
        )
        return PASSWORD

    context.user_data['password'] = password

    message = """⏰ <b>Enter Subscription Duration</b>

Please enter the number of days for the subscription:

Examples:
• 7 (for 7 days)
• 15 (for 15 days)
• 30 (for 30 days)
• 90 (for 90 days)

Enter number of days:"""
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='cancel_add_user')]]
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    return DURATION

async def get_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the subscription duration and complete the process"""
    duration_text = update.message.text.strip()

    # Validate that input is a number
    try:
        duration_days = int(duration_text)
        if duration_days <= 0:
            raise ValueError("Duration must be positive")
        if duration_days > 365:
            raise ValueError("Duration cannot exceed 365 days")
    except ValueError:
        await update.message.reply_text(
            "❌ Please enter a valid number of days (1-365).\n\n"
            "Examples: 7, 15, 30, 90\n\n"
            "Enter number of days:",
            parse_mode='HTML'
        )
        return DURATION

    duration = f"{duration_days} days"

    # Get stored data from context
    target_userid = context.user_data.get('target_userid')
    target_username = context.user_data.get('target_username')
    email = context.user_data.get('email')
    password = context.user_data.get('password')

    # Add user to subscription
    target_user = users_db(target_userid)
    success = target_user.add_user(target_userid, email, password, duration)

    if success:
        message = f"""✅ <b>User Added Successfully!</b> ✅

👤 <b>User:</b> {target_username}
📧 <b>Email:</b> {email}
⏰ <b>Duration:</b> {duration}
🔐 <b>Password:</b> {password}

The user now has access to Netflix codes for the specified duration."""
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='get_started')]]
        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    else:
        await update.message.reply_text("❌ Failed to add user. Reason - User may already have a current subscription.", parse_mode='HTML')

    # Clear context data
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the add user conversation"""
    context.user_data.clear()

    # Handle callback query (button press)
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("❌ User addition cancelled.", parse_mode='HTML')

    
    return ConversationHandler.END


async def update_user(update:Update, context: ContextTypes.DEFAULT_TYPE):
    """Update user information"""
    query = update.callback_query
    await query.answer()
    message = """👤 <b>Update User Information</b> 👤

Please enter the User ID of the subscriber you want to update.

You can find their User ID by asking them to start a conversation with this bot first."""
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Menu", callback_data='cancel_update_user')]
    ]
    await query.message.edit_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    return UPDATE_USERID


async def get_update_userid(update:Update, context:ContextTypes.DEFAULT_TYPE):
    """Get the target user ID"""
    userid = update.message.text.strip()
    user = users_db(userid)
    data = user.get_user()
    if not data:
        await update.message.reply_text("❌ User not found in database. Please make sure the user has started a conversation with this bot first.\n\n"
            "Please enter a valid User ID:",
            parse_mode='HTML'
        )
        return UPDATE_USERID
    context.user_data['target_userid'] = userid
    message = """📝 <b>Update Field Selection</b>

Please select a field to update:

• <code>email</code> - Email address (e.g. user@example.com)
• <code>password</code> - Account password
• <code>duration</code> - Subscription length (e.g. 7 days)
• <code>subscribed</code> - Subscription status (True/False)

Enter the field name:"""
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='cancel_update_user')]]
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    return UPDATE_FIELD


async def get_field(update:Update, context:ContextTypes.DEFAULT_TYPE):
    """Get the field to update"""
    field = update.message.text.strip()
    field_dic = {'email': "Enter the new email address",
                 'password': "Enter the new password",
                 'duration': "Enter the new duration in days (e.g. 7)",
                 'subscribed': "Enter True or False"}
    if field not in field_dic:
        await update.message.reply_text("❌ Please enter a valid field name:\n\n"
            "Options: email, password, duration, subscribed",
            parse_mode='HTML'
        )
        return UPDATE_FIELD
    context.user_data['field'] = field
    
    message = field_dic[field]
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='cancel_update_user')]]
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    
    var_mapping = {"email": UPDATE_EMAIL,
                   "password": UPDATE_PASSWORD,
                   "duration": UPDATE_DURATION,
                   "subscribed": UPDATE_SUBSCRIBED
                   }
    return var_mapping[field]


async def update_field(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update the field"""
    field = context.user_data.get('field')
    value = update.message.text.strip()
    target_userid = context.user_data.get('target_userid')
    target_user = users_db(target_userid)
    
    if field == 'email':
        # Basic email validation
        if '@' not in value or '.' not in value:
            await update.message.reply_text("❌ Please enter a valid email address", parse_mode='HTML')
            return UPDATE_EMAIL
        target_user.update_user(None, value, None, None, None, target_userid)
    elif field == 'password':
        if len(value) < 6:
            await update.message.reply_text("❌ Password must be at least 6 characters long", parse_mode='HTML')
            return UPDATE_PASSWORD
        target_user.update_user(None, None, value, None, None, target_userid)
    elif field == 'duration':
        try:
            duration_days = int(value)
            if duration_days <= 0 or duration_days > 365:
                raise ValueError()
            value = f"{duration_days} days"
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number of days (1-365)", parse_mode='HTML')
            return UPDATE_DURATION
        target_user.update_user(None, None, None, value, None, target_userid)
    elif field == 'subscribed':
        if value == 'True':
            value = True
        elif value == 'False':
            value = False
        else:
            await update.message.reply_text("❌ Please enter a valid value:\n\nOptions: True, False", parse_mode='HTML')
            return UPDATE_SUBSCRIBED
        target_user.update_user(None, None, None, None, value, target_userid)
    
    # Success message
    await update.message.reply_text(f"✅ Successfully updated {field} to: {value}", parse_mode='HTML')
    
    # Clear context and end conversation
    context.user_data.clear()
    return ConversationHandler.END


async def cancel_updation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data.clear()
    await update.callback_query.message.edit_text("❌ User updation cancelled.", parse_mode='HTML')
    return ConversationHandler.END


# Remove User functionality
async def start_remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the remove user conversation - only for admins"""
    query = update.callback_query
    await query.answer()
    user = users_db(str(query.message.chat_id))
    admin_username, admin_ids = user.get_admin_users()

    if str(query.message.chat_id) in admin_ids:
        message = """❌ <b>Remove User</b> ❌

Please enter the User ID of the person you want to remove from the system.

⚠️ <b>Warning:</b> This will permanently delete the user and all their data.

Enter the User ID:"""
        await query.message.edit_text(message, parse_mode='HTML')
        return REMOVE_USERID
    else:
        await query.message.edit_text("❌ You don't have permission to remove users.", parse_mode='HTML')
        return ConversationHandler.END

async def get_remove_userid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the target user ID for removal"""
    userid = update.message.text.strip()

    # Check if user exists in database
    target_user = users_db(userid)
    user_info = target_user.get_user()

    if not user_info:
        await update.message.reply_text(
            "❌ User not found in database. Please make sure you entered the correct User ID.\n\n"
            "Please enter a valid User ID:",
            parse_mode='HTML'
        )
        return REMOVE_USERID

    # Check if trying to remove an admin
    if user_info.get('admin', False):
        await update.message.reply_text(
            "❌ Cannot remove admin users. Please remove admin privileges first.\n\n"
            "Please enter a different User ID:",
            parse_mode='HTML'
        )
        return REMOVE_USERID

    # Confirm removal
    username = user_info.get('username', 'Unknown')
    message = f"""⚠️ <b>Confirm User Removal</b> ⚠️

<b>User:</b> {username}
<b>User ID:</b> {userid}
<b>Subscriber:</b> {'Yes' if user_info.get('subscriber', False) else 'No'}

Are you sure you want to permanently delete this user?"""

    keyboard = [
        [InlineKeyboardButton("✅ Yes, Remove User", callback_data=f'confirm_remove_{userid}')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel_remove_user')]
    ]

    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    return ConversationHandler.END

async def confirm_remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the confirmation of user removal"""
    query = update.callback_query
    await query.answer()

    if query.data.startswith('confirm_remove_'):
        userid = query.data.replace('confirm_remove_', '')
        target_user = users_db(userid)

        try:
            # Get user info before deletion for confirmation message
            user_info = target_user.get_user()
            username = user_info.get('username', 'Unknown') if user_info else 'Unknown'

            # Delete the user
            target_user.delete_user()

            message = f"""✅ <b>User Removed Successfully!</b> ✅

<b>Removed User:</b> {username}
<b>User ID:</b> {userid}

The user has been permanently deleted from the system."""

        except Exception as e:
            print(f"Error removing user: {e}")
            message = "❌ Failed to remove user. Please try again."

        await query.message.edit_text(message, parse_mode='HTML')

    elif query.data == 'cancel_remove_user':
        await query.message.edit_text("❌ User removal cancelled.", parse_mode='HTML')

    return ConversationHandler.END

async def cancel_remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the remove user conversation"""
    context.user_data.clear()
    await update.message.reply_text("❌ User removal cancelled.", parse_mode='HTML')
    return ConversationHandler.END


# Add Admin functionality
async def start_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the add admin conversation - only for admins"""
    query = update.callback_query
    await query.answer()
    user = users_db(str(query.message.chat_id))
    admin_username, admin_ids = user.get_admin_users()

    if str(query.message.chat_id) in admin_ids:
        message = """👑 <b>Add Admin User</b> 👑

Please enter the User ID of the person you want to promote to admin.

⚠️ <b>Note:</b> Admin users will have full access to manage the bot.

Enter the User ID:"""
        await query.message.edit_text(message, parse_mode='HTML')
        return ADD_ADMIN_USERID
    else:
        await query.message.edit_text("❌ You don't have permission to add admin users.", parse_mode='HTML')
        return ConversationHandler.END

async def get_add_admin_userid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the target user ID for admin promotion"""
    userid = update.message.text.strip()

    # Check if user exists in database
    target_user = users_db(userid)
    user_info = target_user.get_user()

    if not user_info:
        await update.message.reply_text(
            "❌ User not found in database. Please make sure the user has started a conversation with this bot first.\n\n"
            "Please enter a valid User ID:",
            parse_mode='HTML'
        )
        return ADD_ADMIN_USERID

    # Check if user is already an admin
    if user_info.get('admin', False):
        await update.message.reply_text(
            "❌ This user is already an admin.\n\n"
            "Please enter a different User ID:",
            parse_mode='HTML'
        )
        return ADD_ADMIN_USERID

    # Confirm admin promotion
    username = user_info.get('username', 'Unknown')
    message = f"""👑 <b>Confirm Admin Promotion</b> 👑

<b>User:</b> {username}
<b>User ID:</b> {userid}
<b>Current Status:</b> {'Subscriber' if user_info.get('subscriber', False) else 'Regular User'}

Are you sure you want to promote this user to admin?"""

    keyboard = [
        [InlineKeyboardButton("✅ Yes, Make Admin", callback_data=f'confirm_admin_{userid}')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel_add_admin')]
    ]

    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    return ConversationHandler.END

async def confirm_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the confirmation of admin promotion"""
    query = update.callback_query
    await query.answer()

    if query.data.startswith('confirm_admin_'):
        userid = query.data.replace('confirm_admin_', '')
        target_user = users_db(userid)

        try:
            # Get user info before promotion for confirmation message
            user_info = target_user.get_user()
            username = user_info.get('username', 'Unknown') if user_info else 'Unknown'

            # Promote to admin
            target_user.add_admin()

            message = f"""✅ <b>Admin Added Successfully!</b> ✅

<b>New Admin:</b> {username}
<b>User ID:</b> {userid}

The user now has admin privileges and can manage the bot."""

        except Exception as e:
            print(f"Error adding admin: {e}")
            message = "❌ Failed to add admin. Please try again."

        await query.message.edit_text(message, parse_mode='HTML')

    elif query.data == 'cancel_add_admin':
        await query.message.edit_text("❌ Admin promotion cancelled.", parse_mode='HTML')

    return ConversationHandler.END

async def cancel_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the add admin conversation"""
    context.user_data.clear()
    await update.message.reply_text("❌ Admin promotion cancelled.", parse_mode='HTML')
    return ConversationHandler.END


# Credential Management Handlers
async def manage_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show credential management options"""
    query = update.callback_query
    await query.answer()

    user = users_db(str(query.message.chat_id))
    admin_usernames, admin_ids = user.get_admin_users()

    if str(query.message.chat_id) not in admin_ids:
        await query.message.edit_text("❌ You don't have permission to manage credentials.", parse_mode='HTML')
        return

    message = """📧 <b>Credential Management</b> 📧

Manage email/password credentials for the system:"""

    keyboard = [
        [InlineKeyboardButton("➕ Add Single Credential", callback_data='add_credential')],
        [InlineKeyboardButton("📦 Add Multiple Credentials", callback_data='add_bulk_credentials')],
        [InlineKeyboardButton("📋 View All Credentials", callback_data='view_credentials')],
        [InlineKeyboardButton("🗑️ Remove Credential", callback_data='remove_credential')],
        [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data='admin_pannel')]
    ]

    await query.message.edit_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

async def view_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View all available credentials"""
    query = update.callback_query
    await safe_answer_callback(query)

    user = users_db(str(query.message.chat_id))
    credentials = user.get_all_credentials()

    if not credentials:
        message = "📧 <b>No Credentials Found</b> 📧\n\nNo email credentials are currently stored in the system."
    else:
        message = "📧 <b>Available Credentials</b> 📧\n\n"
        for i, cred in enumerate(credentials, 1):
            message += f"{i}. <b>Email:</b> {cred['email']}\n"
            message += f"   <b>Password:</b> <code>{cred['password']}</code>\n\n"

    keyboard = [
        [InlineKeyboardButton("🔙 Back to Credentials", callback_data='manage_credentials')]
    ]

    await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')

# Remove Credential Handler
async def start_remove_credential(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the remove credential conversation"""
    query = update.callback_query
    await safe_answer_callback(query)

    user = users_db(str(query.message.chat_id))
    admin_usernames, admin_ids = user.get_admin_users()

    if str(query.message.chat_id) not in admin_ids:
        await safe_edit_message(query, "❌ You don't have permission to remove credentials.", None, 'HTML')
        return ConversationHandler.END

    # Get all credentials
    credentials = user.get_all_credentials()

    if not credentials:
        await safe_edit_message(query, "📧 <b>No Credentials Found</b> 📧\n\nNo email credentials are stored in the system.", None, 'HTML')
        return ConversationHandler.END

    message = "🗑️ <b>Remove Credential</b> 🗑️\n\n"
    message += "<b>Available Credentials:</b>\n"
    for i, cred in enumerate(credentials, 1):
        message += f"{i}. <code>{cred['email']}</code>\n"

    message += "\n<b>Please enter the email address to remove:</b>"

    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data='cancel_remove_credential')]]
    await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')
    return REMOVE_CREDENTIAL_EMAIL

async def get_remove_credential_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the email to remove from credentials"""
    email = update.message.text.strip()

    # Check if credential exists
    user = users_db(str(update.message.chat_id))
    credential = user.get_credential(email)
    if not credential:
        await update.message.reply_text(
            f"❌ <b>Email Not Found</b>\n\nThe email <code>{email}</code> is not in the credentials system.",
            parse_mode='HTML'
        )
        return REMOVE_CREDENTIAL_EMAIL

    # Remove credential
    success = user.remove_credential(email)

    if success:
        await update.message.reply_text(
            f"✅ <b>Credential Removed Successfully!</b>\n\n"
            f"📧 <b>Removed:</b> <code>{email}</code>\n\n"
            f"The credential has been deleted from the system.",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            f"❌ <b>Failed to Remove Credential</b>\n\nPlease try again later.",
            parse_mode='HTML'
        )

    # Clear context
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_remove_credential(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the remove credential conversation"""
    context.user_data.clear()

    if update.callback_query:
        await safe_answer_callback(update.callback_query)
        await safe_edit_message(update.callback_query, "❌ Remove credential cancelled.", None, 'HTML')
    else:
        await update.message.reply_text("❌ Remove credential cancelled.", parse_mode='HTML')

    return ConversationHandler.END

# View User Info Handlers
async def start_view_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the view user info conversation"""
    query = update.callback_query
    await safe_answer_callback(query)

    user = users_db(str(query.message.chat_id))
    admin_usernames, admin_ids = user.get_admin_users()

    if str(query.message.chat_id) not in admin_ids:
        await safe_edit_message(query, "❌ You don't have permission to view user information.", None, 'HTML')
        return ConversationHandler.END

    message = """👤 <b>View User Information</b> 👤

Please enter the User ID to view their complete information.

<i>Example: 123456789</i>"""

    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data='cancel_view_user_info')]]
    await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')
    return VIEW_USER_INFO_USERID

async def get_view_user_info_userid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the user ID and display complete user information"""
    userid = update.message.text.strip()

    # Validate user ID
    if not userid.isdigit():
        await update.message.reply_text(
            "❌ <b>Invalid User ID</b>\n\nPlease enter a valid numeric User ID.",
            parse_mode='HTML'
        )
        return VIEW_USER_INFO_USERID

    # Get user information
    user = users_db(userid)
    user_info = user.get_user()
    if not user_info:
        await update.message.reply_text(
            f"❌ <b>User Not Found</b>\n\nUser ID <code>{userid}</code> does not exist in the system.",
            parse_mode='HTML'
        )
        return VIEW_USER_INFO_USERID

    # Get user's emails
    user_emails = user.get_user_emails(userid)

    # Build comprehensive user information message
    message = f"👤 <b>Complete User Information</b> 👤\n\n"

    # Basic Information
    message += f"🆔 <b>User ID:</b> <code>{user_info.get('userid', 'N/A')}</code>\n"
    message += f"👤 <b>Username:</b> @{user_info.get('username', 'N/A')}\n"
    message += f"📅 <b>Joined:</b> {user_info.get('joined', 'N/A')}\n"
    message += f"👑 <b>Admin:</b> {'✅ Yes' if user_info.get('admin', False) else '❌ No'}\n"
    message += f"💳 <b>Subscriber:</b> {'✅ Yes' if user_info.get('subscriber', False) else '❌ No'}\n\n"

    # Email Information
    if user_emails:
        message += f"📧 <b>Email Accounts ({len(user_emails)}):</b>\n"
        for i, email_data in enumerate(user_emails, 1):
            email = email_data.get('email', 'N/A')
            password = email_data.get('password', 'N/A')
            duration = email_data.get('duration')

            message += f"\n<b>{i}. Email Account:</b>\n"
            message += f"   📧 <b>Email:</b> <code>{email}</code>\n"
            message += f"   🔐 <b>Password:</b> <code>{password}</code>\n"

            # Handle duration safely
            if duration:
                try:
                    from datetime import datetime
                    duration_str = datetime.fromtimestamp(float(duration)).strftime('%Y-%m-%d %H:%M:%S')
                    message += f"   ⏰ <b>Expires:</b> {duration_str}\n"
                except (ValueError, TypeError):
                    message += f"   ⏰ <b>Expires:</b> Invalid date\n"
            else:
                message += f"   ⏰ <b>Expires:</b> Not set\n"
    else:
        message += "📧 <b>Email Accounts:</b> None assigned\n"

    # Legacy fields (if they exist)
    if 'email' in user_info:
        message += f"\n📧 <b>Legacy Email:</b> <code>{user_info.get('email', 'N/A')}</code>\n"
    if 'password' in user_info:
        message += f"🔐 <b>Legacy Password:</b> <code>{user_info.get('password', 'N/A')}</code>\n"
    if 'duration' in user_info:
        duration = user_info.get('duration')
        if duration:
            try:
                from datetime import datetime
                duration_str = datetime.fromtimestamp(float(duration)).strftime('%Y-%m-%d %H:%M:%S')
                message += f"⏰ <b>Legacy Duration:</b> {duration_str}\n"
            except (ValueError, TypeError):
                message += f"⏰ <b>Legacy Duration:</b> Invalid date\n"

    await update.message.reply_text(message, parse_mode='HTML')

    # Clear context
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_view_user_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the view user info conversation"""
    context.user_data.clear()

    if update.callback_query:
        await safe_answer_callback(update.callback_query)
        await safe_edit_message(update.callback_query, "❌ View user info cancelled.", None, 'HTML')
    else:
        await update.message.reply_text("❌ View user info cancelled.", parse_mode='HTML')

    return ConversationHandler.END

# Add Credential Conversation Handler
async def start_add_credential(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the add credential conversation"""
    query = update.callback_query
    await safe_answer_callback(query)

    user = users_db(str(query.message.chat_id))
    admin_usernames, admin_ids = user.get_admin_users()

    if str(query.message.chat_id) not in admin_ids:
        await safe_edit_message(query, "❌ You don't have permission to add credentials.", None, 'HTML')
        return ConversationHandler.END

    message = """📧 <b>Add New Credential</b> 📧

Please enter the email address:

<i>Example: netflix@gmail.com</i>"""

    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data='cancel_add_credential')]]
    await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')
    return ADD_CREDENTIAL_EMAIL

async def get_credential_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the email for the credential"""
    email = update.message.text.strip()

    # Validate email format
    if '@' not in email or '.' not in email or email.startswith('@') or email.endswith('@') or len(email) < 5:
        await update.message.reply_text(
            "❌ <b>Invalid Email Format</b>\n\nPlease enter a valid email address.\n\n<i>Example: netflix@gmail.com</i>",
            parse_mode='HTML'
        )
        return ADD_CREDENTIAL_EMAIL

    # Check if email already exists
    user = users_db(str(update.message.chat_id))
    existing_cred = user.get_credential(email)
    if existing_cred:
        await update.message.reply_text(
            f"❌ <b>Email Already Exists</b>\n\nThe email <code>{email}</code> is already in the system.",
            parse_mode='HTML'
        )
        return ADD_CREDENTIAL_EMAIL

    # Store email in context
    context.user_data['credential_email'] = email

    await update.message.reply_text(
        f"✅ <b>Email Saved</b>\n\nEmail: <code>{email}</code>\n\nNow please enter the password:",
        parse_mode='HTML'
    )
    return ADD_CREDENTIAL_PASSWORD

async def get_credential_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the password for the credential"""
    password = update.message.text.strip()
    email = context.user_data.get('credential_email')

    if not email:
        await update.message.reply_text("❌ Error: Email not found. Please start over.", parse_mode='HTML')
        return ConversationHandler.END

    # Add credential to database
    user = users_db(str(update.message.chat_id))
    success = user.add_credential(email, password)

    if success:
        await update.message.reply_text(
            f"✅ <b>Credential Added Successfully!</b>\n\n"
            f"📧 <b>Email:</b> <code>{email}</code>\n"
            f"🔐 <b>Password:</b> <code>{password}</code>\n\n"
            f"This credential is now available for user assignment.",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            "❌ <b>Failed to Add Credential</b>\n\nPlease try again later.",
            parse_mode='HTML'
        )

    # Clear context
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_add_credential(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the add credential conversation"""
    context.user_data.clear()

    if update.callback_query:
        await safe_answer_callback(update.callback_query)
        await safe_edit_message(update.callback_query, "❌ Credential addition cancelled.", None, 'HTML')
    else:
        await update.message.reply_text("❌ Credential addition cancelled.", parse_mode='HTML')

    return ConversationHandler.END

# Bulk Add Credentials Handler
async def start_add_bulk_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the bulk add credentials conversation"""
    query = update.callback_query
    await safe_answer_callback(query)

    user = users_db(str(query.message.chat_id))
    admin_usernames, admin_ids = user.get_admin_users()

    if str(query.message.chat_id) not in admin_ids:
        await safe_edit_message(query, "❌ You don't have permission to add credentials.", None, 'HTML')
        return ConversationHandler.END

    message = """📦 <b>Add Multiple Credentials</b> 📦

Please enter multiple email:password pairs, one per line.

<b>Format:</b>
<code>email1@gmail.com:password1
email2@yahoo.com:password2
email3@outlook.com:password3</code>

<b>Example:</b>
<code>netflix1@gmail.com:mypass123
netflix2@yahoo.com:secret456
netflix3@outlook.com:pass789</code>

<i>You can add as many as you want, just put each on a new line.</i>"""

    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data='cancel_add_bulk_credentials')]]
    await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')
    return ADD_BULK_CREDENTIALS

async def process_bulk_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the bulk credentials input"""
    text = update.message.text.strip()

    if not text:
        await update.message.reply_text(
            "❌ <b>No Input Received</b>\n\nPlease enter email:password pairs.",
            parse_mode='HTML'
        )
        return ADD_BULK_CREDENTIALS

    lines = text.split('\n')
    user = users_db(str(update.message.chat_id))

    successful_adds = []
    failed_adds = []

    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue

        if ':' not in line:
            failed_adds.append(f"Line {line_num}: Missing ':' separator - {line}")
            continue

        parts = line.split(':', 1)  # Split only on first ':'
        if len(parts) != 2:
            failed_adds.append(f"Line {line_num}: Invalid format - {line}")
            continue

        email = parts[0].strip()
        password = parts[1].strip()

        # Validate email format
        if '@' not in email or '.' not in email or email.startswith('@') or email.endswith('@') or len(email) < 5:
            failed_adds.append(f"Line {line_num}: Invalid email format - {email}")
            continue

        if len(password) < 1:
            failed_adds.append(f"Line {line_num}: Empty password - {email}")
            continue

        # Try to add credential
        try:
            success = user.add_credential(email, password)
            if success:
                successful_adds.append(f"✅ {email}")
            else:
                failed_adds.append(f"Line {line_num}: Database error - {email}")
        except Exception as e:
            failed_adds.append(f"Line {line_num}: Error - {email} ({str(e)})")

    # Prepare result message
    message = f"📦 <b>Bulk Credential Addition Results</b> 📦\n\n"

    if successful_adds:
        message += f"<b>✅ Successfully Added ({len(successful_adds)}):</b>\n"
        for success in successful_adds:
            message += f"{success}\n"
        message += "\n"

    if failed_adds:
        message += f"<b>❌ Failed ({len(failed_adds)}):</b>\n"
        for failure in failed_adds:
            message += f"{failure}\n"
        message += "\n"

    if not successful_adds and not failed_adds:
        message += "❌ No valid credentials found in input."
    else:
        message += f"<b>Summary:</b> {len(successful_adds)} added, {len(failed_adds)} failed"

    await update.message.reply_text(message, parse_mode='HTML')

    # Clear context
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_add_bulk_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the bulk add credentials conversation"""
    context.user_data.clear()

    if update.callback_query:
        await safe_answer_callback(update.callback_query)
        await safe_edit_message(update.callback_query, "❌ Bulk credential addition cancelled.", None, 'HTML')
    else:
        await update.message.reply_text("❌ Bulk credential addition cancelled.", parse_mode='HTML')

    return ConversationHandler.END

# Add User Email Handlers
async def start_add_user_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the add user email conversation"""
    query = update.callback_query
    await safe_answer_callback(query)

    user = users_db(str(query.message.chat_id))
    admin_usernames, admin_ids = user.get_admin_users()

    if str(query.message.chat_id) not in admin_ids:
        await safe_edit_message(query, "❌ You don't have permission to add user emails.", None, 'HTML')
        return ConversationHandler.END

    message = """📨 <b>Add Email to User</b> 📨

Please enter the User ID of the person you want to add an email to.

<i>Example: 123456789</i>"""

    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data='cancel_add_user_email')]]
    await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')
    return ADD_USER_EMAIL_USERID

async def get_add_user_email_userid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the user ID for adding email"""
    userid = update.message.text.strip()

    # Validate user ID
    if not userid.isdigit():
        await update.message.reply_text(
            "❌ <b>Invalid User ID</b>\n\nPlease enter a valid numeric User ID.",
            parse_mode='HTML'
        )
        return ADD_USER_EMAIL_USERID

    # Check if user exists
    user = users_db(userid)
    user_info = user.get_user()
    if not user_info:
        await update.message.reply_text(
            f"❌ <b>User Not Found</b>\n\nUser ID <code>{userid}</code> does not exist in the system.",
            parse_mode='HTML'
        )
        return ADD_USER_EMAIL_USERID

    # Store user ID in context
    context.user_data['target_userid'] = userid

    # Show available credentials
    admin_user = users_db(str(update.message.chat_id))
    credentials = admin_user.get_all_credentials()

    if not credentials:
        await update.message.reply_text(
            "❌ <b>No Credentials Available</b>\n\nNo email credentials are stored in the system. Please add some credentials first.",
            parse_mode='HTML'
        )
        return ConversationHandler.END

    message = f"✅ <b>User Found</b>\n\nUser ID: <code>{userid}</code>\nUsername: @{user_info.get('username', 'Unknown')}\n\n"
    message += "<b>Available Emails:</b>\n"
    for i, cred in enumerate(credentials, 1):
        message += f"{i}. <code>{cred['email']}</code>\n"

    message += "\n<b>Please enter the email address to assign:</b>"

    await update.message.reply_text(message, parse_mode='HTML')
    return ADD_USER_EMAIL_EMAIL

async def get_add_user_email_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the email to add to user"""
    email = update.message.text.strip()
    target_userid = context.user_data.get('target_userid')

    if not target_userid:
        await update.message.reply_text("❌ Error: User ID not found. Please start over.", parse_mode='HTML')
        return ConversationHandler.END

    # Check if email exists in credentials
    admin_user = users_db(str(update.message.chat_id))
    credential = admin_user.get_credential(email)
    if not credential:
        await update.message.reply_text(
            f"❌ <b>Email Not Found</b>\n\nThe email <code>{email}</code> is not in the credentials system.",
            parse_mode='HTML'
        )
        return ADD_USER_EMAIL_EMAIL

    # Store email in context
    context.user_data['target_email'] = email

    await update.message.reply_text(
        f"✅ <b>Email Found</b>\n\nEmail: <code>{email}</code>\n\nNow please enter the duration in days:\n\n<i>Example: 30</i>",
        parse_mode='HTML'
    )
    return ADD_USER_EMAIL_DURATION

async def get_add_user_email_duration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the duration and complete the email assignment"""
    duration_text = update.message.text.strip()
    target_userid = context.user_data.get('target_userid')
    target_email = context.user_data.get('target_email')

    if not target_userid or not target_email:
        await update.message.reply_text("❌ Error: Missing information. Please start over.", parse_mode='HTML')
        return ConversationHandler.END

    # Validate duration
    try:
        duration_days = int(duration_text)
        if duration_days <= 0:
            raise ValueError("Duration must be positive")
    except ValueError:
        await update.message.reply_text(
            "❌ <b>Invalid Duration</b>\n\nPlease enter a valid number of days (e.g., 30).",
            parse_mode='HTML'
        )
        return ADD_USER_EMAIL_DURATION

    # Add email to user
    user = users_db(target_userid)
    success, message_text = user.add_user_email(target_userid, target_email, f"{duration_days} days")

    if success:
        await update.message.reply_text(
            f"✅ <b>Email Added Successfully!</b>\n\n"
            f"👤 <b>User ID:</b> <code>{target_userid}</code>\n"
            f"📧 <b>Email:</b> <code>{target_email}</code>\n"
            f"⏰ <b>Duration:</b> {duration_days} days\n\n"
            f"The user now has access to Netflix codes using this email.",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            f"❌ <b>Failed to Add Email</b>\n\n{message_text}",
            parse_mode='HTML'
        )

    # Clear context
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_add_user_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the add user email conversation"""
    context.user_data.clear()

    if update.callback_query:
        await safe_answer_callback(update.callback_query)
        await safe_edit_message(update.callback_query, "❌ Add user email cancelled.", None, 'HTML')
    else:
        await update.message.reply_text("❌ Add user email cancelled.", parse_mode='HTML')

    return ConversationHandler.END

# Remove User Email Handlers
async def start_remove_user_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the remove user email conversation"""
    query = update.callback_query
    await safe_answer_callback(query)

    user = users_db(str(query.message.chat_id))
    admin_usernames, admin_ids = user.get_admin_users()

    if str(query.message.chat_id) not in admin_ids:
        await safe_edit_message(query, "❌ You don't have permission to remove user emails.", None, 'HTML')
        return ConversationHandler.END

    message = """🗑️ <b>Remove Email from User</b> 🗑️

Please enter the User ID of the person you want to remove an email from.

<i>Example: 123456789</i>"""

    keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data='cancel_remove_user_email')]]
    await safe_edit_message(query, message, InlineKeyboardMarkup(keyboard), 'HTML')
    return REMOVE_USER_EMAIL_USERID

async def get_remove_user_email_userid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the user ID for removing email"""
    userid = update.message.text.strip()

    # Validate user ID
    if not userid.isdigit():
        await update.message.reply_text(
            "❌ <b>Invalid User ID</b>\n\nPlease enter a valid numeric User ID.",
            parse_mode='HTML'
        )
        return REMOVE_USER_EMAIL_USERID

    # Check if user exists and get their emails
    user = users_db(userid)
    user_info = user.get_user()
    if not user_info:
        await update.message.reply_text(
            f"❌ <b>User Not Found</b>\n\nUser ID <code>{userid}</code> does not exist in the system.",
            parse_mode='HTML'
        )
        return REMOVE_USER_EMAIL_USERID

    # Get user's emails
    user_emails = user.get_user_emails(userid)
    if not user_emails:
        await update.message.reply_text(
            f"❌ <b>No Emails Found</b>\n\nUser ID <code>{userid}</code> has no emails assigned.",
            parse_mode='HTML'
        )
        return REMOVE_USER_EMAIL_USERID

    # Store user ID in context
    context.user_data['target_userid'] = userid

    message = f"✅ <b>User Found</b>\n\nUser ID: <code>{userid}</code>\nUsername: @{user_info.get('username', 'Unknown')}\n\n"
    message += "<b>User's Emails:</b>\n"
    for i, email_data in enumerate(user_emails, 1):
        message += f"{i}. <code>{email_data['email']}</code>\n"

    message += "\n<b>Please enter the email address to remove:</b>"

    await update.message.reply_text(message, parse_mode='HTML')
    return REMOVE_USER_EMAIL_EMAIL

async def get_remove_user_email_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the email to remove from user"""
    email = update.message.text.strip()
    target_userid = context.user_data.get('target_userid')

    if not target_userid:
        await update.message.reply_text("❌ Error: User ID not found. Please start over.", parse_mode='HTML')
        return ConversationHandler.END

    # Check if user has this email
    user = users_db(target_userid)
    user_emails = user.get_user_emails(target_userid)
    user_email_addresses = [email_data['email'] for email_data in user_emails]

    if email not in user_email_addresses:
        await update.message.reply_text(
            f"❌ <b>Email Not Found</b>\n\nThe user does not have the email <code>{email}</code> assigned.",
            parse_mode='HTML'
        )
        return REMOVE_USER_EMAIL_EMAIL

    # Remove email from user
    success, message_text = user.remove_user_email(target_userid, email)

    if success:
        await update.message.reply_text(
            f"✅ <b>Email Removed Successfully!</b>\n\n"
            f"👤 <b>User ID:</b> <code>{target_userid}</code>\n"
            f"📧 <b>Removed Email:</b> <code>{email}</code>\n\n"
            f"The user no longer has access to this email.",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            f"❌ <b>Failed to Remove Email</b>\n\n{message_text}",
            parse_mode='HTML'
        )

    # Clear context
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_remove_user_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the remove user email conversation"""
    context.user_data.clear()

    if update.callback_query:
        await safe_answer_callback(update.callback_query)
        await safe_edit_message(update.callback_query, "❌ Remove user email cancelled.", None, 'HTML')
    else:
        await update.message.reply_text("❌ Remove user email cancelled.", parse_mode='HTML')

    return ConversationHandler.END


# Simple Add User Email Handler (for /add command)
async def handle_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add userid email duration command"""
    try:
        # Parse command: /add userid email duration
        args = context.args
        if len(args) != 3:
            await update.message.reply_text(
                "❌ <b>Invalid Format</b>\n\n"
                "Usage: <code>/add userid email duration</code>\n\n"
                "Example: <code>/add 123456789 user@gmail.com 30</code>",
                parse_mode='HTML'
            )
            return

        userid, email, duration = args

        # Check if user is admin
        admin_user = users_db(str(update.message.chat_id))
        admin_usernames, admin_ids = admin_user.get_admin_users()

        if str(update.message.chat_id) not in admin_ids:
            await update.message.reply_text("❌ You don't have permission to add users.", parse_mode='HTML')
            return

        # Add email to user
        user = users_db(userid)
        success, message_text = user.add_user_email(userid, email, f"{duration} days")

        if success:
            await update.message.reply_text(
                f"✅ <b>Success!</b>\n\n"
                f"Added email <code>{email}</code> to user <code>{userid}</code> for {duration} days.",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                f"❌ <b>Failed:</b> {message_text}",
                parse_mode='HTML'
            )

    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>Error:</b> {str(e)}",
            parse_mode='HTML'
        )

# Simple Remove User Email Handler (for /remove command)
async def handle_remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /remove userid email command"""
    try:
        # Parse command: /remove userid email
        args = context.args
        if len(args) != 2:
            await update.message.reply_text(
                "❌ <b>Invalid Format</b>\n\n"
                "Usage: <code>/remove userid email</code>\n\n"
                "Example: <code>/remove 123456789 user@gmail.com</code>",
                parse_mode='HTML'
            )
            return

        userid, email = args

        # Check if user is admin
        admin_user = users_db(str(update.message.chat_id))
        admin_usernames, admin_ids = admin_user.get_admin_users()

        if str(update.message.chat_id) not in admin_ids:
            await update.message.reply_text("❌ You don't have permission to remove user emails.", parse_mode='HTML')
            return

        # Remove email from user
        user = users_db(userid)
        success, message_text = user.remove_user_email(userid, email)

        if success:
            await update.message.reply_text(
                f"✅ <b>Success!</b>\n\n"
                f"Removed email <code>{email}</code> from user <code>{userid}</code>.",
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                f"❌ <b>Failed:</b> {message_text}",
                parse_mode='HTML'
            )

    except Exception as e:
        await update.message.reply_text(
            f"❌ <b>Error:</b> {str(e)}",
            parse_mode='HTML'
        )







def main():
    application = Application.builder().token(token).build()

    # Add user conversation handler
    add_user_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_user, pattern='add_subscriber')],
        states={
            USERID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_userid)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
            DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_duration)]
        },
        fallbacks=[CallbackQueryHandler(cancel_add_user, pattern='cancel_add_user')],
        per_chat=True,
        per_user=True
    )
    update_user_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(update_user, pattern='update_user')],
        states={
            UPDATE_USERID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_update_userid)],
            UPDATE_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_field)],
            UPDATE_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_field)],
            UPDATE_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_field)],
            UPDATE_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_field)],
            UPDATE_SUBSCRIBED: [MessageHandler(filters.TEXT & ~filters.COMMAND, update_field)]
        },
        fallbacks=[CallbackQueryHandler(cancel_updation, pattern='cancel_update_user')],
        per_chat=True,
        per_user=True
    )

    # Remove user conversation handler
    remove_user_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_remove_user, pattern='remove_subscriber')],
        states={
            REMOVE_USERID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_remove_userid)]
        },
        fallbacks=[CommandHandler('cancel', cancel_remove_user)],
        per_chat=True,
        per_user=True
    )

    # Add admin conversation handler
    add_admin_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_admin, pattern='add_admin')],
        states={
            ADD_ADMIN_USERID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_add_admin_userid)]
        },
        fallbacks=[CommandHandler('cancel', cancel_add_admin)],
        per_chat=True,
        per_user=True
    )

    # Add credential conversation handler
    add_credential_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_credential, pattern='add_credential')],
        states={
            ADD_CREDENTIAL_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_credential_email)],
            ADD_CREDENTIAL_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_credential_password)]
        },
        fallbacks=[CallbackQueryHandler(cancel_add_credential, pattern='cancel_add_credential')],
        per_chat=True,
        per_user=True
    )

    # Add bulk credentials conversation handler
    add_bulk_credential_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_bulk_credentials, pattern='add_bulk_credentials')],
        states={
            ADD_BULK_CREDENTIALS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_bulk_credentials)]
        },
        fallbacks=[CallbackQueryHandler(cancel_add_bulk_credentials, pattern='cancel_add_bulk_credentials')],
        per_chat=True,
        per_user=True
    )

    # Add user email conversation handler
    add_user_email_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_user_email, pattern='add_user_email')],
        states={
            ADD_USER_EMAIL_USERID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_add_user_email_userid)],
            ADD_USER_EMAIL_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_add_user_email_email)],
            ADD_USER_EMAIL_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_add_user_email_duration)]
        },
        fallbacks=[CallbackQueryHandler(cancel_add_user_email, pattern='cancel_add_user_email')],
        per_chat=True,
        per_user=True
    )

    # Remove user email conversation handler
    remove_user_email_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_remove_user_email, pattern='remove_user_email')],
        states={
            REMOVE_USER_EMAIL_USERID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_remove_user_email_userid)],
            REMOVE_USER_EMAIL_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_remove_user_email_email)]
        },
        fallbacks=[CallbackQueryHandler(cancel_remove_user_email, pattern='cancel_remove_user_email')],
        per_chat=True,
        per_user=True
    )



    # Remove credential conversation handler
    remove_credential_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_remove_credential, pattern='remove_credential')],
        states={
            REMOVE_CREDENTIAL_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_remove_credential_email)]
        },
        fallbacks=[CallbackQueryHandler(cancel_remove_credential, pattern='cancel_remove_credential')],
        per_chat=True,
        per_user=True
    )

    # View user info conversation handler
    view_user_info_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_view_user_info, pattern='view_user_info')],
        states={
            VIEW_USER_INFO_USERID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_view_user_info_userid)]
        },
        fallbacks=[CallbackQueryHandler(cancel_view_user_info, pattern='cancel_view_user_info')],
        per_chat=True,
        per_user=True
    )

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('add', handle_add_command))
    application.add_handler(CommandHandler('remove', handle_remove_command))
    application.add_handler(add_user_conv_handler)
    application.add_handler(update_user_conv_handler)
    application.add_handler(remove_user_conv_handler)
    application.add_handler(add_admin_conv_handler)
    application.add_handler(add_credential_conv_handler)
    application.add_handler(add_bulk_credential_conv_handler)
    application.add_handler(remove_credential_conv_handler)
    application.add_handler(view_user_info_conv_handler)
    application.add_handler(add_user_email_conv_handler)
    application.add_handler(remove_user_email_conv_handler)

    # Add confirmation handlers for remove user and add admin
    application.add_handler(CallbackQueryHandler(confirm_remove_user, pattern=r'^confirm_remove_'))
    application.add_handler(CallbackQueryHandler(confirm_remove_user, pattern='cancel_remove_user'))
    application.add_handler(CallbackQueryHandler(confirm_add_admin, pattern=r'^confirm_admin_'))
    application.add_handler(CallbackQueryHandler(confirm_add_admin, pattern='cancel_add_admin'))

    # Add credential management handlers
    application.add_handler(CallbackQueryHandler(manage_credentials, pattern='manage_credentials'))
    application.add_handler(CallbackQueryHandler(view_credentials, pattern='view_credentials'))

    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling()

if __name__ == '__main__':
    main()




import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import db
import time
from google.cloud.firestore_v1.base_query import FieldFilter

cred = credentials.Certificate('db.json')

firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://nf-codes-db-default-rtdb.firebaseio.com/'
})

db = firestore.client()

class users_db:
    def __init__(self, userid):
        self.userid = userid

    ##delete user##        
    def delete_user(self):
        doc_ref = db.collection('users').document(self.userid)
        doc_ref.delete()
        
    ##get user info##      
    def get_user(self):
        doc_ref = db.collection('users').document(self.userid)
        doc = doc_ref.get()
        return doc.to_dict()
    
    ##get all user id##    
    def get_all_userid(self):
        doc_ref = db.collection('users')
        docs = doc_ref.stream()
        uids = []
        for doc in docs:
            uids.append(doc.id)
        return uids
    
    def add_admin(self):
        doc_ref = db.collection('users').document(self.userid)
        doc_ref.update({
            'admin': True
        })

## register user ##
    def register_user(self, username):
        if self.get_user():
            return False
        doc_ref = db.collection('users').document(self.userid)
        doc_ref.set({
            'userid': self.userid,
            'username': username,
            'joined': firestore.SERVER_TIMESTAMP,
            'admin': False,
            'subscriber': False
        })
        
    ##add user##
    def add_user(self, target_userid, email, password, duration):
        """Add subscription to an existing user by their userid"""
        doc_ref = db.collection('users').document(target_userid)
        doc = doc_ref.get()
        if doc.exists:
            if doc.to_dict()['subscriber'] == True:
                return False
            # Calculate expiration time based on duration in days
            current_time = time.time()
            # Extract number of days from duration string (e.g., "7 days", "30 days")
            duration_days = int(duration.split()[0])
            duration_seconds = duration_days * 24 * 60 * 60  # Convert days to seconds

            expiration_time = current_time + duration_seconds

            doc_ref.update({
                'email': email,
                'password': password,
                'duration': expiration_time,
                'subscriber': True
            })
            return True
        return False

    ##update user##    
    def update_user(self, username, email, password, duration, subscribed, target_userid):
        doc_ref = db.collection(u'users').document(target_userid)
        if username :
            doc_ref.update({
                'username': username
            })
        if email :
            doc_ref.update({
                'email': email
            })
        if password :
            doc_ref.update({
                'password': password
            })
        if duration:
            current_time = time.time()
            # Extract number of days from duration string (e.g., "7 days", "30 days")
            duration_days = int(duration.split()[0])
            duration_seconds = duration_days * 24 * 60 * 60  # Convert days to seconds
            expiration_time = current_time + duration_seconds
            doc_ref.update({
                'duration': expiration_time
            })
        if subscribed:
            doc_ref.update({
                'subscriber': subscribed
            })


    def get_admin_users(self):
        """Get all users who are admins"""
        users_ref = db.collection('users')
        docs = users_ref.where(filter=FieldFilter('admin', '==', True)).stream()
        admin_users = []
        admin_ids = []        
        for doc in docs:
            user_data = doc.to_dict()
            if user_data and 'username' in user_data:
                admin_users.append(user_data['username'])
                admin_ids.append(str(doc.id))
        return admin_users, admin_ids
    
    def remove_expired_subscriber(self):
        user = self.get_user()
        if user['subscriber'] == True:
            if user['duration'] < time.time():
                doc_ref = db.collection('users').document(self.userid)
                doc_ref.update({
                    'subscriber': False
                })
        else:
            return False
        
    def remove_expired_subscriptions(self):
        """Remove expired subscriptions for all users - updated for new email array structure"""
        users_ref = db.collection('users')
        docs = users_ref.stream()
        current_time = time.time()

        for doc in docs:
            user_data = doc.to_dict()
            if user_data and 'emails' in user_data:
                emails = user_data['emails']
                updated_emails = []

                # Filter out expired emails
                for email_data in emails:
                    if email_data.get('duration', 0) > current_time:
                        updated_emails.append(email_data)

                # Update user document if emails changed
                if len(updated_emails) != len(emails):
                    doc_ref = db.collection('users').document(doc.id)
                    doc_ref.update({
                        'emails': updated_emails,
                        'subscriber': len(updated_emails) > 0  # Set subscriber based on active emails
                    })

    # Credential Management System
    def add_credential(self, email, password):
        """Add email/password credential to the credentials collection"""
        try:
            doc_ref = db.collection('credentials').document(email)
            doc_ref.set({
                'email': email,
                'password': password,
                'created_at': time.time()
            })
            return True
        except Exception as e:
            print(f"Error adding credential: {e}")
            return False

    def get_credential(self, email):
        """Get password for a specific email from credentials collection"""
        try:
            doc_ref = db.collection('credentials').document(email)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting credential: {e}")
            return None

    def get_all_credentials(self):
        """Get all available email credentials"""
        try:
            docs = db.collection('credentials').stream()
            credentials = []
            for doc in docs:
                data = doc.to_dict()
                credentials.append({
                    'email': data.get('email'),
                    'password': data.get('password')
                })
            return credentials
        except Exception as e:
            print(f"Error getting credentials: {e}")
            return []

    def remove_credential(self, email):
        """Remove a credential from the credentials collection"""
        try:
            doc_ref = db.collection('credentials').document(email)
            doc_ref.delete()
            return True
        except Exception as e:
            print(f"Error removing credential: {e}")
            return False

    def add_bulk_credentials(self, credentials_list):
        """Add multiple credentials at once

        Args:
            credentials_list: List of tuples [(email, password), ...]

        Returns:
            tuple: (successful_count, failed_list)
        """
        successful_count = 0
        failed_list = []

        try:
            batch = db.batch()

            for email, password in credentials_list:
                try:
                    doc_ref = db.collection('credentials').document(email)
                    batch.set(doc_ref, {
                        'email': email,
                        'password': password,
                        'created_at': time.time()
                    })
                    successful_count += 1
                except Exception as e:
                    failed_list.append((email, str(e)))

            # Commit the batch
            if successful_count > 0:
                batch.commit()

        except Exception as e:
            print(f"Error in bulk credential addition: {e}")
            # If batch fails, try individual additions
            successful_count = 0
            failed_list = []

            for email, password in credentials_list:
                success = self.add_credential(email, password)
                if success:
                    successful_count += 1
                else:
                    failed_list.append((email, "Individual add failed"))

        return successful_count, failed_list

    # Multi-email User Management
    def add_user_email(self, target_userid, email, duration):
        """Add an email to a user's account"""
        try:
            # Get credential for this email
            credential = self.get_credential(email)
            if not credential:
                return False, "Email not found in credentials"

            # Check if user exists
            user_ref = db.collection('users').document(target_userid)
            user_doc = user_ref.get()

            if not user_doc.exists:
                return False, "User not found"

            # Calculate expiration time
            current_time = time.time()
            duration_days = int(duration.split()[0]) if 'days' in duration else int(duration)
            duration_seconds = duration_days * 24 * 60 * 60
            expiration_time = current_time + duration_seconds

            # Add email to user's emails array
            user_data = user_doc.to_dict()
            emails = user_data.get('emails', [])

            # Check if email already exists for this user
            for existing_email in emails:
                if existing_email.get('email') == email:
                    return False, "Email already assigned to this user"

            # Add new email
            emails.append({
                'email': email,
                'password': credential['password'],
                'duration': expiration_time,
                'added_at': current_time
            })

            # Update user document
            user_ref.update({
                'emails': emails,
                'subscriber': True
            })

            return True, "Email added successfully"

        except Exception as e:
            print(f"Error adding user email: {e}")
            return False, f"Error: {str(e)}"

    def remove_user_email(self, target_userid, email):
        """Remove a specific email from a user's account"""
        try:
            user_ref = db.collection('users').document(target_userid)
            user_doc = user_ref.get()

            if not user_doc.exists:
                return False, "User not found"

            user_data = user_doc.to_dict()
            emails = user_data.get('emails', [])

            # Remove the specified email
            updated_emails = [e for e in emails if e.get('email') != email]

            if len(updated_emails) == len(emails):
                return False, "Email not found for this user"

            # Update user document
            user_ref.update({
                'emails': updated_emails,
                'subscriber': len(updated_emails) > 0  # Set subscriber to False if no emails left
            })

            return True, "Email removed successfully"

        except Exception as e:
            print(f"Error removing user email: {e}")
            return False, f"Error: {str(e)}"

    def get_user_emails(self, target_userid):
        """Get all emails for a specific user"""
        try:
            user_ref = db.collection('users').document(target_userid)
            user_doc = user_ref.get()

            if not user_doc.exists:
                return []

            user_data = user_doc.to_dict()
            emails = user_data.get('emails', [])

            # Filter out expired emails
            current_time = time.time()
            active_emails = []
            for email_data in emails:
                if email_data.get('duration', 0) > current_time:
                    active_emails.append(email_data)

            return active_emails

        except Exception as e:
            print(f"Error getting user emails: {e}")
            return []


import logging
import time
import requests
import imaplib
import email
from email.header import decode_header
import re
from typing import Optional, Dict

# Import helpers from the installed package
from iitkgp_erp_login.erp import (
    get_sessiontoken, 
    get_secret_question, 
    get_login_details, 
    request_otp as lib_request_otp, 
    signin, 
    session_alive, 
    HOMEPAGE_URL, 
    LoginDetails,
    ErpLoginError,
    ErpCreds
)
from iitkgp_erp_login.logger import logger

class ERPClient:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'timeout': '20',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.94 Chrome/37.0.2062.94 Safari/537.36'
        }
        
    def is_session_alive(self) -> bool:
        try:
            return session_alive(self.session)
        except Exception:
            return False

    def _connect_imap(self, email_addr, app_password):
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_addr, app_password)
        mail.select("inbox")
        return mail

    def _get_latest_id_imap(self, email_addr, app_password) -> int:
        try:
            mail = self._connect_imap(email_addr, app_password)
            subject_query = '(SUBJECT "OTP for Sign In in ERP Portal of IIT Kharagpur")'
            status, messages = mail.search(None, subject_query)
            mail.close()
            mail.logout()
            
            if messages and messages[0]:
                ids = messages[0].split()
                if ids:
                    return int(ids[-1])
            return 0
        except Exception as e:
            logger.error(f"IMAP Init Error: {e}")
            return 0

    def _delete_email(self, email_addr, app_password, msg_id: int):
        try:
            logger.info(f"Deleting OTP email (ID: {msg_id})...")
            mail = self._connect_imap(email_addr, app_password)
            mail.store(str(msg_id), "+FLAGS", "\\Deleted")
            mail.expunge()
            mail.close()
            mail.logout()
            logger.info("OTP email deleted successfully.")
        except Exception as e:
            logger.error(f"Failed to delete email: {e}")

    def _wait_for_new_otp(self, email_addr, app_password, previous_id: int) -> tuple[Optional[str], Optional[int]]:
        """Fetch NEW OTP using IMAP (checking for ID > previous_id)."""
        logger.info(f"Waiting for OTP email newer than ID {previous_id}...")
        
        start_time = time.time()
        timeout = 60 # 60 seconds
        
        while time.time() - start_time < timeout:
            try:
                mail = self._connect_imap(email_addr, app_password)
                subject_query = '(SUBJECT "OTP for Sign In in ERP Portal of IIT Kharagpur")'
                status, messages = mail.search(None, subject_query)
                
                found_new = False
                otp = None
                latest_id = None
                
                if messages and messages[0]:
                    ids = messages[0].split()
                    if ids:
                        latest_id = int(ids[-1])
                        
                        if latest_id > previous_id:
                            found_new = True
                            # Fetch content
                            status, msg_data = mail.fetch(str(latest_id), "(RFC822)")
                            for response_part in msg_data:
                                if isinstance(response_part, tuple):
                                    msg = email.message_from_bytes(response_part[1])
                                    body = ""
                                    if msg.is_multipart():
                                        for part in msg.walk():
                                            if part.get_content_type() == "text/plain":
                                                body = part.get_payload(decode=True).decode()
                                                break
                                    else:
                                        body = msg.get_payload(decode=True).decode()
                                    
                                    logger.info(f"DEBUG - Full Email Body: \n{body}")
                                    parts = [p for p in body.split() if p.isdigit()]
                                    if parts:
                                        otp = parts[-1]
                
                mail.close()
                mail.logout()
                
                if found_new and otp:
                    logger.info(f"DEBUG - Extracted OTP: {otp}")
                    return otp, latest_id
                    
            except Exception as e:
                logger.error(f"IMAP Polling Error: {e}")
            
            time.sleep(4)
            
        return None, None

    def login_with_credentials(self, creds: Dict, status_callback=None) -> bool:
        """
        Custom login flow that avoids blocking input() and supports IMAP OTP.
        creds dict must contain:
        - roll_number
        - erp_password
        - security_answers (dict)
        - google_email (optional, for IMAP)
        - google_app_password (optional, for IMAP)
        """
        roll = creds.get('roll_number')
        password = creds.get('erp_password')
        sec_answers = creds.get('security_answers', {})
        
        if not roll or not password:
            raise ValueError("Missing Roll Number or Password")

        if status_callback: status_callback(f"Initiating login for {roll}...")

        try:
            # 1. Get Session Token
            session_token = get_sessiontoken(self.session, log=True)
            
            # 2. Get Security Question
            question = get_secret_question(self.headers, self.session, roll, log=True)
            answer = sec_answers.get(question)
            
            if not answer:
                raise ValueError(f"No answer stored for security question: {question}")
            
            login_details = get_login_details(roll, password, answer, session_token)
            
            # PRE-OTP: Check latest email ID
            prev_email_id = 0
            if creds.get('google_email') and creds.get('google_app_password'):
                if status_callback: status_callback("Checking latest email ID...")
                prev_email_id = self._get_latest_id_imap(creds['google_email'], creds['google_app_password'])
            
            # 3. Request OTP
            if status_callback: status_callback("Requesting OTP...")
            lib_request_otp(self.headers, self.session, login_details, log=True)
            
            # 4. Fetch OTP
            otp = None
            msg_id = None
            if creds.get('google_email') and creds.get('google_app_password'):
                 if status_callback: status_callback("Listening for new OTP email...")
                 otp, msg_id = self._wait_for_new_otp(creds['google_email'], creds['google_app_password'], prev_email_id)
            
            if not otp:
                 raise ValueError("Could not fetch OTP via IMAP. Email/AppPassword missing or retrieval failed.")
                 
            login_details['email_otp'] = otp
            
            # 5. Sign In
            if status_callback: status_callback("Submitting valid OTP...")
            sso_token = signin(self.headers, self.session, login_details, log=True)
            
            # 6. Verify
            if self.is_session_alive():
                 if status_callback: status_callback("Login Successful!")
                 
                 # Delete OTP Email
                 if msg_id and creds.get('google_email') and creds.get('google_app_password'):
                     self._delete_email(creds['google_email'], creds['google_app_password'], msg_id)
                     
                 return True
            else:
                 if status_callback: status_callback("Login flow finished but session not alive.")
                 return False

        except Exception as e:
            if status_callback: status_callback(f"Login failed: {str(e)}")
            logger.error(f"Login Exception: {e}")
            raise e

    def fetch_security_questions(self, roll_number: str) -> list[str]:
        """
        Attempts to fetch all security questions for a roll number.
        Since the server returns one at a time, we try multiple times with fresh sessions.
        """
        questions = set()
        attempts = 0
        max_attempts = 15
        
        # We try until we have 3 or run out of attempts
        while len(questions) < 3 and attempts < max_attempts:
            try:
                # Use a fresh session to prompt rotation (if server supports it)
                temp_session = requests.Session()
                q = get_secret_question(self.headers, temp_session, roll_number)
                if q and q != "FALSE":
                    questions.add(q)
            except Exception:
                pass 
            attempts += 1
            time.sleep(0.2)
            
        return list(questions)

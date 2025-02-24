from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import requests  # To make API calls
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] ='./actions/google_vision.json'
from google.cloud import vision
import  re
from datetime import datetime, timedelta
import jwt


class ActionsRefundSubscription(Action):
    def name(self) -> Text:
        return "action_refund_subscription"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]] :
        user_email = tracker.get_slot("email")
        user_contact_number = tracker.get_slot("number")
        user_uuid = tracker.get_slot("uuid")

        print("refunddd")

        api_url = f"https://level-core-backend.api.level.game/v1/refundSubscription"
        payload = {
            "email": user_email,
            "contact_number": user_contact_number,
            "uuid": user_uuid,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, "LVB97M-lKA1-bGcwNLRYXySuThn3pTYKZIN9CRYsBvY", algorithm="HS256")
        print(token)

        headers = {
            "Authorization": f"auth {token}",
            "Content-Type": "application/json"
        }


class ActionCancelSubscription(Action):
    def name(self) -> Text:
        return "action_cancel_subscription"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]] :
        user_email = tracker.get_slot("email")
        user_contact_number = tracker.get_slot("number")
        user_uuid = tracker.get_slot("uuid")

        print("cancellll")

        api_url = f"https://level-core-backend.api.level.game/v1/cancelSubscription"
        payload = {
            "email": user_email,
            "contact_number": user_contact_number,
            "uuid": user_uuid,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, "LVB97M-lKA1-bGcwNLRYXySuThn3pTYKZIN9CRYsBvY", algorithm="HS256")
        print(token)

        headers = {
            "Authorization": f"auth {token}",
            "Content-Type": "application/json"
        }



class ActionRunGoogleReceiptDetection(Action):
    def name(self) -> Text:
        return "action_check_google_receipt"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        vision_client = vision.ImageAnnotatorClient()
        image = vision.Image()
        user_message = tracker.latest_message.get("text", "")  # Get the latest user message text


        url_pattern = r'(https?://[^\s]+)'
        urls = re.findall(url_pattern, user_message)

        if urls:
            IMAGE_URI = urls[0]  # Take the first URL from the list
        else:
            dispatcher.utter_message("I couldn't find a URL in your message.")
            return []



        image.source.image_uri = IMAGE_URI

        response = vision_client.text_detection(image=image)

        text = response.text_annotations[0].description

        print(extract_subscription_details(text))
        dispatcher.utter_message("thanks")
        return []

def extract_subscription_details(text):
    details = {}

    # Extract trial end date
    trial_end_match = re.search(r"trial will end on (\d{1,2} \w+ \d{4}, \d{1,2}:\d{2} [ap]m GMT[+-]\d{1,2}:\d{2})", text)
    details["trial_end"] = trial_end_match.group(1) if trial_end_match else "Not found"

    # Extract order number
    order_number_match = re.search(r"Order number: (GPA\.\d{4}-\d{4}-\d{4}-\d{5})", text)
    details["order_number"] = order_number_match.group(1) if order_number_match else "Not found"

    order_date_match = re.search(r"Order date: (\d{1,2} \w+ \d{4})", text)
    if order_date_match:
        raw_date = order_date_match.group(1)  # Example: "14 Feb 2025"
        parsed_date = datetime.strptime(raw_date, "%d %b %Y")  # Parse the date
        formatted_date = parsed_date.strftime("%Y/%m/%d")  # Convert to yyyy/MM/dd
        details["premium_start_date"] = formatted_date
    else:
        details["premium_start_date"] = "Not found"

    # Extract user email
    email_match = re.search(r"Your account: ([\w\.-]+@[\w\.-]+)", text)
    details["email"] = email_match.group(1) if email_match else "Not found"

    # Extract subscription type (without relying on 'Test' keyword)
    subscription_match = re.search(r"Item\n(.+?)\nAuto-renewing subscription", text, re.DOTALL)

    subscription_type =   (subscription_match.group(1).strip()) if subscription_match else "Not found"
    details["subscription_type"] = subscription_type

    if "Annual" in subscription_type:
        details["plan_type"] = "yearly"
    elif "6 month" in subscription_type:
        details["plan_type"] = "halfyearly"
    elif "Monthly" in subscription_type:
        details["plan_type"] = "monthly"

    price_match = re.search(r"Total:\s*([^\d\s]+)([\d.,]+)", text)
    if price_match:
        details["currency"] = price_match.group(1)  # Extract currency symbol (e.g., ₹, $, €)
        details["amount"] = int(float(price_match.group(2).replace(",", "")))  # Convert amount to int
    else:
        details["currency"] = "Not found"
        details["amount"] = 0

    # Extract payment method
    payment_match = re.search(r"Payment method:\n(.+)", text)
    details["payment_method"] = "Google Play"
    details["device_type"] = "1"

    return details

class ActionCheckSubscription(Action):
    def name(self) -> Text:
        return "action_check_subscription"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_email = tracker.get_slot("email")
        user_contact_number = tracker.get_slot("number")
        user_uuid = tracker.get_slot("uuid")
        api_url = f"https://level-core-backend.api.level.game/v1/checkForSubscription"
        payload = {
            "email": user_email,
            "contact_number": user_contact_number,
            "uuid": user_uuid,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        token = jwt.encode(payload, "LVB97M-lKA1-bGcwNLRYXySuThn3pTYKZIN9CRYsBvY", algorithm="HS256")
        print(token)

        headers = {
            "Authorization": f"auth {token}",
            "Content-Type": "application/json"
        }

        # Make the GET request with headers
        response = requests.get(api_url, headers=headers)
        print(response.json())
        if not user_email:
            dispatcher.utter_message(text="I couldn't find your email. Could you please provide it?")
            return []

        if response.status_code == 200:
            data = response.json()

            # Check if subscription exists
            if data.get("id") == 1 and "data" in data and len(data["data"]) > 0:
                subscription = data["data"][0]  # Get the first subscription record


                premium_ends_on = subscription.get("premium_ends_on", "unknown date")
                plan_type = subscription.get("plan_type", "a premium")

                # Structuring the reply message
                dispatcher.utter_message(
                    text=f"Your {plan_type} premium subscription is active until {premium_ends_on}. "
                         "Try logging out and logging in again if you face issues."
                )
            else:
                dispatcher.utter_message(
                    text="It looks like you don't have an active premium subscription. Would you like help with purchasing?"
                )
        else:
            dispatcher.utter_message(text="There was an issue checking your subscription. Please try again later.")



        return []


class ActionExtractCourse(Action):
    def name(self) -> Text:
        return "action_extract_course"

    def extract_course_name(self, text: Text) -> Text:
        # List of known courses (update as needed)
        courses = [
            "overthink session", "spirituality pack", "stress relief course",
            "beginners meditation", "rajarshi nandi course"
        ]

        for course in courses:
            if re.search(rf"\b{re.escape(course)}\b", text, re.IGNORECASE):
                return course

        return None

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text", "")
        course_name = self.extract_course_name(user_message)

        if course_name:
            return [{"event": "slot", "name": "course_name", "value": course_name}]
        else:
            return [{"event": "slot", "name": "course_name", "value": None}]


class ActionHandleCourseIssue(Action):
    def name(self) -> Text:
        return "action_handle_course_issue"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        course_name = tracker.get_slot("course_name")

        if course_name:
            dispatcher.utter_message(text=f"I see you purchased the '{course_name}'. Let me check your access issue.")
        else:
            dispatcher.utter_message(text="I couldn't identify the course. Please specify the course name.")

        return []

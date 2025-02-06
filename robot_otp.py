import tkinter as tk
from tkinter import ttk
import time
import requests

class OTPVerifier:
    def __init__(self):
        self.current_otp = None
        self.current_delivery_id = None
        self.otp_window = None
        self.door_callback = None
        self.server_url = "http://192.168.0.217:5000/api/owner/deliveries"  # Replace with actual server URL

    def set_door_callback(self, callback):
        """Set the callback function for door control"""
        self.door_callback = callback

    def set_otp(self, otp, delivery_id):
        """Set new OTP and show verification window"""
        self.current_otp = otp
        self.current_delivery_id = delivery_id
        self.create_otp_window()

    def create_otp_window(self):
        """Create and show OTP verification window"""
        if self.otp_window is not None:
            self.otp_window.destroy()
        
        self.otp_window = tk.Tk()
        self.otp_window.title("Robot Door Control")
        self.otp_window.geometry("800x480")  # Common screen size for Jetson
        
        style = ttk.Style()
        style.configure("TEntry", padding=10, font=('Helvetica', 20))
        style.configure("TButton", padding=10, font=('Helvetica', 16))
        
        main_frame = ttk.Frame(self.otp_window, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(main_frame, text="Enter OTP", font=('Helvetica', 24)).grid(row=0, column=0, pady=20)
        
        otp_var = tk.StringVar()
        otp_entry = ttk.Entry(main_frame, textvariable=otp_var, font=('Helvetica', 32), width=10, justify='center')
        otp_entry.grid(row=1, column=0, pady=20)
        
        def verify_otp():
            entered_otp = otp_var.get()
            if entered_otp == self.current_otp:
                self.otp_window.destroy()
                self.otp_window = None
                
                # Call door control callback
                if self.door_callback:
                    self.door_callback("open")

                # Send OTP verification request to server
                self.notify_server_otp_verified()

                # Clear OTP after successful verification
                self.current_otp = None
                self.current_delivery_id = None
            else:
                ttk.Label(main_frame, text="Invalid OTP!", font=('Helvetica', 16), foreground='red').grid(row=3, column=0)
        
        ttk.Button(main_frame, text="Verify OTP", command=verify_otp).grid(row=2, column=0, pady=20)
        
        self.otp_window.mainloop()

    def notify_server_otp_verified(self):
        if not self.current_delivery_id:
            print("No delivery ID found for OTP verification")
            return

        # First, fetch ownerId from backend using deliveryId
        owner_id = self.get_owner_id(self.current_delivery_id)
        if not owner_id:
            print("Failed to retrieve ownerId")
            return

        url = f"{self.server_url}/{self.current_delivery_id}/verify-otp"
        payload = {
            "otp": self.current_otp,
            "ownerId": owner_id  # Correct ownerId from backend
        }

        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print("OTP verified and door opening notification sent to server.")
            else:
                print(f"Failed to verify OTP on server: {response.text}")
        except Exception as e:
            print(f"Error sending OTP verification request: {e}")

    def get_owner_id(self, delivery_id):
        """Fetch ownerId from backend using deliveryId"""
        try:
            url = f"{self.server_url}/{delivery_id}"  # API to get delivery details
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("ownerId")  # Extract ownerId from delivery data
            else:
                print(f"Error fetching ownerId: {response.text}")
                return None
        except Exception as e:
            print(f"Exception while fetching ownerId: {e}")
            return None


    def verify_delivery_id(self, delivery_id):
        """Verify if the delivery ID matches the current one"""
        return delivery_id == self.current_delivery_id

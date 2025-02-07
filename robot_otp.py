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
        self.server_url = "http://192.168.0.217:5000/api/owner/deliveries"

    def set_door_callback(self, callback):
        self.door_callback = callback

    def set_otp(self, otp, delivery_id):
        self.current_otp = otp
        self.current_delivery_id = delivery_id
        self.create_otp_window()

    def create_otp_window(self):
        if self.otp_window is not None:
            self.otp_window.destroy()
        
        self.otp_window = tk.Tk()
        self.otp_window.title("Robot Door Control")
        self.otp_window.geometry("800x480")
        self.otp_window.configure(bg='#f0f2f5')
        
        # Configure styles
        style = ttk.Style()
        style.configure("NumPad.TButton", 
                       font=('Helvetica', 24, 'bold'),
                       padding=20,
                       width=4)
        style.configure("Action.TButton",
                       font=('Helvetica', 20),
                       padding=15,
                       width=8)
        style.configure("Display.TLabel",
                       font=('Helvetica', 36),
                       background='#f0f2f5')
        style.configure("Title.TLabel",
                       font=('Helvetica', 28, 'bold'),
                       background='#f0f2f5')
        style.configure("Error.TLabel",
                       font=('Helvetica', 16),
                       foreground='#dc2626',
                       background='#f0f2f5')

        # Main container
        main_frame = ttk.Frame(self.otp_window, padding="20", style="Main.TFrame")
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title
        ttk.Label(main_frame, 
                 text="Enter Security Code", 
                 style="Title.TLabel").grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # OTP display
        self.otp_var = tk.StringVar()
        self.otp_display = ttk.Label(main_frame, 
                                   textvariable=self.otp_var,
                                   style="Display.TLabel",
                                   width=8)
        self.otp_display.grid(row=1, column=0, columnspan=3, pady=(0, 30))

        # Error message label
        self.error_label = ttk.Label(main_frame, text="", style="Error.TLabel")
        self.error_label.grid(row=2, column=0, columnspan=3)

        # Number pad frame
        numpad_frame = ttk.Frame(main_frame)
        numpad_frame.grid(row=3, column=0, columnspan=3, pady=10)

        # Create number pad
        numbers = [
            ['1', '2', '3'],
            ['4', '5', '6'],
            ['7', '8', '9'],
            ['C', '0', '?']
        ]

        for i, row in enumerate(numbers):
            for j, num in enumerate(row):
                btn = ttk.Button(numpad_frame,
                               text=num,
                               style="NumPad.TButton",
                               command=lambda x=num: self.handle_button(x))
                btn.grid(row=i, column=j, padx=5, pady=5)

        # Verify button
        verify_btn = ttk.Button(main_frame,
                              text="Verify",
                              style="Action.TButton",
                              command=self.verify_otp)
        verify_btn.grid(row=4, column=0, columnspan=3, pady=(20, 0))

        self.otp_window.mainloop()

    def handle_button(self, value):
        current = self.otp_var.get()
        
        if value == '?':  # Backspace
            self.otp_var.set(current[:-1])
        elif value == 'C':  # Clear
            self.otp_var.set('')
        elif len(current) < 6:  # Limit to 6 digits
            self.otp_var.set(current + value)
        
        # Clear any error message
        self.error_label.config(text="")

    def verify_otp(self):
        entered_otp = self.otp_var.get()
        if entered_otp == self.current_otp:
            self.otp_window.destroy()
            self.otp_window = None
            
            if self.door_callback:
                self.door_callback("open")

            self.notify_server_otp_verified()
            self.current_otp = None
            self.current_delivery_id = None
        else:
            self.error_label.config(text="Invalid security code. Please try again.")
            self.otp_var.set('')  # Clear the input

    def notify_server_otp_verified(self):
        if not self.current_delivery_id:
            print("No delivery ID found for OTP verification")
            return

        owner_id = self.get_owner_id(self.current_delivery_id)
        if not owner_id:
            print("Failed to retrieve ownerId")
            return

        url = f"{self.server_url}/{self.current_delivery_id}/verify-otp"
        payload = {
            "otp": self.current_otp,
            "ownerId": owner_id
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
        try:
            url = f"{self.server_url}/{delivery_id}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("ownerId")
            else:
                print(f"Error fetching ownerId: {response.text}")
                return None
        except Exception as e:
            print(f"Exception while fetching ownerId: {e}")
            return None

    def verify_delivery_id(self, delivery_id):
        return delivery_id == self.current_delivery_id

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
        window_width = 800
        window_height = 450
        screen_width = self.otp_window.winfo_screenwidth()
        self.otp_window.overrideredirect(True)
        screen_height = self.otp_window.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.otp_window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.otp_window.configure(bg='#000000')
        
        # Configure styles
        main_frame = tk.Frame(self.otp_window, bg='#000000', padx=40, pady=40)
        main_frame.pack(expand=True, fill='both')
        
        # PIN display
        self.pin = ""
        self.pin_var = tk.StringVar()
        self.error_label= ""
        
        # Create and configure display frame
        display_frame = tk.Frame(main_frame, bg='#000000')
        display_frame.pack(fill='x', pady=(0, 20))
        
        # PIN entry display - make it wider and more prominent
        self.pin_entry = tk.Entry(
            display_frame,
            textvariable=self.pin_var,
            show='?',
            font=('Arial', 32),
            bg='white',
            relief='flat',
            justify='center'
        )
        self.pin_entry.pack(fill='x', ipady=15)
        
        # Create keypad frame
        keypad_frame = tk.Frame(main_frame, bg='#000000')
        keypad_frame.pack(expand=True, fill='both')
        
        # Configure grid with more spacing
        for i in range(4):
            keypad_frame.grid_rowconfigure(i, weight=1)
        for i in range(3):
            keypad_frame.grid_columnconfigure(i, weight=1)
        
        # Create number buttons with updated styling
        numbers = [
            ['1', '2', '3'],
            ['4', '5', '6'],
            ['7', '8', '9'],
            ['X', '0', '>']
        ]
        
        for i, row in enumerate(numbers):
            for j, num in enumerate(row):
                # Common button properties with enhanced styling
                button_props = {
                    'font': ('Arial', 36, 'bold'),
                    'bg': '#000000',
                    'activebackground': '#333333',
                    'activeforeground': 'white',
                    'relief': 'flat',
                    'borderwidth': 0,
                    'width': 4,
                    'height': 1,
                    'text': num,
                    'cursor': 'hand2'  # Hand cursor on hover
                }
                
                if num == 'X':
                    button_props['fg'] = '#ff0000'  # Bright red
                    button_props['command'] = self.clear
                elif num == '>':
                    button_props['fg'] = '#00ff00'  # Bright green
                    button_props['command'] = self.verify_otp
                else:
                    button_props['fg'] = 'white'
                    button_props['command'] = lambda n=num: self.handle_button(n)
                
                btn = tk.Button(keypad_frame, **button_props)
                
                # Add hover effect
                btn.bind('<Enter>', lambda e, b=btn: b.configure(bg='#333333'))
                btn.bind('<Leave>', lambda e, b=btn: b.configure(bg='#000000'))
                
                # Grid with more spacing
                btn.grid(row=i, column=j, padx=10, pady=10, sticky='nsew')
                
                # Add separator lines
                if j < 2:  # Vertical lines
                    separator = tk.Frame(keypad_frame, width=1, bg='#ffffff')
                    separator.grid(row=i, column=j, sticky='nse', padx=(0, 0), pady=10)
                if i < 3:  # Horizontal lines
                    separator = tk.Frame(keypad_frame, height=1, bg='#ffffff')
                    separator.grid(row=i, column=j, sticky='sew', padx=10, pady=(0, 0))
                    
        

        self.otp_window.mainloop()

    def handle_button(self, number):
        if len(self.pin) < 4:
            self.pin += number
            self.pin_var.set(self.pin)
        
        # Clear any error message
        self.error_label.config(text="")
    def clear(self):
        self.pin = ""
        self.pin_var.set("")

    def verify_otp(self):
        entered_otp = self.pin_var.get()
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
            self.pin_var.set('')  # Clear the input

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

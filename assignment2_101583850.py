"""
Author: Lisandro Vasquez Matre
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""

# Import the required modules (Step ii)
# socket, threading, sqlite3, os, platform, datetime
import socket 
import threading
import sqlite3
import os
import platform
import datetime


# Print Python version and OS name (Step iii)
pyVersion = platform.python_version()
osName = platform.system()
print (f"The Python version is: {pyVersion}")
print (f"The operating System's name is: {osName}")

# Create the common_ports dictionary (Step iv)
# Add a 1-line comment above it explaining what it stores

# This is a Dictionary which stores common port integers as keys with the asscociated type of Port it is commonly used for in strings
commonPorts = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    3306: "MySQL",
    3389: "RDP",
    8080: "HTTP-Alt"
}

# Create the NetworkTool parent class (Step v)
# - Constructor: takes target, stores as private self.__target
# - @property getter for target
# - @target.setter with empty string validation
# - Destructor: prints "NetworkTool instance destroyed"

class NetworkTool:
    def __init__(self, target:str):
        self.__target = target
    
    @property
    def target(self):
        return self.__target
    
    @target.setter
    def target(self, value:str):
        if value!="":
            self.__target = value
        else:
            print("Value cannot be empty")

    def __del__(self):
        print ("NetworkTool instance destroyed")

# Q3: What is the benefit of using @property and @target.setter?

# The benefit of using @property and @target.setter is it allows you to better encapsulate the private variable in the NetworkTool 
# by limiting access, as well as regulating the inputs into the variables 


# Q1: How does PortScanner reuse code from NetworkTool?

    # By using the inheritence to add onto the __init__ and __del__ functions as well as using super(). to 
    # access and modify the target variable
#

# Create the PortScanner child class that inherits from NetworkTool (Step vi)
# - Constructor: call super().__init__(target), initialize self.scan_results = [], self.lock = threading.Lock()
# - Destructor: print "PortScanner instance destroyed", call super().__del__()

class PortScanner(NetworkTool):
    def __init__(self, target: str):
        super().__init__(target)
        self.scan_results = []
        self.lock = threading.Lock() 
    
    def __del__(self):
        print("PortScanner instance destroyed.")
        super().__del__()

    def scan_port(self, port):
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.target, port))
            service_name = commonPorts.get (port, "unknown")
            if (result == 0):
                status = "Open"
            else:
                status = "Close"
            with self.lock:
                self.scan_results.append ((port, status, service_name))

        except socket.error as e:
            print (f"Error scanning port {port}: {e}")
        
        finally:
            sock.close()

# - scan_port(self, port):
#     Q4: What would happen without try-except here?

# If I tried to do scan_port without a try-except it could cause the entire program to crash is the port being scanned does not exist.
# By adding a try-except it allows the scanner to continue running without crashing the program while also accounting for exceptions.

#     - try-except with socket operations
#     - Create socket, set timeout, connect_ex
#     - Determine Open/Closed status
#     - Look up service name from common_ports (use "Unknown" if not found)
#     - Acquire lock, append (port, status, service_name) tuple, release lock
#     - Close socket in finally block
#     - Catch socket.error, print error message

    def get_open_ports(self):
        return [result for result in self.scan_results if result[1] == "Open"]

# - get_open_ports(self):
#     - Use list comprehension to return only "Open" results
#
#     Q2: Why do we use threading instead of scanning one port at a time?

# We use threading instead of individually scanning one port at a time because it allows us to check multiple ports at the same time
# instead of checking each one individually, which would take more time compared to threading.

    def scan_range(self, start_port, end_port):
        threads = []
        for port in range(start_port, end_port):
            thread = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

# - scan_range(self, start_port, end_port):
#     - Create threads list
#     - Create Thread for each port targeting scan_port
#     - Start all threads (one loop)
#     - Join all threads (separate loop)

    def save_results(self, target, results):
        try:
            conn = sqlite3.connect("scan_history.db")
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT,
                port INTEGER,
                status TEXT,
                service TEXT,
                scan_date TEXT)"""
            )
            scan_date = str(datetime.datetime.now())

            for port, status, service in results:
                cursor.execute("""
                    INSERT INTO scans (target, port, status, service, scan_date)
                    VALUES (?, ?, ?, ?, ?)""", (target, port, status, service, scan_date)
                    )
            conn.commit()
            conn.close( )
            print(f"Succesfully saved Results into Scan_history.db")
        except sqlite3.Error as e:
            print(f"Error Saving Results: {e}")

# Create save_results(target, results) function (Step vii)
# - Connect to scan_history.db
# - CREATE TABLE IF NOT EXISTS scans (id, target, port, status, service, scan_date)
# - INSERT each result with datetime.datetime.now()
# - Commit, close
# - Wrap in try-except for sqlite3.Error

    def load_past_scans(self):
        conn = None
        try:
            conn = sqlite3.connect("scan_history.db")
            cursor = conn.cursor()

            cursor.execute("""SELECT * FROM scans """)
            rows = cursor.fetchall()
        # Result order: ID INTEGER, target TEXT,port INTEGER,status TEXT,service TEXT,scan_date TEXT
            if not rows:
                print("No past scans found.")
            else:
                print("Target IP | Port | Status | Service | Scan date")
                for row in rows:
                    print (f"{row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
        except sqlite3.InterfaceError as e:
            print("No past scans found.")
        except sqlite3.Error as e:
            print(f"Error loading past scans: {e}")
        finally:
            conn.commit()
            conn.close()

# Create load_past_scans() function (Step viii)
# - Connect to scan_history.db
# - SELECT all from scans
# - Print each row in readable format
# - Handle missing table/db: print "No past scans found."
# - Close connection


# ============================================================
# MAIN PROGRAM
# ============================================================
if __name__ == "__main__":
    try:
        target_ip = input("Enter a target IP address (default 127.0.0.1): ").strip()
        if not target_ip:
            target_ip = "127.0.0.1"

        while True:
            try:
                start_port = int(input("Enter a starting port from 1-1024: "))
                end_port = int(input(f"Enter an ending port from 1-1024: "))

                if not (1 <= start_port <= 1024 and 1 <= end_port <= 1024):
                    print("Port must be between 1 and 1024.")
                    continue

                if end_port < start_port:
                    print("End port must be greater than or equal to start port.")
                    continue
            
                break 
            except ValueError:
                print("Invalid input. Please enter a valid integer.")

# Create a PortScanner object with the target IP
        scanner = PortScanner(target_ip)

# Print: "Scanning {target} from port {start} to {end}..."
        print(f"\nScanning {target_ip} from port {start_port} to {end_port}...")

# Call scan_range(start_port, end_port)
        scanner.scan_range(start_port, end_port)

# Call get_open_ports() and print each open port with its service name, for example: 
        open_ports = scanner.get_open_ports()

# --- Scan Results for 127.0.0.1 ---
# Port 22: Open (SSH)
# Port 80: Open (HTTP)
# Port 443: Open (HTTPS)
# ------
# Total open ports found: 3
        print(f"\n--- Scan Results for {target_ip} ---")
        if not open_ports:
            print("No open ports found.")
        else:
            for port, status, service in open_ports:
                print(f"Port {port}: {status} ({service})")
        print("------")
        print(f"\nTotal open ports found: {len(open_ports)}")

# Call save_results() to save the results to the database
        scanner.save_results(target_ip, scanner.scan_results)

# Ask the user: "Would you like to see past scan history? (yes/no): "
# If the user enters "yes", call load_past_scans()       
        view_history = input("\nWould you like to see past scan history? (yes/no): ").lower()
        if view_history == "yes":
            scanner.load_past_scans()

    except KeyboardInterrupt:
        print("\nScan cancelled by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    # Get user input with try-except (Step ix)
    # - Target IP (default "127.0.0.1" if empty)
    # - Start port (1-1024)
    # - End port (1-1024, >= start port)
    # - Catch ValueError: "Invalid input. Please enter a valid integer."
    # - Range check: "Port must be between 1 and 1024."

    # After valid input (Step x)
    # - Create PortScanner object
    # - Print "Scanning {target} from port {start} to {end}..."
    # - Call scan_range()
    # - Call get_open_ports() and print results
    # - Print total open ports found
    # - Call save_results()
    # - Ask "Would you like to see past scan history? (yes/no): "
    # - If "yes", call load_past_scans()


# Q5: New Feature Proposal
# TODO: Your 2-3 sentence description here... (Part 2, Q5)
# Diagram: See diagram_studentID.png in the repository root

# A new Feature that could be added to this Program is a menu interface. Currently the entire program works as a single string but if 
# the ports have already been scanned you will always need to rescan a group, and add it to the SQLite database. But by adding a menu 
# a user would be able to check the database without going through the entire program first. 
import socket
import json
import time
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345

def read_parameters_from_file(file_path):
    """
    Reads the message parameters from a file.
    """
    with open(file_path, 'r') as file:
        data = file.read()
    parameters = {}
    for line in data.splitlines():
        key, value = line.split(':', 1)
        parameters[key.strip()] = value.strip().strip('"')
    return parameters

def send_message_with_boundary(client_socket, message_number, message_data):
    """
    Sends a message with a number and a 4-byte length prefix.
    """
    message = f"{message_number}:{message_data}"
    message_bytes = message.encode('utf-8')
    message_length = len(message_bytes)
    length_prefix = f"{message_length:04}".encode('utf-8')
    client_socket.send(length_prefix + message_bytes)

def start_client():
    """
    Implements the sliding window protocol on the client side.
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))

    # Get parameters from user or file
    source = input("Enter 'file' to read parameters from a file or 'input' to provide manually: ").strip().lower()
    if source == 'file':
        file_path = input("Enter the file path: ").strip()
        params = read_parameters_from_file(file_path)
        message = params['message']
        max_size = int(params['maximum_msg_size'])
        window_size = int(params['window_size'])
        timeout = int(params['timeout'])
    else:
        message = input("Enter the message: ").strip()
        max_size = int(input("Enter the maximum message size: ").strip())
        window_size = int(input("Enter the sliding window size: ").strip())
        timeout = int(input("Enter the timeout in seconds: ").strip())

    # Request the max message size from the server
    client_socket.send("MAX_SIZE_REQUEST".encode('utf-8'))
    max_size_response = client_socket.recv(1024).decode('utf-8')
    print(f"Max message size from server is: {max_size_response} bytes")

    max_size = min(max_size, int(max_size_response))  # Adjust to server's max size
    print(f"Adjusted maximum message size: {max_size} bytes")

    # Send the sliding window size to the server
    client_socket.send(f"WINDOW_SIZE:{window_size}".encode('utf-8'))

    # Define the message to be sent
    # Comment left unchanged to preserve your original notes
    message_parts = [message[i:i + max_size] for i in range(0, len(message), max_size)]
    print(f"Message chunks: {message_parts}")

    # Initialize the sliding window
    unacknowledged = 0  # First unacknowledged message
    next_to_send = 0    # Next message to send
    total_messages = len(message_parts)

    ack_buffer = ""  # Buffer to store received ACKs

    while unacknowledged < total_messages:
        # Send messages within the window
        while next_to_send < unacknowledged + window_size and next_to_send < total_messages:
            send_message_with_boundary(client_socket, next_to_send, message_parts[next_to_send])
            print(f"Sent message {next_to_send}: {message_parts[next_to_send]}")
            next_to_send += 1
        time.sleep(5)
        try:
            # Wait for ACK responses with a timeout only if there are unacknowledged messages
            client_socket.settimeout(timeout)
            ack_response = client_socket.recv(1024).decode('utf-8')
            ack_buffer += ack_response  # Add the received ACKs to the buffer

            # Process all ACKs in the buffer
            while "ACK" in ack_buffer:
                ack_index = ack_buffer.find("ACK")  # Find the next ACK
                try:
                    # Extract the number starting after "ACK"
                    start_index = ack_index + 3
                    end_index = start_index
                    while end_index < len(ack_buffer) and ack_buffer[end_index].isdigit():
                        end_index += 1
                    ack_number = int(ack_buffer[start_index:end_index])  # Extract multi-digit ACK number
                    print(f"Server acknowledged up to message {ack_number}")
                    unacknowledged = max(unacknowledged, ack_number + 1)  # Slide the window
                    ack_buffer = ack_buffer[end_index:]  # Remove processed ACK from buffer
                except ValueError:
                    break  # Wait for more data if the ACK is incomplete

            # Reset the timeout when all ACKs are processed
            if unacknowledged == total_messages:
                client_socket.settimeout(None)

        except socket.timeout:
            print("Timeout occurred, resending unacknowledged messages...")
            # Resend all unacknowledged messages
            for i in range(unacknowledged, next_to_send):
                send_message_with_boundary(client_socket, i, message_parts[i])
                print(f"Resent message {i}: {message_parts[i]}")

    print("All messages sent and acknowledged!")
    client_socket.close()

if __name__ == "__main__":
    start_client()

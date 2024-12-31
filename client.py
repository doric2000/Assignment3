import socket

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345

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

    # Request the max message size from the server
    client_socket.send("MAX_SIZE_REQUEST".encode('utf-8'))
    max_size_response = client_socket.recv(1024).decode('utf-8')
    print(f"Max message size is: {max_size_response} bytes")
    max_size = int(max_size_response)

    # Ask the user for the sliding window size
    window_size = int(input("Please Insert the sliding window size: "))
    print(f"Sliding window size: {window_size}")
    # Send the sliding window size to the server
    client_socket.send(f"WINDOW_SIZE:{window_size}".encode('utf-8'))

    # Define the message to be sent
    message = "my name is dor hagever and i am an akbar akbar akbar gever"
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

        # Wait for ACK responses
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

    print("All messages sent and acknowledged!")
    client_socket.close()


if __name__ == "__main__":
    start_client()

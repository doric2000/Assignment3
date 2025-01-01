import socket
import time
# setting variables for the Server's IP and port.
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345


def recv_message_with_boundary(client_socket):
    """
    Reads a message with a 4-byte length prefix.
    """
    try:
        length_prefix = client_socket.recv(4).decode('utf-8')
        if not length_prefix:
            return None  # Connection closed
        message_length = int(length_prefix)
        # Read the exact number of bytes for the message
        message = client_socket.recv(message_length).decode('utf-8')
        return message
    except ValueError:
        print("Error: Received an invalid message length prefix.")
        return None

def start_server():
    """
    Starts the server and implements sliding window logic.
    """
    # Creating a socket.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Binding the socket to the address and the port of the server
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(2)  # a queue of 2 requests for any case

    print(f"Server is listening on {SERVER_HOST}:{SERVER_PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Connection from {client_address} has been established.")

        # Getting the request from the client for the max-message-size
        data = client_socket.recv(1024).decode('utf-8')
        if data.startswith("MAX_SIZE_REQUEST"):
            max_size = 10  # Example maximum size
            client_socket.send(str(max_size).encode('utf-8'))

        # Receive the sliding window size from the client
        data = client_socket.recv(1024).decode('utf-8')
        if data.startswith("WINDOW_SIZE:"):
            window_size = int(data.split(":")[1])
            print(f"Sliding window size received: {window_size}")

        received_messages = {}  # Stores out-of-order messages
        highest_contiguous_ack = -1  # Tracks the highest sequentially received message

        while True:
            data = recv_message_with_boundary(client_socket)
            if not data:
                break  # End the loop and finish the connection

            print(f"Received: {data}")
            try:
                # Extract the message number and data
                message_number, message_data = data.split(":", 1)
                message_number = int(message_number)
            except ValueError:
                print("Error parsing message.")
                continue

            if message_number == highest_contiguous_ack + 1:
                # Correct order, update highest_contiguous_ack
                print(f"Message {message_number} arrived in the correct order: {message_data}")
                highest_contiguous_ack = message_number

                # Check for any buffered messages that can now be acknowledged
                while highest_contiguous_ack + 1 in received_messages:
                    highest_contiguous_ack += 1
                    print(f"Adding buffered message {highest_contiguous_ack}: {received_messages.pop(highest_contiguous_ack)}")
                    # Send updated ACK
                    ack_message = f"ACK{highest_contiguous_ack}"
                    client_socket.send(ack_message.encode('utf-8'))
                    print(f"Sent: {ack_message}")
            else:
                # Out of order, store the message
                print(f"Message {message_number} out of order, storing: {message_data}")
                received_messages[message_number] = message_data

                # Resend the last valid ACK
                ack_message = f"ACK{highest_contiguous_ack}"
                client_socket.send(ack_message.encode('utf-8'))
                print(f"Resent: {ack_message}")



        print("Connection closed.")
        client_socket.close()

if __name__ == "__main__":
    start_server()
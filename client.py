import socket
# setting variables for the Clients's ip and port.
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 1234

#create a func that will send each time the mmessage with the already known max size after getting it.
def send_message_with_boundary(client_socket, message_number, message_data):
    message = f"{message_number}:{message_data}"
    message_bytes = message.encode('utf-8')
    message_length = len(message_bytes)
    # Create a 4-byte length prefix
    length_prefix = f"{message_length:04}".encode('utf-8')
    # Send the length prefix followed by the actual message
    client_socket.send(length_prefix + message_bytes)

def start_client():
# creating a socket and connecting to the sever

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST,SERVER_PORT))

# asking to get the max message size from the server.

    client_socket.send("MAX_SIZE_REQUEST".encode('utf-8'))
    max_size_response = client_socket.recv(1024).decode('utf-8')
    print(f"Max message size is : {max_size_response} bytes")
    max_size = int(max_size_response)

#Asking from the user to enter the sliding window size:
    window_size = int(input("Please Insert the sliding window size: "))
    print(f"Sliding window size: {window_size}")


    message = "my name is dor hagever and i am an akbar akbar akbar gever"

# splitting the message to parts according to max size:
    message_parts = [message[i:i+max_size] for i in range (0, len(message),max_size)]
    print(f"Message chunks: {message_parts}")

    # printing our messages by the partition that we were given. DEBUG
    # for index, segment in enumerate(message_parts):
    #     print(f"Message {index}: {segment}")

#now we will have to create a loop that sends the messages and checks if ACKS
# are being received relating to the window side and the max size of a message.
# using the func enumerate that returns a tuple of (index,message) part from our list of messages.
    unacknowledged = 0  # first unacknowledged message
    while unacknowledged < len(message_parts):
        for i in range(unacknowledged, min(unacknowledged + window_size, len(message_parts))):
            send_message_with_boundary(client_socket, i, message_parts[i])
            print(f"Sent message {i}: {message_parts[i]}")

        # Wait for ACK
        ack_response = client_socket.recv(1024).decode('utf-8')
        print(f"Received: {ack_response}")

        if ack_response.startswith("ACK"):
            ack_number = int(ack_response[3:])
            print(f"Server acknowledged up to message {ack_number}")
            unacknowledged = ack_number + 1

#understand how to work with chunks..
if __name__ == "__main__":
    start_client()
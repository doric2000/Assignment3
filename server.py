import socket
import time
# setting variables for the Server's ip and port.
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345
#window_size=0

def recv_message_with_boundary(client_socket):
    length_prefix = client_socket.recv(4).decode('utf-8')
    if not length_prefix:
        return None  # Connection closed
    message_length = int(length_prefix)
    # Read the exact number of bytes for the message
    message = client_socket.recv(message_length).decode('utf-8')
    return message



def start_server():
    # creating a socket.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # binding the socket to the address and the port of the server
    # and make it listen until a request to connect will arrive
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(2) #a queue of 2 requests for any case

    print(f"Server is listening on {SERVER_HOST}:{SERVER_PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Connection from {client_address} has been established.")

        # getting the request from the client with the max-message-size ;
        data = client_socket.recv(1024).decode('utf-8')
        if data.startswith("MAX_SIZE_REQUEST"):
            # than send the message max size back
            max_size = 10  # a.e 400 bytes.
            client_socket.send(str(max_size).encode('utf-8'))

        # Receive the sliding window size from the client
        data = client_socket.recv(1024).decode('utf-8')
        if data.startswith("WINDOW_SIZE:"):
            window_size = int(data.split(":")[1])
            print(f"Sliding window size received: {window_size}")

        #a temporal list that will save all the messages that haven't been arrived in the correct order.
        received_messages = {}
        #now we will have to track the messages that arrive by numbering the next expected message
        expected_msg_num = 0
        #count the sequence number of the highest row of acks that we have got.
        highest_contiguous_ack = -1
        # Keep track of the number of messages received in the current window
        messages_received_in_window = 0
        #keep getting messages:
        while True:
            data = recv_message_with_boundary(client_socket)
            if not data:
                break #end the loop and finish the connection.

            #printing each message arriving

            print(f"Received: {data}")

            #get into a variable the number of the msg and the data separate to track them.
            try:
                # Split only at the first occurrence of ":" to prevent future bugs (if our message contains ":" for example)
                message_number, message_data = data.split(":", 1)
                # Convert message_number to an integer
                message_number = int(message_number)
            except ValueError as e:
                print(f"Error parsing message: {e}")
                continue

            # Check if this is the message that we are expecting to get.
            if message_number == highest_contiguous_ack + 1:
                print(f"Message {message_number} arrived in the correct order: {message_data}")
                highest_contiguous_ack += 1
                messages_received_in_window += 1
                # Now , when we have got the message we were expecting to , we have to check if the next messages have
                # already arrived before (can be because packet loos) and update our highest_contiguous_ack to update our server that he already received them
                #And it should keep checking from the last one received
                while highest_contiguous_ack + 1 in received_messages:
                    highest_contiguous_ack += 1
                    messages_received_in_window += 1
                    print(
                        f"Adding early messages: {highest_contiguous_ack}: {received_messages[highest_contiguous_ack]}")
                    del received_messages[highest_contiguous_ack] #deleting the message that has been added.
            # message get but not in order , so we have to store it until we will get the messages before it in order.
            else:
                print(f"Message {message_number} not in order,storing the message: {message_data}")
                received_messages[message_number] = message_data

            # Send ACK only after receiving `window_size` messages or all messages
            if messages_received_in_window == window_size or highest_contiguous_ack == len(received_messages) - 1:
                ack_message = f"ACK{highest_contiguous_ack}"
                try:
                    client_socket.send(ack_message.encode('utf-8'))
                    print(f"Sent: {ack_message}")
                    messages_received_in_window = 0  # Reset the count for the next window
                except BrokenPipeError:
                    print("Client disconnected. Closing connection.")
                    break
                except ConnectionResetError:
                    print("Connection reset by client. Closing connection.")
                    break

        client_socket.close()



if __name__ == "__main__":
    start_server()
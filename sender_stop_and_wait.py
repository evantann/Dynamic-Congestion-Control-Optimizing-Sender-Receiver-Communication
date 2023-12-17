import socket
import time

# total packet size
PACKET_SIZE = 1024
# bytes reserved for sequence id
SEQ_ID_SIZE = 4
# bytes available for message
MESSAGE_SIZE = PACKET_SIZE - SEQ_ID_SIZE

# read data
with open('/Users/evant/Documents/ECS 152A/congestion_control_ecs152a-main/docker/file.mp3', 'rb') as f:
    data = f.read()

# create a udp socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:

    start_time = time.time()

    # bind the socket to a OS port
    udp_socket.bind(("localhost", 5000))
    udp_socket.settimeout(1)

    # start sending data from 0th sequence
    seq_id = 0

    packet_delay = 0
    transmission_count = 0
    while seq_id < len(data):
        # construct message
        # sequence id of length SEQ_ID_SIZE + message of remaining PACKET_SIZE - SEQ_ID_SIZE bytes
        message = int.to_bytes(seq_id, SEQ_ID_SIZE, signed=True, byteorder='big') + data[seq_id: seq_id + MESSAGE_SIZE]
        # send message out
        udp_socket.sendto(message, ('localhost', 5001))
        start_delay = time.time()

        # wait for acknowledgment
        while True:
            try:
                # wait for ack
                ack, _ = udp_socket.recvfrom(PACKET_SIZE)
                end_delay = time.time()

                transmission_count += 1

                per_packet_delay = end_delay - start_delay
                packet_delay += per_packet_delay

                # extract ack id
                ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')

                seq_id += MESSAGE_SIZE

                # ack id == sequence id, move on
                if ack_id == seq_id:
                    break
                if ack_id == len(data):
                    break
            except socket.timeout:
                # no ack, resend message
                udp_socket.sendto(message, ('localhost', 5001))

        # move sequence id forward

    # send final closing message
    final_message = int.to_bytes(len(data), SEQ_ID_SIZE, signed=True, byteorder='big') + b''
    udp_socket.sendto(final_message, ('localhost', 5001))

    # wait for acknowledgment for the final message
    while True:
        try:
            ack, _ = udp_socket.recvfrom(PACKET_SIZE)
            ack_id = int.from_bytes(ack[:SEQ_ID_SIZE], byteorder='big')

            # ack id == sequence id for the final message, move on
            if ack_id == len(data) + 3:
                end_time = time.time()
                break
        except socket.timeout:
            # no ack, resend final message
            udp_socket.sendto(final_message, ('localhost', 5001))

    # send '==FINACK==' to signal receiver to exit
    finack_message = int.to_bytes(seq_id + 1, SEQ_ID_SIZE, signed=True, byteorder='big') + b'==FINACK=='
    udp_socket.sendto(finack_message, ('localhost', 5001))

    time_elapsed = end_time - start_time
    throughput = len(data) / time_elapsed

    per_packet_delay = packet_delay / transmission_count

    performance_metric = throughput / per_packet_delay

    print(f"{round(throughput, 2)}, {round(per_packet_delay, 2)}, {round(performance_metric, 2)}")